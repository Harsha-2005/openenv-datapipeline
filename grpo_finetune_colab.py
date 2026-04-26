#!/usr/bin/env python3
"""
OpenEnv Data Pipeline Debugger — GRPO Fine-Tuning Script (v3 — Fixed Prompts)
==============================================================================
Run this on Google Colab (free T4 GPU, 16GB VRAM).

IMPORTANT: Before running this script:
  1. Go to Runtime → Restart runtime (to free GPU memory)
  2. Run:  !pip install unsloth trl accelerate datasets
  3. Then run this cell

Hardware: Colab T4 (free tier)
Model:    Qwen2.5-3B-Instruct (4-bit) → ~5GB VRAM (safe for T4)
Time:     ~30-45 minutes for 1 epoch
Cost:     $0 (Colab free tier)
"""

import os
import gc
import json
import torch

# === Step 0: VRAM optimization ===
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,max_split_size_mb:128"
torch.cuda.empty_cache()
gc.collect()
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

from unsloth import FastLanguageModel
from trl import GRPOConfig, GRPOTrainer
from datasets import Dataset

# === Step 1: Load model in 4-bit ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = "unsloth/Qwen2.5-3B-Instruct-unsloth-bnb-4bit",
    max_seq_length = 512,
    load_in_4bit   = True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r              = 8,
    target_modules = ["q_proj", "v_proj"],
    lora_alpha     = 16,
    lora_dropout   = 0,
    use_gradient_checkpointing = "unsloth",
)

torch.cuda.empty_cache()
gc.collect()
print(f"\nAfter model load — VRAM used: {torch.cuda.memory_allocated()/1e9:.2f} GB")

# === Step 2: Build CHAT-FORMATTED prompts ===
# The key fix: Qwen needs chat template format, not raw strings.
# We also include a few-shot example so the model knows the expected JSON format.

SYSTEM_MSG = """You are a data pipeline debugger. You MUST output ONLY a single JSON object.
No explanation, no markdown, no code fences. Raw JSON only.

Valid actions: inspect, cast_column, drop_nulls, fill_nulls, drop_duplicates,
filter_outliers, rename_column, reorder_stages, apply_business_rule, validate, submit

Example output: {"action_type": "cast_column", "column": "age", "value": "int"}
Example output: {"action_type": "fill_nulls", "column": "revenue", "value": "median"}
Example output: {"action_type": "drop_duplicates"}
Example output: {"action_type": "validate"}"""

TASK_PROMPTS = [
    # Easy
    "Step 1/10 | Task: task_easy_schema_fix\nSchema: age: object MISMATCH→int, revenue: object MISMATCH→float, name: object OK\nNulls: 5, Dups: 3\nOutput the JSON action to fix the first schema mismatch:",
    "Step 3/10 | Task: task_easy_schema_fix\nSchema: age: int OK, revenue: object MISMATCH→float\nNulls: 5, Dups: 3\nThe age column is fixed. Now fix the revenue column. Output JSON action:",
    "Step 5/10 | Task: task_easy_schema_fix\nSchema: age: int OK, revenue: float OK\nNulls: 5, Dups: 3\nAll schemas fixed. Now handle the null values. Output JSON action:",
    "Step 7/10 | Task: task_easy_schema_fix\nSchema: age: int OK, revenue: float OK\nNulls: 0, Dups: 3\nNulls handled. Now remove duplicates. Output JSON action:",
    "Step 9/10 | Task: task_easy_schema_fix\nAll issues fixed. Validate and submit. Output JSON action:",
    # Medium
    "Step 1/15 | Task: task_medium_data_quality\nSchema: quantity: object MISMATCH→int, unit_price: object MISMATCH→float\nNulls: 12, Dups: 5\nFix the quantity column type first. Output JSON action:",
    "Step 4/15 | Task: task_medium_data_quality\nSchema: quantity: int OK, unit_price: float OK\nNulls in region: 8, order_date: 4\nFill nulls in the region column. Output JSON action:",
    "Step 8/15 | Task: task_medium_data_quality\nNulls: 0, Dups: 5, Outliers in unit_price detected\nFilter outliers in unit_price. Output JSON action:",
    # Hard
    "Step 1/20 | Task: task_hard_pipeline_orchestration\nStage order: [load, transform, ingest, validate, enrich] — WRONG\nCorrect order is: ingest, validate, transform, enrich, load\nReorder the stages. Output JSON action:",
    "Step 5/20 | Task: task_hard_pipeline_orchestration\nStages reordered. Business rule discount_lte_1 not applied.\nApply the business rule. Output JSON action:",
    # Expert
    "Step 1/25 | Task: task_expert_multi_source_join\nSchema: customer_name: object OK, product_name: object OK, order_total: object MISMATCH→float\nNulls: 20, Dups: 8\nInspect the data first. Output JSON action:",
    "Step 10/25 | Task: task_expert_multi_source_join\nAll schemas fixed. Nulls: 15. Apply business rule currency_3char. Output JSON action:",
]

# Format each prompt using the chat template
formatted_prompts = []
for user_msg in TASK_PROMPTS:
    messages = [
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "user",   "content": user_msg},
    ]
    # Apply chat template — this wraps in <|im_start|>system/user/assistant tokens
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    formatted_prompts.append(formatted)

# Repeat to get enough training data
all_prompts = formatted_prompts * 9  # 12 * 9 = 108 samples
dataset = Dataset.from_dict({"prompt": all_prompts})
print(f"Dataset: {len(dataset)} chat-formatted prompts")

# === Step 3: Reward function ===
def reward_fn(completions, **kwargs):
    """
    Reward function with graduated scoring:
      +0.8  → valid JSON with a 'fix' action (cast_column, fill_nulls, etc.)
      +0.5  → valid JSON with any valid action
      +0.1  → valid JSON but unknown action (partial credit for format)
      -0.5  → parseable JSON but missing action_type
      -1.0  → not valid JSON at all
    """
    rewards = []
    for c in completions:
        text = c.strip() if isinstance(c, str) else str(c)
        # Strip any markdown fences the model might add
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        # Try to extract JSON from the text
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            text = text[json_start:json_end]
        try:
            action = json.loads(text)
            if isinstance(action, dict) and "action_type" in action:
                at = action["action_type"]
                fix_actions = {"cast_column","fill_nulls","filter_outliers",
                               "drop_nulls","apply_business_rule","reorder_stages"}
                valid_actions = fix_actions | {"inspect","drop_duplicates",
                                               "rename_column","validate","submit"}
                if at in fix_actions:
                    rewards.append(0.8)   # best: a fix action
                elif at in valid_actions:
                    rewards.append(0.5)   # good: valid action
                else:
                    rewards.append(0.1)   # ok: valid JSON, wrong action name
            else:
                rewards.append(-0.5)      # partial: JSON but no action_type
        except (json.JSONDecodeError, Exception):
            rewards.append(-1.0)          # bad: not JSON
    return rewards

# === Step 4: Train ===
config = GRPOConfig(
    output_dir          = "./grpo_checkpoints",
    num_train_epochs    = 3,             # 3 epochs for better convergence
    per_device_train_batch_size = 1,
    gradient_accumulation_steps = 4,
    learning_rate       = 5e-5,          # slightly higher LR for small model
    logging_steps       = 5,
    save_steps          = 50,
    max_completion_length = 128,         # a bit more room for the model
    max_prompt_length   = 384,           # limit prompt length
    num_generations     = 2,
    report_to           = "none",
)

trainer = GRPOTrainer(
    model            = model,
    args             = config,
    train_dataset    = dataset,
    processing_class = tokenizer,
    reward_funcs     = reward_fn,
)

torch.cuda.empty_cache()
gc.collect()

print(f"\nBefore training — VRAM used: {torch.cuda.memory_allocated()/1e9:.2f} GB")
print("\nStarting GRPO training …")
print("Watch for 'reward' to climb from -1.0 toward +0.5/+0.8\n")
trainer.train()

# === Step 5: Save ===
model.save_pretrained("./openenv-debugger-grpo")
tokenizer.save_pretrained("./openenv-debugger-grpo")
print("\n✅ Done! Model saved to ./openenv-debugger-grpo")

# Quick test — generate one action
FastLanguageModel.for_inference(model)
test_messages = [
    {"role": "system", "content": SYSTEM_MSG},
    {"role": "user",   "content": "Step 1/10 | Task: task_easy_schema_fix\nSchema: age: object MISMATCH→int\nOutput JSON action:"},
]
inputs = tokenizer.apply_chat_template(test_messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
outputs = model.generate(input_ids=inputs, max_new_tokens=64, temperature=0.1)
result = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
print(f"\n🧪 Test output: {result}")

# To push to HuggingFace:
# model.push_to_hub("your-username/openenv-debugger-grpo")
