# GD-001 — AI Agent Guardrail DoS Resilience

> Self-designed defense (pgf). Targets arXiv:2606.14517 — "From Shield to Target:
> Denial-of-Service Attacks on LLM-Based Agent Guardrails" (Zhou et al., June 2026).

## Threat: Guardrail DoS

LLM-based guardrails protect autonomous agents from prompt injection and jailbreak
attacks. However, Zhou et al. demonstrate that the very reasoning capability
enabling this protection introduces a novel vulnerability:

- Attackers inject **crafted data** that traps the guardrail in **extended
  reasoning loops**, consuming disproportionate compute
- A **single poisoned document** can saturate shared guardrail infrastructures
- Co-located agents are **starved** of guardrail protection, paralyzing the
  entire multi-agent system
- Two attack frameworks: **beam-search optimization** and **mechanism-aware
  mutations** systematically maximize guardrail reasoning length

Key insight: the guardrail's own intelligence becomes the attack surface.

## Defense Design (5 Controls)

### 1. reasoning-budget-hard-cap (GD-001-R1)
**Circuit breaker**: Enforce absolute maximum (4096 tokens / 5 seconds) for any
single guardrail LLM evaluation. If exceeded, abort the evaluation immediately.
This prevents infinite reasoning loops regardless of input craftiness.

### 2. per-agent-cost-isolation (GD-001-R2)
**Resource isolation**: Each agent/tenant receives an independent guardrail
compute budget. No shared quota pool. A poisoned document targeting Agent A
cannot consume Agent B's guardrail budget. Prevents the "single document
paralyzes entire system" scenario.

### 3. circuit-breaker-fail-open (GD-001-R3)
**Availability**: When guardrail is under DoS attack (>50% error rate or >90%
quota exhaustion), fail open with alert. Do not block all agent operations
waiting for guardrail resolution. Brief degradation is acceptable; total
paralysis is not.

### 4. guardrail-pattern-diversity (GD-001-R4)
**Redundancy**: Deploy at least 2 independent guardrail implementations (e.g.,
different LLM models, or rule-based + LLM hybrid). Rotate or ensemble. No single
point of DoS failure. If one guardrail is saturated, fall back to the secondary.

### 5. reasoning-loop-detection (GD-001-R5)
**Anomaly detection**: Track per-document guardrail reasoning length distribution.
Documents triggering >3 stddev above mean reasoning length are flagged and
quarantined for review. This detects beam-search and mechanism-aware mutation
payloads before they reach the guardrail.

## Verification Rationale

Each control maps directly to an attack technique from the paper:

| Control | Attack Technique Addressed |
|---------|--------------------------|
| reasoning-budget-hard-cap | reasoning-loop-exploitation |
| per-agent-cost-isolation | guardrail-dos (cross-agent starvation) |
| circuit-breaker-fail-open | guardrail-dos (system-wide paralysis) |
| guardrail-pattern-diversity | mechanism-aware-mutation (single-model targeting) |
| reasoning-loop-detection | single-document-poisoning |

## Reference

Zhou, Wang, Ma, Xue, Wang, Wang. "From Shield to Target: Denial-of-Service
Attacks on LLM-Based Agent Guardrails." arXiv:2606.14517, June 2026.
