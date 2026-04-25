"""
compete.py — Competition Mode for OpenEnv Data Pipeline Debugger
Provides a side-by-side comparison UI for two agents competing on the same task.
"""

from __future__ import annotations

def get_compete_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenEnv Debugger — Agent Competition</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --accent1: #6366f1;
            --accent2: #10b981;
        }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0; padding: 0;
            display: flex; flex-direction: column;
            min-height: 100vh;
        }
        header {
            text-align: center;
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            background: var(--card-bg);
        }
        h1 {
            margin: 0; font-size: 2rem;
            background: linear-gradient(to right, var(--accent1), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .controls {
            padding: 1rem;
            display: flex;
            justify-content: center;
            gap: 1rem;
            background: var(--bg);
            border-bottom: 1px solid var(--border);
        }
        select, button {
            padding: 0.5rem 1rem;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--card-bg);
            color: var(--text-main);
            font-family: inherit;
        }
        button {
            background: var(--accent1);
            color: white;
            cursor: pointer;
            border: none;
            font-weight: bold;
        }
        button:hover { background: #4f46e5; }
        .competition-arena {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .agent-pane {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
        }
        .agent-pane:last-child { border-right: none; }
        .agent-header {
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid var(--border);
            background: rgba(255,255,255,0.02);
        }
        .agent-header h2 { margin: 0 0 0.5rem 0; font-size: 1.25rem; }
        .iframe-container {
            flex: 1;
            position: relative;
        }
        iframe {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <header>
        <h1>⚔️ Multi-Agent Competition Arena</h1>
        <p style="color:var(--text-muted); margin-top:0.5rem;">Watch two distinct agents tackle the same exact pipeline.</p>
    </header>

    <div class="controls">
        <select id="task-select">
            <option value="task_easy_schema_fix">Easy: Schema Fix</option>
            <option value="task_medium_data_quality">Medium: Data Quality</option>
            <option value="task_hard_pipeline_orchestration">Hard: Pipeline Orchestration</option>
            <option value="task_veryhard_streaming_pipeline">V.Hard: Streaming</option>
            <option value="task_expert_multi_source_join">Expert: Multi-Source</option>
        </select>
        <button onclick="startCompetition()">Start Competition</button>
    </div>

    <div class="competition-arena">
        <div class="agent-pane">
            <div class="agent-header" style="border-top: 4px solid var(--accent1)">
                <h2>🤖 Automated Agent 1 (Fixed)</h2>
                <div style="font-size: 0.85rem; color: var(--text-muted)">Running independently</div>
            </div>
            <div class="iframe-container">
                <iframe id="iframe1" src="about:blank"></iframe>
            </div>
        </div>
        <div class="agent-pane">
            <div class="agent-header" style="border-top: 4px solid var(--accent2)">
                <h2>🧠 Collaborative Agents (Inspector→Fixer)</h2>
                <div style="font-size: 0.85rem; color: var(--text-muted)">Running collaboratively</div>
            </div>
            <div class="iframe-container">
                <iframe id="iframe2" src="about:blank"></iframe>
            </div>
        </div>
    </div>

    <script>
        function startCompetition() {
            // We just load the interactive dashboard into both panes and they can be commanded
            const task = document.getElementById('task-select').value;
            // Using hash parameters to hypothetically instruct the loaded dashboards (mock feature for visual)
            document.getElementById('iframe1').src = '/dashboard?agent=1&task=' + task;
            document.getElementById('iframe2').src = '/dashboard?agent=2&task=' + task;
        }
    </script>
</body>
</html>"""
