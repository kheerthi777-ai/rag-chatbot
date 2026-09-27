# Architecture — HDFC Mutual Fund Facts Assistant

**Source of truth for product behavior:** [PRD.md](PRD.md)  
**Date:** 27 Sep 2026  
**Scope:** Local prototype. Five HDFC Direct–Growth scheme pages. Facts-only answers with one citation.

This document locks how the system is split, how data moves, and what each stage is allowed to do. It does not add schemes, advice, or a second retrieval strategy.

---

## 1. System in one picture

Two pipelines share one embedding model and one Chroma collection. They do not share a process.

```
                    OFFLINE (you run it)
 ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
 │ 5 Groww  │──▶│  Load +  │──▶│ Recursive│──▶│ MiniLM   │──▶│ Chroma  │
 │ URLs or  │   │  clean   │   │  chunk   │   │  embed   │   │ upsert  │
 │ data/raw │   └──────────┘   └──────────┘   └──────────┘   └─────────┘
 └──────────┘                                                       │
                                                                    │ persistent
                                                                    ▼
                    ONLINE (each question)                    data/chroma/
 ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
 │  Browser │──▶│ Intent   │──▶│ Embed    │──▶│ Retrieve │──▶│ Generate│
 │  one page│   │ gate     │   │ question │   │ top 4    │   │ or refuse│
 └──────────┘   └──────────┘   └──────────┘   └──────────┘   └─────────┘
                     │                                              │
                     └──────── canned refusal (no LLM) ────────────┘
```

Ingest never imports the UI. The UI never writes documents into Chroma. User text is never embedded into the corpus.

---

## 2. Runtime

| Piece | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | `sentence-transformers` and Chroma are native here |
| Web | FastAPI + one static HTML page | Ingest stays a CLI. The page only calls `POST /ask` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | 384-d. Same model for pages and questions |
| Vector store | ChromaDB persistent at `data/chroma/` | One collection: `hdfc_schemes`. Cosine space |
| Generator | One function `generate(question, passages) -> str` | Model is swappable. Retrieval does not change when the model changes |
| Process model | Two entrypoints | `python -m ingest` and `uvicorn app.main:app` |

There is no login, no database of users, and no chat-history store. The only durable data is the page snapshots, the Chroma index, and a redacted event log.

**Generator default for the prototype:** a local or free chat model behind `generate()`. If no model is configured, factual questions return the best passage text trimmed to three sentences plus the citation. Refusals do not need the model at all.

---

## 3. Repository layout

```
ingest/
  __main__.py      # python -m ingest
  catalog.py       # the five schemes (id, name, category, url)
  load.py          # fetch or read snapshot, clean text
  chunk.py         # recursive section-aware splitter
  embed.py         # MiniLM batch encode
  store.py         # Chroma upsert
app/
  main.py          # FastAPI: GET / serves the page, POST /ask
  ask.py           # query orchestration
  intent.py        # PII, advice, returns, factual
  retrieve.py      # embed query, filter, top 4
  generate.py      # prompt + model call
  citation.py      # force exactly one corpus URL
  static/
    index.html     # the only screen
prompts/
  system.txt       # factual generation instructions
  refusals.txt     # canned advice / returns / pii / not_found
data/
  raw/             # {scheme_id}.md snapshots
  chroma/          # persistent index
  events.log       # redacted events only
Docs/
  PRD.md
  architecture.md
  sources.md       # written by ingest
  sample-qa.md     # written by you after a run
README.md
```

`ingest/` must not import `app/`. `app/` may import `ingest/catalog.py` for the scheme list and URL allow-list. `app/` must not import `ingest/load.py` or `ingest/store.py` upsert helpers.

---

## 4. Corpus catalog

Hard-coded in `ingest/catalog.py`. Ingest refuses any URL that is not in this table. The citation checker refuses any URL that is not in this table.

| scheme_id | scheme_name | category | URL |
|---|---|---|---|
| `hdfc-large-cap` | HDFC Large Cap Fund | Large Cap | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| `hdfc-flexi-cap` | HDFC Flexi Cap Fund | Flexi Cap | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| `hdfc-elss` | HDFC ELSS Tax Saver Fund | ELSS | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| `hdfc-small-cap` | HDFC Small Cap Fund | Small Cap | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| `hdfc-balanced-advantage` | HDFC Balanced Advantage Fund | Hybrid | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

All five are Direct–Growth. No other plan, scheme, or AMC enters the index.

---

## 5. Ingest pipeline

Run: `python -m ingest`

Idempotent. A second run replaces chunks for the same ids. It does not append duplicates.

```
for scheme in CATALOG:
  text = read data/raw/{scheme_id}.md if present
  else text = fetch(url) and write data/raw/{scheme_id}.md
  if text is empty: record failure, skip scheme, do not invent a substitute source
  sections = clean(text)
  chunks = split(sections)
  vectors = embed(chunks)          # batched
  upsert(collection, chunks, vectors)
write Docs/sources.md              # scheme, category, url, fetched_at
```

### 5.1 Load and clean

1. Prefer the snapshot in `data/raw/{scheme_id}.md`. Re-fetch only when the snapshot is missing, or when the command is `python -m ingest --refresh`.
2. If a live fetch returns an empty body or a block page, keep the existing snapshot if one exists. If neither exists, skip that scheme and print the URL. Do not replace it with a blog or a PDF that is not in the catalog.
3. Drop scripts, nav, footer, cookie banners, and “similar funds” blocks once those markers are known.
4. Keep headings that carry facts: Expense ratio, Exit load, Minimum SIP, Lock-in, Riskometer, Benchmark, Tax, Statement.
5. Stamp `fetched_at` as the calendar date the snapshot was written (`YYYY-MM-DD`). Later answers copy this date. They do not claim the page was read at question time.

### 5.2 Chunk

Recursive and section-aware. Not semantic.

| Rule | Value |
|---|---|
| Separators, in order | `\n## `, `\n# `, `\n\n`, `\n`, `. `, ` ` |
| Target size | 500 characters |
| Overlap | 80 characters |
| Short section | If the section is under 500 characters, one chunk |
| Prefix on every chunk | `# {scheme_name} ({category})\nSource: {url}\n` |
| Drop | Empty text and repeated legal boilerplate |

The prefix is part of the embedded text so the vector still carries the scheme when the body is only “Exit load: 1% if redeemed within 1 year.”

### 5.3 Chunk record

| Field | Role |
|---|---|
| `id` | `{scheme_id}:{section_slug}:{chunk_index}` |
| `document` | Prefix + chunk body. This is what gets embedded |
| `scheme_id` | Filter key |
| `scheme_name` | Used in the answer |
| `category` | Large Cap, Flexi Cap, ELSS, Small Cap, Hybrid |
| `source_url` | The only legal citation for this chunk |
| `fetched_at` | Index date |
| `section` | Heading text, or `body` when no heading was seen |

Ids are stable. Re-ingest upserts the same ids. Chunks that disappear because the page got shorter should be deleted for that `scheme_id` before upsert, so retired paragraphs do not stay searchable.

### 5.4 Embed and store

- Model: `sentence-transformers/all-MiniLM-L6-v2`.
- Normalize vectors.
- Chroma collection `hdfc_schemes`, metadata `hnsw:space = cosine`.
- Embed in batches at ingest. Store the vector with the chunk. Do not re-embed the corpus on a question.
- User questions are not passed to this stage.

---

## 6. Query pipeline

`POST /ask` with `{ "question": "..." }`.

Order is fixed. A later stage must not run if an earlier stage already returned.

```
1. Reject empty question
2. PII check          → if match: refuse, do not log the raw text
3. Advice check       → if match: canned refusal + one catalog URL
4. Returns check      → if match: canned refusal + one catalog URL
5. Embed the question with MiniLM
6. Resolve scheme_id  → filter, else unfiltered retry
7. Take top 4
8. If best distance is weak or passages lack the fact → not_found
9. generate() from those passages only
10. Citation check    → exactly one catalog URL that was in the retrieved set
11. Attach last-updated line from fetched_at
12. Log a redacted event
```

PII is first so a message that both contains a PAN and asks for advice never reaches the log, the embedder, or the generator.

### 6.1 Intent gate

Implemented in `app/intent.py` with patterns, not with the LLM.

| Intent | Detect | Result `kind` | Generator called? |
|---|---|---|---|
| PII | PAN shape, 12-digit Aadhaar, email, phone, OTP phrasing, long digit account strings | `refused_pii` | No |
| Advice | should I, buy, sell, hold, invest in, recommend, which is better, portfolio, allocate | `refused_advice` | No |
| Returns | CAGR, returns, 1 year, 3 year, 5 year, alpha, NAV performance, compare performance, highest return | `refused_returns` | No |
| Otherwise | — | continue to retrieve | Yes, after retrieval |

Advice is checked before returns so “should I buy the one with the best return?” still takes the advice refusal.

**URL on a refusal**

- If the question names one scheme, use that scheme’s catalog URL.
- If it names none, use the Large Cap URL (`hdfc-large-cap`) as the neutral educational link.
- PII refusal has **no** requirement to echo the user’s text. It uses the fixed copy from the PRD and does not include the blocked string.

### 6.2 Scheme filter

Match on the question text, case-insensitive, in this order:

| If the question contains | scheme_id |
|---|---|
| elss, tax saver | `hdfc-elss` |
| small cap | `hdfc-small-cap` |
| large cap | `hdfc-large-cap` |
| flexi, flexicap, equity fund | `hdfc-flexi-cap` |
| balanced advantage, balanced-advantage | `hdfc-balanced-advantage` |

“HDFC Equity Fund” is the flexi-cap page in this catalog. Do not create a sixth scheme for that name.

If two scheme ids match, do not filter. Retrieve across the collection and let the generator answer only what the passages support. If the passages disagree, prefer `not_found` over blending two schemes into one number.

### 6.3 Retrieval

| Parameter | Value |
|---|---|
| k | 4 |
| Space | cosine distance (lower is closer) |
| First query | `where scheme_id == detected` when a single scheme matched |
| Fallback | If the filter returns 0 chunks, query again with no filter |
| Weak match | If the best cosine distance is greater than `0.45`, return `not_found` |

`0.45` is a starting cutoff (similarity about 0.55). Tune it only against `Docs/sample-qa.md`. Do not lower it to force an answer.

Statement-download questions often name no scheme. They take the unfiltered path. The generator may describe steps only when a retrieved chunk contains them. Otherwise the response is `not_found`. No invented app menu.

### 6.4 Generation

Input to `generate()`:

- The question.
- Up to four passages, each with `scheme_name`, `source_url`, `section`, and `document`.
- `prompts/system.txt`, which states:
  - Use only the passages.
  - At most three sentences.
  - Name the scheme.
  - Do not invent a URL. The app attaches the citation after generation.
  - No quality words (attractive, cheap, good for you).
  - No returns, comparisons, or “you should”.
  - If the passages do not contain the fact, reply with the single token `NOT_FOUND`.

The model does not choose the citation. `app/citation.py` does.

### 6.5 Citation check

After generation:

1. If the model text is `NOT_FOUND`, or the fact is clearly absent, replace the body with the not-found copy. `source_url` is null.
2. Otherwise set `source_url` to the URL of the **highest-ranked retrieved chunk** whose `scheme_id` matches the scheme named in the answer. If none match, use the highest-ranked chunk’s URL.
3. That URL must be one of the five catalog URLs and one of the URLs in the retrieved set. If it is not, discard the answer and return `not_found`.
4. Append `Last updated from sources: {fetched_at}` using that chunk’s date.
5. If the body is longer than three sentences, truncate to three. Do not add a fourth sentence to fit the date; the date is a separate field the UI prints under the answer.

### 6.6 Response shape

```json
{
  "kind": "answer | refused_advice | refused_returns | refused_pii | not_found | error",
  "text": "string shown to the user",
  "source_url": "https://groww.in/... or null",
  "fetched_at": "YYYY-MM-DD or null",
  "scheme_id": "hdfc-elss or null"
}
```

| kind | source_url | UI |
|---|---|---|
| `answer` | one catalog URL | Answer, link, last-updated line |
| `refused_advice` | one catalog URL | Refusal copy and link |
| `refused_returns` | one catalog URL | Refusal copy and link |
| `refused_pii` | null | Refusal copy. Clear the input box |
| `not_found` | null | Not-found copy. No link |
| `error` | null | “The index isn’t available…” or “The answer service failed. Your question was not saved.” |

Copy strings are the ones in PRD §9. The UI disclaimer is always visible and is not part of this payload.

### 6.7 Errors

| Condition | HTTP | kind | User text |
|---|---|---|---|
| Chroma directory missing or collection empty | 503 | `error` | The index isn’t available. Run ingest, then try again. |
| Embedder fails to load | 503 | `error` | The index isn’t available. Run ingest, then try again. |
| Generator throws | 502 | `error` | The answer service failed. Your question was not saved. |
| Question missing or blank | 400 | `error` | Ask a factual question about one of the five schemes. |

Do not include stack traces in the response.

---

## 7. UI

One static page, `app/static/index.html`. No router, no account, no history list.

| Region | Behavior |
|---|---|
| Title | HDFC scheme facts |
| Disclaimer | Always visible: “Facts-only. No investment advice. Answers come from the indexed public pages and can be outdated. This is not a recommendation to buy or sell any scheme.” |
| Scheme line | Large Cap · Flexi Cap · ELSS · Small Cap · Balanced Advantage |
| Three chips | Submit the locked example questions through the same `POST /ask` path |
| Text box + Ask | Primary action. Disabled while a request is in flight |
| Status | “Searching scheme pages…” during the request |
| Result | Renders `text`, then the link if `source_url` is set, then the date if `fetched_at` is set |

Chips:

1. What is the expense ratio of HDFC Large Cap Fund Direct Growth?
2. What is the lock-in period for HDFC ELSS Tax Saver?
3. What is the minimum SIP for HDFC Small Cap Fund?

On `refused_pii`, clear the text box so the identifier is not left on screen.

---

## 8. Logging

Append-only file `data/events.log`. One JSON object per line.

Allowed fields: `ts`, `kind`, `scheme_id`, `question_redacted`.

- For `refused_pii`, `question_redacted` is the literal `pii_blocked`. The raw question is not written.
- For every other kind, store the question with emails, phone numbers, and long digit runs replaced by `[redacted]`.
- Never log retrieved chunk text in full if the question was blocked.
- Never log into Chroma.

Event names match the PRD: `ask_submitted`, `answer_cited`, `refused_advice`, `refused_returns`, `refused_pii`, `not_found`, `error`.

---

## 9. Component contracts

```
load(scheme) -> RawPage
  scheme_id, scheme_name, category, source_url, fetched_at, text

chunk(page) -> list[Chunk]
  id, document, scheme_id, scheme_name, category, source_url, fetched_at, section

embed_documents(texts) -> list[vector]     # ingest only
embed_query(text) -> vector                # ask only

upsert(chunks, vectors) -> None
query(vector, scheme_id | None, k=4) -> list[Hit]
  Hit = Chunk + distance

classify(question) -> Intent
  factual | advice | returns | pii
  plus optional scheme_id

generate(question, hits) -> str | NOT_FOUND

cite(answer, hits) -> AskResponse
```

`AskResponse` is the JSON in §6.6.

---

## 10. Trust boundaries

| Data | Allowed in | Forbidden in |
|---|---|---|
| The five public pages | `data/raw/`, Chroma | — |
| User question | Request body, then discarded | Chroma, `data/raw/` |
| PAN, Aadhaar, account, OTP, email, phone | Nowhere on disk | Logs, Chroma, raw snapshots, generator prompt |
| Model answer | HTTP response | Corpus |
| Blog posts, SID PDFs, other AMCs | Nowhere | Loader, Chroma, citations |

The generator sees only retrieved chunks. It does not see the open web, and it does not get a tool to fetch URLs.

---

## 11. What this architecture will not do

- Semantic chunking, a second vector store, or a reranker.
- Agents, tool calling, or browsing beyond the five snapshots.
- Return math, NAV series, or scheme ranking.
- Account lookup or statement download on behalf of a person.
- Multi-user sessions, auth, or a conversation memory that is fed back into retrieval.
- Swapping in HDFC AMC PDFs. That can reuse `RawPage` and `Chunk` later. It is not this build.

---

## 12. How to verify the architecture

These checks map to PRD §13. Run them against a freshly built index.

| Check | Expected path |
|---|---|
| `python -m ingest` twice | Same chunk ids. No duplicate facts |
| Example chip: expense ratio | `kind=answer`, Large Cap URL, ≤3 sentences, `fetched_at` set |
| Example chip: ELSS lock-in | `kind=answer`, ELSS URL |
| Example chip: Small Cap min SIP | `kind=answer`, Small Cap URL |
| “Should I buy HDFC Small Cap?” | `kind=refused_advice`, Small Cap URL, generator not called |
| “Which has the highest 3-year return?” | `kind=refused_returns`, no ranking |
| Question containing a fake PAN | `kind=refused_pii`, raw string absent from `data/` |
| “Expense ratio of HDFC Nifty 200 Momentum?” | `kind=not_found`, `source_url=null` |
| Start the app with `data/chroma/` missing | `kind=error`, index message |

A pass is 8 of 10 sample rows in `Docs/sample-qa.md` matching the live page text, each factual row carrying one of the five URLs.
