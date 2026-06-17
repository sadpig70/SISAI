# DEF-5e4bdec3 — AI Gateway SQL Injection Defense + Supply-Chain Hardening

> Adapted from LiteLLM CVE-2026-42208 advisory (April 2026), OWASP Top 10,
> and NIST SSDF. Targets pre-auth SQL injection in AI gateways and broader
> supply-chain risks in AI infrastructure.

## Threat: CVE-2026-42208

LiteLLM (22k+ GitHub stars) is a widely-used open source AI Gateway that provides
a unified interface to 100+ LLM providers. The vulnerability exists in the proxy
API key validation path:

```python
# VULNERABLE (v1.81.16 to < v1.83.7):
query = f"SELECT * FROM api_keys WHERE key = '{caller_supplied_key}'"
# Attacker sends: ' OR '1'='1' -- 
# Results in: SELECT * FROM api_keys WHERE key = '' OR '1'='1' --'
```

Root cause: caller-supplied input was **concatenated** into the SQL query string
instead of being passed as a **separate parameter**.

- CVSS: 9.8 (Critical)
- Exploited in the wild within 36 hours of disclosure
- Fixed in v1.83.7-stable (April 19, 2026)
- Chainable with CVE-2026-42271 + CVE-2026-48710 for full RCE

## Defense Controls

### 1. param-bind-sql
**What**: Use parameterized queries exclusively. Never concatenate user input into
SQL strings. In Python: `cursor.execute("SELECT * FROM api_keys WHERE key = ?", (key,))`.
**Why CVE-2026-42208**: Directly addresses the root cause. The vulnerability
would not exist if the API key were passed as a bound parameter.

### 2. pre-auth-input-validation
**What**: Validate all inputs before they reach the database layer. API keys
should match expected format (length, character set) before any query is constructed.
**Why CVE-2026-42208**: Malformed API keys containing SQL metacharacters would be
rejected at the edge, preventing injection from reaching the database.

### 3. aibom-sbom
**What**: Maintain an AI Bill of Materials (AIBOM) and Software Bill of Materials
(SBOM) for all AI gateway dependencies. Track versions, known vulnerabilities,
and update status for every package in the AI supply chain.
**Why supply-chain**: LiteLLM's dependency tree (100+ LLM provider integrations)
is a large attack surface. SBOM visibility enables rapid identification of
affected components when a CVE is disclosed.

### 4. patch-prioritization-critical
**What**: Establish a tiered patch SLA: Critical (CVSS 9+) within 24h, High within
72h, Medium within 7 days. Automate dependency vulnerability scanning in CI/CD.
**Why CVE-2026-42208**: This vulnerability was exploited in 36 hours. Organizations
without rapid patch capability remained exposed. A 24h SLA would have outpaced
the exploitation window.

### 5. gateway-waf-rules
**What**: Deploy WAF rules at the AI gateway edge to detect and block SQL injection
patterns (UNION, stacked queries, time-based blind injection). Apply rate limiting
on API key validation endpoints.
**Why CVE-2026-42208**: Provides defense-in-depth. Even if application-layer
parameter binding fails, WAF rules catch SQLi patterns before they reach the backend.

## Broader Supply-Chain Coverage

These controls extend beyond CVE-2026-42208 to address:
- **pypi-poisoning**: SBOM visibility + dependency pinning
- **lora-adapter-poisoning**: Artifact provenance verification in the AI supply chain
- **ai-gateway-abuse**: WAF + rate limiting as gateway hardening

## References

- GitHub Advisory: LiteLLM CVE-2026-42208 — Pre-Auth SQL Injection in AI Proxy
- NVD: CVE-2026-42208 — CVSS 9.8 (NVD, verified 2026-06-17)
- The Hacker News: "LiteLLM SQL Injection Exploited within 36 Hours of Disclosure"
- CSA Research Note: "LiteLLM CVE-2026-42208: Pre-Auth SQL Injection in AI Proxy"
- OWASP Top 10: A03 Injection
- NIST SP 800-218 (SSDF): Patch management, vulnerability scanning
