# Alert Rules and Runbooks

## Alert Configuration (config/alert_rules.yaml)

All 3 alerts are configured in `config/alert_rules.yaml`:

```yaml
alerts:
  - name: high_latency_p95
    severity: P2
    condition: latency_p95_ms > 5000 for 30m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#1-high-latency-p95
    
  - name: high_error_rate
    severity: P1
    condition: error_rate_pct > 5 for 5m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#2-high-error-rate
    
  - name: cost_budget_spike
    severity: P2
    condition: hourly_cost_usd > 2x_baseline for 15m
    type: symptom-based
    owner: finops-owner
    runbook: docs/alerts.md#3-cost-budget-spike
```

---

## 1. High Latency P95

**Alert Rule:** `latency_p95_ms > 5000 for 30m`
- **Severity:** P2 (Medium)
- **Owner:** team-oncall
- **Impact:** Tail latency (P95) breaches SLO (target: 3000ms)
- **Expected Frequency:** Low (prod issue)

### Troubleshooting Runbook

#### Step 1: Verify Alert (5 min)
```bash
# Check current metrics
curl http://localhost:8000/metrics | jq '.latency_p95'

# Expected: > 5000ms if alert is firing
```

#### Step 2: Investigate Root Cause (10 min)
1. **Check trace waterfall** (Langfuse)
   - Group by feature (qa vs summary)
   - Compare RAG span duration vs LLM span
   - Which component is slow?

2. **Check logs** for slow spans
   ```
   grep "latency_ms" data/logs.jsonl | jq '.|select(.latency_ms > 5000)'
   ```
   
3. **Check incident toggles**
   ```bash
   # Is rag_slow enabled?
   curl http://localhost:8000/health | jq '.incidents'
   ```

#### Step 3: Mitigation (5-10 min)
| Root Cause | Fix |
|--------|----|
| RAG retrieval slow | Reduce context window, use faster retriever |
| LLM inference slow | Route to faster model, use prompt cache |
| Both slow | Truncate queries, reduce batch size |
| Incident injected | Disable via: `python scripts/inject_incident.py --scenario none` |

#### Step 4: Verify Fix
```bash
# Monitor next 5 requests
python scripts/load_test.py --concurrency 1

# Check updated metrics
python scripts/export_metrics.py
```

---

## 2. High Error Rate

**Alert Rule:** `error_rate_pct > 5 for 5m`
- **Severity:** P1 (High - User-facing)
- **Owner:** team-oncall
- **Impact:** >5% of requests fail, users see errors
- **Expected Frequency:** Very low (prod outage)

### Troubleshooting Runbook

#### Step 1: Verify Alert (2 min)
```bash
# Check current error rate
curl http://localhost:8000/metrics | jq '.error_rate_pct'

# Expected: > 5%
```

#### Step 2: Investigate Root Cause (10 min)
1. **Group errors by type**
   ```bash
   grep "request_failed" data/logs.jsonl | jq -r '.error_type' | sort | uniq -c
   ```

2. **Check trace failures** (Langfuse)
   - Filter by `status: error`
   - View stack traces
   - Determine: LLM? Tool? Schema?

3. **Check incident toggles**
   ```bash
   curl http://localhost:8000/health | jq '.incidents'
   ```

#### Step 3: Mitigation (5-10 min)
| Root Cause | Fix |
|--------|----|
| LLM errors | Retry, fallback to different model |
| Tool/RAG errors | Disable tool, use simple baseline |
| Schema validation | Check logs for validation errors, fix parsing |
| Incident injected | Disable via: `python scripts/inject_incident.py --scenario none` |

#### Step 4: Escalation
- If not resolved in 5 min: Page on-call engineer
- If > 10% errors for > 10 min: Consider service degradation page

---

## 3. Cost Budget Spike

**Alert Rule:** `hourly_cost_usd > 2x_baseline for 15m`
- **Severity:** P2 (Medium)
- **Owner:** finops-owner
- **Impact:** Burn rate exceeds budget (~$2.5/day limit)
- **Expected Frequency:** Low (optimization required)

### Troubleshooting Runbook

#### Step 1: Verify Alert (5 min)
```bash
# Check current cost metrics
curl http://localhost:8000/metrics | jq '.{total_cost_usd, avg_cost_usd, tokens_in_total, tokens_out_total}'

# Baseline: ~$0.002 per request (340 tokens in, 1463 tokens out)
# Alert triggers if running ~2x higher
```

#### Step 2: Investigate Root Cause (10 min)
1. **Split traces by feature**
   ```bash
   # Which feature is expensive?
   grep "response_sent" data/logs.jsonl | jq '{feature, cost_usd} | group_by(.feature)'
   ```

2. **Compare token usage**
   - Input tokens vs baseline
   - Output tokens vs baseline
   - Is prompt enlarged? Is response longer?

3. **Check incident toggles**
   ```bash
   curl http://localhost:8000/health | jq '.incidents.cost_spike'
   ```

#### Step 3: Mitigation (10-15 min)
| Root Cause | Fix |
|--------|----|
| Longer prompts | Reduce context window, summarize inputs |
| Longer responses | Add output length limit to prompt |
| Expensive feature | Route easy queries to cheaper model |
| Token explosion | Add cache, reuse computed embeddings |
| Incident injected | Disable via: `python scripts/inject_incident.py --scenario none` |

#### Step 4: Verify
```bash
# Monitor cost over next hour
for i in {1..20}; do
  python scripts/load_test.py --concurrency 1
  sleep 10
done
python scripts/export_metrics.py
# Cost should return to ~$0.002/request
```

---

## Testing Alerts

### Quick Test Workflow:

#### Trigger Alert 1: High Latency
```bash
# Enable rag_slow incident (will increase latency)
python scripts/inject_incident.py --scenario rag_slow

# Monitor dashboard
python scripts/generate_dashboard.py

# You'll see: latency_p95 increases
# Alert would fire if sustained for 30m
```

#### Trigger Alert 2: High Error Rate
```bash
# Enable tool_fail incident (will cause errors)
python scripts/inject_incident.py --scenario tool_fail

# Send requests
python scripts/load_test.py --concurrency 5

# Check metrics
curl http://localhost:8000/metrics | jq '.error_rate_pct'

# Alert would fire if error_rate > 5% for 5m
```

#### Trigger Alert 3: Cost Spike
```bash
# Enable cost_spike incident
python scripts/inject_incident.py --scenario cost_spike

# Send requests (will show inflated tokens)
python scripts/load_test.py --concurrency 5

# Check cost metrics
python scripts/export_metrics.py
```

#### Cleanup: Disable All Incidents
```bash
# Disable all incidents
python scripts/inject_incident.py --scenario none
```

---

## Alert Response SLO

| Alert | Max Response Time | Escalation |
|-------|-------------------|-----------|
| P1 (Error Rate) | 5 min | Page on-call |
| P2 (Latency, Cost) | 15 min | Slack notification |

---

## Alert Testing Checklist

- [ ] Alert 1 (High Latency) can be triggered with `rag_slow` incident
- [ ] Alert 2 (High Error Rate) can be triggered with `tool_fail` incident
- [ ] Alert 3 (Cost Spike) can be triggered with `cost_spike` incident
- [ ] All incidents can be disabled/cleared
- [ ] Metrics dashboard updates when incidents are triggered
- [ ] Runbooks are actionable (can follow steps to resolve)
