\# Personal Budget Assistant Agent (Topic T1)



CSE476 — Agentic AI and Intelligent Automation, CA1 Project 1



\## Two Tools



1\. \*\*add\_expense(item, amount, category)\*\* — Records a purchase into session memory.

2\. \*\*get\_summary(category?)\*\* — Returns total spending, optionally filtered by category.



\## What Memory Does



The `BudgetMemory` class stores every expense added and every conversation turn (goal, tool calls, observations). When the user asks a follow-up like \*"Can I still afford the trip?"\*, the agent reads back the running total from earlier turns instead of starting from zero.



\## One Honest Failure



Initially, the plan phase generated all steps upfront, and the act phase ran them blindly. This broke when Step 2 (`get\_summary`) ran before Step 1 (`add\_expense`) finished writing to memory, causing the summary to show stale data. I fixed it by making the act loop strictly sequential: each step completes and writes to memory before the next step is executed, so later steps always see updated state.



\## How to Run



```bash

python budget\_agent.py

