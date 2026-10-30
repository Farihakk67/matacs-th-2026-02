# \# MATACS-TH-2026-02: AI Proposal Triage Design

# 

# \- \*\*Name:\*\* Fariha Ghazi

# \- \*\*Reference:\*\* MATACS-TH-2026-02

# \- \*\*Time actually spent:\*\* 1 Hour

# \## Files

# 

# \- \[WRITEUP.md](WRITEUP.md): answers to the five questions

# \- \[diagram/process-flow.png](diagram/process-flow.png): flow from upload to ranked output (AI steps, rule steps, human checkpoints)

# \- \[PROMPTS.md](PROMPTS.md): extraction and reason prompts

# \- \[ranking.json](ranking.json): expected ranking of proposals A-E

# \- \[prototype/](prototype/): small deterministic scoring script (`python score.py extracted.json`); the AI step is represented by the saved `extracted.json`, so no API key is needed

# 

# \## How I used AI tools

# 

# I used Claude to help draft the write-up structure, the prompts, the flow diagram and the scoring script, and to check the scoring maths. I then read the outputs and made the final decisions on the design myself: AI only extracts facts, and eligibility, scoring and ranking are plain code with human checkpoints.

# 

# One example where I reviewed the AI’s work critically: its scoring script normalised price and timeline against flagged proposals too, so a proposal not yet cleared by a human could shift everyone else’s scores. I noted this as a limitation, and in a real system I would normalise only against eligible, human-cleared proposals.

