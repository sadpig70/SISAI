# DEF-ghe-001 -- AI IDE Sandbox Integrity: Git Write Protection + Scope Isolation

> Adapted from Cursor CVE-2026-26268 advisory (March 2026) and SentinelOne
> vulnerability analysis. Targets AI agent sandbox escape via Git hook injection.

## Threat: CVE-2026-26268

Cursor (v2.4 and earlier) allowed AI agents to write to `.git/config` and
`.git/hooks` files inside the project. A malicious prompt could:

1. **Indirect injection** -- attacker embeds instructions in external content
2. **Rewrite `.git/config`** -- inject `core.hooksPath` or hook definitions
3. **Inject malicious hooks** -- write `pre-commit`, `post-checkout` hooks
4. **Trigger RCE** -- next Git operation executes the hook outside the sandbox

This is a sandbox escape: the AI agent is sandboxed, but Git hooks execute at
the **host level**, breaking containment.

- CVSS: 9.9 (Critical, NVD, verified 2026-06-17)
- Fixed in Cursor 2.5
- Attack chain: prompt injection -> .git manipulation -> hook execution -> host RCE

## Defense Controls

### 1. git-config-write-protection (filesystem-level)
**What**: Block AI agent write access to `.git/config` and `.git/hooks/*` at the
filesystem level. Use OS-level ACLs or sandbox policies.
**Why CVE-2026-26268**: Directly prevents the attack. If the agent cannot write
to hook files, it cannot inject malicious hooks regardless of prompt content.

### 2. sandbox-git-isolation (virtual .git)
**What**: Route all Git operations through a virtual `.git` directory inside the
sandbox. The real `.git` is mounted read-only or not mounted at all.
**Why CVE-2026-26268**: Even if the agent writes hooks, they execute in the
sandbox environment, not on the host. Breaks the escape chain at the boundary.

### 3. agent-filesystem-scope (workspace-only)
**What**: Limit AI agent write access to the project workspace directory only.
Exclude `.git`, `.cursor`, and other metadata directories from the write scope.
**Why CVE-2026-26268**: Defense in depth. Even if one protection fails, the
agent's limited write scope prevents `.git` manipulation.

### 4. hook-execution-audit (detection)
**What**: Log every Git hook execution with: hook path, hook content hash,
trigger event, and user notification. Alert on hook content changes since last
approval.
**Why CVE-2026-26268**: If hooks are somehow injected, audit trails enable
rapid detection and forensic analysis before lateral movement.

### 5. sandbox-integrity-check (verification)
**What**: Periodically verify sandbox boundaries: check that `.git/hooks/`
files match known-good state, verify that no unexpected filesystem mounts
exist, validate that process isolation is intact.
**Why CVE-2026-26268**: Ongoing integrity verification catches sandbox
degradation before it becomes exploitable.

## Relationship to CVE-2026-31854

Both Cursor vulnerabilities exploit the same fundamental weakness: AI agent
in a coding IDE with filesystem access. CVE-2026-26268 targets Git hooks as
the escape vector, while CVE-2026-31854 targets command whitelist bypass.
Combined defense (DEF-26c6a25f + DEF-ghe-001) provides comprehensive coverage.

## References

- NVD: CVE-2026-26268 -- Cursor Sandbox Escape via .git Configuration
- SentinelOne: CVE-2026-26268 Analysis -- Git Hooks as Sandbox Escape
- CVEfeed.io: CVE-2026-26268 -- Cursor sandbox escape via Git hooks
