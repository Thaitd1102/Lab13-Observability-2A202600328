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
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | |
| Error Rate | < 2% | 28d | |
| Cost Budget | < $2.5/day | 1d | |

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
