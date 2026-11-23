---
name: research
description: Research a question based on reliable primary sources and leave the results in a Markdown file. Use when the user asks for research on a topic, fact-checking of documentation or APIs, or delegation of reading work.
---

Launch a **background agent** to do the research and keep working while it reads. At launch, it starts with a fresh context window.

Its job:

1. Investigate the question against **primary sources** (official documentation, source code, specifications, the provider's API). Do not settle for secondary explanations. Trace each claim back to the source that owns it
2. Write the results to a single Markdown file, citing the source for each claim
3. Match the save location to the convention the repository already uses for such files. If there is no convention, put it in a reasonable place and tell the user where
