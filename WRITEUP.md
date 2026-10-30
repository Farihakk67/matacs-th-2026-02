# Write-up: AI Proposal Triage Design

**Flow in one line:** upload → text extraction (code) → AI extracts facts with quotes → code validates → code checks mandatory criteria → code scores and ranks → human reviews → decision logged. See `diagram/`.

## 1. AI vs. rules

**AI is used for one thing only:** reading messy proposal text and pulling out facts (licence stated?, install count, price, weeks, warranty years, team details) into a fixed JSON schema, each with a short supporting quote. An optional second AI call turns the final numbers into a one-line reason.

**Everything else is plain code:** PDF-to-text, schema validation, mandatory pass/fail, score formulas, weights, ranking, tie-breaks, logging.

**Why there:** language understanding is what AI is good at, and proposals are free text. Arithmetic and eligibility must be exact, repeatable and auditable, and code does that better than an AI. The AI never sees the weights and never produces a score.

## 2. Consistency and explainability

- Extraction runs at temperature 0 with enforced JSON schema, pinned model version and a versioned prompt. Scoring is deterministic code, so the same extracted facts always give the same score.
- Honest answer to "same result twice?": the code is identical every time, and the AI step is very stable but not guaranteed. So I save the extraction output per proposal and reuse it on re-runs. A re-rank re-uses the stored extraction unless the reviewer asks to re-extract. Optionally extract twice and flag any field where the two runs disagree.
- Each score is a plain formula (e.g. price = lowest eligible price ÷ this price × 100; warranty = panel years and workmanship years against caps). The reviewer sees a table: each criterion, the extracted value, the quote and page, the points awarded and the weight. Rank reasons are generated from that table, not invented.

## 3. Human in the loop

- **Checkpoint 1 (before scoring):** reviewer sees extracted values next to quotes and can correct any field. Missing or low-confidence fields are highlighted.
- **Checkpoint 2 (flags):** proposals that fail mandatory checks, have missing critical facts, or trip the injection detector go to a review queue rather than being silently ranked or dropped.
- **Checkpoint 3 (result):** the ranking is advisory. The reviewer can override a rank or an eligibility call with a mandatory written reason. A human makes the award decision.
- **Audit log (append-only):** proposal file hash, who uploaded, criteria version, prompt version, model name and version, raw AI output, validated extraction, every score and formula input, every human edit or override (who, when, before, after, reason), final decision.

## 4. Changing criteria

Criteria are versioned. Each scoring run stores the criteria version it used. If an admin edits weights or criteria:

- Old results stay as they were and are labelled with their old version. Nothing is silently rescored.
- Weight-only changes need no AI call: code re-scores from the stored extractions, so it is cheap and instant.
- If a criterion is added or its definition changes, only that field is re-extracted.
- The UI marks affected results as "scored under an older version" and the reviewer chooses to re-run. A single ranking must never mix versions. Active in-progress rankings are locked to the version in use until the reviewer re-runs.

## 5. Risks

| Risk | Safeguard |
|---|---|
| Wrong extraction | Quote required for every value, schema validation, check that the quote really appears in the source text, reviewer sees quotes at checkpoint 1 |
| Made-up facts | "Return null if not stated" rule, evidence rule (no quote means null), code check that quotes exist in the PDF text |
| Prompt injection / manipulation | Proposal text is treated as data in tags; the AI only extracts and never scores, so an instruction cannot change a score; a detector flags suspicious instructions and routes the proposal to a human; no tools or actions available to the AI |
| Vague or conditional claims | "To be confirmed" counts as not stated. Mandatory checks need a firm statement by the bidder |
| Bias | Scoring uses only admin criteria. Company name and location are not scoring inputs; the reviewer can see all components, and an audit report can compare outcomes |
| Scanned or bad PDFs | OCR fallback; if text quality is low, flag the file instead of guessing |
| Unfair price/timeline scaling | Normalisation is shown to the reviewer; extreme outliers are flagged |
| Cost | One short call per proposal, cached extractions, re-scoring is free |
| Privacy | Only the necessary text is sent to the model; logs are access-controlled |

## How it handles the sample set

- **A, E** pass mandatory checks and are ranked (A first, E second).
- **B** fails the mandatory licence check (relies on a subcontractor still to be named), so it is ineligible no matter how cheap it is.
- **C** contains an embedded instruction aimed at automated reviewers. It is ignored, flagged and sent to a human. On its genuine content it would rank third.
- **D** passes mandatory checks and has the lowest eligible price, but has no committed schedule, so the timeline cannot be scored. It is flagged and the reviewer asks for a date rather than the tool guessing.

## Assumptions

- Experience score = qualifying installs capped at 15. Workmanship warranty capped at 12 years. Team score = 4 equal checklist items. These are my own assumptions and are admin-configurable.
- Price and timeline are scored relative to the best eligible proposal. A hard cap applies at budget ceiling and 16 weeks.
- A proposal that is flagged but not ineligible is excluded from the ranked list until a human clears it.
