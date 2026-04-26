#!/usr/bin/env python3
"""
demo.py — Self-running Demo Mode for OpenEnv Data Pipeline Debugger.
Produces a standalone or served HTML page with embedded replays and charts to showcase the project to judges.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Any

def get_demo_html() -> str:
    """Return the full HTML for the self-running demo dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenEnv Debugger — Auto-Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0e1a;
            --bg-card: #1a1f35;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: #1e293b;
        }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            margin: 0;
            padding: 2rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 3rem;
        }
        header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        .card h2 {
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
        }
        .tab {
            padding: 0.5rem 1.5rem;
            background: rgba(99,102,241,0.1);
            color: var(--text-secondary);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .tab:hover, .tab.active {
            background: var(--accent);
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
            animation: fadeIn 0.4s;
        }
        @keyframes fadeIn {
            from {opacity: 0; transform: translateY(10px);}
            to {opacity: 1; transform: translateY(0);}
        }
        iframe {
            width: 100%;
            height: 600px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #fff;
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🎬 OpenEnv Auto-Demo Mode</h1>
        <p style="color:var(--text-secondary)">Experience the autonomous ETL debugging agent without running any code.</p>
    </header>

    <div class="card">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('training')">📈 Training Curve</div>
            <div class="tab" onclick="switchTab('replay-easy')">🟢 Easy Replay</div>
            <div class="tab" onclick="switchTab('replay-medium')">🟡 Medium Replay</div>
            <div class="tab" onclick="switchTab('replay-hard')">🔴 Hard Replay</div>
            <div class="tab" onclick="switchTab('dashboard')">⚙️ Interactive Dashboard</div>
        </div>

        <div id="tab-training" class="tab-content active">
            <h2>Curriculum Learning Progress</h2>
            <p style="color:var(--text-secondary);margin-bottom:1rem;">
                This chart demonstrates how the agent improves over time, starting from random actions 
                to mastering complex, multi-stage pipelines.
            </p>
            <div style="background:rgba(255,255,255,0.05);padding:2rem;border-radius:8px;text-align:center;">
                <!-- Placeholder for training chart if available -->
                <p>Run training to generate the reward curve chart, or check the 'Interactive Dashboard' tab to run dynamically.</p>
            </div>
        </div>

        <div id="tab-replay-easy" class="tab-content">
            <h2>Easy Task: Schema Fix</h2>
            <div style="padding:1rem;background:rgba(16,185,129,0.1);border-radius:8px;margin-bottom:1rem;">
                <strong>Goal:</strong> Fix wrong column types in a CSV. Agent must correctly cast types to make the schema valid.
            </div>
            <iframe src="/dashboard" sandbox="allow-scripts allow-same-origin" title="Interactive Dashboard"></iframe>
            <div style="text-align:center;margin-top:0.5rem;font-size:0.85rem;color:var(--text-muted);">
                Loaded interactive dashboard due to missing static replay template
            </div>
        </div>

        <div id="tab-replay-medium" class="tab-content">
             <h2>Medium Task: Data Quality Remediation</h2>
            <div style="padding:1rem;background:rgba(245,158,11,0.1);border-radius:8px;margin-bottom:1rem;">
                <strong>Goal:</strong> Clean a multi-source ingestion pipeline with nulls, outliers, and duplicates in the right order.
            </div>
            <iframe src="/dashboard" sandbox="allow-scripts allow-same-origin" title="Interactive Dashboard"></iframe>
            <div style="text-align:center;margin-top:0.5rem;font-size:0.85rem;color:var(--text-muted);">
                Loaded interactive dashboard due to missing static replay template
            </div>
        </div>

        <div id="tab-replay-hard" class="tab-content">
             <h2>Hard Task: Pipeline Orchestration</h2>
            <div style="padding:1rem;background:rgba(239,68,68,0.1);border-radius:8px;margin-bottom:1rem;">
                <strong>Goal:</strong> Fix a scrambled 5-stage pipeline with interconnected bugs and strict schemas.
            </div>
            <iframe src="/dashboard" sandbox="allow-scripts allow-same-origin" title="Interactive Dashboard"></iframe>
            <div style="text-align:center;margin-top:0.5rem;font-size:0.85rem;color:var(--text-muted);">
                Loaded interactive dashboard due to missing static replay template
            </div>
        </div>

        <div id="tab-dashboard" class="tab-content">
             <h2>Interactive Dashboard</h2>
             <p style="color:var(--text-secondary);margin-bottom:1rem;">Explore the agent directly.</p>
             <iframe src="/dashboard" sandbox="allow-scripts allow-same-origin" title="Interactive Dashboard"></iframe>
        </div>
    </div>
</div>

<script>
            --bg-color: #f9fafb; --text-color: #111827; --text-muted: #6b7280;
            --border-color: #e5e7eb; --primary-color: #2563eb; --primary-hover: #1d4ed8;
            --bg-card: #ffffff; --success: #059669; --danger: #dc2626; --navbar-height: 56px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',system-ui,sans-serif; background:var(--bg-color); color:var(--text-color); line-height:1.6; }

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

        /* ── Page Content ── */
        .page-wrapper { margin-top:var(--navbar-height); padding:2rem; max-width:1280px; margin-left:auto; margin-right:auto; }
        .hero { text-align:center; padding:3rem 1rem 2rem; }
        .hero h1 { font-size:2.2rem; font-weight:800; background:linear-gradient(135deg,#2563eb,#6366f1,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.5rem; }
        .hero p { color:var(--text-muted); font-size:1.05rem; max-width:600px; margin:0 auto; }

        .stats-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin:2rem 0; }
        .stat-card { background:var(--bg-card); border:1px solid var(--border-color); border-radius:10px; padding:1.25rem; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.06); transition:transform 0.2s,box-shadow 0.2s; }
        .stat-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.1); }
        .stat-card .stat-num { font-size:2rem; font-weight:800; color:var(--primary-color); }
        .stat-card .stat-label { font-size:0.8rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; margin-top:0.25rem; }

        .card { background:var(--bg-card); border:1px solid var(--border-color); border-radius:10px; padding:1.75rem; margin-bottom:1.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.06); }
        .card h2 { font-size:1.15rem; font-weight:700; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid var(--border-color); }
        .card h3 { font-size:0.95rem; font-weight:600; margin-bottom:0.5rem; color:var(--text-color); }

        .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }
        @media(max-width:768px) { .grid-2 { grid-template-columns:1fr; } }

        /* Tabs */
        .tabs { display:flex; gap:0.5rem; margin-bottom:1.5rem; flex-wrap:wrap; }
        .tab { padding:0.5rem 1.25rem; background:var(--bg-color); border:1px solid var(--border-color); color:var(--text-muted); border-radius:8px; cursor:pointer; font-size:0.85rem; font-weight:600; transition:all 0.2s; }
        .tab:hover { border-color:var(--primary-color); color:var(--primary-color); }
        .tab.active { background:var(--primary-color); color:#fff; border-color:var(--primary-color); }
        .tab-content { display:none; animation:fadeUp 0.3s ease; }
        .tab-content.active { display:block; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

        /* Agent Cards */
        .agent-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1rem; }
        .agent-card { background:var(--bg-color); border:1px solid var(--border-color); border-radius:10px; padding:1.25rem; transition:transform 0.2s,box-shadow 0.2s; border-top:3px solid var(--primary-color); }
        .agent-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.08); }
        .agent-card .agent-icon { font-size:1.5rem; margin-bottom:0.5rem; }
        .agent-card .agent-name { font-weight:700; font-size:0.9rem; margin-bottom:0.25rem; }
        .agent-card .agent-desc { font-size:0.78rem; color:var(--text-muted); line-height:1.5; }
        .agent-card:nth-child(2) { border-top-color:#6366f1; }
        .agent-card:nth-child(3) { border-top-color:#10b981; }
        .agent-card:nth-child(4) { border-top-color:#f59e0b; }
        .agent-card:nth-child(5) { border-top-color:#ef4444; }
        .agent-card:nth-child(6) { border-top-color:#8b5cf6; }

        /* Algorithm Flow */
        .flow-steps { display:flex; align-items:center; gap:0; flex-wrap:wrap; justify-content:center; margin:1rem 0; }
        .flow-step { background:var(--bg-color); border:1px solid var(--border-color); border-radius:8px; padding:0.6rem 1rem; font-size:0.8rem; font-weight:600; white-space:nowrap; }
        .flow-arrow { color:var(--primary-color); font-weight:700; padding:0 0.4rem; font-size:1rem; }

        /* Chart Canvas */
        .chart-container { background:var(--bg-color); border:1px solid var(--border-color); border-radius:8px; padding:1rem; position:relative; height:280px; }
        canvas { width:100%!important; height:100%!important; }

        /* Table */
        .data-table { width:100%; border-collapse:collapse; font-size:0.85rem; }
        .data-table th,.data-table td { padding:0.6rem 1rem; text-align:left; border-bottom:1px solid var(--border-color); }
        .data-table th { font-weight:600; color:var(--text-muted); background:var(--bg-color); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.04em; }
        .badge { display:inline-block; padding:0.15rem 0.6rem; border-radius:999px; font-size:0.72rem; font-weight:600; }
        .badge-green { background:#d1fae5; color:#059669; }
        .badge-blue { background:#dbeafe; color:#2563eb; }
        .badge-yellow { background:#fef3c7; color:#d97706; }
        .badge-red { background:#fee2e2; color:#dc2626; }
        .badge-purple { background:#ede9fe; color:#7c3aed; }

        iframe { width:100%; height:500px; border:1px solid var(--border-color); border-radius:10px; background:#fff; }
    </style>
</head>
<body>

    <!-- ── Shared Navbar ── -->
    <nav class="topnav">
        <a class="topnav-brand" href="/"><span class="logo-dot"></span> OpenEnv Debugger</a>
        <div class="topnav-links">
            <a class="topnav-link" href="/dashboard"><span class="nav-icon">📊</span> Dashboard</a>
            <a class="topnav-link active" href="/demo"><span class="nav-icon">🎬</span> Demo</a>
            <a class="topnav-link" href="/compete"><span class="nav-icon">⚔️</span> Compete</a>
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
            <h1>🎬 OpenEnv Auto-Demo</h1>
            <p>Experience the autonomous ETL debugging agent — explore agents, algorithms, and live replays.</p>
        </div>

        <!-- Stats Row -->
        <div class="stats-row">
            <div class="stat-card"><div class="stat-num">6</div><div class="stat-label">Agents</div></div>
            <div class="stat-card"><div class="stat-num">5</div><div class="stat-label">Difficulty Levels</div></div>
            <div class="stat-card"><div class="stat-num">11</div><div class="stat-label">Action Space</div></div>
            <div class="stat-card"><div class="stat-num">3</div><div class="stat-label">Multi-Agent Roles</div></div>
            <div class="stat-card"><div class="stat-num">5</div><div class="stat-label">Training Algorithms</div></div>
        </div>

        <!-- Tabs -->
        <div class="card">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('agents')">🤖 Agents</div>
                <div class="tab" onclick="switchTab('algorithm')">🧠 Algorithm</div>
                <div class="tab" onclick="switchTab('training')">📈 Training Curve</div>
                <div class="tab" onclick="switchTab('tasks')">📋 Tasks</div>
                <div class="tab" onclick="switchTab('dashboard')">⚙️ Live Dashboard</div>
            </div>

            <!-- Agents Tab -->
            <div id="tab-agents" class="tab-content active">
                <h2>Agents Overview (6 Total)</h2>
                <div class="agent-grid">
                    <div class="agent-card"><div class="agent-icon">📏</div><div class="agent-name">Rule-Based Agent</div><div class="agent-desc">Heuristic debugger using priority-ordered if/else rules. Acts as baseline and fallback.</div></div>
                    <div class="agent-card"><div class="agent-icon">🧠</div><div class="agent-name">LLM Agent (Qwen2.5-72B)</div><div class="agent-desc">AI-powered action selector via OpenAI-compatible API with JSON output parsing.</div></div>
                    <div class="agent-card"><div class="agent-icon">🔍</div><div class="agent-name">Inspector Agent</div><div class="agent-desc">Analyzes pipeline state, identifies schema mismatches, nulls, duplicates, and rule violations.</div></div>
                    <div class="agent-card"><div class="agent-icon">🔧</div><div class="agent-name">Fixer Agent</div><div class="agent-desc">Receives diagnosis from Inspector, builds priority queue, applies fixes in correct order.</div></div>
                    <div class="agent-card"><div class="agent-icon">✅</div><div class="agent-name">Validator Agent</div><div class="agent-desc">Validates fix quality against thresholds. Decides submit or request re-inspection.</div></div>
                    <div class="agent-card"><div class="agent-icon">📚</div><div class="agent-name">Curriculum Agent</div><div class="agent-desc">Simulated improving agent for curriculum learning — tracks skill growth across all levels.</div></div>
                </div>
            </div>

            <!-- Algorithm Tab -->
            <div id="tab-algorithm" class="tab-content">
                <h2>Training Algorithm — Hybrid Approach</h2>
                <div class="grid-2">
                    <div>
                        <h3>1. Curriculum Learning</h3>
                        <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1rem;">Progressive difficulty: Easy→Medium→Hard→VeryHard→Expert. Agent advances when rolling average score ≥ threshold for 3+ consecutive episodes.</p>
                        <h3>2. ε-Greedy Exploration</h3>
                        <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1rem;">Noise starts at 0.80 (80% random), decays ×0.96 per episode to 0.05. Balances exploration vs exploitation.</p>
                        <h3>3. Rule-Based Fallback</h3>
                        <p style="font-size:0.85rem;color:var(--text-muted);">Priority-ordered: inspect → cast → reorder → dedup → fill_nulls → filter → business_rules → validate → submit.</p>
                    </div>
                    <div>
                        <h3>4. GRPO/PPO Fine-Tuning</h3>
                        <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1rem;">Unsloth + TRL with Qwen2.5-7B-Instruct. LoRA (r=16) on q_proj & v_proj. Group Relative Policy Optimization.</p>
                        <h3>5. Adaptive Difficulty</h3>
                        <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1rem;">Auto-scales: if avg > target+0.15 → harder (less hints); if avg < target-0.15 → easier (more hints).</p>
                        <h3>Pipeline Flow</h3>
                        <div class="flow-steps">
                            <div class="flow-step">Reset</div><span class="flow-arrow">→</span>
                            <div class="flow-step">Observe</div><span class="flow-arrow">→</span>
                            <div class="flow-step">Act</div><span class="flow-arrow">→</span>
                            <div class="flow-step">Reward</div><span class="flow-arrow">→</span>
                            <div class="flow-step">Submit</div>
                        </div>
                    </div>
                </div>
                <div style="margin-top:1.5rem;background:var(--bg-color);border:1px solid var(--border-color);border-radius:8px;padding:1rem;">
                    <h3>Reward Formula</h3>
                    <pre style="font-size:0.82rem;color:var(--text-muted);margin:0;">R(t) = base_progress + novelty_bonus + cascade_bonus - regression_penalty - step_cost - repeat_penalty + (if final: submission_score × bonus)</pre>
                </div>
            </div>

            <!-- Training Tab -->
            <div id="tab-training" class="tab-content">
                <h2>Curriculum Learning Progress</h2>
                <p style="color:var(--text-muted);font-size:0.88rem;margin-bottom:1rem;">Simulated training curve showing agent improvement from random to mastery.</p>
                <div class="chart-container"><canvas id="trainChart"></canvas></div>
                <div style="margin-top:1rem;display:flex;gap:1rem;flex-wrap:wrap;">
                    <div class="badge badge-green">● Easy</div>
                    <div class="badge badge-blue">● Medium</div>
                    <div class="badge badge-yellow">● Hard</div>
                    <div class="badge badge-red">● Very Hard</div>
                    <div class="badge badge-purple">● Expert</div>
                </div>
            </div>

            <!-- Tasks Tab -->
            <div id="tab-tasks" class="tab-content">
                <h2>Available Tasks</h2>
                <table class="data-table">
                    <thead><tr><th>Task</th><th>Difficulty</th><th>Step Limit</th><th>Advance Threshold</th></tr></thead>
                    <tbody>
                        <tr><td>task_easy_schema_fix</td><td><span class="badge badge-green">Easy</span></td><td>10</td><td>0.80</td></tr>
                        <tr><td>task_medium_data_quality</td><td><span class="badge badge-blue">Medium</span></td><td>20</td><td>0.75</td></tr>
                        <tr><td>task_hard_pipeline_orchestration</td><td><span class="badge badge-yellow">Hard</span></td><td>40</td><td>0.70</td></tr>
                        <tr><td>task_veryhard_streaming_pipeline</td><td><span class="badge badge-red">Very Hard</span></td><td>50</td><td>0.65</td></tr>
                        <tr><td>task_expert_multi_source_join</td><td><span class="badge badge-purple">Expert</span></td><td>60</td><td>0.60</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- Dashboard Tab -->
            <div id="tab-dashboard" class="tab-content">
                <h2>Interactive Dashboard</h2>
                <p style="color:var(--text-muted);font-size:0.88rem;margin-bottom:1rem;">Explore the agent directly via the embedded dashboard.</p>
                <iframe src="/dashboard" sandbox="allow-scripts allow-same-origin" title="Interactive Dashboard"></iframe>
            </div>
        </div>
    </div>

<script>
// Tab switching
function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector(`.tab[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');
    if (tabId === 'training' && !window._chartDrawn) drawChart();
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

// Simulated training chart
function drawChart() {
    window._chartDrawn = true;
    const canvas = document.getElementById('trainChart');
    const ctx = canvas.getContext('2d');
    const W = canvas.parentElement.clientWidth - 32;
    const H = canvas.parentElement.clientHeight - 32;
    canvas.width = W * 2; canvas.height = H * 2;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.scale(2, 2);

    // Generate simulated data
    const episodes = 200;
    const data = [];
    let score = 0.15, taskIdx = 0;
    const thresholds = [0.80, 0.75, 0.70, 0.65, 0.60];
    const penalties = [0, 0.1, 0.2, 0.3, 0.4];
    const colors = ['#059669','#2563eb','#d97706','#dc2626','#7c3aed'];
    for (let i = 0; i < episodes; i++) {
        score += (0.006 + Math.random() * 0.008) - penalties[taskIdx] * 0.002;
        score = Math.min(0.99, Math.max(0.05, score + (Math.random()-0.5)*0.04));
        if (score >= thresholds[taskIdx] && taskIdx < 4) { taskIdx++; score -= penalties[taskIdx] * 0.3; }
        data.push({ ep: i, score: score, task: taskIdx, color: colors[taskIdx] });
    }

    const padL=40, padR=10, padT=10, padB=30;
    const gW=W-padL-padR, gH=H-padT-padB;

    // Grid
    ctx.strokeStyle='#e5e7eb'; ctx.lineWidth=0.5;
    for(let i=0;i<=4;i++){const y=padT+gH*(1-i/4);ctx.beginPath();ctx.moveTo(padL,y);ctx.lineTo(padL+gW,y);ctx.stroke();ctx.fillStyle='#9ca3af';ctx.font='10px Inter';ctx.textAlign='right';ctx.fillText((i*0.25).toFixed(2),padL-5,y+3);}

    // Line
    ctx.beginPath(); ctx.lineWidth=1.5;
    data.forEach((d,i) => {
        const x=padL+(i/episodes)*gW, y=padT+gH*(1-d.score);
        if(i===0)ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.strokeStyle='#2563eb'; ctx.stroke();

    // Dots colored by task
    data.forEach((d,i) => {
        if(i%5!==0)return;
        const x=padL+(i/episodes)*gW, y=padT+gH*(1-d.score);
        ctx.beginPath();ctx.arc(x,y,2.5,0,Math.PI*2);ctx.fillStyle=d.color;ctx.fill();
    });

    // X label
    ctx.fillStyle='#6b7280'; ctx.font='10px Inter'; ctx.textAlign='center';
    ctx.fillText('Episodes', padL+gW/2, H-4);
}
</script>
</body>
</html>"""
