# How this gets built, in plain English

This sits beside [implementation.md](implementation.md). That file is the builder’s checklist. This one says the same thing without the code.

The product is a small facts desk for five HDFC mutual fund schemes. A person asks one question, such as “what is the lock-in?” or “what is the minimum SIP?”. They get a short answer, one link back to the page the fact came from, and a date. If they ask “should I buy this?”, the desk refuses. It does not give investment advice, it does not rank returns, and it does not take PAN numbers or phone numbers.

Work happens in order. A step is finished only when its check passes. We do not decorate the screen, add more funds, or put it on the internet while an earlier step is still open.

---

## The two jobs

Think of a library, then a front desk.

**Job 1, done once (and again only when pages change).** Collect the five public pages, tidy them, cut them into small labeled notes, and file those notes so a question can find the right one. The person asking a question never sees this job.

**Job 2, every question.** Read the question first. If it is advice, a return contest, or someone’s identity, reply with a fixed refusal and stop. Otherwise find the closest notes and answer only from those notes, with one link.

The filing cabinet is never filled with what a user typed. Questions stay in the conversation. They are not saved into the fund notes.

---

## Rules that apply the whole way

- The preparation job and the question desk stay separate. Preparing pages does not open the website. The website does not add new fund notes.
- Every factual answer carries one link, and that link must be one of the five pages we chose. The system picks the link. A chat model is not allowed to invent one.
- Advice, return comparisons, and personal details get a pre-written reply. We do not let a chat model improvise those.
- If a day runs long, we cut extras inside that step. We do not add a new feature to make the demo look bigger.
- Saved copies of the five pages are kept. The searchable filing cabinet and the private log are not shared as part of the project.

If no paid or local chat model is switched on, the desk still works. It reads the best matching note and shortens it to three sentences. The link is attached the same way either way. Refusals do not need a chat model at all.

---

## Phase 0 — Agree the boundaries

**Already done.** No product is built here.

We agreed:

- Only five HDFC schemes, Direct–Growth, from the five Groww pages already chosen.
- Notes stay short, and each note repeats the scheme name and the page link so a number is never separated from “whose expense ratio” it is.
- One simple screen, three example questions, and a line that says this is facts only, not advice.

Nothing else is in the prototype until these stay true.

---

## Phase 1 — Set the table

**What happens.** Create the empty project and write down the only five funds that are allowed. Also write the house rules the desk will read later: how to answer, and the exact refusal sentences for advice, returns, missing facts, and personal data.

**Why.** If the list of funds is not fixed first, later steps will quietly add blogs, other schemes, or made-up links.

**You know it is done when.** The project can name exactly those five funds and no others.

**Not yet.** Downloading pages, answering questions, or showing a screen.

---

## Phase 2 — Save a clean copy of each page

**What happens.** Download each of the five pages and save a tidy text copy. Menus, footers, cookie banners, and “similar funds” blocks are thrown away. What stays is the labeled facts: expense ratio, exit load, minimum SIP, lock-in, risk level, benchmark, tax notes, and how statements are downloaded if the page actually says so.

If a page is blank or the site blocks us, we print that page’s address and skip it. We do not replace it with a blog or some other website. If we already have an older clean copy, we keep that copy.

Each saved file is dated with the day it was written. Later answers use that date. They do not pretend the number was checked live at the moment of the question.

**Why.** The desk can only be as honest as these copies. A fee with no label, or a number from the wrong fund, is a wrong answer.

**You know it is done when.** There are five saved notes, each titled with the fund name, and a figure still sits next to its label (not a lonely “1%”). If a page could not be saved, its address is printed and that file is simply missing.

**Not yet.** Cutting notes into cards, or answering anyone.

---

## Phase 3 — Cut the pages into small cards

**What happens.** Each saved page is split into small cards. A short section stays as one card. A long section is split, with a little overlap so a sentence is not sliced in half. Every card starts with the fund name, the type of fund, and the page link.

**Why.** A question about ELSS lock-in should not pick up the Large Cap expense ratio just because both pages mention “HDFC”.

**You know it is done when.** Every card carries the fund name and the link, short sections are left whole, and there are only a modest number of cards per fund. Hundreds of cards means we accidentally kept menus or big tables, and we fix the cleaning before going on.

**Not yet.** The searchable filing cabinet, or a chat box.

---

## Phase 4 — File the cards so questions can find them

**What happens.** Each card is turned into a fingerprint that represents its meaning, and those fingerprints are stored in a local filing cabinet. Running the preparation a second time replaces the old cards for that fund. It does not stack duplicates.

A short source list is written: fund name, type, link, and the date the copy was saved. Funds that failed to download are left out and named in the command output.

**Why.** When someone asks about exit load, the desk needs a way to pull the exit-load card instead of reading all five pages by hand.

**You know it is done when.** The cabinet exists, the source list has the successful funds, and a second run does not create duplicate cards.

**Not yet.** The actual answers people will read. A quick private check that “exit load” finds the right card is allowed. That check is not the product.

---

## Phase 5 — Decide what kind of question this is

**What happens.** Before any search, the question is sorted:

- A fact (“what is the expense ratio of HDFC Large Cap?”) may continue.
- “Should I buy?” is advice. Stop.
- “Which fund earned more?” is a return contest. Stop.
- A question that includes something like a PAN, Aadhaar, phone, or email is personal data. Stop, and do not keep the number.

The sorter is a list of phrases, not a chat model. Advice is caught even if the same sentence also mentions returns (“should I buy the one with the best return?”).

If the question names one fund, later search looks in that fund first. “Equity fund” means the flexi-cap page in our list. If two funds are named, we do not force a single fund.

**Why.** The dangerous replies are the ones that recommend a fund, invent a ranking, or store someone’s identity. Those must be stopped before any clever answering starts.

**You know it is done when.** A fixed list of sample questions is sorted correctly, and a fake PAN is never handed onward as something to save.

**Not yet.** Searching the cabinet, or opening a web page.

---

## Phase 6 — Answer from the cards

**What happens.** One path handles a question with no screen yet:

1. If the question was refused in Phase 5, send the pre-written reply and one official link where a link is appropriate. Personal-data refusals do not repeat what the person typed.
2. Otherwise search the cabinet. If the question named one fund, search that fund first. Take the four closest cards. If none of them are actually close, say the fact is not in the pages. Do not guess.
3. Write at most three sentences from those cards only. If no chat model is configured, read the best card and shorten it. The link is chosen from the cards we just found, and only if it is one of the five official pages.
4. Put the “last updated” date on real answers. Leave it off refusals and “not found”.
5. Keep a plain log of what kind of question it was. If it contained personal data, the log says only that personal data was blocked. It does not store the number.

**Why.** This is the product’s promise: a short fact, the right fund, one real link, or a clean no.

**You know it is done when.** The sample questions behave like this, even before any webpage exists:

- Expense ratio, ELSS lock-in, and Small Cap minimum SIP each come back with the matching fund’s link.
- “Should I buy HDFC Small Cap?” is refused, with that fund’s link, and no recommendation.
- “Which has the highest 3-year return?” is refused, with no ranking.
- A fake PAN is refused and does not appear anywhere in the saved files.
- A fund we do not cover (“HDFC Nifty 200 Momentum”) gets “I can’t find that”, with no link.
- If the filing cabinet is missing, the reply says to prepare the pages first.

A factual answer names the scheme, stays within three sentences, and never says “you should”.

**Not yet.** The visual page. The answers are proven as data first.

---

## Phase 7 — The one screen, and the homework pack

**What happens.** A single page opens in the browser. It shows the title, the facts-only warning, the five fund names, three example questions, a box, and an Ask button. While it searches, the button waits and the page says “Searching scheme pages…”. The answer appears, then the link only when there is one, then the date only when there is one. If someone typed a PAN, the box is cleared.

Then we write the submission pieces: a sample of 8 to 10 questions with the real answers and links, a readme that says how to start the project and what it will not do, and a check that the source list is still right.

**Why.** This is the first time a person can use it. The warning has to be visible without hunting for it.

**You know it is done when.** You can click the three examples and see a cited fact, ask the buy question and see the refusal, and at least 8 of the 10 written samples match the saved pages.

**Not yet.** A new visual design, a phone-specific layout, or putting it on a public website. A short video is only a backup if you cannot hand someone the local page.

The demo, when this phase is ready:

1. Prepare the pages once.
2. Click the three examples. Each answer has one Groww link and a last-updated line.
3. Ask “Should I buy HDFC Small Cap?” and show the refusal.
4. The facts-only line is visible on the first screen.

---

## Phase 8 — Let someone else try it

**What happens.** Only after 8 of 10 samples are right. Give one other person the local address and one sentence: “Facts about five HDFC schemes. It will not tell you what to buy.” They ask five questions on their own. You watch whether they notice the warning and at least one link without you pointing.

Write down what they asked. If a number is wrong, fix the notes or the search and re-check the sample list. If they only dislike a phrase, leave the wording alone for now. Do not add funds.

**You know it is done when.** That person got a fact, saw the warning, and saw a source, without a tour.

---

## Phase 9 — Make it safe to run twice

**What happens.** After someone else has used it:

- Prepare the pages twice. The second time must not duplicate cards.
- Ask with a PAN. The number must not be sitting in any saved file. The log may say personal data was blocked, and nothing else.
- Hide the filing cabinet and open the page. It should say the pages need to be prepared first, not crash.
- The readme still matches what the page actually does.

**Not in this step.** New kinds of questions, extra funds, or hosting.

---

## The week

| When | What you should be able to see |
|---|---|
| Monday 28 Sep | The five funds are listed, and the five page copies exist (or a skipped address is named). |
| Tuesday 29 Sep | Cards are filed, a second filing does not duplicate them, and the source list exists. |
| Wednesday 30 Sep | Sample questions are answered correctly, still without the pretty page. |
| Thursday 1 Oct | The three example buttons work in the browser. |
| Friday 2 Oct | The readme and sample answers are done. If 8 of 10 are right, someone else tries it. |
| After that | The double-check: no duplicates, no saved PAN, a clear message when the filing cabinet is missing. |

If the pages fail to download, fix the copies before building the screen. A desk with an empty cabinet is not a demo.

---

## What this prototype will not become

More fund houses, user accounts, chat history, return calculators, “which fund is better”, or a public website. Those are out on purpose. The win is a short, sourced fact, or a polite no.
