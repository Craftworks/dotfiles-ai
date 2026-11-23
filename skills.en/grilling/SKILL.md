---
name: grilling
description: Relentlessly grill the user about a plan, decision, or idea. Use when you want to stress-test your thinking, or when a 'grill'-style trigger phrase is used.
---

Interview the user relentlessly until you reach a shared understanding. Picture this as a **design tree**: every decision branches into the decisions that hang beneath it.

Work through the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask **now** without guessing at answers you haven't heard yet. Ask the entire frontier in one round: number each question and attach a recommended answer. Then wait for the user's answers before moving to the next round.

Write each question so it is self-contained, with its premises and options judgeable on the spot. The round format is as follows:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Phrase each question so that answering "yes" adopts your recommendation.

With every round the user answers, the tree changes shape: settled decisions push the frontier outward and unblock the questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a **later** round, not this one.

Finding **facts** is the agent's job, never the user's. If a frontier question needs a fact from the environment (the filesystem, tools, etc.), dispatch a subagent with a fresh context window to look it up. Don't ask the user what you can look up yourself. Don't block on it either: an investigation in progress is an unsettled prerequisite, so only the questions downstream of it wait for the subagent's report, and the rest of the frontier is asked now. **Decisions** belong to the user: present each decision to the user, and wait.

The session is complete when the frontier is empty: every branch of the design tree has been visited, and nothing is left implicitly assumed. Do not act on it until the user confirms that you have reached a shared understanding.
