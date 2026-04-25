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
            try {
                const res = await fetch('/health');
                if (res.ok) {
                    badge.textContent = 'System Online';
                    badge.classList.add('online');
                } else {
                    badge.textContent = 'Server Error';
                    badge.classList.remove('online');
                }
            } catch {
                badge.textContent = 'Server Offline';
                badge.classList.remove('online');
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
    </script>
</body>
</html>"""
