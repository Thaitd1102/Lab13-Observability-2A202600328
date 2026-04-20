#!/usr/bin/env python3
"""Test alert rules by triggering incidents and monitoring metrics."""

import time
import json
import subprocess
from pathlib import Path

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    exit(1)


def get_health():
    """Get app health status."""
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=5.0)
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to get health: {e}")
        return None


def get_metrics():
    """Get current metrics."""
    try:
        resp = httpx.get("http://localhost:8000/metrics", timeout=5.0)
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to get metrics: {e}")
        return None


def inject_incident(scenario: str):
    """Inject an incident."""
    try:
        resp = httpx.post(f"http://localhost:8000/incidents/{scenario}/enable", timeout=5.0)
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to inject incident: {e}")
        return None


def run_load_test(concurrency: int = 3, requests: int = 10):
    """Run load test."""
    try:
        cmd = f"python scripts/load_test.py --concurrency {concurrency}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        return False


def test_alert_1_high_latency():
    """Test Alert 1: High Latency."""
    print("\n" + "="*70)
    print("[ALERT 1] High Latency P95 (> 5000ms)")
    print("="*70)
    
    # Enable rag_slow incident
    print("\nStep 1: Enabling rag_slow incident...")
    result = inject_incident("rag_slow")
    if result:
        print(f"[OK] Incident enabled: {result.get('incidents', {})}")
    
    # Generate load
    print("\nStep 2: Generating load test requests...")
    if run_load_test(concurrency=3):
        print("[OK] Load test completed")
    
    # Check metrics
    print("\nStep 3: Checking metrics...")
    metrics = get_metrics()
    if metrics:
        p95 = metrics.get("latency_p95", 0)
        print(f"   Current P95 Latency: {p95:.1f}ms")
        
        if p95 > 5000:
            print(f"   [ALERT FIRES] P95 ({p95:.1f}ms) > 5000ms threshold")
        else:
            print(f"   [INFO] Alert threshold not reached (need sustained > 5000ms for 30m)")
    
    # Show troubleshooting
    print("\nStep 4: Troubleshooting steps:")
    print("   - Check Langfuse traces for slow RAG spans")
    print("   - Compare RAG duration vs LLM duration")
    print("   - Mitigation: reduce context window, use cache")


def test_alert_2_high_error_rate():
    """Test Alert 2: High Error Rate."""
    print("\n" + "="*70)
    print("[ALERT 2] High Error Rate (> 5%)")
    print("="*70)
    
    # Enable tool_fail incident
    print("\nStep 1: Enabling tool_fail incident...")
    result = inject_incident("tool_fail")
    if result:
        print(f"[OK] Incident enabled: {result.get('incidents', {})}")
    
    # Generate load
    print("\nStep 2: Generating load test requests...")
    if run_load_test(concurrency=3):
        print("[OK] Load test completed")
    
    # Check metrics
    print("\nStep 3: Checking metrics...")
    metrics = get_metrics()
    if metrics:
        error_rate = metrics.get("error_rate_pct", 0)
        error_count = metrics.get("error_breakdown", {})
        print(f"   Current Error Rate: {error_rate:.2f}%")
        print(f"   Error Breakdown: {error_count}")
        
        if error_rate > 5:
            print(f"   [ALERT FIRES] Error rate ({error_rate:.2f}%) > 5% threshold")
        else:
            print(f"   [INFO] Alert threshold not reached (need > 5% for 5m)")
    
    # Show troubleshooting
    print("\nStep 4: Troubleshooting steps:")
    print("   - Group logs by error_type: grep 'request_failed' logs | group by error")
    print("   - Check failed traces in Langfuse")
    print("   - Determine: LLM? Tool? Schema validation?")
    print("   - Mitigation: rollback, disable tool, retry with fallback")


def test_alert_3_cost_spike():
    """Test Alert 3: Cost Budget Spike."""
    print("\n" + "="*70)
    print("[ALERT 3] Cost Budget Spike (> 2x baseline)")
    print("="*70)
    
    # Enable cost_spike incident
    print("\nStep 1: Enabling cost_spike incident...")
    result = inject_incident("cost_spike")
    if result:
        print(f"[OK] Incident enabled: {result.get('incidents', {})}")
    
    # Generate load
    print("\nStep 2: Generating load test requests...")
    if run_load_test(concurrency=3):
        print("[OK] Load test completed")
    
    # Check metrics
    print("\nStep 3: Checking metrics...")
    metrics = get_metrics()
    if metrics:
        cost = metrics.get("total_cost_usd", 0)
        avg_cost = metrics.get("avg_cost_usd", 0)
        baseline = 0.002  # ~$0.002 per request baseline
        tokens_in = metrics.get("tokens_in_total", 0)
        tokens_out = metrics.get("tokens_out_total", 0)
        
        print(f"   Total Cost: ${cost:.4f}")
        print(f"   Avg Cost/Request: ${avg_cost:.6f}")
        print(f"   Baseline: ${baseline:.6f}")
        print(f"   Cost Multiplier: {avg_cost/baseline:.2f}x")
        print(f"   Tokens: in={tokens_in}, out={tokens_out}")
        
        if avg_cost > (baseline * 2):
            print(f"   [ALERT FIRES] Cost ({avg_cost:.6f}) > 2x baseline")
        else:
            print(f"   [INFO] Alert threshold not reached (need > 2x baseline for 15m)")
    
    # Show troubleshooting
    print("\nStep 4: Troubleshooting steps:")
    print("   - Split traces by feature (qa vs summary)")
    print("   - Compare token usage per request")
    print("   - Check if prompts are enlarged")
    print("   - Mitigation: shorter context, output limits, cache")


def cleanup():
    """Disable all incidents."""
    print("\n" + "="*70)
    print("[CLEANUP] Disabling all incidents")
    print("="*70)
    
    # Get health to see current incidents
    health = get_health()
    if health and health.get("incidents"):
        print(f"\nCurrent incidents: {health['incidents']}")
    
    # Disable incidents (by enabling all and then disabling - OR just reset app)
    print("\nTo disable all incidents, restart the app or:")
    print("  - Disable individually: python scripts/inject_incident.py --scenario <name>/disable")
    print("  - Check health: curl http://localhost:8000/health")


def main():
    """Run all alert tests."""
    print("\n" + "="*70)
    print("ALERT TESTING SUITE - Day 13 Observability Lab")
    print("="*70)
    
    # Check app is running
    print("\n[1/3] Checking app health...")
    health = get_health()
    if not health:
        print("[ERROR] App is not running. Start with: uvicorn app.main:app --reload")
        exit(1)
    print(f"[OK] App is healthy. Tracing enabled: {health.get('tracing_enabled')}")
    
    # Run tests
    try:
        test_alert_1_high_latency()
        time.sleep(2)
        
        test_alert_2_high_error_rate()
        time.sleep(2)
        
        test_alert_3_cost_spike()
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test interrupted by user")
    
    # Cleanup
    cleanup()
    
    print("\n" + "="*70)
    print("[COMPLETE] Alert Testing Suite Completed")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review metrics for each alert")
    print("  2. Check logs for alert events")
    print("  3. Verify runbooks are actionable")
    print("  4. Test incident disable/recovery")


if __name__ == "__main__":
    main()
