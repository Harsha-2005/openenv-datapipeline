#!/usr/bin/env python3
"""
benchmarks/run_benchmarks.py — Run all baseline agents and generate comparison report.

Usage:
    python benchmarks/run_benchmarks.py
    python benchmarks/run_benchmarks.py --episodes 5 --output benchmark_report.html
"""

from __future__ import annotations
import json, os, sys, time
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.agents import RandomAgent, GreedyAgent, FixedStrategyAgent
from env.environment import DataPipelineEnv
from env.models import Action, ActionType


BENCHMARK_TASKS = [
    "task_easy_schema_fix",
    "task_medium_data_quality",
    "task_hard_pipeline_orchestration",
]


def run_agent_on_task(agent, task_id: str, seed: int = 42) -> Dict:
    """Run a single agent on a single task, return results dict."""
    env = DataPipelineEnv(task_id=task_id, seed=seed)
    obs_obj = env.reset()
    obs = obs_obj.model_dump() if hasattr(obs_obj, "model_dump") else obs_obj

    if hasattr(agent, "set_task"):
        agent.set_task(task_id)
    agent.reset()

    done = obs.get("done", False)
    max_steps = obs.get("max_steps", 40)
    step = 0
    total_reward = 0.0
    start_time = time.time()

    while not done and step < max_steps:
        action_dict = agent.choose_action(obs, step)

        at = action_dict.get("action_type", "inspect")
        col = action_dict.get("column")
        val = action_dict.get("value")
        params = action_dict.get("parameters")

        try:
            action = Action(
                action_type=ActionType(at),
                column=col, value=val, parameters=params,
            )
            obs_obj = env.step(action)
            obs = obs_obj.model_dump() if hasattr(obs_obj, "model_dump") else obs_obj
            done = obs.get("done", False)
            step += 1
        except Exception:
            step += 1
            continue

        # Force submit near end
        if max_steps - step <= 1 and not done:
            try:
                obs_obj = env.step(Action(action_type=ActionType.SUBMIT))
                obs = obs_obj.model_dump() if hasattr(obs_obj, "model_dump") else obs_obj
                done = True
                step += 1
            except Exception:
                done = True

    elapsed = time.time() - start_time

    # Extract score
    score = 0.0
    if env.history:
        last = env.history[-1]
        score = last.cumulative_reward if hasattr(last, "cumulative_reward") else 0.0

    return {
        "agent": agent.name,
        "task_id": task_id,
        "score": round(score, 4),
        "steps": step,
        "time_sec": round(elapsed, 3),
    }


def run_all_benchmarks(episodes: int = 3) -> List[Dict]:
    """Run all agents across all tasks, averaging over episodes."""
    agents = [
        RandomAgent(seed=42),
        GreedyAgent(),
        FixedStrategyAgent(),
    ]

    all_results = []

    for agent in agents:
        print(f"\n{'='*60}")
        print(f"  Running: {agent.name} Agent")
        print(f"{'='*60}")

        for task_id in BENCHMARK_TASKS:
            episode_scores = []
            episode_steps = []
            episode_times = []

            for ep in range(episodes):
                result = run_agent_on_task(agent, task_id, seed=42 + ep)
                episode_scores.append(result["score"])
                episode_steps.append(result["steps"])
                episode_times.append(result["time_sec"])
                print(f"  {agent.name:>15} | {task_id:<40} | ep {ep}: score={result['score']:.4f} steps={result['steps']}")

            avg_result = {
                "agent": agent.name,
                "task_id": task_id,
                "avg_score": round(sum(episode_scores) / len(episode_scores), 4),
                "avg_steps": round(sum(episode_steps) / len(episode_steps), 1),
                "avg_time": round(sum(episode_times) / len(episode_times), 3),
                "best_score": round(max(episode_scores), 4),
                "scores": episode_scores,
            }
            all_results.append(avg_result)

    return all_results


def generate_benchmark_html(results: List[Dict], output_path: str = "benchmark_report.html") -> str:
    """Generate a stunning HTML benchmark comparison report."""

    # Group by agent
    agents = {}
    for r in results:
        agents.setdefault(r["agent"], []).append(r)

    # Build table rows
    table_rows = ""
    for r in results:
        task_short = r["task_id"].replace("task_", "").replace("_", " ").title()
        bar_width = max(2, r["avg_score"] * 100)
        bar_color = "#10b981" if r["avg_score"] > 0.7 else "#f59e0b" if r["avg_score"] > 0.3 else "#ef4444"
        table_rows += f"""
            <tr>
                <td><span class="agent-badge">{r['agent']}</span></td>
                <td>{task_short}</td>
                <td>
                    <div class="score-bar-bg">
                        <div class="score-bar" style="width:{bar_width}%;background:{bar_color}"></div>
                    </div>
                    <span class="score-val">{r['avg_score']:.4f}</span>
                </td>
                <td>{r['avg_steps']:.0f}</td>
                <td>{r['avg_time']:.3f}s</td>
                <td>{r['best_score']:.4f}</td>
            </tr>"""

    # Build summary cards per agent
    agent_cards = ""
    for agent_name, agent_results in agents.items():
        avg_all = sum(r["avg_score"] for r in agent_results) / len(agent_results)
        avg_steps = sum(r["avg_steps"] for r in agent_results) / len(agent_results)
        color = "#10b981" if avg_all > 0.7 else "#f59e0b" if avg_all > 0.3 else "#ef4444"
        agent_cards += f"""
            <div class="agent-card">
                <div class="agent-card-header" style="border-bottom: 3px solid {color}">
                    <h3>{agent_name}</h3>
                </div>
                <div class="agent-card-body">
                    <div class="metric">
                        <span class="metric-val" style="color:{color}">{avg_all:.4f}</span>
                        <span class="metric-label">Avg Score</span>
                    </div>
                    <div class="metric">
                        <span class="metric-val">{avg_steps:.0f}</span>
                        <span class="metric-label">Avg Steps</span>
                    </div>
                </div>
            </div>"""

    # Chart data
    chart_data = json.dumps({
        agent_name: {r["task_id"].replace("task_", ""): r["avg_score"] for r in agent_results}
        for agent_name, agent_results in agents.items()
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenEnv Benchmark Report</title>
<style>
    :root {{
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --accent: #6366f1;
        --accent-glow: rgba(99, 102, 241, 0.3);
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --border: #334155;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
        line-height: 1.6;
        min-height: 100vh;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
    header {{
        text-align: center;
        padding: 3rem 0 2rem;
        background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1a3e 100%);
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }}
    header h1 {{
        font-size: 2.2rem;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }}
    header p {{ color: var(--text-secondary); font-size: 1.1rem; }}

    .cards-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.2rem;
        margin-bottom: 2.5rem;
    }}
    .agent-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .agent-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    }}
    .agent-card-header {{
        padding: 1rem 1.2rem 0.8rem;
    }}
    .agent-card-header h3 {{ font-size: 1.1rem; }}
    .agent-card-body {{
        padding: 0.8rem 1.2rem 1.2rem;
        display: flex;
        gap: 2rem;
    }}
    .metric {{ text-align: center; }}
    .metric-val {{ font-size: 1.8rem; font-weight: 700; display: block; }}
    .metric-label {{ font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }}

    table {{
        width: 100%;
        border-collapse: collapse;
        background: var(--bg-card);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border);
        margin-bottom: 2.5rem;
    }}
    th {{
        padding: 1rem;
        text-align: left;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border);
        background: rgba(99, 102, 241, 0.05);
    }}
    td {{
        padding: 0.85rem 1rem;
        border-bottom: 1px solid var(--border);
        font-size: 0.95rem;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover {{ background: rgba(99, 102, 241, 0.05); }}
    .agent-badge {{
        background: var(--accent);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .score-bar-bg {{
        width: 120px;
        height: 8px;
        background: var(--border);
        border-radius: 4px;
        display: inline-block;
        vertical-align: middle;
        margin-right: 0.5rem;
    }}
    .score-bar {{
        height: 100%;
        border-radius: 4px;
        transition: width 1s ease;
    }}
    .score-val {{ font-weight: 600; font-variant-numeric: tabular-nums; }}

    .chart-container {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
    }}
    .chart-container h2 {{
        margin-bottom: 1.5rem;
        font-size: 1.3rem;
    }}
    canvas {{ max-width: 100%; }}

    footer {{
        text-align: center;
        padding: 2rem;
        color: var(--text-secondary);
        font-size: 0.85rem;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .animated {{ animation: fadeIn 0.6s ease forwards; }}
</style>
</head>
<body>
<header>
    <div class="container">
        <h1>🏆 Benchmark Comparison Report</h1>
        <p>OpenEnv Data Pipeline Debugger — Agent Performance Analysis</p>
    </div>
</header>

<div class="container">
    <h2 style="margin-bottom:1rem;color:var(--text-secondary);font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;">Agent Summary</h2>
    <div class="cards-grid animated">{agent_cards}</div>

    <h2 style="margin-bottom:1rem;color:var(--text-secondary);font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;">Detailed Results</h2>
    <table class="animated" style="animation-delay:0.2s">
        <thead>
            <tr>
                <th>Agent</th>
                <th>Task</th>
                <th>Score</th>
                <th>Steps</th>
                <th>Time</th>
                <th>Best</th>
            </tr>
        </thead>
        <tbody>{table_rows}</tbody>
    </table>

    <div class="chart-container animated" style="animation-delay:0.4s">
        <h2>Score Comparison by Task</h2>
        <canvas id="barChart" height="300"></canvas>
    </div>
</div>

<footer>
    <p>Generated by OpenEnv Data Pipeline Debugger Benchmark Suite</p>
</footer>

<script>
const data = {chart_data};
const canvas = document.getElementById('barChart');
const ctx = canvas.getContext('2d');

function drawChart() {{
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = 600;
    ctx.scale(2, 2);

    const agents = Object.keys(data);
    const tasks = Object.keys(data[agents[0]] || {{}});
    const colors = ['#ef4444', '#f59e0b', '#10b981', '#6366f1'];
    const barWidth = 30;
    const groupWidth = (agents.length * barWidth) + 20;
    const startX = 80;
    const chartHeight = 250;
    const startY = 270;

    // Y axis
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {{
        const y = startY - (i * chartHeight / 5);
        ctx.beginPath();
        ctx.moveTo(startX, y);
        ctx.lineTo(startX + tasks.length * groupWidth + 20, y);
        ctx.stroke();
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText((i * 0.2).toFixed(1), startX - 10, y + 4);
    }}

    // Bars
    tasks.forEach((task, ti) => {{
        const groupX = startX + ti * groupWidth + 30;
        agents.forEach((agent, ai) => {{
            const score = data[agent][task] || 0;
            const barH = score * chartHeight;
            const x = groupX + ai * barWidth;
            const y = startY - barH;

            ctx.fillStyle = colors[ai % colors.length];
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth - 4, barH, [4, 4, 0, 0]);
            ctx.fill();

            // Score label
            ctx.fillStyle = '#f1f5f9';
            ctx.font = 'bold 10px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(score.toFixed(2), x + (barWidth - 4) / 2, y - 6);
        }});

        // Task label
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';
        const labelX = groupX + (agents.length * barWidth) / 2;
        ctx.fillText(task.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase()), labelX, startY + 20);
    }});

    // Legend
    const legendY = 10;
    agents.forEach((agent, i) => {{
        const x = startX + i * 130;
        ctx.fillStyle = colors[i % colors.length];
        ctx.fillRect(x, legendY, 14, 14);
        ctx.fillStyle = '#f1f5f9';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(agent, x + 20, legendY + 12);
    }});
}}

drawChart();
window.addEventListener('resize', () => {{ ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.setTransform(1,0,0,1,0,0); drawChart(); }});
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[benchmarks] Benchmark report saved -> {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run benchmark comparison")
    parser.add_argument("--episodes", type=int, default=3, help="Episodes per task per agent")
    parser.add_argument("--output", type=str, default="benchmark_report.html", help="Output HTML file")
    args = parser.parse_args()

    print("OpenEnv Data Pipeline Debugger -- Benchmark Suite")
    print("=" * 60)

    results = run_all_benchmarks(episodes=args.episodes)

    # Print summary table
    print(f"\n{'='*60}")
    print(f"  {'Agent':<18} {'Task':<35} {'Score':>8} {'Steps':>6}")
    print(f"{'='*60}")
    for r in results:
        task_short = r["task_id"].replace("task_", "")
        print(f"  {r['agent']:<18} {task_short:<35} {r['avg_score']:>8.4f} {r['avg_steps']:>6.0f}")

    # Generate HTML report
    generate_benchmark_html(results, output_path=args.output)

    # Save JSON results
    json_path = args.output.replace(".html", ".json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[benchmarks] JSON results saved -> {json_path}")


if __name__ == "__main__":
    main()
