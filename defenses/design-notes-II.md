# Design notes — II-001 multi-tenant isolation monitoring (self-designed)

> **DESIGN_DEFENSE** (kind `designed`, origin `pgf`). No external solution was
> adopted; the detection control was self-designed for threat **THR-85f99df4**
> (category `infra-isolation`; techniques: tenant-escape, lateral-movement,
> token-exposure). **Defensive-only**: this is detection-and-flag, not an
> exploit, escape tool, or lateral-movement automation.

## Problem

Multi-tenant infrastructure (shared Kubernetes clusters, container hosts, cloud
projects) fails when the isolation boundary between tenants leaks. The threat
surfaces as observable *indicators* in logs, orchestrator config, and audit
streams — not as a single payload. SISAI ingests such text as **data**; per
`docs/SELF-DEFENSE.md` the deterministic boundary forbids elevating ingested
text to instructions, so the control must emit a **verdict only**.

## Detection strategy (indicator classes → patterns)

We mirror the PI-001 shape: a JSON rule of regexes, a pure-stdlib detector
(`load_rule` + `scan`), a labeled JSONL suite, and an evidence gate. Seven
indicator classes cover the threat's three techniques:

1. **cross-tenant-access** (tenant-escape) — an identity scoped to one
   tenant/namespace/project touching another's resource; explicit
   `cross-tenant` / `tenant boundary` markers and "belonging to other tenant".
2. **container-escape** (tenant-escape, critical) — host-path writes,
   `release_agent` abuse, `nsenter --target 1`, escape-to-host markers.
3. **privileged-breakout** (tenant-escape) — `privileged: true`,
   `hostPID/hostNetwork/hostPath: true`, `cap_add SYS_ADMIN`, `docker.sock`
   mounted into a workload (matched in either word order).
4. **lateral-movement** (lateral-movement) — `east-west` / `pod-to-pod` /
   cross-namespace connections that are *unexpected/unauthorized/denied*, and
   pivot-to-host/node markers.
5. **token-exposure** (token-exposure, critical) — SA/bearer tokens leaked in
   logs, the mounted `serviceaccount/token` path, JWT-shaped triplets, and
   cloud metadata (`169.254.169.254`) credential dumps.
6. **over-scoped-token** (token-exposure) — `cluster-admin` bound to a tenant
   SA/workload, wildcard RBAC verbs/resources, IAM `Action:* Resource:*`.
7. **namespace-cgroup-violation** (tenant-escape) — `setns/unshare` onto a
   foreign/host namespace, cgroup subtree-write breakout, AVC/seccomp/apparmor
   *denied* on mount/setns/ptrace.

## False-positive discipline

The benign half of the suite deliberately includes *normal* infra telemetry
that superficially shares vocabulary: healthy pod scheduling, an in-namespace
RBAC read, an ordinary container start, intra-tenant east-west traffic that is
*allowed/expected*, a successful token rotation with "no tokens exposed", a
multi-tenancy explainer doc, and a metadata-endpoint *hardening* note. Patterns
are scoped (e.g. lateral-movement requires an `unexpected/unauthorized/denied`
qualifier; token-exposure requires a `leak/exposed/dumped/plaintext` qualifier
or a concrete secret shape) so descriptive or healthy lines do not match.

## Verification

Gate: `python defenses/verify_ii_001.py` — PASS iff **recall == 1.0 AND
precision >= 0.85**. Measured over 19 labeled samples (12 malicious / 7 benign):
**recall = 1.0, precision = 1.0, tp=12 fp=0 tn=7 fn=0** → exit 0.

## Scope / non-goals

Output is an advisory verdict routed to `flag / isolate / require_human_review`.
This control does **not** perform tenant escape, generate escape primitives, or
automate lateral movement. It is a detection signature set for monitoring
ingested infra logs/config/audit text.
