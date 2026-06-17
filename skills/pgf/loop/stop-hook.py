#!/usr/bin/env python3
"""
PGF-Loop runtime adapter (Python version).

This script is usable by any runtime that can call a command and feed optional
JSON on stdin. Hook-based runtimes may use the returned block/directive JSON;
manual runtimes may read the same prompt and continue the next node explicitly.

stdin: optional JSON { "session_id": "...", "transcript_path": "..." }
stdout: JSON { "decision": "block", "reason": "...", "systemMessage": "..." }
        or exit 0 with no output (normal termination)
"""
import sys, json, re
import os
from pathlib import Path

# Korean status normalization
KO_STATUS = {
    "\uc644\ub8cc": "done",         # 완료
    "\uc9c4\ud589\uc911": "in_progress",  # 진행중
    "\uc124\uacc4\uc911": "pending",      # 설계중
    "\ubcf4\ub958": "blocked",            # 보류
}

def normalize_status(s):
    return KO_STATUS.get(s, s)

STATE_FILE = Path(os.environ.get("PGF_LOOP_STATE_FILE", ".pgf/runtime/pgf-loop-state.json"))

def select_next_node(workplan_path, status_path):
    """Select the next non-terminal node from WORKPLAN order."""
    try:
        status = json.loads(Path(status_path).read_text(encoding="utf-8"))
    except:
        return ""

    nodes = status.get("nodes", {})
    workplan_text = Path(workplan_path).read_text(encoding="utf-8") if Path(workplan_path).exists() else ""

    # Find first non-terminal node in WORKPLAN order
    # Parse node names from workplan (lines with status markers)
    wp_nodes = []
    for line in workplan_text.split("\n"):
        m = re.match(r'[|\s├└─]*\s*[\d.]+\s+(\S+)', line)
        if m:
            wp_nodes.append(m.group(1))

    # Fallback: use status.json keys
    if not wp_nodes:
        wp_nodes = list(nodes.keys())

    for name in wp_nodes:
        if name in nodes:
            st = normalize_status(nodes[name].get("status", ""))
            if st not in ("done", "blocked", "skipped"):
                return name

    return ""

def extract_ppr(node_name, workplan_path, design_path=""):
    """Extract the PPR block for a node (DESIGN → WORKPLAN fallback)."""
    # Strategy 1: DESIGN PPR
    if design_path and Path(design_path).exists():
        text = Path(design_path).read_text(encoding="utf-8")
        # Find ```ppr ... ``` or def {node_name} block
        pattern = rf'(def\s+{re.escape(node_name)}\s*\(.*?\n(?:.*?\n)*?(?:\s*#\s*acceptance:.*?\n))'
        m = re.search(pattern, text)
        if m:
            return m.group(1)

    # Strategy 2: WORKPLAN inline comments
    if Path(workplan_path).exists():
        text = Path(workplan_path).read_text(encoding="utf-8")
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if node_name in line:
                # Collect inline comment (# ...) on same line or following lines
                comments = []
                # Check same line
                if "#" in line:
                    comments.append(line.split("#", 1)[1].strip())
                # Check following indented comment lines
                for j in range(i+1, min(i+10, len(lines))):
                    stripped = lines[j].strip()
                    if stripped.startswith("#"):
                        comments.append(stripped[1:].strip())
                    elif stripped == "":
                        continue
                    else:
                        break
                if comments:
                    return "\n".join(comments)
    return ""

def main():
    # 1. Check state file
    if not STATE_FILE.exists():
        sys.exit(0)

    # 2. Parse stdin
    try:
        hook_raw = sys.stdin.read()
        hook_input = json.loads(hook_raw) if hook_raw.strip() else {}
    except:
        sys.exit(0)
    hook_sid = hook_input.get("session_id", "")

    # 3. Load state
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except:
        STATE_FILE.unlink(missing_ok=True)
        sys.exit(0)

    state_sid = state.get("session_id", "")
    iteration = int(state.get("iteration", 0))
    max_iter = int(state.get("max_iterations", 0))
    workplan_path = state.get("workplan_path", "")
    design_path = state.get("design_path", "")
    status_path = state.get("status_path", "")
    current_node = state.get("current_node", "")
    loop_mode = state.get("mode", "standard")
    policy = state.get("policy", {})

    # 4. Session isolation
    if state_sid and hook_sid and state_sid != hook_sid:
        sys.exit(0)

    # 5. Iteration limit
    if max_iter > 0 and iteration >= max_iter:
        STATE_FILE.unlink(missing_ok=True)
        print(f"[PGF-Loop] max_iterations ({max_iter}) reached.", file=sys.stderr)
        sys.exit(0)

    # 6. Load status.json
    if not Path(status_path).exists():
        STATE_FILE.unlink(missing_ok=True)
        print(f"[PGF-Loop] status.json not found: {status_path}", file=sys.stderr)
        sys.exit(0)

    try:
        status = json.loads(Path(status_path).read_text(encoding="utf-8"))
    except:
        STATE_FILE.unlink(missing_ok=True)
        sys.exit(0)

    # 7. Select next node
    next_node = select_next_node(workplan_path, status_path)
    if not next_node:
        STATE_FILE.unlink(missing_ok=True)
        print("[PGF-Loop] All nodes terminal. Loop complete.", file=sys.stderr)
        sys.exit(0)

    # 7.1 Retry tracking
    max_retry = int(policy.get("max_retry", 3)) if policy else 3
    retry_counts = state.get("retry_counts", {})

    if next_node == current_node:
        retry_count = int(retry_counts.get(next_node, 0)) + 1
        retry_counts[next_node] = retry_count

        if retry_count > max_retry:
            nodes = status.get("nodes", {})
            if next_node in nodes:
                nodes[next_node]["status"] = "blocked"
                nodes[next_node]["blocker"] = f"max_retry ({max_retry}) exceeded after {retry_count} attempts"
                Path(status_path).write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

            on_blocked = policy.get("on_blocked", "skip_and_continue") if policy else "skip_and_continue"
            if on_blocked == "halt":
                STATE_FILE.unlink(missing_ok=True)
                print("[PGF-Loop] on_blocked=halt. Loop terminated.", file=sys.stderr)
                sys.exit(0)

            next_node = select_next_node(workplan_path, status_path)
            if not next_node:
                STATE_FILE.unlink(missing_ok=True)
                sys.exit(0)
    else:
        retry_counts[next_node] = 0

    state["retry_counts"] = retry_counts

    # 8. Extract PPR
    ppr_block = extract_ppr(next_node, workplan_path, design_path)

    # 9. Progress
    nodes = status.get("nodes", {})
    done_count = sum(1 for n in nodes.values() if normalize_status(n.get("status", "")) == "done")
    total_count = len(nodes)

    # 10. Construct prompt
    mode_label = " [Lightweight]" if loop_mode == "lightweight" else ""
    prompt = f"[PGF-Loop]{mode_label} Node Execution Directive\n\n"
    prompt += f"Project: {state.get('project', '')}\n"
    prompt += f"Current node: {next_node}\n"
    prompt += f"Progress: {done_count}/{total_count} nodes done\n"
    prompt += f"WORKPLAN: {workplan_path}\n"
    if design_path:
        prompt += f"DESIGN: {design_path}\n"
    prompt += f"status.json: {status_path}\n"

    if ppr_block and ppr_block.strip():
        if loop_mode == "lightweight":
            prompt += f"\n## Task Spec for This Node (WORKPLAN Inline)\n\n{ppr_block}\n\nImplement according to the intent of the above task spec.\n"
        else:
            prompt += f"\n## PPR Implementation Spec for This Node\n\n{ppr_block}\n\nImplement according to the intent of the above PPR. Execute AI_ prefixed functions as AI cognitive operations directly, and implement regular functions as actual code.\n"
    else:
        prompt += "\nThis is an atomic node. Read the node description from WORKPLAN and implement directly.\n"

    prompt += f"""
## Required Post-Completion Tasks

1. Change this node's ({next_node}) status to (done) in WORKPLAN ({workplan_path})
2. Update this node to "done" in status ({status_path}) + record completed_at + recalculate summary
3. Progress report: [PGF] {next_node} (done) | N/M nodes done | next: NextNode

## On Failure
- Up to {max_retry} retries allowed
- On final failure, change status to (blocked) and record blocker reason
"""

    # 11. Update state
    state["iteration"] = iteration + 1
    state["current_node"] = next_node
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    # 12. Return block decision
    result = {
        "decision": "block",
        "reason": prompt,
        "systemMessage": f"[PGF-Loop]{mode_label} iteration {iteration + 1} | node: {next_node} | {done_count}/{total_count} done"
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
