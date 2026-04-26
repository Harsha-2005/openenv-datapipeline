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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f9fafb; --text-color: #111827; --text-muted: #6b7280;
            --border-color: #e5e7eb; --primary-color: #2563eb; --primary-hover: #1d4ed8;
            --bg-card: #ffffff; --success: #059669; --danger: #dc2626; --navbar-height: 56px;
            --accent1: #6366f1; --accent2: #10b981;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',system-ui,sans-serif; background:var(--bg-color); color:var(--text-color); line-height:1.6; min-height:100vh; display:flex; flex-direction:column; }

        /* ── Shared Navbar (identical to dashboard.py) ── */
        .topnav { position:fixed; top:0; left:0; right:0; height:var(--navbar-height); background:#0f172a; border-bottom:1px solid #1e293b; display:flex; align-items:center; padding:0 1.5rem; z-index:1000; box-shadow:0 2px 8px rgba(0,0,0,0.25); }
        .topnav-brand { display:flex; align-items:center; gap:0.6rem; font-weight:700; font-size:0.95rem; color:#f1f5f9; text-decoration:none; margin-right:2rem; letter-spacing:-0.01em; white-space:nowrap; }
        .topnav-brand .logo-dot { width:8px; height:8px; background:#6366f1; border-radius:50%; display:inline-block; }
        .topnav-links { display:flex; align-items:center; gap:0.25rem; flex:1; }
        .topnav-link { display:flex; align-items:center; gap:0.4rem; padding:0.4rem 0.85rem; border-radius:6px; color:#94a3b8; text-decoration:none; font-size:0.85rem; font-weight:500; transition:background 0.18s,color 0.18s; white-space:nowrap; }
        .topnav-link:hover { background:rgba(255,255,255,0.07); color:#f1f5f9; }
        .topnav-link.active { background:rgba(99,102,241,0.18); color:#818cf8; }
        .topnav-link .nav-icon { font-size:0.9rem; }
        .topnav-divider { width:1px; height:20px; background:#1e293b; margin:0 0.5rem; }
        .topnav-status { display:flex; align-items:center; gap:0.5rem; font-size:0.78rem; font-weight:500; margin-left:auto; }
        .status-dot { width:7px; height:7px; border-radius:50%; background:#334155; transition:background 0.3s; }
        .status-dot.online { background:#10b981; box-shadow:0 0 6px #10b981; }
        .status-dot.offline { background:#ef4444; }

        /* ── Page ── */
        .page-wrapper { margin-top:var(--navbar-height); flex:1; display:flex; flex-direction:column; }

        /* Hero */
        .hero { text-align:center; padding:1.5rem 1rem; border-bottom:1px solid var(--border-color); background:var(--bg-card); }
        .hero h1 { font-size:1.8rem; font-weight:800; background:linear-gradient(to right,var(--accent1),var(--accent2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.25rem; }
        .hero p { color:var(--text-muted); font-size:0.9rem; }

        /* Controls */
        .controls { padding:1rem 1.5rem; display:flex; justify-content:center; gap:1rem; align-items:center; background:var(--bg-card); border-bottom:1px solid var(--border-color); flex-wrap:wrap; }
        select { padding:0.5rem 1rem; border-radius:6px; border:1px solid var(--border-color); background:var(--bg-card); color:var(--text-color); font-family:inherit; font-size:0.85rem; }
        .btn { padding:0.5rem 1.5rem; border-radius:6px; border:none; font-family:inherit; font-size:0.85rem; font-weight:600; cursor:pointer; transition:all 0.2s; }
        .btn-primary { background:var(--primary-color); color:#fff; }
        .btn-primary:hover { background:var(--primary-hover); transform:translateY(-1px); box-shadow:0 2px 8px rgba(37,99,235,0.3); }

        /* Arena */
        .arena { display:flex; flex:1; min-height:0; }
        .agent-pane { flex:1; display:flex; flex-direction:column; border-right:1px solid var(--border-color); }
        .agent-pane:last-child { border-right:none; }

        .agent-header { padding:1rem; text-align:center; border-bottom:1px solid var(--border-color); background:var(--bg-card); }
        .agent-header h2 { margin:0 0 0.25rem; font-size:1.1rem; font-weight:700; }
        .agent-header .subtitle { font-size:0.78rem; color:var(--text-muted); }
        .agent-header.left { border-top:3px solid var(--accent1); }
        .agent-header.right { border-top:3px solid var(--accent2); }

        .iframe-wrap { flex:1; position:relative; min-height:500px; }
        .iframe-wrap iframe { position:absolute; top:0; left:0; width:100%; height:100%; border:none; }

        /* VS divider */
        .vs-divider { width:48px; display:flex; align-items:center; justify-content:center; background:var(--bg-color); border-left:1px solid var(--border-color); border-right:1px solid var(--border-color); flex-shrink:0; }
        .vs-badge { width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,var(--accent1),var(--accent2)); color:#fff; font-weight:800; font-size:0.7rem; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.15); animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.08)} }

        /* Role cards */
        .roles-bar { display:flex; gap:0.75rem; justify-content:center; padding:1rem; background:var(--bg-card); border-bottom:1px solid var(--border-color); flex-wrap:wrap; }
        .role-chip { display:flex; align-items:center; gap:0.4rem; padding:0.4rem 0.8rem; background:var(--bg-color); border:1px solid var(--border-color); border-radius:8px; font-size:0.78rem; font-weight:600; }
        .role-arrow { color:var(--text-muted); font-size:0.8rem; }

        /* Score cards */
        .score-bar { display:flex; gap:1rem; justify-content:center; padding:0.75rem 1rem; background:var(--bg-card); border-top:1px solid var(--border-color); }
        .score-card { text-align:center; padding:0.5rem 1.5rem; background:var(--bg-color); border:1px solid var(--border-color); border-radius:8px; min-width:120px; }
        .score-card .score-label { font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.04em; }
        .score-card .score-val { font-size:1.3rem; font-weight:800; }
        .score-card .score-val.blue { color:var(--accent1); }
        .score-card .score-val.green { color:var(--accent2); }

        @media(max-width:768px) {
            .arena { flex-direction:column; }
            .vs-divider { width:100%; height:40px; border:none; border-top:1px solid var(--border-color); border-bottom:1px solid var(--border-color); }
            .agent-pane { border-right:none; border-bottom:1px solid var(--border-color); }
        }
    </style>
</head>
<body>
<<<<<<< HEAD
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
=======

    <!-- ── Shared Navbar ── -->
    <nav class="topnav">
        <a class="topnav-brand" href="/"><span class="logo-dot"></span> OpenEnv Debugger</a>
        <div class="topnav-links">
            <a class="topnav-link" href="/dashboard"><span class="nav-icon">📊</span> Dashboard</a>
            <a class="topnav-link" href="/demo"><span class="nav-icon">🎬</span> Demo</a>
            <a class="topnav-link active" href="/compete"><span class="nav-icon">⚔️</span> Compete</a>
            <div class="topnav-divider"></div>
            <a class="topnav-link" href="/docs" target="_blank"><span class="nav-icon">📖</span> API Docs</a>
            <a class="topnav-link" href="/tasks" target="_blank"><span class="nav-icon">📋</span> Tasks</a>
            <a class="topnav-link" href="/health" target="_blank"><span class="nav-icon">🩺</span> Health</a>
        </div>
        <div class="topnav-status">
            <span class="status-dot" id="nav-dot"></span>
            <span id="nav-status-text" style="color:#94a3b8;">Connecting...</span>
        </div>
    </nav>

    <div class="page-wrapper">
        <div class="hero">
            <h1>⚔️ Multi-Agent Competition Arena</h1>
            <p>Watch two distinct agents tackle the same pipeline — side by side.</p>
        </div>

        <!-- Multi-agent role flow -->
        <div class="roles-bar">
            <div class="role-chip">🔍 Inspector</div>
            <span class="role-arrow">→</span>
            <div class="role-chip">🔧 Fixer</div>
            <span class="role-arrow">→</span>
            <div class="role-chip">✅ Validator</div>
            <span style="margin:0 0.5rem;color:var(--text-muted);font-size:0.75rem;">vs</span>
            <div class="role-chip">📏 Rule-Based Solo</div>
        </div>

        <div class="controls">
            <select id="task-select">
                <option value="task_easy_schema_fix">Easy: Schema Fix</option>
                <option value="task_medium_data_quality">Medium: Data Quality</option>
                <option value="task_hard_pipeline_orchestration">Hard: Pipeline Orchestration</option>
                <option value="task_veryhard_streaming_pipeline">V.Hard: Streaming Pipeline</option>
                <option value="task_expert_multi_source_join">Expert: Multi-Source Join</option>
            </select>
            <button class="btn btn-primary" onclick="startCompetition()">▶ Start Competition</button>
        </div>

        <!-- Arena -->
        <div class="arena">
            <div class="agent-pane">
                <div class="agent-header left">
                    <h2>🤖 Automated Agent (Fixed Policy)</h2>
                    <div class="subtitle">Rule-based heuristic — runs independently</div>
                </div>
                <div class="iframe-wrap">
                    <iframe id="iframe1" src="about:blank"></iframe>
                </div>
            </div>

            <div class="vs-divider">
                <div class="vs-badge">VS</div>
            </div>

            <div class="agent-pane">
                <div class="agent-header right">
                    <h2>🧠 Collaborative Agents (Inspector→Fixer→Validator)</h2>
                    <div class="subtitle">Multi-agent cooperative pipeline</div>
                </div>
                <div class="iframe-wrap">
                    <iframe id="iframe2" src="about:blank"></iframe>
                </div>
            </div>
        </div>

        <!-- Score bar -->
        <div class="score-bar">
            <div class="score-card">
                <div class="score-label">Agent 1 Score</div>
                <div class="score-val blue" id="score1">—</div>
            </div>
            <div class="score-card">
                <div class="score-label">Task</div>
                <div class="score-val" id="taskDisplay" style="font-size:0.85rem;color:var(--text-muted);">Select & Start</div>
            </div>
            <div class="score-card">
                <div class="score-label">Agent 2 Score</div>
                <div class="score-val green" id="score2">—</div>
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)
            </div>
        </div>
    </div>

<<<<<<< HEAD
    <script>
        function startCompetition() {
            // We just load the interactive dashboard into both panes and they can be commanded
            const task = document.getElementById('task-select').value;
            // Using hash parameters to hypothetically instruct the loaded dashboards (mock feature for visual)
            document.getElementById('iframe1').src = '/dashboard?agent=1&task=' + task;
            document.getElementById('iframe2').src = '/dashboard?agent=2&task=' + task;
        }
    </script>
=======
<script>
function startCompetition() {
    const task = document.getElementById('task-select').value;
    document.getElementById('iframe1').src = '/dashboard?agent=1&task=' + task;
    document.getElementById('iframe2').src = '/dashboard?agent=2&task=' + task;
    document.getElementById('taskDisplay').textContent = task.replace('task_','').replace(/_/g,' ');
}

// Health check (shared logic)
async function checkHealth() {
    const dot = document.getElementById('nav-dot');
    const txt = document.getElementById('nav-status-text');
    try {
        const r = await fetch('/health');
        if (r.ok) { dot.className='status-dot online'; txt.textContent='Online'; txt.style.color='#10b981'; }
        else { dot.className='status-dot offline'; txt.textContent='Error'; txt.style.color='#ef4444'; }
    } catch { dot.className='status-dot offline'; txt.textContent='Offline'; txt.style.color='#ef4444'; }
}
setInterval(checkHealth, 15000); checkHealth();
</script>
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)
</body>
</html>"""
