# PGF Agent Protocol — PG-Based Inter-Agent Communication Specification

> When dispatching an agent, pass a **PG specification** instead of a natural-language prompt.
> This is the shared language for AI-to-AI task delegation.

---

## 1. Why Communicate in PG

| Natural-language prompt | PG task specification |
|---|---|
| Intent can be ambiguous | Inputs/outputs are explicit via `def` signature |
| Verification criteria are implicit | `acceptance_criteria` is built in |
| Execution order is buried in prose | Structured via `@dep:`, `→` |
| Failure handling is unclear | Failure Strategy is explicit |
| Result format is inconsistent | Return contract via `-> ReturnType` |

Communicating in PG means:
- The **dispatching AI** conveys intent precisely
- The **executing AI** can self-verify against acceptance_criteria
- The **result** is typed, making integration easy

---

## 2. TaskSpec — Agent Dispatch Specification Format

Write the task you hand to an agent in the following PG structure:

```python
def task_name(
    # input parameters — all context needed for execution
    target_crate: Path,
    existing_pattern: Path,      # existing code to reference
    workspace_root: Path = "D:\\project\\ocwr",
) -> TaskResult:
    """One-line task description"""

    # context: (files/info the executing AI must read first)
    #   - Read(target_crate / "src/lib.rs")
    #   - Read(existing_pattern)

    # steps:
    #   1. Analyze the existing pattern
    #   2. Implement the new module
    #   3. Write tests
    #   4. cargo check + clippy

    # implementation:
    AI_implement_following_pattern(existing_pattern, target="new_module")

    # acceptance_criteria:
    #   - cargo check -p {crate} → 0 errors
    #   - cargo clippy -p {crate} -- -D warnings → 0 warnings
    #   - tests >= N
    #   - existing tests unchanged

    # failure_strategy:
    #   - compile error → AI_fix_compile_error(error_msg)
    #   - clippy warning → AI_fix_clippy_warning(warning_msg)
    #   - max_retry: 3

    # return:
    #   TaskResult = {
    #       files_created: list[Path],
    #       files_modified: list[Path],
    #       test_count: int,
    #       summary: str,
    #   }
```

### Required Sections

| Section | Role | Required |
|---|---|---|
| `def` signature | Input parameters + return type | ✅ |
| `"""docstring"""` | One-line task description | ✅ |
| `# context:` | Files to read before execution | ✅ |
| `# acceptance_criteria:` | Completion criteria | ✅ |
| `# steps:` | Execution order (optional) | ○ |
| `# implementation:` | Core logic (`AI_` or actual code) | ○ |
| `# failure_strategy:` | Handling on failure | ○ |
| `# return:` | Result structure | ○ |

---

## 3. Parallel Dispatch — [parallel] TaskSpec

When dispatching multiple agents simultaneously:

```python
[parallel]

def implement_discord_adapter(channels: Path) -> AdapterResult:
    """Discord REST API adapter"""
    # context: Read(channels / "adapters/slack.rs")
    # acceptance_criteria: cargo check, tests >= 10

def implement_slack_adapter(channels: Path) -> AdapterResult:
    """Slack Web API adapter"""
    # context: Read(channels / "adapters/discord.rs")  # reference the one completed first
    # acceptance_criteria: cargo check, tests >= 10

def implement_telegram_adapter(channels: Path) -> AdapterResult:
    """Telegram Bot API adapter"""
    # context: Read(channels / "adapter.rs")
    # acceptance_criteria: cargo check, tests >= 10

[/parallel]

# integration verification — after all parallel tasks complete
def verify_all_adapters(workspace: Path) -> VerifyResult:
    """Integration verification of all adapters"""
    # @dep: implement_discord_adapter, implement_slack_adapter, implement_telegram_adapter
    cargo_check(workspace, "--workspace")
    cargo_test(workspace, "-p ocwr_channels")
```

---

## 4. Dependency-Chain Dispatch — @dep TaskSpec

Delegating ordered tasks:

```python
def expand_adapter_traits(channels: Path) -> TraitResult:
    """Add 7 channel adapter interfaces"""
    # acceptance_criteria: AdapterKind.TOTAL == 16

def implement_adapters(channels: Path) -> list[AdapterResult]:
    """Implement 6 channel adapters"""
    # @dep: expand_adapter_traits
    # ↑ run only after the trait expansion is complete
    [parallel]
    AI_implement("discord")
    AI_implement("slack")
    AI_implement("telegram")
    [/parallel]
```

---

## 5. Result Reporting Format — TaskResult

The result returned by the executing AI also follows a PG structure:

```python
# success result
TaskResult = {
    "status": "done",
    "files_created": ["src/adapters/discord.rs"],
    "files_modified": ["src/adapters/mod.rs", "src/lib.rs"],
    "test_count": 12,
    "summary": "Discord REST API adapter: send/embed/react/delete + 12 tests",
    "acceptance": {
        "cargo_check": "pass",
        "clippy": "pass",
        "tests": "12/12 pass",
    },
}

# failure result
TaskResult = {
    "status": "blocked",
    "blocker": "reqwest crate not in workspace dependencies",
    "attempted_fix": "Added reqwest to Cargo.toml but version conflict with existing dep",
    "suggestion": "Upgrade workspace reqwest from 0.11 to 0.12",
}
```

---

## 6. Orchestrator → Agent Flow

When PGF's execute phase encounters a `[parallel]` block:

```python
def orchestrate_parallel_block(nodes: list[GantreeNode], design: Path):
    """Dispatch the nodes of a [parallel] block as agents"""

    for node in nodes:
        # 1. Extract the TaskSpec from the node's PPR def or # comments
        task_spec = extract_task_spec(node, design)

        # 2. Pass the PG-format TaskSpec as the agent prompt
        agent_prompt = format_pg_task_spec(task_spec)

        # 3. Dispatch via the Agent tool
        Agent(
            prompt=agent_prompt,
            name=node.name,
            mode="bypassPermissions",
            run_in_background=True,
        )

    # 4. Wait for all agents to complete
    # 5. Collect each agent's TaskResult
    # 6. Cross-verify acceptance_criteria
```

### PG TaskSpec → Agent Prompt Conversion Rules

```python
def format_pg_task_spec(spec: TaskSpec) -> str:
    """Convert a PG TaskSpec into a prompt the agent can understand

    Key: convert into executable instructions while preserving the PG structure.
    Minimize natural-language explanation; the PG specification is the body of the instruction.
    """
    prompt = f"""You are executing a PG TaskSpec.

## TaskSpec

```python
{spec.to_pg_string()}
```

## Execution Rules
1. Read files listed in `# context:` first
2. Follow `# steps:` in order
3. Verify against `# acceptance_criteria:` before reporting done
4. On failure, apply `# failure_strategy:`
5. Return result in TaskResult format
"""
    return prompt
```

---

## 7. Worked Example — Natural Language → PG Conversion from a Previous Session

### Before (natural-language prompt)

```
Implement a Discord channel adapter for the OCWR Rust project at D:\openclaw\ocwr.
The channel adapter framework is in crates/ocwr_channels/src/adapter.rs — read it first...
Create DiscordAdapter struct that contains bot token, HTTP client, Discord API base URL...
Implement send_message, send_embed, add_reaction, delete_message...
Add unit tests, run cargo check, run clippy...
```

### After (PG TaskSpec)

```python
def implement_discord_adapter(
    channels_crate: Path = "D:\\openclaw\\ocwr\\crates\\ocwr_channels",
) -> AdapterResult:
    """Implement Discord REST API channel adapter"""

    # context:
    #   - Read(channels_crate / "src/adapter.rs")      # check trait types
    #   - Read(channels_crate / "src/adapters/mod.rs")  # registration pattern
    #   - Read(channels_crate / "src/message.rs")       # message types

    # implementation:
    adapter = DiscordAdapter(
        config: DiscordConfig = {bot_token: str, guild_id: str, command_prefix: Optional[str]},
        client: reqwest.Client,
        base_url: str = "https://discord.com/api/v10",
    )

    methods = [
        send_message(channel_id: str, content: str) -> DiscordMessage,
        send_embed(channel_id: str, embed: DiscordEmbed) -> DiscordMessage,
        add_reaction(channel_id: str, message_id: str, emoji: str) -> None,
        delete_message(channel_id: str, message_id: str) -> None,
        get_guild_channels(guild_id: str) -> list[DiscordChannel],
        get_guild_members(guild_id: str) -> list[DiscordUser],
    ]

    # acceptance_criteria:
    #   - cargo check -p ocwr_channels → 0 errors
    #   - cargo clippy -p ocwr_channels -- -D warnings → 0 warnings
    #   - tests >= 10 (config, serde, construction, API URL building)
    #   - Authorization header: "Bot {token}"
    #   - Debug output: token redacted

    # failure_strategy:
    #   - compile error → AI_fix_compile_error(error_msg, max_retry=3)
    #   - clippy warning → AI_fix_clippy_warning(warning_msg)

    # return:
    #   AdapterResult = {files_created, files_modified, test_count, summary}
```

**Difference**: natural language 17 lines → PG 35 lines, but **intent clarity, verifiability, and failure handling** are structurally built in.

---

## 8. Application Rules

### Application in the PGF execute Phase

1. **When dispatching the nodes of a `[parallel]` block as agents**: use a PG TaskSpec instead of natural language
2. **When dispatching a single node as an agent** (because it is large): use a PG TaskSpec
3. **When executing directly** (because it is small): no TaskSpec needed — interpret/execute the PPR def directly

### Criteria for Deciding to Use a PG TaskSpec

| Situation | Use TaskSpec |
|---|---|
| Direct execution (within 15 minutes) | ❌ direct execution |
| Agent dispatch (simple task) | ○ brief TaskSpec |
| Agent dispatch (complex task) | ✅ full TaskSpec |
| Parallel dispatch of multiple agents | ✅ required — type contracts needed for result integration |

### Integrating Results After Agent Execution

```python
def integrate_agent_results(results: list[TaskResult]) -> IntegrationResult:
    """Integrate parallel agent results + cross-verify"""

    # 1. Confirm all agents met acceptance_criteria
    failed = [r for r in results if r["status"] != "done"]
    if failed:
        AI_handle_failures(failed)

    # 2. Workspace-wide integration verification
    cargo_check("--workspace")

    # 3. Cross-dependency verification (does agent A's result affect agent B?)
    AI_verify_cross_dependencies(results)
```
