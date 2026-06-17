# DEF-d27540ac — AI Agent Least Privilege with Zero-Trust Command Execution

> Adapted from Microsoft "When Prompts Become Shells" (May 2026) and
> OWASP Agentic Top 10 2026. Targets CVE-2026-2256 (MS-Agent Shell tool RCE)
> and the broader "prompt injection → shell" attack class.

## Threat: CVE-2026-2256

ModelScope MS-Agent (v1.6.0rc1 and earlier) has a built-in Shell tool that allows
the AI agent to execute OS commands. The tool concatenates **prompt-derived** input
directly into shell commands without sanitization. A single malicious prompt can
trigger `rm -rf /`, exfiltrate secrets, or establish persistence.

Root cause: **agent identity is text** — the framework treats LLM output as trusted
parameters. Regex-based safety checks are trivially bypassed.

## Defense Controls

### 1. param-bind-not-interpolate
**What**: Never concatenate prompt-derived text into shell command strings. Use
parameterized execution APIs (`subprocess.run([cmd, arg1, arg2])` with fixed arg lists).
**Why CVE-2026-2256**: The Shell tool builds `os.system(f"echo {user_input}")`.
Parameter binding would prevent injection even if the prompt contains shell metacharacters.

### 2. tool-command-allowlist
**What**: Whitelist which commands/tools the agent can invoke. Deny by default.
Only pre-approved commands with validated argument schemas are accessible.
**Why CVE-2026-2256**: If the Shell tool were allowlist-gated, only safe commands
(e.g., `ls`, `cat`) would be permitted. `rm`, `curl`, `chmod` would be denied.

### 3. shell-container-isolation
**What**: Execute agent tool calls in an isolated container/sandbox with no host
filesystem access, limited network, and CPU/memory quotas.
**Why CVE-2026-2256**: Even if prompt injection compromises the Shell tool, the
blast radius is contained to the sandbox. Host compromise is prevented.

### 4. behavior-anomaly-detection
**What**: Monitor agent command sequences for anomalous patterns — unexpected
command types, excessive tool invocations, access to sensitive paths, outbound
network connections from tools that shouldn't need them.
**Why CVE-2026-2256**: An agent hijack attempt will produce unusual command
sequences (e.g., file download → permission change → execution). Pattern
detection flags this before damage occurs.

### 5. agent-output-as-untrusted
**What**: Apply zero-trust to all LLM outputs. Every model-generated command/parameter
passes through a validation gate before execution. Validate against schema, not regex.
**Why CVE-2026-2256**: The vulnerability exists because the framework trusts LLM
output. A validation layer between model output and system call breaks the
attack chain entirely.

## Applicability

These controls apply to any AI agent framework with tool/plugin execution:
- MS-Agent (ModelScope)
- Semantic Kernel (Microsoft)
- LangChain / CrewAI
- Custom agent implementations

## References

- Microsoft Security Blog: "When prompts become shells: RCE vulnerabilities in AI agent frameworks" (2026-05-07)
- NVD: CVE-2026-2256 — CVSS 6.5 (NVD, verified 2026-06-17)
- OWASP Agentic Top 10 2026: A01 (Prompt Injection), A06 (Excessive Agency)
- CVE-2026-26030, CVE-2026-25592 (Semantic Kernel — same class)
