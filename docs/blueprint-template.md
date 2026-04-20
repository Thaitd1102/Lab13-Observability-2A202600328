# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Lab13-Observability-2A202600328
- [REPO_URL]: https://github.com/Thaitd1102/Lab13-Observability-2A202600328.git
- [MEMBERS]:
  - Member A: [Duc Thai] | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: (to be updated)
- [PII_LEAKS_FOUND]: 0 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: (to be added)
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: (to be added)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: (to be added)
- [TRACE_WATERFALL_EXPLANATION]: 

**A1 - Correlation ID & Log Enrichment (COMPLETED ✓)**

Implementation:
- **middleware.py**: Generate x-request-id with format "req-<8-char-hex>", bind to structlog contextvars via `bind_contextvars()`, add response headers (x-request-id, x-response-time-ms)
- **logging_config.py**: Enable PII scrubbing processor in structlog pipeline (scrub_event)
- **main.py**: Enrich /chat endpoint logs with context binding:
  - user_id_hash (hashed user_id)
  - session_id
  - feature (qa/summary)
  - model (claude-sonnet-4-5)
  - env (dev/prod)

Results:
- ✅ All required log fields present (ts, level, event, correlation_id, etc.)
- ✅ 10 unique correlation IDs found across requests
- ✅ No PII leaks detected (credit cards, SSNs redacted)
- ✅ Validation Score: 100/100

Sample Log Output:
```json
{
  "correlation_id": "req-7815c060",
  "user_id_hash": "105a9cef3903",
  "session_id": "s10",
  "feature": "qa",
  "model": "claude-sonnet-4-5",
  "env": "dev",
  "ts": "2026-04-20T08:16:28.197991Z",
  "level": "info",
  "event": "response_sent",
  "latency_ms": 150
}
```

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: data/dashboard_report.html
- [SLO_TABLE]:
| SLI | Target | Window | Current Value | Status |
|---|---:|---|---:|---|
| Latency P95 | < 3000ms | 28d | 150.0ms | ✅ PASS |
| Error Rate | < 2% | 28d | 0.0% | ✅ PASS |
| Cost Budget | < $2.5/day | 1d | $0.0198 | ✅ PASS |
| Quality Score | > 0.75 | 28d | 0.88 | ✅ PASS |

**A2 - Dashboard & SLO (COMPLETED ✓)**

Implementation:
- **scripts/export_metrics.py**: 
  - Fetches metrics from running app API (`http://localhost:8000/metrics`)
  - Exports to JSON and CSV formats
  - Automatically calculates `error_rate_pct` from error_breakdown
  
- **scripts/generate_dashboard.py**: Generates 6-panel dashboard
  - **Panel 1**: Request count (total requests, error count)
  - **Panel 2**: Latency distribution (P50, P95, P99)
  - **Panel 3**: Error rate (with breakdown by error type)
  - **Panel 4**: SLO compliance status (pass/fail for each SLO)
  - **Panel 5**: LLM cost breakdown (total cost, avg cost/request, tokens)
  - **Panel 6**: RAG & quality metrics (quality score vs benchmark)
  - Generates both HTML report + text console report
  - Color-coded SLO pass/fail status

- **config/slo.yaml**: SLO definitions (pre-configured):
  - latency_p95_ms: 3000ms objective (99.5% target)
  - error_rate_pct: 2% objective (99% target)
  - daily_cost_usd: $2.5 objective (100% target)
  - quality_score_avg: 0.75 objective (95% target)

Files Generated:
- `data/metrics.json`: Metrics snapshot with timestamp
- `data/metrics.csv`: Detailed metrics in CSV format
- `data/dashboard_report.html`: Interactive 6-panel dashboard HTML report

Sample Metrics:
```json
{
  "traffic": 10,
  "latency_p50": 150.0,
  "latency_p95": 150.0,
  "latency_p99": 150.0,
  "avg_cost_usd": 0.002,
  "total_cost_usd": 0.0198,
  "quality_avg": 0.88,
  "error_rate_pct": 0.0
}
```

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: (e.g., rag_slow)
- [SYMPTOMS_OBSERVED]: 
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]: 
- [PREVENTIVE_MEASURE]: 

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
