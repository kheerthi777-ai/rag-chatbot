# PRD — HDFC Mutual Fund Facts Assistant (prototype)

**Status:** Draft for review. Stop here before build.  
**Date:** 27 Sep 2026  
**Product:** Facts-only RAG chatbot over five HDFC Direct–Growth schemes  
**Audience for this doc:** You, building the prototype

---

## 1. Problem

Retail investors and support teams hunt the same scheme facts (expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, how to download a statement) across long public pages. They either miss the fact, mix up two schemes, or get an opinion when they asked for a number.

**One sentence:** People who need a single verifiable fact about an HDFC scheme cannot get it in one place with a source link, without investment advice attached.

| | |
|---|---|
| **Who feels it** | Primary: retail user comparing or checking one HDFC scheme. Secondary: support or content person answering the same factual questions repeatedly. |
| **When** | While reading a scheme page, filling a SIP form, or answering “what is the lock-in / exit load / min SIP?” |
| **How often** | Repeated per scheme lookup; the same five fact types dominate. |
| **Workaround today** | Scroll Groww (or AMC) pages, search inside a PDF factsheet, or ask a person who may answer with an opinion. |
| **Why this prototype** | A graded milestone: prove retrieval-augmented answers that stay factual, cited, and short. |
| **Outcome this prototype must prove** | A stranger can ask a fact, get ≤3 sentences, see one source link, and get a polite refusal on “should I buy?” |

**Anti-user:** Anyone seeking a buy/sell/hold call, return comparison, portfolio allocation, or account-specific documents (PAN, statements tied to an identity).

### Open questions

| Question | Type | Default if you do not override |
|---|---|---|
| Are Groww pages acceptable as the corpus? The brief names AMC/SEBI/AMFI pages and also pastes these five Groww URLs. Groww is a distributor, not the AMC. | Blocker for “official source” purity | **Use the five Groww URLs as the only corpus** for the prototype. Cite those URLs. Do not add blogs. |
| Which LLM generates the answer? | Assumption | Local or free chat model behind a single `generate()` function. Swap the model without changing retrieval. |
| Where does the app run? | Assumption | Local web app (FastAPI or Streamlit). Hosted link is a deliverable only if easy; otherwise a ≤3-min demo video. |

---

## 2. Users, job, metrics

**Primary JTBD:** When I am looking at an HDFC scheme and need one fact, I want a short answer with the page it came from, so I can trust the number without taking advice.

**Secondary JTBD:** When a user asks the same fee or process question again, I want the assistant to answer from the corpus, so I do not re-read five pages.

### North-star (prototype)

**Cited-fact accuracy:** share of the sample Q&A (8–10 queries) where the answer is factually correct, ≤3 sentences, has exactly one working source link, and refuses advice when the question is opinionated.

Target: **8/10 pass** on a written sample before you call the prototype done.

### Supporting metrics

| Metric | Target for prototype |
|---|---|
| Time to first useful answer | Under 15 seconds on a local machine after the index exists |
| Citation coverage | 100% of factual answers include one corpus URL |
| Refusal correctness | 100% of buy/sell/portfolio questions refused; no return math |
| PII refusal | 100% of PAN / Aadhaar / account / OTP / email / phone inputs rejected and not stored |
| Answer length | ≤3 sentences on factual replies |

### Non-goals

- Investment advice, suitability, or “best scheme.”
- Computing, ranking, or comparing returns, NAV history, or alpha.
- Logging in, fetching a user’s statement, or storing identity.
- Covering AMCs other than HDFC, or schemes outside the five URLs.
- Production scale, auth, or multi-user history.

---

## 3. Journey and pains

```
Land → see disclaimer + examples → ask a fact
  → wait → read answer + one link → (optional) ask another
  → if advice / PII / no source → see refusal or “not in sources”
```

| Step | User intent | Pain | Severity | MVP? |
|---|---|---|---|---|
| Land | Know this is safe to ask | Advice bots hide the disclaimer | H | Yes — welcome line, three examples, “Facts-only. No investment advice.” |
| Ask | Type or tap a known fact | Blank box, no idea what is in scope | H | Yes — example chips fill the box |
| Wait | Trust it is working | Silent spinner feels hung | M | Yes — “Searching scheme pages…” |
| Read | Check the number and the source | Answer without a link, or a link to a blog | H | Yes — one corpus link, ≤3 sentences, “Last updated from sources: {date}” |
| Advice ask | “Should I buy HDFC Small Cap?” | Model gives a recommendation | H | Yes — fixed refusal + one educational corpus link |
| Returns ask | “Which fund performed better?” | Model computes or ranks returns | H | Yes — refuse the comparison; point to the factsheet URL |
| PII | Paste PAN to “download my statement” | Data stored in chat logs | H | Yes — detect and refuse; do not write the value to logs or the vector store |
| Missing fact | Ask something not on the five pages | Hallucinated number | H | Yes — “I can’t find this in the indexed pages.” No invented figure |
| Error | Index missing or page failed to load | Generic crash | M | Yes — say which stage failed (load / retrieve / generate) |

---

## 4. What to build (impact × effort)

| Bet | Impact | Effort | Call |
|---|---|---|---|
| Ingest the 5 URLs with source metadata | H | L | MVP |
| Chunk so a fact stays tied to its scheme | H | L | MVP |
| Embed with `all-MiniLM-L6-v2`, store in Chroma | H | L | MVP |
| Retrieve top passages and answer with one citation | H | L | MVP |
| Refusal for advice, returns math, and PII | H | L | MVP |
| Tiny single-screen UI | H | L | MVP |
| Sample Q&A file + source list + README + disclaimer | H | L | MVP (submission) |
| Scheme detector to filter Chroma by fund name | H | M | MVP if cheap; otherwise retrieve across all five and let the prompt name the scheme |
| Semantic chunking model | L | H | Out — pages are short and labeled |
| Multi-AMC, user accounts, statement download | L | H | Out |
| Live NAV or returns calculator | — | — | Out (forbidden) |

**MVP is the high-impact, low-effort loop:** ask a fact → cited answer, or a clean refusal.

---

## 5. Pre-mortem

Assume the demo fails review. Causes and what the prototype does about them:

| Failure | Leading sign | Mitigation |
|---|---|---|
| Hallucinated expense ratio | Sample Q&A disagrees with the page | Answer only from retrieved chunks. If retrieval score is weak, say the fact was not found. |
| Advice leaks through | “Should I invest?” gets a yes | System prompt + a refusal path that does not call free-form generation for advice intent. |
| Returns get compared | Two schemes ranked by 1Y/3Y | Detect comparison/returns intent; link the factsheet; do not calculate. |
| Wrong scheme’s fact | Large Cap expense ratio quoted for ELSS | Chunk metadata: `scheme_id`, `scheme_name`, `source_url`. Prefer chunks whose scheme matches the question. |
| Citation is missing or off-corpus | Link empty or not one of the five | Post-check: factual answers must contain exactly one of the indexed URLs. |
| PII lands in Chroma or logs | PAN visible in a stored question | Reject before embed and before log. Never index user text. |
| Groww blocks scraping | Loader returns empty HTML | Save fetched text once under `data/raw/`. README says re-fetch may fail and the snapshot is the corpus. |
| Stale facts | Expense ratio changed on the site | Stamp `Last updated from sources: YYYY-MM-DD` from the ingest date. Do not pretend it is live. |
| Chunk splits “0.98%” from the label | Answer says the ratio without the label | Section-aware recursive chunks (decision below), overlap, and scheme name repeated in each chunk header. |

No fatal risk is unmitigated for a local prototype. The accepted risk is **distributor data, not the AMC PDF**: numbers can differ from the SID. The UI says answers come from the indexed public pages, dated.

---

## 6. MVP definition

### In

| Item | Job | Kill criterion |
|---|---|---|
| Five-URL corpus | Bound what “truth” is | Drop a URL that returns no extractable text; do not replace it with a blog |
| Ingest pipeline | Load → chunk → embed → Chroma | If you cannot re-run ingest from a clean folder, the pipeline is not done |
| Facts-only answers | Expense ratio, exit load, min SIP, lock-in, riskometer, benchmark, statement how-to | Any sample answer over 3 sentences or without a corpus link fails |
| Refusals | Advice, portfolio, return math, PII | Any refusal that still recommends a scheme fails |
| Tiny UI | Welcome, 3 examples, disclaimer, question, answer, citation | If the disclaimer is easy to miss, it fails |
| Submission pack | Source list, README, sample Q&A, disclaimer text | Missing any deliverable in §11 fails the milestone |

### Out

- Buy/sell/hold, asset allocation, “which is better.”
- Return, CAGR, or NAV calculations and comparisons.
- Accepting or storing PAN, Aadhaar, account numbers, OTP, email, phone.
- Third-party blogs, screenshots of a broker back-end, or pages outside the five URLs.
- Chat history as a product feature, accounts, payments, notifications.
- Extra schemes or AMCs.

### Later (after the prototype is accepted)

- Swap Groww HTML for HDFC AMC factsheet / KIM / SID PDFs, same metadata schema.
- Stronger scheme filter and evaluation set (20+ questions).
- Hosted URL.

---

## 7. Corpus (locked)

AMC: **HDFC**. Plans: **Direct–Growth** only.

| Scheme | Category | URL |
|---|---|---|
| HDFC Large Cap Fund | Large Cap | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| HDFC Flexi Cap Fund (listed as HDFC Equity Fund) | Flexi Cap | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| HDFC ELSS Tax Saver Fund | ELSS | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| HDFC Small Cap Fund | Small Cap | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| HDFC Balanced Advantage Fund | Hybrid | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

Source list file for submission: `docs/sources.md` (or CSV) with these five rows: scheme, category, url, date fetched.

---

## 8. RAG architecture

Two stages, always in this order. Do not embed inside the chat request path except for the user query.

```
INGEST (offline, re-runnable)
  Load 5 pages → clean text → chunk → embed → upsert Chroma

QUERY (online)
  Classify intent → (if blocked: refuse)
  Embed question → retrieve → generate from passages only
  → attach one URL + “Last updated from sources”
```

### 8.1 Loading

- HTTP fetch of the five URLs, or read the saved snapshot in `data/raw/{scheme_id}.txt` (or `.md`).
- Strip nav, footer, scripts, and “similar funds” carousels when possible.
- Keep section headings (Expense ratio, Exit load, Minimum SIP, Lock-in, Risk, Benchmark, Tax, Statement).
- Persist `source_url`, `scheme_id`, `scheme_name`, `category`, `fetched_at` on every document.
- User messages are never loaded into the corpus.

### 8.2 Chunking (decision)

**Use recursive, section-aware splitting. Do not use semantic chunking for this prototype.**

Why, given this data:

- Each page is a **short fact sheet**: labeled fields and short paragraphs, not a long narrative.
- The failure mode that matters is a **number separated from its label and scheme** (“1%” with no “exit load” / “ELSS”).
- Semantic chunking spends an embedding pass to find topic breaks the headings already mark, and it can still cut a label from its value.
- Recursive splitting on headings is deterministic, free to re-run, and easy to inspect.

Rules:

| Parameter | Value |
|---|---|
| Split order | `\n## `, `\n# `, `\n\n`, `\n`, `. `, ` ` |
| Target size | 500 characters (~120–180 tokens for this model) |
| Overlap | 80 characters |
| Header prepended to every chunk | `# {scheme_name} ({category})\nSource: {url}\n` |
| Metadata on each chunk | `scheme_id`, `scheme_name`, `category`, `source_url`, `fetched_at`, `section` if a heading was seen |
| Do not chunk | Empty extracts, cookie banners, legal footer repeated on every page (drop boilerplate once it is identified) |

If a section is under ~500 characters, keep it as one chunk. If “Exit load” text is a single sentence, that sentence plus the scheme header is the chunk.

### 8.3 Embedding

- Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Same model for documents and queries.
- Normalize embeddings if the Chroma space is cosine.
- Batch embed at ingest time. At query time, embed only the question.

### 8.4 Vector store

- **ChromaDB**, persistent directory `data/chroma/`.
- One collection, e.g. `hdfc_schemes`.
- Upsert ids stable from `scheme_id + section + chunk_index` so re-ingest replaces rows instead of duplicating them.
- Query: top **4** chunks. If the question names a scheme (or ELSS / small cap / large cap / flexi / balanced advantage), filter metadata to that `scheme_id` first; if the filter returns nothing, retry unfiltered once, then prefer “not found” over a cross-scheme guess.
- “How do I download a capital-gains statement?” may be general. Retrieve across schemes and answer only if a chunk actually describes the steps; otherwise say it is not in the indexed pages and do not invent a menu path.

### 8.5 Generation

- Context = the retrieved chunks only, each labeled with scheme name and URL.
- Instructions baked into the prompt:
  - Facts from context only. If the fact is absent, say so.
  - At most 3 sentences.
  - Exactly one URL, copied from the chunk metadata, not invented.
  - End factual answers with `Last updated from sources: {fetched_at}`.
  - No performance numbers, no comparisons, no “you should.”
- Intent gate **before** generation:
  - **Advice / portfolio / “should I”** → canned refusal (below). Do not let the model improvise a recommendation.
  - **Returns comparison or “calculate my return”** → canned refusal plus the relevant scheme URL if one scheme is named, else the Large Cap URL as a neutral factsheet entry.
  - **PII pattern** (PAN shape, Aadhaar 12 digits, account-number-like strings, OTP, email, phone) → canned refusal. Do not log the raw message; log only `pii_blocked`.

### 8.6 Suggested layout (when you build)

```
app/            UI + /ask
ingest/         load, chunk, embed, chroma upsert
prompts/        system + refusals
data/raw/       fetched page text
data/chroma/    persistent index
docs/sources.md
docs/sample-qa.md
README.md
```

Module boundary: ingest never imports the UI. The UI never writes to the corpus.

---

## 9. Behavior spec

### Factual answer

- ≤3 sentences.
- States the scheme name in the answer.
- One markdown or plain link to the chunk’s `source_url`.
- Last line: `Last updated from sources: YYYY-MM-DD`.
- No adjectives that imply quality (“attractive”, “low cost”, “good for you”).

### Refusal copy (advice)

> I can only share facts from the indexed scheme pages, not whether to buy, sell, or hold. For the published scheme details, see {url}.

### Refusal copy (returns)

> I don’t calculate or compare returns. The latest published figures are on the scheme page: {url}.

### Refusal copy (PII)

> Don’t send PAN, Aadhaar, account numbers, OTPs, email, or phone numbers. I can’t look up your account. Ask a general question such as how capital-gains statements are downloaded.

### Not found

> I can’t find that in the five indexed HDFC scheme pages. I won’t guess a figure.

### Disclaimer (UI, exact snippet to reuse in the README)

> Facts-only. No investment advice. Answers come from the indexed public pages and can be outdated. This is not a recommendation to buy or sell any scheme.

---

## 10. Tiny UI (low-fi)

One screen. Desktop or a single phone-width column. No navigation.

```
┌─────────────────────────────────────────────┐
│ HDFC scheme facts                           │
│ Facts-only. No investment advice.           │
│                                             │
│ Ask a fact about these Direct–Growth funds: │
│ Large Cap · Flexi Cap · ELSS · Small Cap ·  │
│ Balanced Advantage                          │
│                                             │
│ [ Expense ratio of HDFC Large Cap? ]        │
│ [ What is the ELSS lock-in? ]               │
│ [ Minimum SIP for HDFC Small Cap? ]         │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Ask a factual question…                 │ │
│ └─────────────────────────────────────────┘ │
│                              [ Ask ]        │
│                                             │
│ Answer                                      │
│ …three sentences…                           │
│ Source: https://groww.in/…                  │
│ Last updated from sources: 2026-09-27       │
└─────────────────────────────────────────────┘
```

| State | What the user sees |
|---|---|
| Empty | Welcome, disclaimer, three chips, empty answer area |
| Loading | Ask disabled, “Searching scheme pages…” |
| Success | Answer + one link + last-updated line |
| Refusal | Refusal copy + one educational link; input cleared of any PII |
| Not found | Not-found copy; no fake link |
| Error | “The index isn’t available. Run ingest, then try again.” or “The answer service failed. Your question was not saved.” |

**Primary action:** Ask.  
**Secondary:** the three example chips (they only fill and send the same Ask path).

Example questions (locked for the prototype):

1. What is the expense ratio of HDFC Large Cap Fund Direct Growth?
2. What is the lock-in period for HDFC ELSS Tax Saver?
3. What is the minimum SIP for HDFC Small Cap Fund?

**Analytics (local log only, no PII):** `ask_submitted`, `answer_cited`, `refused_advice`, `refused_returns`, `refused_pii`, `not_found`, `error`. Store a hash or a redacted question, never the raw text if a PII check fired.

### Feature cards

**Cited answer**  
Job: return one scheme fact with its page.  
Conversion role: trust.  
Happy path: chip or typed fact → 4 chunks → ≤3 sentences + URL.  
Failure: number from the wrong scheme or no link.  
Harm: user acts on a wrong fee or lock-in.  
Effort L / Impact H. MVP: yes.  
Kill: sample set has any factual answer with a wrong figure or a missing corpus URL.

**Advice refusal**  
Job: stop recommendations.  
Conversion role: trust.  
Happy path: “Should I buy?” → canned copy + link.  
Failure: model adds “but it suits long-term investors.”  
Harm: user treats the bot as an advisor.  
Effort L / Impact H. MVP: yes.  
Kill: one advice answer that recommends a scheme.

**PII block**  
Job: keep identity out of logs and the index.  
Conversion role: trust.  
Happy path: message with a PAN → refusal, nothing persisted.  
Failure: raw PAN in `data/` or server logs.  
Harm: privacy breach on a demo machine.  
Effort L / Impact H. MVP: yes.  
Kill: any persisted user identifier.

---

## 11. Submission deliverables

| Deliverable | Where |
|---|---|
| Working prototype or ≤3-min demo | Local app; video only if you cannot host |
| Source list of the 5 URLs | `docs/sources.md` |
| README: setup, AMC + schemes, known limits | `README.md` |
| 8–10 sample Q&As with answers and links | `docs/sample-qa.md` |
| Disclaimer snippet | In the UI and copied in the README |

Sample set must include at least: expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer or benchmark, statement download, one advice refusal, one returns refusal, one missing-fact case.

### Known limits (README must say these)

- Corpus is five Groww pages, not the AMC SID/KIM PDFs.
- Facts are as of the ingest date, not a live quote.
- No account access, so “download my statement” is generic process only, if the page contains it.
- English only.
- Not SEBI-registered advice; the product refuses advice on purpose.

---

## 12. Roadmap

| Phase | Outcome | When | Owner | Checkpoint |
|---|---|---|---|---|
| Discover | This PRD agreed (corpus, chunking, in/out) | 27 Sep 2026 | You | Accept, or change the five URLs / UI copy |
| MVP | Ingest runs; UI answers and refuses; sample Q&A ≥8/10 | Week of 28 Sep 2026 | You + build agent | Sample file reviewed against the live pages |
| Prove | A second person asks 5 questions without coaching | Same week if MVP passes | You | They find the disclaimer and a citation without help |
| Harden | Re-ingest is idempotent; PII test; empty-index error | Only after Prove | You | Re-run ingest twice, no duplicate facts |
| Scale | Not in this project | — | — | Do not add AMCs until the sample set stays green |

---

## 13. How you will know the prototype works

1. `ingest` on a clean machine fills Chroma from the five pages (or the saved snapshots).
2. Each example chip returns a scheme-correct fact, one Groww link, and the last-updated line.
3. “Should I buy HDFC Small Cap?” returns the advice refusal and no recommendation.
4. “Which of these has the highest 3-year return?” returns the returns refusal and no ranking.
5. A fake PAN in the box returns the PII refusal and does not appear in `data/`.
6. A nonsense fact (“What is the expense ratio of HDFC Nifty 200 Momentum?”) returns not-found.
7. `docs/sample-qa.md` records 8–10 of these with the actual answers.

---

## 14. Gate — please confirm before any build

Recommended defaults, already written into this PRD:

1. Corpus = the five Groww URLs above, cited as such.
2. Chunking = recursive, section-aware, 500 characters, 80 overlap, scheme header on every chunk.
3. Stack = Hugging Face `all-MiniLM-L6-v2` + ChromaDB persistent.
4. UI = one screen, three example questions, disclaimer always visible.
5. LLM = pluggable; refusals for advice, returns, and PII are canned, not free-form.

Reply with changes, or say **go** and the next step is the ingest pipeline and this screen — not more schemes, and not a visual redesign.
