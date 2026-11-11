# e2e/demo/

## Why this folder exists

A scripted, repeatable screen-recording demo for LinkedIn and the root README: three new tickets (easy, medium, complex) are typed at a fast-typist pace into Compare, and Jev + LLM run on each. It is not a test: it runs on the **real** app (ports 8000 and 5173) with local models, and it **creates three real tickets** each time.

## Files

| File | Purpose |
|---|---|
| `record.sh` | One-command take (macOS). Records the main display with `screencapture`, runs `record-demo.mjs`, saves `~/Movies/ticketlens-demo-<time>.mov`. |
| `ticketlens-demo.gif`, `ticketlens-demo.mp4` | The published take (58 s, 1920x1080), recorded 2026-11-11 on local models and converted from the recorder's `.mov`. The GIF (12.5 MB) is embedded in the root `README.md`; the MP4 (19.9 MB) is linked from it. Replacing either adds another copy to git history, so keep takes few. |
| `record-demo.mjs` | Playwright script: opens the launcher, opens Chrome for Testing full screen, types the tickets, runs both sides, shows captions, prints each run's numbers. |

## Run it

```bash
e2e/demo/record.sh              # 58 s, 1920x1080 .mov in ~/Movies
RECORD_SECONDS=70 e2e/demo/record.sh out.mov
```

Before a take: the app must already be running (`start-ticketlens.command`), Ollama must have both models loaded (run one ticket first, or the first run is slow), and Screen Recording must be allowed for the app you run it from (System Settings, Privacy & Security). Close private windows and turn on Do Not Disturb, because the whole main display is recorded. Do not touch the mouse or keyboard during the take.

## Rules & gotchas

- `screencapture` cannot be stopped early without losing the file, so the length is fixed (`RECORD_SECONDS`, default 58). The script holds its last caption until the recording ends. If it prints `WARNING: too slow`, retake.
- Captions use only numbers read from the page (server time per side). Tokens are left out on purpose: the local Jev adapter asks in two steps and used about 60% more tokens than the LLM (about 1,000 against 620 per ticket).
- Use new ticket wording for each take. Ollama caches identical prompts, and a repeat of earlier text comes back in under a second, which would flatter Jev.
- Jev must be loaded before the take. A cold Jev took 7 to 14 s in rehearsal, slower than the LLM. Memory is tight on this Mac (models use about 17 GB), so close heavy apps.
- The launcher intro runs `open --env NO_BROWSER=1`, so your own browser never opens on screen. The script's own browser plays the part of the browser.
- Typing: about 60 ms a key on average, which is the slowest pace that fits one minute with three tickets. Slower, more natural typing needs a longer video (`RECORD_SECONDS`) and longer ticket text budgets.
- `DEMO_WINDOWED=1 DEMO_NO_LAUNCH=1 APP_URL=http://localhost:5174 node demo/record-demo.mjs` rehearses without recording, for example against the isolated stack (see `e2e/README.md`, "Other provider modes").
- Every take adds three tickets to the database it runs on.
