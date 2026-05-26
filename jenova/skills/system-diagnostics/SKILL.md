---
name: system-diagnostics
description: Runs local diagnostic checks on the Jenova host machine before routing.
version: 1.0.0
trigger: "When the user asks about system health, connectivity, or internal status."
---

# System Diagnostics Rules
When evaluating system health, you must:
1. Always check the local system time first.
2. If the user asks for network status, execute the local `ping_test.py` script from the `/scripts` directory.
3. Format the diagnostic output cleanly before routing further requests.
