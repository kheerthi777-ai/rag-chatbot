# HDFC scheme facts

A small facts-only assistant for five HDFC Direct–Growth schemes. It answers from saved public pages and attaches one source link. It does not give investment advice.

## Disclaimer

- **Facts-only.** No investment advice. Answers come from the indexed public pages and can be outdated. This is not a recommendation to buy or sell any scheme.
- **Not SEBI-registered advice.** The product refuses buy, sell, and hold questions on purpose.
- **No account access.** Personal statements, capital-gains downloads, and similar requests are answered only if the saved page describes them. These five pages do not cover account workflows.
- **Privacy.** Do not send PAN, Aadhaar, account numbers, OTPs, email, or phone numbers. Those questions are refused and the identifier is not stored.

## Source list

AMC: HDFC. Plan: Direct–Growth.

| Scheme | Category | URL | Fetched |
|---|---|---|---|
| HDFC Large Cap Fund | Large Cap | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth | 2026-09-27 |
| HDFC Flexi Cap Fund | Flexi Cap | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth | 2026-09-27 |
| HDFC ELSS Tax Saver Fund | ELSS | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth | 2026-09-27 |
| HDFC Small Cap Fund | Small Cap | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth | 2026-09-27 |
| HDFC Balanced Advantage Fund | Hybrid | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth | 2026-09-27 |

Canonical copy: `Docs/sources.md`.

## Sample Q&A

Representative questions against the local index (five Groww pages). Factual rows match the saved pages.

| # | Question | Kind | Answer | Link |
|---|---|---|---|---|
| 1 | What is the expense ratio of HDFC Large Cap Fund Direct Growth? | answer | The expense ratio of HDFC Large Cap Fund is 1.03%, and the base expense ratio is 0.84%. The scheme seeks to provide long-term capital appreciation/income by investing predominantly in Large-Cap companies. | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| 2 | What is the exit load of HDFC Flexi Cap Fund? | answer | The exit load of HDFC Flexi Cap Fund is 1% if redeemed within 1 year. The scheme seeks to generate capital appreciation / income from a portfolio, predominantly invested in equity & equity related instruments. | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| 3 | What is the minimum SIP for HDFC Small Cap Fund? | answer | The minimum SIP for HDFC Small Cap Fund is 100, and the minimum lump-sum investment is 100. The scheme seeks to provide long-term capital appreciation /income by investing predominantly in Small-Cap companies. | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| 4 | What is the lock-in period for HDFC ELSS Tax Saver? | answer | The lock-in period for HDFC ELSS Tax Saver Fund is 3 years. The scheme seeks to generate capital appreciation / income from a portfolio, comprising predominantly of equity & equity related instruments. | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| 5 | What is the riskometer of HDFC Balanced Advantage? | answer | The riskometer for HDFC Balanced Advantage Fund is Very High. The Scheme seeks to provide long term capital appreciation / income from a dynamic mix of equity and debt investments. | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |
| 6 | How do I download a capital-gains statement? | not_found | I can’t find that in the five indexed HDFC scheme pages. I won’t guess a figure. | — |
| 7 | Should I buy HDFC Small Cap? | refused_advice | I can only share facts from the indexed scheme pages, not whether to buy, sell, or hold. For the published scheme details, see https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth. | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| 8 | Which of these has the highest 3-year return? | refused_returns | I don’t calculate or compare returns. The latest published figures are on the scheme page: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth. | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| 9 | Expense ratio of HDFC Nifty 200 Momentum? | not_found | I can’t find that in the five indexed HDFC scheme pages. I won’t guess a figure. | — |

Canonical copy: `Docs/sample-qa.md`.

## Setup

From this folder, with Python 3.11+:

```bash
python -m pip install -r requirements.txt
python -m ingest
python -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/

## Hosting

The public copy runs on Render from `render.yaml`. The build installs dependencies and runs `python -m ingest`, which indexes the saved pages in `data/raw/`. The service listens on Render's `PORT`.

The free instance has 512 MB of RAM and sleeps when idle. The first question after a sleep takes longer because the embedding model loads then. Questions still use the same facts-only path as the local app.

`python -m ingest` reads the saved pages in `data/raw/`. Add `--refresh` only when you want to download the five Groww pages again. A second ingest replaces cards for the same schemes. It does not duplicate them.

If no chat model is configured, answers are taken from the closest saved passage and shortened to three sentences. Refusals do not use a chat model.

## Known limits

- The corpus is five Groww pages, not the AMC SID or KIM PDFs.
- Facts are as of the ingest date, not a live quote.
- English only.
