#!/usr/bin/env python3
"""
dashboard.py — OpenEnv Data Pipeline Debugger
Simple, professional, and reliable UI frontend.
"""

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenEnv Pipeline Debugger</title>
    <style>
        :root {
            --bg-color: #f9fafb;
            --text-color: #111827;
            --text-muted: #6b7280;
            --border-color: #e5e7eb;
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --bg-card: #ffffff;
            --sidebar-width: 240px;
            --success: #059669;
            --danger: #dc2626;
        }

            --navbar-height: 56px;
        }

        /* ── Global Navbar ───────────────────────────── */
        .topnav {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: var(--navbar-height);
            background: #0f172a;
            border-bottom: 1px solid #1e293b;
            display: flex;
            align-items: center;
            padding: 0 1.5rem;
            gap: 0;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        }
        .topnav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-weight: 700;
            font-size: 0.95rem;
            color: #f1f5f9;
            text-decoration: none;
            margin-right: 2rem;
            letter-spacing: -0.01em;
            white-space: nowrap;
        }
        .topnav-brand .logo-dot {
            width: 8px; height: 8px;
            background: #6366f1;
            border-radius: 50%;
            display: inline-block;
        }
        .topnav-links {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            flex: 1;
        }
        .topnav-link {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.85rem;
            border-radius: 6px;
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: background 0.18s, color 0.18s;
            white-space: nowrap;
        }
        .topnav-link:hover {
            background: rgba(255,255,255,0.07);
            color: #f1f5f9;
        }
        .topnav-link.active {
            background: rgba(99,102,241,0.18);
            color: #818cf8;
        }
        .topnav-link .nav-icon { font-size: 0.9rem; }
        .topnav-divider {
            width: 1px;
            height: 20px;
            background: #1e293b;
            margin: 0 0.5rem;
        }
        .topnav-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.78rem;
            font-weight: 500;
            margin-left: auto;
        }
        .status-dot {
            width: 7px; height: 7px;
            border-radius: 50%;
            background: #334155;
            transition: background 0.3s;
        }
        .status-dot.online  { background: #10b981; box-shadow: 0 0 6px #10b981; }
        .status-dot.offline { background: #ef4444; }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5;
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background-color: var(--bg-card);
            border-right: 1px solid var(--border-color);
            padding: 1.5rem 0;
            position: fixed;
            height: 100vh;
            top: var(--navbar-height);
            height: calc(100vh - var(--navbar-height));
            overflow-y: auto;
        }

        .brand {
            padding: 0 1.5rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }

        .brand h1 {
            font-size: 1.2rem;
            font-weight: 600;
        }

        .nav-item {
            padding: 0.75rem 1.5rem;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }

        .nav-item:hover {
            background-color: var(--bg-color);
            color: var(--text-color);
        }

        .nav-item.active {
            color: var(--primary-color);
            background-color: #eff6ff;
            border-left-color: var(--primary-color);
            font-weight: 500;
        }

        .nav-header {
            padding: 1rem 1.5rem 0.5rem;
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 0.05em;
        }

        /* Main Content */
        .main {
            margin-left: var(--sidebar-width);
            margin-top: var(--navbar-height);
            flex: 1;
            padding: 2rem 3rem;
            max-width: 1200px;
        }

        .page-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        .page-title h2 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .status-badge {
            font-size: 0.75rem;
            background-color: var(--border-color);
            color: var(--text-color);
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-weight: 500;
        }

        .status-badge.online {
            background-color: #d1fae5;
            color: var(--success);
        }

        /* Cards */
        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .card-header {
            font-weight: 600;
            margin-bottom: 1rem;
            font-size: 1rem;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        /* Stats */
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-box {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1.25rem;
        }

        .stat-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }

        .stat-val {
            font-size: 1.5rem;
            font-weight: 600;
        }

        /* Buttons & Forms */
        .ctrl-group {
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1rem;
        }

        select, input, button {
            padding: 0.5rem 1rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 0.9rem;
            font-family: inherit;
        }

        button {
            background-color: var(--bg-card);
            cursor: pointer;
            transition: 0.2s;
            font-weight: 500;
        }

        button:hover { background-color: var(--bg-color); }

        button.primary {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }

        button.primary:hover { background-color: var(--primary-hover); }

        /* Tables & Lists */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        .data-table th, .data-table td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        .data-table th {
            font-weight: 500;
            color: var(--text-muted);
            background-color: #f8fafc;
        }

        /* Timeline Log */
        .timeline {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }

        .timeline-item {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.85rem;
        }

        .timeline-item:last-child { border-bottom: none; }
        .timeline-action { font-weight: 600; margin-bottom: 0.2rem; }
        .timeline-desc { color: var(--text-muted); }
        .pos-amount { color: var(--success); font-weight: 600; }
        .neg-amount { color: var(--danger); font-weight: 600; }

        /* Panels */
        .panel { display: none; }
        .panel.active { display: block; }

    </style>
</head>
<body>

    <!-- ── Global Navigation Bar ────────────────────────── -->
    <nav class="topnav">
        <a class="topnav-brand" href="/">
            <span class="logo-dot"></span> OpenEnv Debugger
        </a>
        <div class="topnav-links">
            <a class="topnav-link active" href="/dashboard">
                <span class="nav-icon">📊</span> Dashboard
            </a>
            <a class="topnav-link" href="/demo">
                <span class="nav-icon">🎬</span> Demo
            </a>
            <a class="topnav-link" href="/compete">
                <span class="nav-icon">⚔️</span> Compete
            </a>
            <div class="topnav-divider"></div>
            <a class="topnav-link" href="/docs" target="_blank">
                <span class="nav-icon">📖</span> API Docs
            </a>
            <a class="topnav-link" href="/tasks" target="_blank">
                <span class="nav-icon">📋</span> Tasks
            </a>
            <a class="topnav-link" href="/health" target="_blank">
                <span class="nav-icon">🩺</span> Health
            </a>
        </div>
        <div class="topnav-status">
            <span class="status-dot" id="nav-dot"></span>
            <span id="nav-status-text" style="color:#94a3b8;">Connecting...</span>
        </div>
    </nav>

    <nav class="sidebar">
        <div class="brand">
            <h1>OpenEnv Debugger</h1>
        </div>
        
        <div class="nav-header">Workspace</div>
        <div class="nav-item active" onclick="showPanel('overview')">Overview</div>
        <div class="nav-item" onclick="showPanel('runner')">Run Episode</div>
        
        <div class="nav-header">Evaluation</div>
        <div class="nav-item" onclick="showPanel('benchmarks')">Benchmarks</div>
        <div class="nav-item" onclick="showPanel('docs')">System Docs</div>
        <div class="nav-header">Advanced</div>
        <div class="nav-item" id="nav-explain" onclick="showPanel('explain')">&#129504; Explainability</div>
        <div class="nav-item" id="nav-live" onclick="showPanel('live')">&#128307; Live Training</div>
        <div class="nav-item" id="nav-upload" onclick="showPanel('upload')">&#128196; CSV Auto-Debug</div>
    </nav>

    <main class="main">
        
        <!-- Overview Panel -->
        <div id="panel-overview" class="panel active">
            <div class="page-title">
                <h2>Dashboard Overview</h2>
                <span id="sys-status" class="status-badge">Connecting...</span>
            </div>

            <div class="stats">
                <div class="stat-box">
                    <div class="stat-label">Tasks Configured</div>
                    <div class="stat-val">5</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Action Space</div>
                    <div class="stat-val">11</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Baseline Agents</div>
                    <div class="stat-val">3</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Multi-Agent Roles</div>
                    <div class="stat-val">3</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Available Tasks</div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Task Identifier</th>
                            <th>Difficulty</th>
                            <th>Step Limit</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>task_easy_schema_fix</td><td>Easy</td><td>10</td></tr>
                        <tr><td>task_medium_data_quality</td><td>Medium</td><td>20</td></tr>
                        <tr><td>task_hard_pipeline_orchestration</td><td>Hard</td><td>40</td></tr>
                        <tr><td>task_veryhard_streaming_pipeline</td><td>Very Hard</td><td>50</td></tr>
                        <tr><td>task_expert_multi_source_join</td><td>Expert</td><td>60</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Runner Panel -->
        <div id="panel-runner" class="panel">
            <div class="page-title">
                <h2>Interactive Episode Runner</h2>
            </div>
            
            <div class="card">
                <div class="ctrl-group">
                    <select id="run-task">
                        <option value="task_easy_schema_fix">Easy: Schema Fix</option>
                        <option value="task_medium_data_quality">Medium: Data Quality</option>
                        <option value="task_hard_pipeline_orchestration">Hard: Orchestration</option>
                        <option value="task_veryhard_streaming_pipeline">Very Hard: Streaming</option>
                        <option value="task_expert_multi_source_join">Expert: Multi-Source</option>
                    </select>
                    <input type="number" id="run-seed" value="42" style="width: 80px;" placeholder="Seed">
                    <button class="primary" onclick="runEpisode()">Run Episode</button>
                    <button onclick="clearResults()">Clear</button>
                    <button class="primary" id="run-btn" onclick="runEpisode()">&#9654; Run Episode</button>
                    <button onclick="clearResults()">Clear</button>
                    <span id="run-progress" style="font-size:0.85rem;color:var(--text-muted)"></span>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-header">Execution Metrics</div>
                    <div id="metrics-output" style="font-size: 0.9rem; color: var(--text-muted);">
                        Ready to run.
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">Step-by-Step Log</div>
                    <div id="log-output" class="timeline">
                        <div style="padding:1rem;color:var(--text-muted);font-size:0.9rem;">No data.</div>
                    </div>
                </div>
            </div>

            <!-- Charts row -->
            <div class="grid" id="run-charts" style="display:none">
                <div class="card">
                    <div class="card-header">&#128200; Step Reward</div>
                    <canvas id="rewardChart" style="width:100%;display:block;height:180px"></canvas>
                </div>
                <div class="card">
                    <div class="card-header">&#128203; Metric Progression</div>
                    <canvas id="metricChart" style="width:100%;display:block;height:180px"></canvas>
                </div>
            </div>
        </div>

        <!-- Benchmarks Panel -->
        <div id="panel-benchmarks" class="panel">
            <div class="page-title">
                <h2>Baseline Benchmarks</h2>
            </div>
            <div class="card">
                <div class="ctrl-group">
                    <button class="primary" onclick="runBenchmarks()">Start Local Evaluation</button>
                    <span id="bench-status" style="font-size:0.85rem;color:var(--text-muted);"></span>
                </div>
            </div>
            <div id="benchmark-results">
                <div class="card">
                    <p style="color:var(--text-muted);font-size:0.9rem;text-align:center;padding:2rem;">
                        Click start to evaluate agents across available tasks.
                    </p>
                </div>
            </div>
        </div>

        <!-- Docs Panel -->
        <div id="panel-docs" class="panel">
            <div class="page-title">
                <h2>System Architecture</h2>
            </div>
            <div class="grid">
                <div class="card">
                    <div class="card-header">Data Flow</div>
                    <ul style="font-size:0.9rem;margin-left:1.2rem;line-height:2;">
                        <li><strong>Reset:</strong> Environment mounts task and injects flaws.</li>
                        <li><strong>Observe:</strong> Agent retrieves data slice, schema, and error logs.</li>
                        <li><strong>Act:</strong> Agent dispatches action commands to REST layer.</li>
                        <li><strong>Reward:</strong> Environment diffs constraints and calculates novelty points.</li>
                        <li><strong>Submit:</strong> Evaluated against multiple graders for accuracy.</li>
                    </ul>
                </div>
                <div class="card">
                    <div class="card-header">Reward Formula</div>
                    <pre style="background:#f1f5f9;padding:1rem;border-radius:4px;font-size:0.85rem;overflow-x:auto;">
R(t) = base_progress
      + novelty_bonus
      + cascade_bonus
      - regression_penalty
      - step_cost
      - repeat_penalty
      + (if final: submission_score × bonus)
                    </pre>
                </div>
            </div>
        </div>

        <!-- Explainability Panel -->
        <div id="panel-explain" class="panel">
            <div class="page-title"><h2>&#129504; Explainability Replay</h2></div>
            <div class="card" style="margin-bottom:1rem">
                <div class="card-header">Load Last Episode Replay</div>
                <div class="ctrl-group">
                    <button class="primary" onclick="loadReplay()">Load Replay from Last Episode</button>
                    <span id="explain-status" style="font-size:0.85rem;color:var(--text-muted)"></span>
                </div>
            </div>
            <div id="explain-steps"></div>
        </div>

        <!-- Live Training Panel -->
        <div id="panel-live" class="panel">
            <div class="page-title"><h2>&#128307; Live Training Stream</h2></div>
            <div class="card">
                <div class="ctrl-group">
                    <button class="primary" id="train-btn" onclick="startTraining()">&#9654; Run Training Episode</button>
                    <span id="ws-status" style="font-size:0.85rem;color:var(--text-muted)">WebSocket: disconnected</span>
                </div>
                <div style="display:flex;gap:1rem;margin-top:0.75rem;flex-wrap:wrap">
                    <div class="stat-box" style="flex:1"><div class="stat-label">Episode</div><div class="stat-val" id="live-ep">0</div></div>
                    <div class="stat-box" style="flex:1"><div class="stat-label">Step</div><div class="stat-val" id="live-step">-</div></div>
                    <div class="stat-box" style="flex:1"><div class="stat-label">Cumulative Reward</div><div class="stat-val" id="live-reward">0.00</div></div>
                    <div class="stat-box" style="flex:1"><div class="stat-label">Last Action</div><div class="stat-val" id="live-action" style="font-size:1rem">-</div></div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">Score Chart (real-time)</div>
                <canvas id="liveChart" height="200" style="width:100%;display:block"></canvas>
            </div>
            <div class="card">
                <div class="card-header">Step Log</div>
                <div id="live-log" class="timeline" style="max-height:250px"></div>
            </div>
        </div>

        <!-- CSV Upload Panel -->
        <div id="panel-upload" class="panel">
            <div class="page-title"><h2>&#128196; CSV Auto-Debug</h2></div>
            <div class="card">
                <div class="card-header">Upload Your CSV</div>
                <div id="drop-zone" onclick="document.getElementById('csv-file').click()" style="border:2px dashed var(--border-color);border-radius:8px;padding:3rem;text-align:center;cursor:pointer;transition:border-color 0.2s;margin-bottom:1rem" ondragover="event.preventDefault();this.style.borderColor='var(--primary-color)'" ondragleave="this.style.borderColor='var(--border-color)'" ondrop="handleDrop(event)">
                    <div style="font-size:2.5rem;margin-bottom:0.5rem">&#128196;</div>
                    <div style="font-weight:600">Drop your CSV file here or click to browse</div>
                    <div style="font-size:0.85rem;color:var(--text-muted);margin-top:0.25rem">The agent will automatically detect and fix data quality issues</div>
                </div>
                <input type="file" id="csv-file" accept=".csv" style="display:none" onchange="uploadCSV(this.files[0])">
                <span id="upload-status" style="font-size:0.85rem;color:var(--text-muted)"></span>
            </div>
            <div id="upload-summary" style="display:none" class="card">
                <div class="card-header">Dataset Summary</div>
                <div id="upload-meta" style="font-size:0.9rem;line-height:2"></div>
            </div>
            <div id="upload-steps"></div>
        </div>

    </main>

    <script>
        // UI Navigation
        function showPanel(id) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('panel-' + id).classList.add('active');
            event.currentTarget.classList.add('active');
        }

        // Server Health Auto-Check
        async function checkHealth() {
            const badge = document.getElementById('sys-status');
        // Server Health Auto-Check (sidebar badge + navbar dot)
        async function checkHealth() {
            const badge   = document.getElementById('sys-status');
            const dot     = document.getElementById('nav-dot');
            const navText = document.getElementById('nav-status-text');
            try {
                const res = await fetch('/health');
                if (res.ok) {
                    badge.textContent = 'System Online';
                    badge.classList.add('online');
                } else {
                    badge.textContent = 'Server Error';
                    badge.classList.remove('online');
                    dot.className = 'status-dot online';
                    navText.textContent = 'Online';
                    navText.style.color = '#10b981';
                } else {
                    badge.textContent = 'Server Error';
                    badge.classList.remove('online');
                    dot.className = 'status-dot offline';
                    navText.textContent = 'Error';
                    navText.style.color = '#ef4444';
                }
            } catch {
                badge.textContent = 'Server Offline';
                badge.classList.remove('online');
                dot.className = 'status-dot offline';
                navText.textContent = 'Offline';
                navText.style.color = '#ef4444';
            }
        }
        setInterval(checkHealth, 15000);
        checkHealth();

        // Runner Logic
        async function runEpisode() {
            const taskId = document.getElementById('run-task').value;
            const seed = parseInt(document.getElementById('run-seed').value) || 42;
            const metOut = document.getElementById('metrics-output');
            const logOut = document.getElementById('log-output');

            metOut.innerHTML = 'Resetting environment...';
            logOut.innerHTML = '';

            try {
                // Initialize episode
            const prog   = document.getElementById('run-progress');
            const btn    = document.getElementById('run-btn');

            metOut.innerHTML = 'Resetting environment...';
            logOut.innerHTML = '';
            document.getElementById('run-charts').style.display = 'none';
            btn.disabled = true; btn.textContent = '⏳ Running...';
            prog.textContent = '';

            // Per-step data for charts
            const _rewards = [];   // {step, val}
            const _metrics = [];   // {step, completeness, uniqueness, validity}
            const _labels  = [];

            try {
                let res = await fetch('/reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task_id: taskId, seed: seed})
                });
                
                if (!res.ok) throw new Error(await res.text());
                let obs = await res.json();

                let stepNum = 0;
                let done = obs.done || false;
                let logsHtml = '';
                const maxSteps = obs.max_steps || 40;

                metOut.innerHTML = `Running task wrapper for ${taskId}...`;
                let cumReward = 0;

                prog.textContent = `Step 0 / ${maxSteps}`;

                while (!done && stepNum < maxSteps) {
                    const action = chooseSimpleAction(obs, stepNum);
                    const stepRes = await fetch('/step', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(action)
                    });
                    
                    if (!stepRes.ok) throw new Error(await stepRes.text());
                    const payload = await stepRes.json();
                    obs = payload.observation || payload; // Fix structure mismatch
                    
                    stepNum++;
                    done = payload.done || obs.done || false;
                    
                    const rewVal = (typeof payload.reward === 'number') ? payload.reward : (payload.reward?.value || 0);
                    const rewStr = (rewVal > 0) ? `<span class="pos-amount">+${rewVal.toFixed(4)}</span>` : `<span class="neg-amount">${rewVal.toFixed(4)}</span>`;
                    
                    logsHtml += `
                        <div class="timeline-item">
                            <div class="timeline-action">Step ${stepNum}: ${action.action_type}</div>
                            <div class="timeline-desc">${obs.hint || 'Action executed.'} | Reward: ${rewStr}</div>
                        </div>`;
                    if (!stepRes.ok) throw new Error(await stepRes.text());
                    const payload = await stepRes.json();
                    obs = payload.observation || payload;

                    stepNum++;
                    done = payload.done || obs.done || false;
                    const rewVal = (typeof payload.reward === 'number') ? payload.reward : (payload.reward?.value || 0);
                    cumReward = payload.reward?.cumulative ?? (cumReward + rewVal);
                    const m = obs.metrics || {};

                    // Collect chart data
                    _labels.push(`S${stepNum}`);
                    _rewards.push(rewVal);
                    _metrics.push({
                        completeness: m.completeness || 0,
                        uniqueness:   m.uniqueness   || 0,
                        validity:     m.validity     || 0,
                    });

                    const rewStr = rewVal > 0
                        ? `<span class="pos-amount">+${rewVal.toFixed(4)}</span>`
                        : `<span class="neg-amount">${rewVal.toFixed(4)}</span>`;

                    logsHtml += `
                        <div class="timeline-item">
                            <div class="timeline-action">Step ${stepNum}: ${action.action_type}</div>
                            <div class="timeline-desc">${obs.hint || 'Action executed.'} | Reward: ${rewStr} | Cumulative: ${cumReward.toFixed(4)}</div>
                        </div>`;

                    prog.textContent = `Step ${stepNum} / ${maxSteps}  |  Cumulative: ${cumReward.toFixed(4)}`;
                }

                if (!done) {
                    const subRes = await fetch('/step', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({action_type: 'submit'})
                    });
                    obs = await subRes.json();
                    logsHtml += `
                        <div class="timeline-item">
                            <div class="timeline-action">Step ${stepNum+1}: submit</div>
                            <div class="timeline-desc">Forced submission due to timeout.</div>
                        </div>`;
                    const subPayload = await subRes.json();
                    const subObs = subPayload.observation || subPayload;
                    const subRew = subPayload.reward?.value || 0;
                    cumReward = subPayload.reward?.cumulative ?? cumReward;
                    const subM  = subObs.metrics || {};
                    _labels.push(`S${stepNum+1}`);
                    _rewards.push(subRew);
                    _metrics.push({ completeness: subM.completeness||0, uniqueness: subM.uniqueness||0, validity: subM.validity||0 });
                    logsHtml += `
                        <div class="timeline-item">
                            <div class="timeline-action">Step ${stepNum+1}: submit</div>
                            <div class="timeline-desc">Forced submission. Final cumulative: ${cumReward.toFixed(4)}</div>
                        </div>`;
                    obs = subObs;
                }

                const m = obs.metrics || {};
                metOut.innerHTML = `
                    <div style="display:flex; flex-direction:column; gap:0.5rem;">
                        <div><strong>Steps Consumed:</strong> ${stepNum}</div>
                        <div><strong>Data Completeness:</strong> ${(m.completeness||0).toFixed(4)}</div>
                        <div><strong>Data Uniqueness:</strong> ${(m.uniqueness||0).toFixed(4)}</div>
                        <div><strong>Schema Validity:</strong> ${(m.validity||0).toFixed(4)}</div>
                    </div>
                `;
                logOut.innerHTML = logsHtml;

            } catch (err) {
                metOut.innerHTML = `<span style="color:var(--danger)">Error: ${err.message}</span>`;
            }
        }

                    <div style="display:flex;flex-direction:column;gap:0.5rem">
                        <div><strong>Steps:</strong> ${stepNum}</div>
                        <div><strong>Cumulative Reward:</strong> <span style="font-weight:700;color:var(--primary-color)">${cumReward.toFixed(4)}</span></div>
                        <div><strong>Completeness:</strong> ${(m.completeness||0).toFixed(4)}</div>
                        <div><strong>Uniqueness:</strong>   ${(m.uniqueness||0).toFixed(4)}</div>
                        <div><strong>Validity:</strong>     ${(m.validity||0).toFixed(4)}</div>
                    </div>`;
                logOut.innerHTML = logsHtml;
                prog.textContent = `Done — ${stepNum} steps, score ${cumReward.toFixed(4)}`;

                // Show container FIRST so clientWidth is non-zero, then draw
                document.getElementById('run-charts').style.display = 'grid';
                requestAnimationFrame(() => {
                    _drawRewardChart(_labels, _rewards);
                    _drawMetricChart(_labels, _metrics);
                });

            } catch (err) {
                metOut.innerHTML = `<span style="color:var(--danger)">Error: ${err.message}</span>`;
            } finally {
                btn.disabled = false; btn.textContent = '▶ Run Episode';
            }
        }

        function _drawRewardChart(labels, rewards) {
            // Build cumulative from per-step rewards
            const cumulative = [];
            let running = 0;
            rewards.forEach(r => { running += r; cumulative.push(running); });
            _drawEpisodeChart('rewardChart', labels, cumulative);
        }

        function _drawMetricChart(labels, metrics) {
            // Use validity as the "quality score" line matching live training style
            const vals = metrics.map(m => m.completeness || 0);
            _drawEpisodeChart('metricChart', labels, vals, '#10b981', 'Completeness');
        }

        function _drawEpisodeChart(canvasId, labels, values, lineColor, lineLabel) {
            lineColor = lineColor || '#6366f1';
            lineLabel = lineLabel || 'Cumulative Reward';
            const canvas = document.getElementById(canvasId);
            const rawW = canvas.parentElement.clientWidth - 32;
            const W = rawW > 50 ? rawW : 400;   // fallback if hidden/0
            const H = 200;
            canvas.width  = W * 2; canvas.height = H * 2;
            canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
            const ctx = canvas.getContext('2d');
            ctx.scale(2, 2);
            ctx.clearRect(0, 0, W, H);

            if (values.length < 1) return;
            const maxV = Math.max(...values.map(Math.abs), 0.01);
            const minV = Math.min(...values, 0);
            const range = maxV - minV || 0.01;

            const pad = {l:44, r:12, t:12, b:32};
            const gW  = W - pad.l - pad.r;
            const gH  = H - pad.t - pad.b;
            const n   = values.length;

            // Grid lines
            ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 0.5;
            for (let i = 0; i <= 4; i++) {
                const y = pad.t + gH * (1 - i/4);
                ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + gW, y); ctx.stroke();
                ctx.fillStyle = '#9ca3af'; ctx.font = '9px sans-serif'; ctx.textAlign = 'right';
                const val = minV + (range * i/4);
                ctx.fillText(val.toFixed(2), pad.l - 5, y + 3);
            }

            // X-axis labels
            ctx.fillStyle = '#9ca3af'; ctx.font = '9px sans-serif'; ctx.textAlign = 'center';
            labels.forEach((l, i) => {
                if (n <= 10 || i % Math.ceil(n/8) === 0) {
                    const x = pad.l + (n === 1 ? gW/2 : (i/(n-1)) * gW);
                    ctx.fillText(l, x, pad.t + gH + 18);
                }
            });

            // Gradient fill under line
            const gradY0 = pad.t;
            const gradY1 = pad.t + gH;
            const grad = ctx.createLinearGradient(0, gradY0, 0, gradY1);
            grad.addColorStop(0, lineColor + '33');
            grad.addColorStop(1, lineColor + '05');
            ctx.beginPath();
            values.forEach((v, i) => {
                const x = pad.l + (n === 1 ? gW/2 : (i/(n-1)) * gW);
                const y = pad.t + gH * (1 - (v - minV) / range);
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            });
            // Close fill to baseline
            ctx.lineTo(pad.l + (n === 1 ? gW/2 : gW), pad.t + gH);
            ctx.lineTo(pad.l, pad.t + gH);
            ctx.closePath();
            ctx.fillStyle = grad; ctx.fill();

            // Main line
            ctx.beginPath(); ctx.lineWidth = 2; ctx.strokeStyle = lineColor;
            ctx.lineJoin = 'round';
            values.forEach((v, i) => {
                const x = pad.l + (n === 1 ? gW/2 : (i/(n-1)) * gW);
                const y = pad.t + gH * (1 - (v - minV) / range);
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            });
            ctx.stroke();

            // Dots — last one is green (episode end)
            values.forEach((v, i) => {
                const x = pad.l + (n === 1 ? gW/2 : (i/(n-1)) * gW);
                const y = pad.t + gH * (1 - (v - minV) / range);
                ctx.beginPath(); ctx.arc(x, y, i === n-1 ? 4 : 2.5, 0, Math.PI*2);
                ctx.fillStyle = i === n-1 ? '#10b981' : lineColor; ctx.fill();
                if (i === n-1) {
                    ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI*2);
                    ctx.strokeStyle = '#10b98144'; ctx.lineWidth = 1.5; ctx.stroke();
                }
            });

            // Legend label top-left
            ctx.fillStyle = lineColor; ctx.font = 'bold 9px sans-serif'; ctx.textAlign = 'left';
            ctx.fillText('● ' + lineLabel, pad.l + 2, pad.t - 2);
        }


        // Basic heuristic client for demo purposes
        function chooseSimpleAction(obs, stepNum) {
            if (stepNum === 0) {
                window._demoHistory = new Set();
                return {action_type: 'inspect'};
            }
            
            const errs = (obs.error_log || []).join(' ').toLowerCase();
            const schema = obs.schema_info || [];
            const taskId = obs.task_id || '';
            const history = window._demoHistory || new Set();
            
            // Fix schema mismatches
            for (const sf of schema) {
                if (sf.expected_type && sf.actual_type && sf.expected_type !== sf.actual_type) {
                    return {action_type: 'cast_column', column: sf.name, value: sf.expected_type};
                }
            }
            
            // Fix stage ordering for harder tasks
            if ((taskId.includes('hard') || taskId.includes('expert')) && errs.includes('stage') && !history.has('stage')) {
                history.add('stage');
                return {action_type: 'reorder_stages', parameters: {stages: ['ingest','validate','transform','enrich','load']}};
            }

            if (errs.includes('duplicate') && !history.has('dup')) {
                history.add('dup');
                return {action_type: 'drop_duplicates'};
            }
            
            // Fill nulls in first schema column
            if (errs.includes('null') && schema.length > 0 && !history.has('nulls')) {
                history.add('nulls');
                return {action_type: 'fill_nulls', column: schema[0].name, value: '0'};
            }
            
            // Business rules
            if (errs.includes('discount') && !history.has('rule_disc')) {
                history.add('rule_disc');
                return {action_type: 'apply_business_rule', value: 'discount_lte_1'};
            }
            if (errs.includes('fraud') && !history.has('rule_fraud')) {
                history.add('rule_fraud');
                return {action_type: 'apply_business_rule', value: 'fraud_score_lte_1'};
            }
            if (errs.includes('currency') && !history.has('rule_curr')) {
                history.add('rule_curr');
                return {action_type: 'apply_business_rule', value: 'currency_3char'};
            }

            if (stepNum % 3 === 0 && !history.has('val_' + stepNum)) {
                history.add('val_' + stepNum);
                return {action_type: 'validate'};
            }
            
            return {action_type: 'submit'};
        }

        function clearResults() {
            document.getElementById('metrics-output').innerHTML = 'Ready to run.';
            document.getElementById('log-output').innerHTML = '<div style="padding:1rem;color:var(--text-muted);font-size:0.9rem;">No data.</div>';
        }

        // Benchmarks Logic
        async function runBenchmarks() {
            const stat = document.getElementById('bench-status');
            const resArea = document.getElementById('benchmark-results');
            stat.textContent = 'Evaluating agents... (this may take a few moments)';
            
            try {
                const res = await fetch('/api/benchmark');
                if (!res.ok) throw new Error('Benchmark API failed');
                const data = await res.json();
                
                let rows = '';
                for (const r of data.results || []) {
                    rows += `<tr>
                        <td>${r.agent}</td>
                        <td>${(r.task_id||'').replace('task_','')}</td>
                        <td><strong>${(r.avg_score||r.score||0).toFixed(4)}</strong></td>
                        <td>${(r.avg_steps||r.steps||0).toFixed(1)}</td>
                    </tr>`;
                }

                resArea.innerHTML = `
                    <div class="card">
                        <table class="data-table">
                            <thead><tr><th>Policy Agent</th><th>Dataset Target</th><th>Average Score</th><th>Max Steps</th></tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                `;
                stat.textContent = 'Evaluation complete.';
            } catch(e) {
                stat.textContent = '';
                resArea.innerHTML = `<div class="card" style="color:var(--danger)">Failed to evaluate: ${e.message}</div>`;
            }
        }

        // ── Feature 1: Explainability Replay ──────────────────────────
        async function loadReplay() {
            const status = document.getElementById('explain-status');
            const area   = document.getElementById('explain-steps');
            status.textContent = 'Loading...';
            area.innerHTML = '';
            try {
                const res  = await fetch('/api/replay');
                const data = await res.json();
                if (!data.steps || data.steps.length === 0) {
                    status.textContent = 'No replay data — run an episode first (Run Episode panel).';
                    return;
                }
                status.textContent = `Task: ${data.task_id} | ${data.steps.length} steps`;
                data.steps.forEach(s => {
                    const rColor = s.reward >= 0 ? '#059669' : '#dc2626';
                    const compHtml = Object.entries(s.reward_components || {}).map(
                        ([k,v]) => `<span style="background:#f1f5f9;padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;margin-right:0.3rem">${k}: ${v}</span>`
                    ).join('');
                    area.innerHTML += `
                        <div class="card" style="margin-bottom:1rem;border-left:4px solid ${rColor}">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem">
                                <strong>Step ${s.step}: ${s.action}</strong>
                                <span style="color:${rColor};font-weight:700;font-size:1rem">Reward: ${s.reward >= 0 ? '+' : ''}${s.reward}</span>
                            </div>
                            <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.5rem"><strong>&#128065; Observed:</strong> ${s.observation_summary || '-'}</div>
                            <div style="font-size:0.85rem;margin-bottom:0.5rem;background:#f0fdf4;padding:0.6rem;border-radius:6px">&#129504; <strong>Reasoning:</strong> ${s.reasoning || '-'}</div>
                            <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.35rem"><strong>Description:</strong> ${s.description}</div>
                            <div>${compHtml}</div>
                        </div>`;
                });
            } catch(e) { status.textContent = 'Error: ' + e.message; }
        }

        // ── Feature 2: WebSocket Live Training ────────────────────────
        let _ws = null;
        let _epCount = 0;
        let _chartData = [];
        let _chartCtx  = null;

        function initChart() {
            const canvas = document.getElementById('liveChart');
            if (!canvas) return;
            _chartCtx = canvas.getContext('2d');
        }

        function drawLiveChart() {
            const canvas = document.getElementById('liveChart');
            if (!canvas || !_chartCtx) return;
            const W = canvas.parentElement.clientWidth - 32;
            canvas.width  = W * 2; canvas.height = 400;
            canvas.style.width = W + 'px'; canvas.style.height = '200px';
            const ctx = _chartCtx;
            ctx.scale(2, 2);
            const w = W, h = 200;
            ctx.clearRect(0, 0, w, h);
            if (_chartData.length < 2) return;
            const maxV  = Math.max(..._chartData.map(d => d.v), 0.1);
            const pad = {l:40,r:10,t:10,b:30};
            const gW = w-pad.l-pad.r, gH = h-pad.t-pad.b;
            ctx.strokeStyle='#e5e7eb'; ctx.lineWidth=0.5;
            for (let i=0;i<=4;i++) {
                const y = pad.t + gH*(1-i/4);
                ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(pad.l+gW,y); ctx.stroke();
                ctx.fillStyle='#9ca3af'; ctx.font='9px sans-serif'; ctx.textAlign='right';
                ctx.fillText((maxV*i/4).toFixed(2), pad.l-4, y+3);
            }
            ctx.beginPath(); ctx.lineWidth=2; ctx.strokeStyle='#6366f1';
            _chartData.forEach((d,i) => {
                const x = pad.l + (i/(_chartData.length-1))*gW;
                const y = pad.t + gH*(1 - d.v/maxV);
                i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
            });
            ctx.stroke();
            _chartData.forEach((d,i) => {
                const x = pad.l + (i/(_chartData.length-1))*gW;
                const y = pad.t + gH*(1 - d.v/maxV);
                ctx.beginPath(); ctx.arc(x,y,3,0,Math.PI*2);
                ctx.fillStyle = d.ep_end ? '#10b981' : '#6366f1'; ctx.fill();
            });
        }

        function connectWS() {
            const proto = location.protocol === 'https:' ? 'wss' : 'ws';
            _ws = new WebSocket(`${proto}://${location.host}/ws/train`);
            _ws.onopen = () => {
                document.getElementById('ws-status').textContent = 'WebSocket: connected ✓';
                document.getElementById('ws-status').style.color = '#059669';
            };
            _ws.onclose = () => {
                document.getElementById('ws-status').textContent = 'WebSocket: disconnected';
                document.getElementById('ws-status').style.color = '#dc2626';
            };
            _ws.onmessage = (e) => {
                const msg = JSON.parse(e.data);
                if (msg.type === 'step') {
                    document.getElementById('live-step').textContent   = msg.step;
                    document.getElementById('live-reward').textContent = msg.cumulative.toFixed(4);
                    document.getElementById('live-action').textContent = msg.action;
                    _chartData.push({v: msg.cumulative, ep_end: false});
                    document.getElementById('live-log').innerHTML = `<div class="timeline-item"><div class="timeline-action">Step ${msg.step}: ${msg.action}</div><div class="timeline-desc">Reward: <span class="${msg.reward>=0?'pos':'neg'}-amount">${msg.reward>=0?'+':''}${msg.reward}</span> | Cumulative: ${msg.cumulative.toFixed(4)}</div></div>` + document.getElementById('live-log').innerHTML;
                    drawLiveChart();
                } else if (msg.type === 'episode_end') {
                    _epCount++;
                    document.getElementById('live-ep').textContent = _epCount;
                    _chartData.push({v: msg.final_score, ep_end: true});
                    drawLiveChart();
                }
            };
        }

        async function startTraining() {
            if (!_ws || _ws.readyState !== WebSocket.OPEN) {
                initChart(); connectWS();
                await new Promise(r => setTimeout(r, 600));
            }
            document.getElementById('train-btn').disabled = true;
            document.getElementById('train-btn').textContent = '⏳ Running...';
            try {
                await fetch('/api/train-episode', {method:'POST'});
            } finally {
                document.getElementById('train-btn').disabled = false;
                document.getElementById('train-btn').textContent = '▶ Run Training Episode';
            }
        }

        // ── Feature 3: CSV Upload Auto-Debug ──────────────────────────
        function handleDrop(e) {
            e.preventDefault();
            document.getElementById('drop-zone').style.borderColor = 'var(--border-color)';
            const file = e.dataTransfer.files[0];
            if (file) uploadCSV(file);
        }

        async function uploadCSV(file) {
            if (!file) return;
            const status  = document.getElementById('upload-status');
            const summary = document.getElementById('upload-summary');
            const stepsEl = document.getElementById('upload-steps');
            const meta    = document.getElementById('upload-meta');
            status.textContent = `Uploading ${file.name}...`;
            summary.style.display = 'none';
            stepsEl.innerHTML = '';
            const form = new FormData();
            form.append('file', file);
            try {
                const res  = await fetch('/api/upload-debug', {method:'POST', body:form});
                const data = await res.json();
                if (data.status === 'error') { status.textContent = '❌ ' + data.message; return; }
                status.textContent = '✅ Debug complete!';
                const nullInfo = Object.entries(data.null_counts||{}).filter(([,v])=>v>0).map(([k,v])=>`${k}:${v}`).join(', ');
                meta.innerHTML = `<div><strong>File:</strong> ${data.filename}</div><div><strong>Rows:</strong> ${data.rows}</div><div><strong>Columns:</strong> ${data.columns.join(', ')}</div><div><strong>Nulls:</strong> ${nullInfo||'None'}</div><div><strong>Duplicates:</strong> ${data.duplicate_count}</div><div><strong>Final Score:</strong> <span style="color:var(--success);font-weight:700">${data.final_score}</span></div>`;
                summary.style.display = 'block';
                data.steps.forEach(s => {
                    const rColor = (s.reward||0)>=0 ? '#059669' : '#dc2626';
                    stepsEl.innerHTML += `<div class="card" style="margin-bottom:0.75rem;border-left:4px solid ${rColor}">
                        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem">
                            <strong>Step ${s.step}: ${s.action}</strong>
                            <span style="color:${rColor};font-weight:600">${(s.reward||0)>=0?'+':''}${s.reward||0}</span>
                        </div>
                        <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.35rem">&#128065; ${s.observation_summary||'-'}</div>
                        <div style="font-size:0.85rem;background:#f0fdf4;padding:0.5rem;border-radius:6px">&#129504; ${s.reasoning||'-'}</div>
                        <div style="font-size:0.8rem;color:var(--text-muted);margin-top:0.35rem">${s.description||''}</div></div>`;
                });
            } catch(e) { status.textContent = '❌ Error: ' + e.message; }
        }
    </script>
</body>
</html>"""
