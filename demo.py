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
function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector(`.tab[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');
}
</script>
</body>
</html>"""
