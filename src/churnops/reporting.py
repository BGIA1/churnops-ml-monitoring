"""Static local and GitHub Pages report generation."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from jinja2 import Template

from churnops.config import configured_path
from churnops.io import write_text
from churnops.service import latest_summary

PAGE_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChurnOps MLOps Demo</title>
  <style>
    :root { color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }
    body { max-width: 1100px; margin: 0 auto; padding: 2rem; line-height: 1.55; }
    header { padding: 2rem; border-radius: 18px; background: #17324d; color: white; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(240px,1fr));
      gap: 1rem; margin: 1.5rem 0; }
    article { border: 1px solid #8291a0; border-radius: 14px; padding: 1rem; }
    code, pre { background: #111827; color: #e5e7eb; border-radius: 8px; }
    pre { padding: 1rem; overflow: auto; }
    .ok { color: #31c48d; } .alert { color: #f98080; }
  </style>
</head>
<body>
  <header>
    <p>Local-first, cloud-ready reference implementation</p>
    <h1>ChurnOps MLOps Monitoring &amp; Retraining System</h1>
    <p>Deterministic training, governed promotion, inference, drift,
      performance, and retraining.</p>
  </header>
  <section class="grid">
    <article><h2>Champion</h2><p><code>{{ champion_version }}</code></p></article>
    <article><h2>ROC-AUC</h2><p>{{ roc_auc }}</p></article>
    <article><h2>F1</h2><p>{{ f1 }}</p></article>
    <article><h2>Drift</h2><p class="{{ drift_status }}">{{ drift_status }}</p></article>
    <article><h2>Performance</h2>
      <p class="{{ performance_status }}">{{ performance_status }}</p></article>
  </section>
  <h2>Lifecycle snapshot</h2>
  <pre>{{ summary_json }}</pre>
  <p>This static page contains synthetic demo outputs only. It does not call a live API.</p>
</body>
</html>"""
)


def generate_static_site(config: dict[str, Any]) -> Path:
    summary = latest_summary(config)
    champion = summary.get("champion") or {}
    metrics = champion.get("metrics") or {}
    drift = summary.get("drift") or {}
    performance = summary.get("performance") or {}
    public_summary = {
        "champion": {
            "version": champion.get("version"),
            "metrics": {
                key: metrics.get(key)
                for key in (
                    "roc_auc",
                    "f1",
                    "precision",
                    "recall",
                    "accuracy",
                    "brier_score",
                    "threshold",
                )
            },
        },
        "drift": {
            "status": drift.get("status"),
            "alerts": drift.get("alerts", []),
        },
        "performance": {
            "status": performance.get("status"),
            "alerts": performance.get("alerts", []),
        },
    }
    rendered = PAGE_TEMPLATE.render(
        champion_version=champion.get("version", "not available"),
        roc_auc=metrics.get("roc_auc", "not available"),
        f1=metrics.get("f1", "not available"),
        drift_status=drift.get("status", "not available"),
        performance_status=performance.get("status", "not available"),
        summary_json=html.escape(json.dumps(public_summary, indent=2, default=str)),
    )
    destination = configured_path(config, "site_dir") / "index.html"
    return write_text(destination, rendered)
