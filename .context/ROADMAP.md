# Roadmap: remaining phases and owner inputs

Plain-language order of the remaining work, and exactly where the owner (you) is needed. The full
acceptance criteria for each phase are in `implementation.md`; status is ticked in `PROGRESS.md`.

**Legend:** **You** = the phase needs something from you before or during it. *No input* = I can do it alone.

## Phase sequence

| # | Phase | In simple words | Your input |
|---|---|---|---|
| 0 | Repository setup | Organised folder, docs, git | Done |
| 1 | Scaffold | Empty website and empty server that start | Done |
| 2 | Database connection | Server connects to MongoDB; health check | **You:** install and start MongoDB ([A](#a-install-and-start-mongodb-before-phase-2)) |
| 3 | Rules and categories | The fixed lists: categories, priorities, statuses | *No input* |
| 4 | Tickets in the database | Create, edit, search and delete tickets; IDs like `SK-1001` | *No input* |
| 5 | App frame | Sidebar, pages, light and dark theme | *No input* |
| 6 | Ticket screens | Ticket list, new-ticket form, ticket detail page | *No input* |
| 7 | CSV import and export | Load tickets from a spreadsheet file; download data | *No input* |
| 8 | Fake AI (mock mode) | Pretend AIs, so everything can be built and tested for free | *No input* |
| 9 | Real Jev | Connect to TypeSafe Jev | **You:** Jev API key and credits ([B](#b-add-api-keys-before-phases-9-and-10)) |
| 10 | Real GPT | Connect to OpenAI GPT | **You:** OpenAI API key and model choice ([B](#b-add-api-keys-before-phases-9-and-10), [C](#c-choose-the-gpt-model-and-prices-before-phase-10)) |
| 11 | Run history and cost | Log every AI call with tokens and cost | *No input* |
| 12 | Side-by-side comparison | Run both AIs and show where they agree | *No input* |
| 13 | Bulk runs | Run many tickets at once, with a progress bar | **You:** approve paid bulk runs ([D](#d-approve-spending-on-real-ai-calls)) |
| 14 | Sample data and scores | Fix the 100 sample tickets; accuracy dashboard | **You:** review fixed dataset, approve evaluation spend ([D](#d-approve-spending-on-real-ai-calls), [E](#e-review-the-corrected-sample-dataset-phase-14)) |
| 15 | Settings page | Change model, prompts, categories, prices in the app | *No input* |
| 16 | Testing and security check | Full test pass, failure cases, secret checks | *No input* (optional: live tests cost money, see [D](#d-approve-spending-on-real-ai-calls)) |
| 17 | Final docs | README a newcomer can follow end to end | **You:** follow it once on your Mac to confirm ([F](#f-try-the-setup-guide-phase-17)) |
| 18 | Deployment readiness | Prepare for hosting, without hosting it | **You:** only if you want it online later ([G](#g-deployment-decisions-only-before-going-online)) |

Phases 3 to 8 need nothing from you and can run back to back once MongoDB is running.
Phases 9 and 10 can be built and tested in mock mode before keys arrive; only real calls wait.

## Owner input plans

### A. Install and start MongoDB (before Phase 2)

Why: the app stores everything in a local MongoDB database. Project rules say you install it, not the agent.

1. Open MongoDB's official macOS guide and check the current version:
   https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/
2. In Terminal, the guide's Homebrew steps are currently:
   ```bash
   brew tap mongodb/brew
   brew install mongodb-community
   brew services start mongodb-community
   ```
3. Check it is running: `mongosh --eval 'db.runCommand({ ping: 1 })'` should print `ok: 1`.
4. Keep it local: do not change its network settings to allow other machines. The default (`127.0.0.1` only) is correct.
5. Tell me "MongoDB is running". I will confirm the connection from the app.

Done when: the ping prints `ok: 1`.

### B. Add API keys (before Phases 9 and 10)

Why: real Jev and GPT calls need your accounts. Keys stay on your Mac only.

1. Create accounts if needed: TypeSafe (https://typesafe.ai) and OpenAI (https://platform.openai.com).
2. Create one API key in each. For OpenAI, add a monthly spending limit in its billing settings.
3. For TypeSafe, add credits; an empty balance makes Jev calls fail with "insufficient credits".
4. Copy the template: `cp backend/.env.example backend/.env`.
5. Open `backend/.env` in your editor and paste the keys after `TYPESAFE_API_KEY=` and `OPENAI_API_KEY=`.
6. **Never paste a key into the chat**, a commit or any other file. `backend/.env` is ignored by git, and I am blocked from reading it.
7. Tell me "keys are in place". I will check only that the app sees them as configured, never their values.

Done when: the app's provider status shows both as "Configured".

### C. Choose the GPT model and prices (before Phase 10)

Why: `OPENAI_MODEL` has no default, and prices differ per model and change over time.

1. Pick the OpenAI model to compare against Jev. I can list current options and their prices from OpenAI's official pages when we get there.
2. Set it in `backend/.env` after `OPENAI_MODEL=`.
3. Confirm the input and output price per million tokens for that model, and Jev's current price
   (currently documented as $0.042 per million input tokens, output free). These go into the app's settings, not code.

Done when: the model name is set and both price entries are confirmed.

### D. Approve spending on real AI calls

Why: each real call costs money. Nothing paid runs without your go-ahead.

- Before the first real call, and before any bulk run or evaluation, I will state how many calls it makes and an estimated cost.
- You reply with a yes, or a limit (for example "10 tickets only").
- Default tests never call paid APIs; live tests run only when you ask.

### E. Review the corrected sample dataset (Phase 14)

Why: in the supplied 100 tickets, every title gives away the answer, and there is no Hindi in Devanagari script. Results would be misleading.

1. I create a corrected copy with realistic titles and real Hindi tickets, keeping the same labels and 100 rows.
2. You skim it (I will point to 10 sample rows to check) and say whether it looks realistic.
3. Only then is it used for a paid evaluation run (see D).

### F. Try the setup guide (Phase 17)

Why: proves a newcomer can set the app up from the README alone.

1. Follow the final README on your Mac from the top.
2. Tell me any step that was unclear or failed.

### G. Deployment decisions (only before going online)

Why: the app has no login, so it must not be put online as it is. Phase 18 only prepares; it does not deploy.

Decide these only if and when you want it hosted (details in `DEPLOYMENT_DECISIONS.md`):
hosting platform, production database, login/access control, domain and HTTPS, backups and monitoring, monthly budget.

## Open items from earlier

- **Scope:** "phase 120" was read as Phases 0 to 1. Confirm whether to continue phase by phase with check-ins (default) or straight through.
- **Repository visibility:** the GitHub repository is currently public. Make it private in GitHub settings if that was the intent.
- **Pushing:** you push to GitHub yourself, unless you remove the two `deny` lines (`git push`, `git remote add`) from `.claude/settings.json`.
- **npm cache (small fix):** `~/.npm` has root-owned files, which can make `npm install` fail. Fix once with `sudo chown -R $(whoami) ~/.npm`.
