# HDFC scheme facts

A small facts-only assistant for five HDFC Direct–Growth schemes. It answers from saved public pages and attaches one source link. It does not give investment advice.

## Disclaimer

Facts-only. No investment advice. Answers come from the indexed public pages and can be outdated. This is not a recommendation to buy or sell any scheme.

## Scope

AMC: HDFC. Plan: Direct–Growth.

| Scheme | Category | Page |
|---|---|---|
| HDFC Large Cap Fund | Large Cap | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| HDFC Flexi Cap Fund | Flexi Cap | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| HDFC ELSS Tax Saver Fund | ELSS | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| HDFC Small Cap Fund | Small Cap | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| HDFC Balanced Advantage Fund | Hybrid | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

The source list with fetch dates is in `Docs/sources.md`. Sample questions are in `Docs/sample-qa.md`.

## Setup

From this folder, with Python 3.11+:

```bash
python -m pip install -r requirements.txt
python -m ingest
python -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/

`python -m ingest` reads the saved pages in `data/raw/`. Add `--refresh` only when you want to download the five Groww pages again. A second ingest replaces cards for the same schemes. It does not duplicate them.

If no chat model is configured, answers are taken from the closest saved passage and shortened to three sentences. Refusals do not use a chat model.

## Known limits

- The corpus is five Groww pages, not the AMC SID or KIM PDFs.
- Facts are as of the ingest date, not a live quote.
- There is no account access. A question about downloading a personal statement is answered only if the saved page describes it. These five pages do not, so the assistant says it cannot find that.
- English only.
- This is not SEBI-registered advice. The product refuses buy, sell, and hold questions on purpose.
- Do not send PAN, Aadhaar, account numbers, OTPs, email, or phone numbers. Those questions are refused and the identifier is not stored.
