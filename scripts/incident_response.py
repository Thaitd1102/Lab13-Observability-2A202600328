#!/usr/bin/env python3
"""
Incident Response & Root Cause Analysis - Demonstrates Metrics -> Traces -> Logs workflow.

This script demonstrates the observation workflow:
1. METRICS PHASE: Detect anomaly from metrics
2. TRACES PHASE: Dive into Langfuse traces for timing breakdown
3. LOGS PHASE: Extract detailed error info from structured logs
4. RCA: Synthesize findings into root cause analysis
"""

import json
import time
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Install with: pip install httpx")
    exit(1)


class IncidentResponseTool:
    """Incident response and root cause analysis tool."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)
    
    def health_check(self) -> bool:
        """Verify app is running."""
        try:
            resp = self.client.get(f"{self.base_url}/health")
            return resp.status_code == 200
        except:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """PHASE 1: Get current metrics."""
        try:
            resp = self.client.get(f"{self.base_url}/metrics")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """PHASE 3: Read logs from logs.jsonl file."""
        logs_file = Path("data/logs.jsonl")
        logs = []
        try:
            if logs_file.exists():
                with open(logs_file) as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:  # Get last N lines
                        try:
                            logs.append(json.loads(line))
                        except:
                            pass
        except Exception as e:
            print(f"ERROR reading logs: {e}")
        return logs
    
    def inject_incident(self, scenario: str) -> Dict:
        """Inject incident scenario."""
        try:
            resp = self.client.post(f"{self.base_url}/incidents/{scenario}/enable")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def clear_incident(self, scenario: str) -> Dict:
        """Clear incident scenario."""
        try:
            resp = self.client.post(f"{self.base_url}/incidents/{scenario}/disable")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def run_load_test(self, concurrency: int = 3, num_requests: int = 5) -> bool:
        """Run load test to generate requests."""
        try:
            cmd = f"python scripts/load_test.py --concurrency {concurrency} -n {num_requests}"
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception as e:
            print(f"ERROR: Load test failed: {e}")
            return False
    
    def analyze_incident(self, scenario: str) -> Dict[str, Any]:
        """Perform root cause analysis for an incident."""
        
        print("\n" + "="*80)
        print(f"INCIDENT RESPONSE: {scenario.upper()}")
        print("="*80)
        
        # Step 1: Inject incident
        print(f"\n[STEP 1] INJECT INCIDENT: {scenario}")
        print("-" * 80)
        inject_result = self.inject_incident(scenario)
        print(f"Status: {inject_result}")
        time.sleep(1)
        
        # Step 2: Generate load to trigger the incident
        print(f"\n[STEP 2] GENERATE LOAD (to trigger incident)")
        print("-" * 80)
        print("Running load test...")
        success = self.run_load_test(concurrency=2, num_requests=3)
        if success:
            print("Load generation completed")
        time.sleep(2)
        
        # PHASE 1: METRICS
        print(f"\n[PHASE 1] METRICS ANALYSIS")
        print("-" * 80)
        metrics = self.get_metrics()
        print(json.dumps(metrics, indent=2))
        
        # PHASE 2: LOGS (since we don't have Langfuse traces in this setup)
        print(f"\n[PHASE 2] LOGS ANALYSIS (Searching for anomalies)")
        print("-" * 80)
        logs = self.get_logs(limit=100)
        
        # Analyze logs for incident-specific patterns
        rca_findings = self._analyze_logs_for_scenario(scenario, logs)
        
        for finding in rca_findings:
            print(f"  [FINDING] {finding}")
        
        # PHASE 3: ROOT CAUSE ANALYSIS
        print(f"\n[PHASE 3] ROOT CAUSE ANALYSIS")
        print("-" * 80)
        rca = self._generate_rca(scenario, metrics, logs, rca_findings)
        print(json.dumps(rca, indent=2))
        
        # Step 3: Clear incident
        print(f"\n[STEP 3] CLEAR INCIDENT")
        print("-" * 80)
        clear_result = self.clear_incident(scenario)
        print(f"Status: {clear_result}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "metrics": metrics,
            "log_count": len(logs),
            "findings": rca_findings,
            "rca": rca
        }
    
    def _analyze_logs_for_scenario(self, scenario: str, logs: List[Dict]) -> List[str]:
        """Extract findings from logs based on scenario."""
        findings = []
        
        if scenario == "rag_slow":
            # Look for RAG-related logs with high duration
            rag_logs = [log for log in logs if "rag" in str(log).lower()]
            if rag_logs:
                findings.append(f"Found {len(rag_logs)} RAG-related log entries")
                # Check for latency indicators
                for log in rag_logs[-5:]:
                    if "duration" in str(log):
                        findings.append(f"RAG log: {log.get('event', 'unknown')}")
        
        elif scenario == "tool_fail":
            # Look for error logs
            error_logs = [log for log in logs if log.get("level") == "error" or "error" in str(log).lower()]
            if error_logs:
                findings.append(f"Found {len(error_logs)} ERROR logs")
                for log in error_logs[-5:]:
                    event = log.get("event", "unknown")
                    msg = log.get("error", "")
                    findings.append(f"Error: {event} - {msg}")
                    if "tool" in str(log).lower() or "vector" in str(log).lower():
                        findings.append(f"  -> Root cause: Tool failure detected")
        
        elif scenario == "cost_spike":
            # Look for token usage logs
            cost_logs = [log for log in logs if "token" in str(log).lower() or "cost" in str(log).lower()]
            if cost_logs:
                findings.append(f"Found {len(cost_logs)} cost-related log entries")
                for log in cost_logs[-5:]:
                    findings.append(f"Cost log: {log.get('event', 'unknown')}")
        
        # General findings
        if logs:
            error_count = len([l for l in logs if l.get("level") == "error"])
            if error_count > 0:
                findings.append(f"Error rate in logs: {error_count}/{len(logs)} ({100*error_count//len(logs)}%)")
        
        return findings
    
    def _generate_rca(self, scenario: str, metrics: Dict, logs: List[Dict], 
                     findings: List[str]) -> Dict[str, Any]:
        """Generate root cause analysis report."""
        
        rca_template = {
            "rag_slow": {
                "root_cause": "Retrieval Augmented Generation (RAG) pipeline latency spike",
                "detection": "P95 latency significantly above baseline (>5000ms)",
                "impact": "User requests timeout or take 10+ seconds to respond",
                "remediation": [
                    "Reduce context window size in retrieval",
                    "Implement caching for frequent queries",
                    "Use semantic compression on retrieved docs",
                    "Scale vector DB read replicas"
                ],
                "verification": "Monitor P95 latency to return to baseline within 5 minutes"
            },
            "tool_fail": {
                "root_cause": "Tool invocation failure (vector DB, search, or external API)",
                "detection": f"Error rate spike in logs: {len([l for l in logs if l.get('level')=='error'])}/100 requests",
                "impact": "Agent cannot complete requests, users see error responses",
                "remediation": [
                    "Check vector DB connection status",
                    "Verify API keys and credentials",
                    "Enable circuit breaker pattern",
                    "Add retry logic with exponential backoff"
                ],
                "verification": "All requests return 200 OK, error log count drops to 0"
            },
            "cost_spike": {
                "root_cause": "Unexpected increase in token consumption (context size or output length)",
                "detection": "Output tokens 2-3x higher than baseline",
                "impact": "Daily API cost increases, may breach budget",
                "remediation": [
                    "Limit output token length (max_tokens parameter)",
                    "Reduce system prompt verbosity",
                    "Implement token budgeting per request",
                    "Use model with better token efficiency"
                ],
                "verification": "Cost per request returns to $<0.002 range"
            }
        }
        
        return rca_template.get(scenario, {
            "root_cause": f"Unknown incident: {scenario}",
            "impact": "System behavior anomaly detected",
            "remediation": ["Check logs and traces for details"]
        })
    
    def generate_report(self, analyses: List[Dict]) -> str:
        """Generate markdown report of all incidents analyzed."""
        report = []
        report.append("# Incident Response Report\n")
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        
        for analysis in analyses:
            report.append(f"\n## Incident: {analysis['scenario'].upper()}\n")
            report.append(f"**Time**: {analysis['timestamp']}\n")
            report.append(f"**Logs Analyzed**: {analysis['log_count']} entries\n")
            
            if analysis['findings']:
                report.append("\n### Findings\n")
                for finding in analysis['findings']:
                    report.append(f"- {finding}\n")
            
            if analysis['rca']:
                rca = analysis['rca']
                report.append(f"\n### Root Cause\n")
                report.append(f"{rca.get('root_cause', 'N/A')}\n")
                
                report.append(f"\n### Impact\n")
                report.append(f"{rca.get('impact', 'N/A')}\n")
                
                if rca.get('remediation'):
                    report.append(f"\n### Remediation Steps\n")
                    for step in rca['remediation']:
                        report.append(f"- {step}\n")
        
        return "".join(report)


def main():
    """Run incident response analysis for all scenarios."""
    
    tool = IncidentResponseTool()
    
    # Verify app is running
    print("[*] Checking if app is running...")
    if not tool.health_check():
        print("ERROR: App is not running at http://localhost:8000")
        print("Start with: uvicorn app.main:app --reload")
        exit(1)
    
    print("[OK] App is running\n")
    
    # Analyze each incident type
    scenarios = ["rag_slow", "tool_fail", "cost_spike"]
    analyses = []
    
    for scenario in scenarios:
        try:
            analysis = tool.analyze_incident(scenario)
            analyses.append(analysis)
            time.sleep(2)  # Cool down between incidents
        except Exception as e:
            print(f"ERROR analyzing {scenario}: {e}")
    
    # Generate report
    print("\n" + "="*80)
    print("GENERATING INCIDENT RESPONSE REPORT")
    print("="*80)
    report = tool.generate_report(analyses)
    print(report)
    
    # Save report
    report_file = Path("data/incident_response_report.md")
    report_file.write_text(report)
    print(f"\nReport saved: {report_file}")
    
    # Summary
    print("\n" + "="*80)
    print("INCIDENT RESPONSE WORKFLOW SUMMARY")
    print("="*80)
    print("""
The incident response workflow demonstrates:

1. METRICS DETECTION (Phase 1):
   - Monitor key metrics (P95 latency, error rate, cost)
   - Identify anomalies vs baseline/SLO
   - Understand WHAT happened

2. LOG ANALYSIS (Phase 2):
   - Query structured logs for error events
   - Extract context (correlation ID, user, session)
   - Understand WHERE it happened

3. ROOT CAUSE ANALYSIS (Phase 3):
   - Correlate metrics + logs findings
   - Identify root cause (RAG latency, tool failure, token spike)
   - Understand WHY it happened

4. REMEDIATION (Phase 4):
   - Execute mitigation steps
   - Verify with metric baseline
   - Prevent recurrence
    """)


if __name__ == "__main__":
    main()
