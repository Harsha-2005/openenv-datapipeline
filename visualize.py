"""
visualize.py  —  OpenEnv Data Pipeline Debugger
Updated: added generate_replay_html() for the step-by-step Replay Dashboard.
Original generate_reward_chart() is fully preserved and unchanged.
"""

from __future__ import annotations

import json
import os
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Original  generate_reward_chart()  — unchanged
# ──────────────────────────────────────────────────────────────────────────────

def generate_reward_chart(
    training_results: list[dict],
    output_path: str = "training_results.html",
) -> str:
    """
    Generate an interactive Chart.js reward-curve HTML file.

    Parameters
    ----------
    training_results : list[dict]
        Each dict: {"episode": int, "score": float, "task": str}
    output_path : str
        Where to write the HTML file.

    Returns
    -------
    str  —  absolute path of the written file.
    """
    episodes = [r["episode"] for r in training_results]
    scores   = [round(r["score"], 4) for r in training_results]
    tasks    = [r.get("task", "unknown") for r in training_results]

    # Colour per task tier
    task_colors = {
        "task_easy_schema_fix":              "#1D9E75",
        "task_medium_data_quality":          "#378ADD",
        "task_hard_pipeline_orchestration":  "#EF9F27",
        "task_veryhard_streaming_pipeline":  "#D85A30",
        "task_expert_multi_source_join":     "#534AB7",
    }
    point_colors = [task_colors.get(t, "#888780") for t in tasks]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenEnv — Training Reward Curves</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #f8f8f5; color: #2c2c2a; padding: 2rem; }}
  h1 {{ font-size: 1.3rem; font-weight: 500; margin-bottom: 0.25rem; }}
  .sub {{ font-size: 0.85rem; color: #888780; margin-bottom: 1.5rem; }}
  .card {{ background: #fff; border: 0.5px solid #d3d1c7; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 1.25rem; }}
  .stat {{ background: #f1efe8; border-radius: 8px; padding: 0.75rem 1rem; }}
  .stat-label {{ font-size: 11px; color: #888780; margin-bottom: 3px; }}
  .stat-val {{ font-size: 1.35rem; font-weight: 500; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 1rem; font-size: 12px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
</style>
</head>
<body>
<h1>OpenEnv — Training Reward Curves</h1>
<p class="sub">Curriculum training across {len(episodes)} episodes · {len(set(tasks))} task tiers</p>

<div class="stats">
  <div class="stat"><div class="stat-label">Best score</div><div class="stat-val">{max(scores):.4f}</div></div>
  <div class="stat"><div class="stat-label">Final score</div><div class="stat-val">{scores[-1]:.4f}</div></div>
  <div class="stat"><div class="stat-label">Total episodes</div><div class="stat-val">{len(episodes)}</div></div>
  <div class="stat"><div class="stat-label">Improvement</div><div class="stat-val">+{(scores[-1]-scores[0]):.3f}</div></div>
</div>

<div class="card">
  <canvas id="rewardChart" height="90"></canvas>
  <div class="legend" id="legend"></div>
</div>

<script>
const episodes    = {json.dumps(episodes)};
const scores      = {json.dumps(scores)};
const tasks       = {json.dumps(tasks)};
const pointColors = {json.dumps(point_colors)};
const taskColors  = {json.dumps(task_colors)};

const ctx = document.getElementById('rewardChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: episodes,
    datasets: [{{
      label: 'Score',
      data: scores,
      borderColor: '#1D9E75',
      backgroundColor: 'rgba(29,158,117,0.08)',
      pointBackgroundColor: pointColors,
      pointRadius: 3,
      tension: 0.35,
      fill: true,
      borderWidth: 1.8,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: ctx => `Score: ${{ctx.parsed.y.toFixed(4)}}`,
          afterLabel: ctx => `Task: ${{tasks[ctx.dataIndex].replace('task_','').replace(/_/g,' ')}}`
        }}
      }}
    }},
    scales: {{
      x: {{ title: {{ display: true, text: 'Episode', font: {{ size: 12 }} }} }},
      y: {{ min: 0, max: 1.05, title: {{ display: true, text: 'Score', font: {{ size: 12 }} }},
             ticks: {{ callback: v => v.toFixed(2) }} }}
    }}
  }}
}});

// Build legend
const seen = {{}};
const leg = document.getElementById('legend');
tasks.forEach((t, i) => {{
  if (seen[t]) return;
  seen[t] = true;
  const name = t.replace('task_','').replace(/_/g,' ');
  leg.innerHTML += `<div class="legend-item">
    <div class="legend-dot" style="background:${{taskColors[t] || '#888'}}"></div>
    <span>${{name}}</span>
  </div>`;
}});
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[visualize] Reward chart → {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# NEW  generate_replay_html()  — Replay & Step Debugger Dashboard
# ──────────────────────────────────────────────────────────────────────────────

def generate_replay_html(
    episode_log: list,          # list[StepRecord]  from env.history
    episode_num: int = 0,
    task_id: str = "",
    final_score: float | None = None,
    output_path: str | None = None,
) -> str:
    """
    Generate a standalone Replay & Step Debugger HTML dashboard from one episode.

    Parameters
    ----------
    episode_log : list[StepRecord]
        Populated automatically by DataPipelineEnvironment.history after an episode.
    episode_num : int
        Episode number (for labelling only).
    task_id : str
        Task identifier string.
    final_score : float | None
        Override the final score shown in the stats bar.
    output_path : str | None
        Where to write the file.  Defaults to replay_ep{N}.html.

    Returns
    -------
    str  —  absolute path of the written file.

    Usage
    -----
    >>> from visualize import generate_replay_html
    >>> path = generate_replay_html(env.history, episode_num=69,
    ...                             task_id="task_hard_pipeline_orchestration")
    >>> print(f"Replay saved → {path}")
    """
    if output_path is None:
        output_path = f"replay_ep{episode_num}.html"

    steps_data = [s.to_dict() if hasattr(s, "to_dict") else s for s in episode_log]
    total_steps = len(steps_data)

    if total_steps == 0:
        raise ValueError("episode_log is empty — run an episode first.")

    last  = steps_data[-1]
    score = final_score if final_score is not None else last.get("cumulative_reward", 0)
    task_label = task_id.replace("task_", "").replace("_", " ").title() if task_id else "Unknown task"

    # Chip CSS class per action type
    chip_map = {
        "inspect":             "chip-inspect",
        "cast_column":         "chip-cast",
        "drop_nulls":          "chip-drop",
        "fill_nulls":          "chip-fill",
        "drop_duplicates":     "chip-drop",
        "filter_outliers":     "chip-filter",
        "rename_column":       "chip-cast",
        "reorder_stages":      "chip-reorder",
        "apply_business_rule": "chip-filter",
        "validate":            "chip-validate",
        "submit":              "chip-submit",
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Replay — Episode {episode_num} · {task_label}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  *{{ box-sizing:border-box; margin:0; padding:0; }}
  body{{ font-family:system-ui,sans-serif; background:#f8f8f5; color:#2c2c2a; padding:1.5rem; }}

  /* Stats bar */
  .stats{{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:1rem; }}
  .stat{{ background:#f1efe8; border-radius:8px; padding:0.75rem 1rem; }}
  .stat-label{{ font-size:11px; color:#888780; margin-bottom:2px; }}
  .stat-val{{ font-size:1.4rem; font-weight:500; }}

  /* Cards */
  .card{{ background:#fff; border:0.5px solid #d3d1c7; border-radius:12px; padding:1rem 1.25rem; margin-bottom:1rem; }}
  .card-title{{ font-size:12px; font-weight:500; color:#5f5e5a; margin-bottom:10px; }}

  /* Timeline */
  #timeline{{ display:flex; align-items:center; gap:4px; overflow-x:auto; padding-bottom:4px; }}
  .tl-dot{{ width:10px; height:10px; border-radius:50%; flex-shrink:0; border:1.5px solid transparent; cursor:pointer;
            transition:transform 0.1s; }}
  .tl-dot:hover{{ transform:scale(1.4); }}
  .tl-dot.done{{ background:#1D9E75; border-color:#0F6E56; }}
  .tl-dot.current{{ background:#378ADD; border-color:#185FA5; }}
  .tl-dot.future{{ background:#f1efe8; border-color:#b4b2a9; }}
  .tl-line{{ height:1.5px; flex:1; min-width:4px; transition:background 0.25s; }}

  /* Step detail */
  .step-num{{ font-size:22px; font-weight:500; }}
  .detail-row{{ display:flex; gap:20px; font-size:12px; margin-top:10px; }}
  .detail-row span:first-child{{ color:#888780; display:block; margin-bottom:2px; font-size:11px; }}

  /* Action log */
  .log-row{{ display:flex; align-items:center; gap:10px; padding:7px 0;
             border-bottom:0.5px solid #d3d1c7; font-size:13px; }}
  .log-row.active{{ background:#f1efe8; border-radius:8px; padding:7px 8px; margin:0 -8px; }}
  .log-step{{ font-size:11px; color:#888780; min-width:20px; }}
  .log-desc{{ flex:1; color:#5f5e5a; }}
  .log-rew{{ font-size:12px; font-weight:500; min-width:38px; text-align:right; }}

  /* Action chips */
  .chip{{ display:inline-block; font-size:11px; font-weight:500; padding:2px 8px; border-radius:6px; }}
  .chip-inspect   {{ background:#E6F1FB; color:#0C447C; }}
  .chip-cast      {{ background:#EEEDFE; color:#3C3489; }}
  .chip-fill      {{ background:#EAF3DE; color:#27500A; }}
  .chip-drop      {{ background:#FAEEDA; color:#633806; }}
  .chip-filter    {{ background:#FAECE7; color:#712B13; }}
  .chip-validate  {{ background:#E1F5EE; color:#085041; }}
  .chip-submit    {{ background:#E1F5EE; color:#085041; }}
  .chip-reorder   {{ background:#FBEAF0; color:#72243E; }}

  /* Controls */
  .controls{{ display:flex; align-items:center; gap:10px; justify-content:center; margin-top:1rem; }}
  button{{ background:transparent; border:0.5px solid #b4b2a9; border-radius:8px; padding:6px 18px;
           font-size:13px; cursor:pointer; transition:background 0.15s; }}
  button:hover{{ background:#f1efe8; }}
  button:active{{ transform:scale(0.97); }}
  .kb-hint{{ font-size:11px; color:#b4b2a9; margin-left:6px; }}

  /* Two-col layout */
  .two-col{{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
  @media(max-width:600px){{ .two-col{{ grid-template-columns:1fr; }} .stats{{ grid-template-columns:repeat(2,1fr); }} }}

  @media(prefers-color-scheme:dark){{
    body{{ background:#1e1e1c; color:#d3d1c7; }}
    .stat{{ background:#2c2c2a; }}
    .stat-label,.log-step,.kb-hint{{ color:#888780; }}
    .card{{ background:#252523; border-color:#444441; }}
    .card-title{{ color:#888780; }}
    .log-row{{ border-color:#444441; }}
    .log-row.active,.tl-dot.future{{ background:#2c2c2a; }}
    .tl-dot.future{{ border-color:#5f5e5a; }}
    button{{ border-color:#5f5e5a; }}
    button:hover{{ background:#2c2c2a; }}
    .chip-inspect  {{ background:#042C53; color:#B5D4F4; }}
    .chip-cast     {{ background:#26215C; color:#CECBF6; }}
    .chip-fill     {{ background:#173404; color:#C0DD97; }}
    .chip-drop     {{ background:#412402; color:#FAC775; }}
    .chip-filter   {{ background:#4A1B0C; color:#F5C4B3; }}
    .chip-validate {{ background:#04342C; color:#9FE1CB; }}
    .chip-submit   {{ background:#04342C; color:#9FE1CB; }}
    .chip-reorder  {{ background:#4B1528; color:#F4C0D1; }}
    .log-desc{{ color:#b4b2a9; }}
  }}
</style>
</head>
<body>

<div style="margin-bottom:1rem">
  <div style="font-size:1.15rem;font-weight:500">Replay — Episode {episode_num}</div>
  <div style="font-size:13px;color:#888780">{task_label} &nbsp;·&nbsp; {total_steps} steps recorded</div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-label">Task</div>
    <div class="stat-val" style="font-size:14px;margin-top:3px">{task_label}</div></div>
  <div class="stat"><div class="stat-label">Episode</div>
    <div class="stat-val">{episode_num}</div></div>
  <div class="stat"><div class="stat-label">Final score</div>
    <div class="stat-val" id="hdr-score">{score:.4f}</div></div>
  <div class="stat"><div class="stat-label">Steps used</div>
    <div class="stat-val" id="hdr-steps">— / {total_steps}</div></div>
</div>

<!-- Timeline -->
<div class="card">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
    <span class="card-title" style="margin:0">Episode timeline — click any dot to jump</span>
    <span style="font-size:11px;color:#888780" id="tl-label">Step 1 of {total_steps}</span>
  </div>
  <div id="timeline"></div>
  <div style="display:flex;justify-content:space-between;font-size:10px;color:#888780;margin-top:6px">
    <span>step 1</span><span>step {total_steps // 2}</span><span>step {total_steps}</span>
  </div>
</div>

<!-- Step detail + Chart -->
<div class="two-col">

  <div class="card">
    <div class="card-title">Current step</div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <span class="step-num" id="d-stepnum">1</span>
      <span class="chip" id="d-chip">inspect</span>
    </div>
    <p style="font-size:13px;color:#5f5e5a;margin-bottom:10px;line-height:1.5" id="d-desc">—</p>
    <div class="detail-row">
      <div><span>Reward</span><span style="font-size:16px;font-weight:500" id="d-reward">—</span></div>
      <div><span>Cumulative</span><span style="font-size:16px;font-weight:500" id="d-cum">—</span></div>
      <div><span>Bugs left</span><span style="font-size:16px;font-weight:500" id="d-bugs">—</span></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Reward curve</div>
    <canvas id="mini-chart" height="130"></canvas>
  </div>

</div>

<!-- Action log -->
<div class="card">
  <div class="card-title">Action log (last 6 steps)</div>
  <div id="action-log"></div>
</div>

<!-- Controls -->
<div class="controls">
  <button onclick="seek(currentStep-1)">← Prev</button>
  <button id="play-btn" onclick="togglePlay()">Play ▶</button>
  <button onclick="seek(currentStep+1)">Next →</button>
  <span class="kb-hint">← → arrow keys also work</span>
</div>

<script>
const STEPS = {json.dumps(steps_data, indent=2)};
const CHIP_MAP = {json.dumps(chip_map)};

let currentStep = 0;
let playing = false;
let playTimer = null;
let chart = null;

function chipClass(action) {{
  return CHIP_MAP[action] || 'chip-inspect';
}}

function buildTimeline() {{
  const tl = document.getElementById('timeline');
  tl.innerHTML = '';
  STEPS.forEach((s, i) => {{
    const dot = document.createElement('div');
    dot.className = 'tl-dot ' + (i < currentStep ? 'done' : i === currentStep ? 'current' : 'future');
    dot.title = `Step ${{i+1}}: ${{s.action}}`;
    dot.onclick = () => seek(i);
    tl.appendChild(dot);
    if (i < STEPS.length - 1) {{
      const line = document.createElement('div');
      line.className = 'tl-line';
      line.style.background = i < currentStep ? '#1D9E75' : '#d3d1c7';
      tl.appendChild(line);
    }}
  }});
  document.getElementById('tl-label').textContent = `Step ${{currentStep+1}} of ${{STEPS.length}}`;
}}

function buildLog() {{
  const log = document.getElementById('action-log');
  log.innerHTML = '';
  const start = Math.max(0, currentStep - 5);
  const slice = STEPS.slice(start, currentStep + 1);
  slice.forEach((s, ii) => {{
    const idx = start + ii;
    const row = document.createElement('div');
    row.className = 'log-row' + (idx === currentStep ? ' active' : '');
    const rew = s.reward >= 0 ? `+${{s.reward.toFixed(2)}}` : s.reward.toFixed(2);
    const rewColor = s.reward >= 0 ? '#1D9E75' : '#D85A30';
    row.innerHTML = `
      <span class="log-step">${{idx+1}}</span>
      <span class="chip ${{chipClass(s.action)}}">${{s.action}}</span>
      <span class="log-desc">${{s.description}}</span>
      <span class="log-rew" style="color:${{rewColor}}">${{rew}}</span>
    `;
    log.appendChild(row);
  }});
}}

function updateDetail() {{
  const s = STEPS[currentStep];
  document.getElementById('d-stepnum').textContent = currentStep + 1;
  const chip = document.getElementById('d-chip');
  chip.textContent = s.action;
  chip.className = 'chip ' + chipClass(s.action);
  document.getElementById('d-desc').textContent = s.description;
  const r = s.reward;
  document.getElementById('d-reward').textContent = (r >= 0 ? '+' : '') + r.toFixed(3);
  document.getElementById('d-reward').style.color = r >= 0 ? '#1D9E75' : '#D85A30';
  document.getElementById('d-cum').textContent = s.cumulative_reward.toFixed(3);
  document.getElementById('d-bugs').textContent = s.bugs_remaining;
  document.getElementById('hdr-steps').textContent = `${{currentStep+1}} / ${{STEPS.length}}`;
}}

function buildChart() {{
  const ctx = document.getElementById('mini-chart').getContext('2d');
  const labels = STEPS.map((_, i) => i + 1);
  const data   = STEPS.map(s => s.cumulative_reward);

  if (chart) chart.destroy();

  const isDark = window.matchMedia('(prefers-color-scheme:dark)').matches;
  const gridColor = isDark ? 'rgba(180,178,169,0.1)' : 'rgba(136,135,128,0.12)';
  const tickColor = isDark ? '#888780' : '#5f5e5a';

  chart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels,
      datasets: [{{
        data,
        segment: {{
          borderColor: ctx => ctx.p0DataIndex < currentStep ? '#1D9E75' : '#b4b2a9',
        }},
        pointBackgroundColor: data.map((_, i) =>
          i === currentStep ? '#378ADD' : (i < currentStep ? '#1D9E75' : '#b4b2a9')
        ),
        pointRadius: data.map((_, i) => i === currentStep ? 5 : 2),
        tension: 0.35,
        fill: false,
        borderWidth: 1.8,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: true,
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: c => `Score: ${{c.parsed.y.toFixed(4)}}` }} }} }},
      scales: {{
        x: {{ display: false }},
        y: {{
          min: Math.min(-0.1, Math.min(...data) - 0.05),
          max: Math.max(1.05, Math.max(...data) + 0.05),
          ticks: {{ font: {{ size: 10 }}, color: tickColor, maxTicksLimit: 5,
                    callback: v => v.toFixed(2) }},
          grid: {{ color: gridColor }},
          border: {{ display: false }},
        }}
      }},
      animation: {{ duration: 150 }}
    }}
  }});
}}

function seek(idx) {{
  if (idx < 0 || idx >= STEPS.length) return;
  currentStep = idx;
  buildTimeline();
  buildLog();
  updateDetail();
  buildChart();
}}

function togglePlay() {{
  playing = !playing;
  document.getElementById('play-btn').textContent = playing ? 'Pause ⏸' : 'Play ▶';
  if (playing) {{
    if (currentStep >= STEPS.length - 1) seek(0);
    playTimer = setInterval(() => {{
      if (currentStep >= STEPS.length - 1) {{ togglePlay(); return; }}
      seek(currentStep + 1);
    }}, 900);
  }} else {{
    clearInterval(playTimer);
  }}
}}

document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight') seek(currentStep + 1);
  if (e.key === 'ArrowLeft')  seek(currentStep - 1);
  if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
}});

seek(0);
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[visualize] Replay dashboard → {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)