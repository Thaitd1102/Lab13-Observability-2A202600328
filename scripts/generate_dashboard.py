#!/usr/bin/env python3
"""Generate 6-panel dashboard from metrics data."""

import json
from pathlib import Path
from datetime import datetime

# Try importing matplotlib, if not available create text-based report
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ matplotlib not available - generating text report only")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.metrics import snapshot
from scripts.export_metrics import export_metrics


def generate_html_report(metrics: dict, output_path: str = "data/dashboard_report.html") -> None:
    """Generate HTML dashboard report."""
    
    slo_targets = {
        "latency_p95_ms": {"objective": 3000, "current": metrics.get("latency_p95", 0)},
        "error_rate_pct": {"objective": 2, "current": metrics.get("error_rate_pct", 0)},
        "daily_cost_usd": {"objective": 2.5, "current": metrics.get("total_cost_usd", 0)},
        "quality_score_avg": {"objective": 0.75, "current": metrics.get("quality_avg", 0)},
    }
    
    # Determine SLO compliance
    compliance = {}
    compliance["latency"] = "✅ PASS" if metrics.get("latency_p95", 999) < 3000 else "❌ FAIL"
    compliance["error_rate"] = "✅ PASS" if metrics.get("error_rate_pct", 100) < 2 else "❌ FAIL"
    compliance["cost"] = "✅ PASS" if metrics.get("total_cost_usd", 999) < 2.5 else "❌ FAIL"
    compliance["quality"] = "✅ PASS" if metrics.get("quality_avg", 0) > 0.75 else "❌ FAIL"
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Day 13 Observability Lab - Dashboard Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .panel {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .panel-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .metric-value {{ font-weight: bold; color: #007bff; }}
        .status-pass {{ color: green; font-weight: bold; }}
        .status-fail {{ color: red; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f0f0f0; }}
        .slo-pass {{ color: green; }}
        .slo-fail {{ color: red; }}
        h1 {{ color: #333; }}
        .timestamp {{ color: #666; font-size: 12px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Day 13 Observability Lab - 6-Panel Dashboard</h1>
        <p class="timestamp">Generated: {datetime.utcnow().isoformat()}</p>
        
        <!-- Panel 1: Request Count -->
        <div class="panel">
            <div class="panel-title">Panel 1: Request Count (per endpoint)</div>
            <div class="metric">
                <span>Total Requests</span>
                <span class="metric-value">{metrics.get('traffic', 0)}</span>
            </div>
            <div class="metric">
                <span>Error Count</span>
                <span class="metric-value">{sum(metrics.get('error_breakdown', {}).values())}</span>
            </div>
        </div>
        
        <!-- Panel 2: Latency Distribution -->
        <div class="panel">
            <div class="panel-title">Panel 2: Latency Distribution (P50, P95, P99)</div>
            <div class="metric">
                <span>P50 Latency</span>
                <span class="metric-value">{metrics.get('latency_p50', 0):.1f} ms</span>
            </div>
            <div class="metric">
                <span>P95 Latency</span>
                <span class="metric-value">{metrics.get('latency_p95', 0):.1f} ms</span>
            </div>
            <div class="metric">
                <span>P99 Latency</span>
                <span class="metric-value">{metrics.get('latency_p99', 0):.1f} ms</span>
            </div>
        </div>
        
        <!-- Panel 3: Error Rate -->
        <div class="panel">
            <div class="panel-title">Panel 3: Error Rate</div>
            <div class="metric">
                <span>Error Rate</span>
                <span class="metric-value">{metrics.get('error_rate_pct', 0):.2f}%</span>
            </div>
            <div class="metric">
                <span>Error Types</span>
            </div>
            <table>
                <tr><th>Error Type</th><th>Count</th></tr>
"""
    
    for error_type, count in metrics.get("error_breakdown", {}).items():
        html_content += f"                <tr><td>{error_type}</td><td>{count}</td></tr>\n"
    
    html_content += f"""
            </table>
        </div>
        
        <!-- Panel 4: SLO Compliance -->
        <div class="panel">
            <div class="panel-title">Panel 4: SLO Compliance Status</div>
            <table>
                <tr><th>SLI</th><th>Target</th><th>Current Value</th><th>Status</th><th>Window</th></tr>
                <tr>
                    <td>Latency P95</td>
                    <td>&lt; 3000ms</td>
                    <td>{metrics.get('latency_p95', 0):.1f}ms</td>
                    <td><span class="slo-{('pass' if metrics.get('latency_p95', 999) < 3000 else 'fail')}">{compliance['latency']}</span></td>
                    <td>28d</td>
                </tr>
                <tr>
                    <td>Error Rate</td>
                    <td>&lt; 2%</td>
                    <td>{metrics.get('error_rate_pct', 0):.2f}%</td>
                    <td><span class="slo-{('pass' if metrics.get('error_rate_pct', 100) < 2 else 'fail')}">{compliance['error_rate']}</span></td>
                    <td>28d</td>
                </tr>
                <tr>
                    <td>Cost Budget</td>
                    <td>&lt; $2.5/day</td>
                    <td>${{metrics.get('total_cost_usd', 0):.4f}}</td>
                    <td><span class="slo-{('pass' if metrics.get('total_cost_usd', 999) < 2.5 else 'fail')}">{compliance['cost']}</span></td>
                    <td>1d</td>
                </tr>
                <tr>
                    <td>Quality Score</td>
                    <td>&gt; 0.75</td>
                    <td>{metrics.get('quality_avg', 0):.4f}</td>
                    <td><span class="slo-{('pass' if metrics.get('quality_avg', 0) > 0.75 else 'fail')}">{compliance['quality']}</span></td>
                    <td>28d</td>
                </tr>
            </table>
        </div>
        
        <!-- Panel 5: Cost Breakdown -->
        <div class="panel">
            <div class="panel-title">Panel 5: LLM Cost Breakdown</div>
            <div class="metric">
                <span>Total Cost (all requests)</span>
                <span class="metric-value">${{metrics.get('total_cost_usd', 0):.4f}}</span>
            </div>
            <div class="metric">
                <span>Average Cost per Request</span>
                <span class="metric-value">${{{metrics.get('avg_cost_usd', 0):.6f}}}</span>
            </div>
            <div class="metric">
                <span>Total Input Tokens</span>
                <span class="metric-value">{metrics.get('tokens_in_total', 0)}</span>
            </div>
            <div class="metric">
                <span>Total Output Tokens</span>
                <span class="metric-value">{metrics.get('tokens_out_total', 0)}</span>
            </div>
        </div>
        
        <!-- Panel 6: Quality Score -->
        <div class="panel">
            <div class="panel-title">Panel 6: RAG & Quality Metrics</div>
            <div class="metric">
                <span>Average Quality Score</span>
                <span class="metric-value">{metrics.get('quality_avg', 0):.4f}</span>
            </div>
            <div class="metric">
                <span>Quality Benchmark (Target)</span>
                <span class="metric-value">0.75</span>
            </div>
            <div class="metric">
                <span>Status</span>
                <span class="metric-value {('status-pass' if metrics.get('quality_avg', 0) > 0.75 else 'status-fail')}">{('✅ ABOVE TARGET' if metrics.get('quality_avg', 0) > 0.75 else '❌ BELOW TARGET')}</span>
            </div>
        </div>
        
        <div class="panel">
            <strong>Export Date:</strong> {metrics.get('exported_at', 'N/A')}<br>
            <strong>Total Requests Analyzed:</strong> {metrics.get('traffic', 0)}<br>
        </div>
    </div>
</body>
</html>
"""
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Dashboard report generated: {output_path}")


def generate_text_report(metrics: dict) -> None:
    """Generate text-based dashboard report."""
    
    print("\n" + "="*70)
    print("📊 DAY 13 OBSERVABILITY LAB - 6-PANEL DASHBOARD REPORT")
    print("="*70)
    print(f"Generated: {metrics.get('exported_at', 'N/A')}\n")
    
    # Panel 1
    print("PANEL 1: REQUEST COUNT (PER ENDPOINT)")
    print("-" * 70)
    print(f"  Total Requests: {metrics.get('traffic', 0)}")
    print(f"  Error Count: {sum(metrics.get('error_breakdown', {}).values())}\n")
    
    # Panel 2
    print("PANEL 2: LATENCY DISTRIBUTION (P50, P95, P99)")
    print("-" * 70)
    print(f"  P50 Latency: {metrics.get('latency_p50', 0):.1f} ms")
    print(f"  P95 Latency: {metrics.get('latency_p95', 0):.1f} ms")
    print(f"  P99 Latency: {metrics.get('latency_p99', 0):.1f} ms\n")
    
    # Panel 3
    print("PANEL 3: ERROR RATE")
    print("-" * 70)
    print(f"  Error Rate: {metrics.get('error_rate_pct', 0):.2f}%")
    if metrics.get("error_breakdown"):
        for error_type, count in metrics.get("error_breakdown", {}).items():
            print(f"    - {error_type}: {count}")
    print()
    
    # Panel 4
    print("PANEL 4: SLO COMPLIANCE STATUS")
    print("-" * 70)
    print(f"  Latency P95 < 3000ms: {metrics.get('latency_p95', 0):.1f}ms - {'✅ PASS' if metrics.get('latency_p95', 999) < 3000 else '❌ FAIL'}")
    print(f"  Error Rate < 2%: {metrics.get('error_rate_pct', 0):.2f}% - {'✅ PASS' if metrics.get('error_rate_pct', 100) < 2 else '❌ FAIL'}")
    print(f"  Cost Budget < $2.5/day: ${metrics.get('total_cost_usd', 0):.4f} - {'✅ PASS' if metrics.get('total_cost_usd', 999) < 2.5 else '❌ FAIL'}")
    print(f"  Quality Score > 0.75: {metrics.get('quality_avg', 0):.4f} - {'✅ PASS' if metrics.get('quality_avg', 0) > 0.75 else '❌ FAIL'}\n")
    
    # Panel 5
    print("PANEL 5: LLM COST BREAKDOWN")
    print("-" * 70)
    print(f"  Total Cost: ${metrics.get('total_cost_usd', 0):.4f}")
    print(f"  Avg Cost/Request: ${metrics.get('avg_cost_usd', 0):.6f}")
    print(f"  Total Input Tokens: {metrics.get('tokens_in_total', 0)}")
    print(f"  Total Output Tokens: {metrics.get('tokens_out_total', 0)}\n")
    
    # Panel 6
    print("PANEL 6: RAG & QUALITY METRICS")
    print("-" * 70)
    print(f"  Average Quality Score: {metrics.get('quality_avg', 0):.4f}")
    print(f"  Quality Benchmark (Target): 0.75")
    quality_status = '✅ ABOVE TARGET' if metrics.get('quality_avg', 0) > 0.75 else '❌ BELOW TARGET'
    print(f"  Status: {quality_status}\n")
    
    print("="*70)


if __name__ == "__main__":
    print("📊 Generating Dashboard Report...")
    metrics = export_metrics()
    
    # Generate HTML report
    generate_html_report(metrics)
    
    # Generate text report
    generate_text_report(metrics)
