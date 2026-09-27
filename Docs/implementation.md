# Implementation plan — HDFC Mutual Fund Facts Assistant

**Behavior:** [PRD.md](PRD.md)  
**Structure:** [architecture.md](architecture.md)  
**Date:** 27 Sep 2026  
**Ship target:** end of the week of 28 Sep 2026 — local app, sample Q&A at 8/10, README and source list in place

Build in the order below. A phase is done only when its exit check passes. Do not start UI polish, extra schemes, or a hosted deploy while an earlier exit is open.

---

## 1. Where this sits

| Product phase (PRD §12) | Implementation phases | Status |
|---|---|---|
| Discover | Phase 0 | Done — PRD and architecture exist |
| MVP | Phases 1–7 | Not started |
| Prove | Phase 8 | After MVP |
| Harden | Phase 9 | After Prove |
| Scale | — | Cut for this project |

**Now:** Phases 1–7, one phase at a time.  
**Later:** Phase 8 the same week if the sample set passes. Phase 9 only after someone else can use the page without coaching.  
**Cut:** semantic chunking, reranker, second vector store, accounts, chat history, returns math, other AMCs, AMC PDF swap, production hosting.

---

## 2. Rules for every phase

1. `ingest/` does not import `app/`. The running app does not write chunks.
2. User text never lands in `data/raw/` or Chroma. PII never lands in `data/events.log`.
3. Citations are chosen in `app/citation.py` from the five catalog URLs. The model does not invent links.
4. Advice, returns, and PII are canned refusals. They do not call `generate()`.
5. If a phase slips, drop optional work inside that phase. Do not add a new feature to “save” the demo.
6. Commit page snapshots (`data/raw/`). Do not commit `data/chroma/`, `data/events.log`, or `.env`.

**Generator, so Phase 6 is not blocked on a vendor:** implement `generate()` with two backends behind one function.

- `EXTRACT` (default): stitch the best passage into at most three sentences. No API key.
- `LLM`: used only when `LLM_BACKEND` is set. Same inputs, same citation step after it returns.

Refusals stay canned in both modes. Retrieval does not change between them.

---

## 3. Phase 0 — Lock (done)

No application code.

**Exit already met**

- Corpus is the five Groww Direct–Growth URLs in the PRD.
- Chunking is recursive, 500 characters, 80 overlap, scheme header on every chunk.
- Stack is MiniLM + persistent Chroma + FastAPI.
- One screen, three example questions, disclaimer always visible.

---

## 4. Phase 1 — Scaffold and catalog

**Goal:** a runnable Python project and the only legal list of schemes.  
**Depends on:** Phase 0.  
**Exit:** `python -c "from ingest.catalog import SCHEMES; assert len(SCHEMES)==5"` prints nothing and returns 0.

### Tasks

1. Add `requirements.txt` with pinned-enough ranges: `fastapi`, `uvicorn`, `httpx`, `beautifulsoup4`, `chromadb`, `sentence-transformers`. Add `pytest` for the checks in later phases.
2. Add empty packages `ingest/` and `app/` (`__init__.py` on both).
3. Write `ingest/catalog.py` with the five rows from architecture §4: `scheme_id`, `scheme_name`, `category`, `source_url`. Include `url_for(scheme_id)` and `is_catalog_url(url)`.
4. Add `.gitignore` for `data/chroma/`, `data/events.log`, `.env`, `__pycache__/`, `.venv/`.
5. Add `prompts/system.txt` and `prompts/refusals.txt` with the PRD §9 strings (advice, returns, PII, not-found) and the system rules from architecture §6.4. No application logic yet.
6. Add `data/raw/.gitkeep`.

### Out of this phase

Loaders, Chroma, the web page, any question answering.

---

## 5. Phase 2 — Load snapshots

**Goal:** each scheme becomes one cleaned markdown file, or an explicit skip.  
**Depends on:** Phase 1.  
**Exit:** five files `data/raw/{scheme_id}.md`, each with a title line containing the scheme name and at least one of: expense ratio, exit load, SIP, lock-in, risk, benchmark. If Groww returns an empty or blocked page, the command prints the URL and leaves that file absent. It does not fetch a substitute site.

### Tasks

1. `ingest/load.py`
   - `load(scheme) -> RawPage` as in architecture §9.
   - Read `data/raw/{scheme_id}.md` when it exists.
   - Fetch with `httpx` only when the file is missing, or when the caller passes `refresh=True`.
   - Timeout around 20 seconds. On failure, keep the old snapshot if it exists.
   - Strip scripts, nav, footer, cookie text, and similar-fund blocks when those markers show up in the HTML.
   - Keep headings for expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, tax, and statement.
   - Set `fetched_at` from the snapshot’s write date.
2. A small CLI slice is allowed here only if it helps you see the files: `python -m ingest.load` may write snapshots and stop. The full pipeline arrives in Phase 4.
3. Hand-check one file in an editor. Confirm a number still sits next to its label (for example exit load is not an orphan “1%”).

### Out of this phase

Chunking, embeddings, `/ask`.

---

## 6. Phase 3 — Chunk

**Goal:** facts stay tied to the scheme name and the source URL.  
**Depends on:** Phase 2 (at least one real snapshot; all five before you call ingest done).  
**Exit:** a pytest (or a one-off script you then delete) shows, for every snapshot:

- Every chunk’s `document` starts with `# {scheme_name} ({category})` and `Source: {url}`.
- A section shorter than 500 characters is a single chunk.
- No chunk’s body exceeds 500 characters plus the prefix.
- Overlap is 80 characters where a split happened.
- Ids match `{scheme_id}:{section_slug}:{chunk_index}`.
- Empty boilerplate is not emitted.

### Tasks

1. `ingest/chunk.py` implementing architecture §5.2 and §5.3.
2. Separators in order: `\n## `, `\n# `, `\n\n`, `\n`, `. `, ` `.
3. Tests in `tests/test_chunk.py` using a tiny fixture string, not the network. Add one test that feeds a real snapshot if the file exists.
4. Print a count of chunks per scheme. Expect a small number (tens, not thousands). If you see hundreds, the cleaner is keeping nav or a fund table; fix the cleaner before embedding.

### Out of this phase

Chroma, the LLM, the UI.

---

## 7. Phase 4 — Embed, store, full ingest

**Goal:** `python -m ingest` fills Chroma and `Docs/sources.md`. A second run does not duplicate rows.  
**Depends on:** Phase 3.  
**Exit:**

1. First run creates collection `hdfc_schemes` in `data/chroma/` with cosine space and normalized MiniLM vectors.
2. `Docs/sources.md` lists five rows: scheme, category, url, `fetched_at`.
3. Second run prints the same chunk count. Querying a scheme id returns no duplicate ids.
4. Schemes that failed to load are absent from Chroma and called out in the command output.

### Tasks

1. `ingest/embed.py`: load `sentence-transformers/all-MiniLM-L6-v2` once, `embed_documents(texts)`, L2-normalize.
2. `ingest/store.py`: get-or-create collection `hdfc_schemes` with `hnsw:space=cosine`. Before upserting a scheme, delete existing ids for that `scheme_id`. Then upsert. Metadata fields are the chunk fields except the vector.
3. `ingest/__main__.py`: the loop in architecture §5. Flags: default uses snapshots; `--refresh` refetches. Write `Docs/sources.md` from successful pages only.
4. Do not import FastAPI here.

### Out of this phase

Question answering. You may run a manual Chroma query in the shell to see that “exit load” retrieves the ELSS or Large Cap chunk. That is a sanity check, not the product.

---

## 8. Phase 5 — Intent gate

**Goal:** blocked questions never reach the embedder or the generator.  
**Depends on:** Phase 1 (catalog). Can be written in parallel with Phases 2–4, and must be finished before Phase 6.  
**Exit:** `pytest tests/test_intent.py` passes the table below. For PII cases, assert the classifier does not return the raw string to the caller as something to log.

| Question | Intent | scheme_id |
|---|---|---|
| What is the expense ratio of HDFC Large Cap Fund Direct Growth? | factual | `hdfc-large-cap` |
| What is the lock-in period for HDFC ELSS Tax Saver? | factual | `hdfc-elss` |
| What is the minimum SIP for HDFC Small Cap Fund? | factual | `hdfc-small-cap` |
| Exit load of the flexi cap fund? | factual | `hdfc-flexi-cap` |
| Benchmark of HDFC Balanced Advantage? | factual | `hdfc-balanced-advantage` |
| Should I buy HDFC Small Cap? | advice | `hdfc-small-cap` |
| Which of these has the highest 3-year return? | returns | none |
| Should I buy the one with the best return? | advice | none |
| Expense ratio of HDFC Nifty 200 Momentum? | factual | none |
| A question that includes `ABCDE1234F` | pii | — |

Advice is tested before returns. Scheme matching follows architecture §6.2, including “equity fund” → flexi cap. Two scheme names in one question → no filter.

### Tasks

1. `app/intent.py` with `classify(question) -> Intent`.
2. Patterns only. No model call.
3. `tests/test_intent.py` for the table above.

### Out of this phase

Retrieval and HTTP.

---

## 9. Phase 6 — Ask path

**Goal:** one function turns a question into the JSON in architecture §6.6, without a browser.  
**Depends on:** Phase 4 and Phase 5.  
**Exit:** a pytest or a `python -m app.ask` smoke script, against the local index, returns:

| Input | kind | source |
|---|---|---|
| Large Cap expense-ratio example | `answer` | Large Cap URL |
| ELSS lock-in example | `answer` | ELSS URL |
| Small Cap minimum SIP example | `answer` | Small Cap URL |
| Should I buy HDFC Small Cap? | `refused_advice` | Small Cap URL |
| Which has the highest 3-year return? | `refused_returns` | Large Cap URL (no scheme named) |
| Fake PAN `ABCDE1234F` in the text | `refused_pii` | null, and the string is absent from `data/` |
| Expense ratio of HDFC Nifty 200 Momentum? | `not_found` | null |
| Any call with `data/chroma/` renamed away | `error` | index message |

Factual `text` is at most three sentences, names the scheme, and does not contain “you should”. `fetched_at` is set only on `answer`.

### Tasks

1. `app/retrieve.py`: `embed_query`, top 4, scheme filter then unfiltered retry. Distance cutoff **0.45**. Do not tune this number until Phase 7 shows a real miss or a real false answer.
2. `app/generate.py`: `EXTRACT` default; `LLM` only if `LLM_BACKEND` is set. On missing fact, return `NOT_FOUND`.
3. `app/citation.py`: pick the URL from retrieved hits using architecture §6.5. Reject anything outside the catalog.
4. `app/ask.py`: the order in architecture §6. Write `data/events.log` as specified in §8. PII path logs `question_redacted: "pii_blocked"` only.
5. Wire refusal templates from `prompts/refusals.txt`.
6. Tests that do not need the network: citation picker given fake hits; PII log line. The eight-row smoke test may be marked so it skips when `data/chroma/` is missing.

### Out of this phase

HTML. Prove the JSON first.

---

## 10. Phase 7 — Screen and submission pack

**Goal:** a person can open one page, ask, and see a cited fact or a refusal. The milestone files exist.  
**Depends on:** Phase 6.  
**Exit:** PRD §13 checks 1–7 pass in the browser (or by curl for the API, plus one browser pass for the disclaimer and chips). `Docs/sample-qa.md` has 8–10 rows and at least 8 pass against the snapshot text.

### Tasks

1. `app/main.py`
   - `GET /` serves `app/static/index.html`.
   - `POST /ask` returns the JSON from `ask()`.
   - Map errors to HTTP 400 / 502 / 503 as in architecture §6.7. No stack traces in the body.
2. `app/static/index.html` matching architecture §7:
   - Title, disclaimer (always visible), scheme line, three chips, input, Ask button.
   - Loading: disable Ask, show “Searching scheme pages…”.
   - Render `text`, then the link only when `source_url` is set, then the date only when `fetched_at` is set.
   - On `refused_pii`, clear the input.
3. Run the app with `uvicorn app.main:app --reload` and click each chip. Then type the advice, returns, PAN, and unknown-scheme questions.
4. Write `Docs/sample-qa.md`: question, kind, answer text, link. Include expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer or benchmark, statement download, one advice refusal, one returns refusal, one not-found.
5. Write `README.md`: how to create a venv, install, run ingest, run the app, AMC and the five schemes, the disclaimer paragraph, and the known limits from PRD §11 (Groww not the SID, dated facts, no account access, English only, not advice).
6. Confirm `Docs/sources.md` from Phase 4 is still accurate.

### Out of this phase

Visual redesign, mobile-specific layout work beyond a single readable column, deployment, video. Record a ≤3 minute video only if you cannot hand someone the local URL.

### MVP demo (this is the sprint demo)

1. Start from a clean index: ingest once.
2. Click the three chips. Each answer has one Groww link and a last-updated line.
3. Ask “Should I buy HDFC Small Cap?” and show the refusal.
4. Show the disclaimer without scrolling it off the first screen.

**Metric:** 8/10 rows in `Docs/sample-qa.md` factually match the indexed pages, with citation coverage on every factual row and correct refusals on the three blocked rows.

---

## 11. Phase 8 — Prove

**Goal:** someone who did not build it can get a fact and can see that this is not an advisor.  
**Depends on:** Phase 7 exit.  
**When:** same week, only if 8/10 already holds.  
**Exit:** one other person, unprompted except for the local URL, asks five questions. They notice the disclaimer and at least one citation without you pointing. You fix only defects that break those two observations. You do not add schemes.

### Tasks

1. Give them the URL and the one-line description: “Facts about five HDFC schemes. It will not tell you what to buy.”
2. Write their five questions and the kinds returned at the bottom of `Docs/sample-qa.md`.
3. If they hit a wrong number, fix retrieval or the snapshot cleaner and re-run the Phase 7 table. If they only dislike wording, leave it until Harden.

---

## 12. Phase 9 — Harden

**Goal:** ingest is safe to re-run, the PII path stays clean, a missing index is understandable.  
**Depends on:** Phase 8.  
**Exit:**

1. `python -m ingest` twice: chunk count stable, no duplicate ids for one `scheme_id`.
2. A PAN question: `rg` over `data/` finds no copy of that PAN. `events.log` contains `pii_blocked` and not the PAN.
3. App started with the Chroma directory removed: the page shows “The index isn’t available. Run ingest, then try again.”
4. README limits still match behavior.

### Out of this phase

New fact types, a reranker, changing the distance cutoff without a failing sample row, hosting.

---

## 13. Week of 28 Sep 2026

| Day | Phase | Done when |
|---|---|---|
| Mon 28 | 1 and 2 | Five snapshots or an explicit skip per URL |
| Tue 29 | 3 and 4 | Second ingest does not duplicate; `Docs/sources.md` exists |
| Wed 30 | 5 and 6 | Smoke table in §9 passes without the browser |
| Thu 1 Oct | 7 | Chips work in the browser; sample file started |
| Fri 2 Oct | 7 finish, then 8 if 8/10 | README done; optional second person |
| After Prove | 9 | Re-ingest, PII grep, empty-index message |

If Tuesday’s fetch fails for several URLs, spend Wednesday repairing the cleaner and committing whatever snapshots you do have. Slide the UI, not the corpus. Answering from empty Chroma is not a demo.

---

## 14. File checklist

| File | Phase |
|---|---|
| `requirements.txt`, `.gitignore`, `ingest/catalog.py`, `prompts/*` | 1 |
| `ingest/load.py`, `data/raw/*.md` | 2 |
| `ingest/chunk.py`, `tests/test_chunk.py` | 3 |
| `ingest/embed.py`, `ingest/store.py`, `ingest/__main__.py`, `Docs/sources.md` | 4 |
| `app/intent.py`, `tests/test_intent.py` | 5 |
| `app/retrieve.py`, `app/generate.py`, `app/citation.py`, `app/ask.py` | 6 |
| `app/main.py`, `app/static/index.html`, `Docs/sample-qa.md`, `README.md` | 7 |

---

## 15. Decisions already made

| Date | Decision | Why |
|---|---|---|
| 27 Sep 2026 | Five Groww URLs are the corpus | PRD default. Cite them. Do not add blogs |
| 27 Sep 2026 | Recursive chunks, not semantic | Short labeled pages. Keep the number with the scheme |
| 27 Sep 2026 | FastAPI + one HTML file | Ingest stays a separate command |
| 27 Sep 2026 | `EXTRACT` answers if no LLM is configured | The milestone is retrieval and citation, not the model brand |
| 27 Sep 2026 | Distance cutoff 0.45 until the sample set says otherwise | Stops a weak neighbor from becoming a fact |

Change a row only by editing this file and the architecture doc together. Do not change it inside a phase to make one sample question pass.

---

## 16. Next action

Start **Phase 1** only. Stop when the catalog import check passes, then start Phase 2. Do not scaffold the UI in the same step.
