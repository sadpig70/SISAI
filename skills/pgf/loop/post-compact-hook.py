#!/usr/bin/env python3
"""post-compact-hook — integrated into stop-hook.py. This stub is for backward compatibility."""
import sys, json
# Main logic is in stop-hook.py. This file exists for direct invocation compatibility.
print(json.dumps({"status": "use stop-hook.py"}))
