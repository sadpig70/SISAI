# DEF-26c6a25f — AI IDE Indirect Prompt Injection Defense with Red-Team Governance

> Adapted from Cursor CVE-2026-31854 advisory (March 2026), NIST AI RMF 1.0,
> and OWASP LLM Top 10 LLM01. Targets indirect prompt injection in AI coding
> assistants that leads to automatic command execution.

## Threat: CVE-2026-31854

Cursor is an AI-powered code editor. The vulnerability allowed **indirect prompt
injection** — malicious instructions hidden in external content (pull request
descriptions, README files, issue comments) — to influence the AI agent.

When combined with a **command whitelist bypass**, the injected instructions
could trigger automatic command execution **without the user's explicit intent**.
This transforms the AI assistant from a coding aid into an attack vector.

- CVSS: 8.8 (High)
- Fixed in Cursor 2.0 (March 2026)
- Attack chain: external content → indirect prompt injection → whitelist bypass → RCE

Root cause: **two failures compounded** — (1) untrusted external content treated
as trustworthy by the AI, and (2) regex-based command whitelist that could be
circumvented.

## Defense Controls

### 1. command-user-confirmation
**What**: Require explicit human approval before executing any AI-generated
system command. No automatic execution regardless of whitelist status.
**Why CVE-2026-31854**: The entire attack chain breaks if the user must manually
confirm every command. The "automatic execution without user intent" scenario
is eliminated.

### 2. untrusted-content-isolation
**What**: Treat all external content sources (PR descriptions, README files, issue
comments, git commit messages) as potentially hostile. Isolate them from the
agent's instruction context or apply strict sanitization before processing.
**Why CVE-2026-31854**: Indirect prompt injection originates from external content.
If the AI never processes untrusted content as instructions, the attack vector
is neutralized.

### 3. ai-red-team
**What**: Continuous adversarial testing: regularly test AI coding assistants with
known prompt injection payloads, whitelist bypass techniques, and novel attack
patterns. Track bypass rate as a key security metric.
**Why CVE-2026-31854**: Regex-based whitelists will always have bypasses. Red-team
testing discovers them before attackers do.

### 4. nist-ai-rmf-mapping
**What**: Map all AI IDE security controls to the NIST AI Risk Management Framework
(Govern, Map, Measure, Manage). Document coverage gaps and residual risk.
**Why governance**: CVE-2026-31854 demonstrates that AI coding assistants are
production systems with security requirements. NIST AI RMF provides the governance
framework for ongoing risk management.

### 5. incident-playbook
**What**: Define and rehearse incident response procedures for AI prompt injection:
detection indicators, containment steps (disable agent, revoke tokens), forensic
evidence collection (audit logs, command history), and recovery procedures.
**Why CVE-2026-31854**: When prompt injection is detected in an IDE, response
must be immediate to prevent lateral movement from IDE to host.

## Key Principle: Trust Nothing External

The fundamental lesson of CVE-2026-31854 (and the broader Cursor vulnerability
class including CVE-2026-26268) is: **AI coding assistants must not trust external
content**. Every file, every comment, every PR description is untrusted input
until validated.

## References

- NVD: CVE-2026-31854 — Indirect Prompt Injection in Cursor (CVSS 8.8)
- NVD: CVE-2026-26268 — Cursor Sandbox Escape via Git Hooks
- NIST AI RMF 1.0: Govern, Map, Measure, Manage
- OWASP LLM Top 10: LLM01 Prompt Injection
- OpenCVE: CVE-2026-31854 — Cursor Affected by Arbitrary Code Execution via Prompt Injection
