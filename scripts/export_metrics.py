#!/usr/bin/env python3
"""Export metrics to JSON and CSV for dashboard building."""

import json
import csv
from pathlib import Path
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.metrics import snapshot, ERRORS


def export_metrics_from_api(api_url: str = "http://localhost:8000/metrics") -> dict:
    """Export metrics from running app via API."""
    if not HTTPX_AVAILABLE:
        print("⚠️ httpx not available, using local metrics")
        return export_metrics_local()
    
    try:
        response = httpx.get(api_url, timeout=5.0)
        response.raise_for_status()
        metrics_data = response.json()
    except Exception as e:
        print(f"⚠️ Failed to fetch from API ({e}), falling back to local metrics")
        return export_metrics_local()
    
    # Add timestamp
    metrics_data["exported_at"] = datetime.utcnow().isoformat()
    
    # Calculate additional metrics for dashboard
    metrics_data["error_count"] = sum(metrics_data.get("error_breakdown", {}).values())
    metrics_data["error_rate_pct"] = (
        round((metrics_data["error_count"] / metrics_data["traffic"]) * 100, 2)
        if metrics_data["traffic"] > 0
        else 0.0
    )
    
    return metrics_data


def export_metrics_local() -> dict:
    """Export local metrics snapshot (fallback)."""
    if not HTTPX_AVAILABLE:
        from app.metrics import snapshot, ERRORS
    else:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from app.metrics import snapshot, ERRORS
    
    metrics_data = snapshot()
    
    # Add timestamp
    metrics_data["exported_at"] = datetime.utcnow().isoformat()
    
    # Calculate additional metrics
    metrics_data["error_count"] = sum(ERRORS.values())
    metrics_data["error_rate_pct"] = (
        round((metrics_data["error_count"] / metrics_data["traffic"]) * 100, 2)
        if metrics_data["traffic"] > 0
        else 0.0
    )
    
    return metrics_data


def export_metrics() -> dict:
    """Export current metrics snapshot (from API first, fallback to local)."""
    return export_metrics_from_api()


def save_json(metrics_data: dict, output_path: str = "data/metrics.json") -> None:
    """Save metrics to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"✅ Metrics exported to {output_path}")


def save_csv(metrics: dict, output_path: str = "data/metrics.csv") -> None:
    """Save detailed metrics to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare rows
    rows = [
        ("Metric", "Value", "Unit"),
        ("Traffic (total requests)", metrics["traffic"], "count"),
        ("Latency P50", metrics["latency_p50"], "ms"),
        ("Latency P95", metrics["latency_p95"], "ms"),
        ("Latency P99", metrics["latency_p99"], "ms"),
        ("Average Cost", metrics["avg_cost_usd"], "USD"),
        ("Total Cost", metrics["total_cost_usd"], "USD"),
        ("Quality Score (avg)", metrics["quality_avg"], "score"),
        ("Error Count", metrics["error_count"], "count"),
        ("Error Rate", metrics["error_rate_pct"], "%"),
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"✅ Metrics exported to {output_path}")


if __name__ == "__main__":
    metrics = export_metrics()
    save_json(metrics)
    save_csv(metrics)
    print(f"\n📊 Metrics snapshot:\n{json.dumps(metrics, indent=2)}")
