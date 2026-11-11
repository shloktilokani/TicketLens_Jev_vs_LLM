// Drives the Jev vs LLM demo for a screen recording: three new tickets (easy, medium, complex) typed at a
// human pace in Compare, each followed by "Run Jev + LLM". It records nothing itself: start the macOS
// recorder (`screencapture -v`) first. See e2e/demo/README.md.
//
// Env: APP_URL (default http://localhost:5173), DEMO_NO_LAUNCH=1 (skip the Terminal launcher intro),
// DEMO_WINDOWED=1 (rehearsal: normal window instead of full screen).
import { execFile } from "node:child_process"
import { chromium } from "@playwright/test"

const APP_URL = process.env.APP_URL ?? "http://localhost:5173"
const CHROME = `${process.env.HOME}/.cache/chrome-for-testing/current/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing`
const LAUNCHER = new URL("../../start-ticketlens.command", import.meta.url).pathname

// Synthetic ShopKart tickets only. example.com is reserved for documentation, so no real inbox is hit.
const TICKETS = [
  {
    caption: "Easy ticket",
    title: "Parcel has not arrived",
    description: "My parcel was due two days ago and has not come.",
    name: "Maya Patel",
    email: "maya@example.com",
    channel: "Email",
  },
  {
    caption: "Medium ticket",
    title: "Double charge on my card",
    description: "My card was charged twice for order SK-48213. Please refund one payment.",
    name: "Dan Brooks",
    email: "dan@example.com",
    channel: "Website",
  },
  {
    // Complexity comes from three tangled issues, not from length: the whole video has to fit in a minute.
    caption: "Complex ticket",
    title: "Cracked blender, refund missing",
    description:
      "Blender arrived cracked, I am locked out of my account, and the refund never reached my bank.",
    name: "Priya Nair",
    email: "priya@example.com",
    channel: "Chat",
  },
]

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const between = (lo, hi) => lo + Math.random() * (hi - lo)

// One key at a time with a random gap, a little longer after spaces and punctuation, like a person.
async function typeLikeHuman(locator, text, [lo, hi]) {
  await locator.click()
  for (const ch of text) {
    await locator.pressSequentially(ch)
    await sleep(between(lo, hi) * (/[\s.,]/.test(ch) ? 1.8 : 1))
  }
}

async function caption(page, text) {
  await page.evaluate((t) => {
    let el = document.getElementById("demo-caption")
    if (!el) {
      el = document.createElement("div")
      el.id = "demo-caption"
      el.style.cssText =
        "position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:99999;pointer-events:none;" +
        "padding:10px 22px;border-radius:999px;background:rgba(20,20,20,.88);color:#fff;" +
        "font:600 22px system-ui,sans-serif;letter-spacing:.2px"
      document.body.appendChild(el)
    }
    el.textContent = t
    el.style.display = t ? "block" : "none"
  }, text)
}

// Numbers are read from what the page shows, never typed in.
async function readRun(page) {
  const text = await page.locator("main").innerText()
  const secs = [...text.matchAll(/server time ([\d.]+) s/g)].map((m) => Number(m[1]))
  const tokens = [...text.matchAll(/(\d+) in · (\d+) out/g)].map((m) => Number(m[1]) + Number(m[2]))
  return { jevSeconds: secs[0], llmSeconds: secs[1], jevTokens: tokens[0], llmTokens: tokens[1] }
}

const started = Date.now()
const mark = (label) => console.log(`[${((Date.now() - started) / 1000).toFixed(1)}s] ${label}`)

if (!process.env.DEMO_NO_LAUNCH) {
  // Same as double-clicking it in Finder, except it does not open the owner's own browser: that window
  // would show their personal tabs on screen. This script's browser plays the part of "the browser".
  execFile("open", ["--env", "NO_BROWSER=1", LAUNCHER])
  await sleep(4000) // let the viewer read the launcher output
  mark("launcher shown")
}

const fullScreen = !process.env.DEMO_WINDOWED
const browser = await chromium.launch({
  headless: false,
  executablePath: CHROME,
  args: fullScreen
    ? ["--start-fullscreen", "--window-position=0,0", "--window-size=1920,1080"]
    : ["--window-size=1440,900"],
})
const page = await (await browser.newContext({ viewport: null })).newPage()
await page.goto(`${APP_URL}/compare`)
await page.getByRole("button", { name: "New ticket" }).waitFor()
mark("compare page open")

const results = []
for (const t of TICKETS) {
  await caption(page, t.caption)
  await page.getByRole("button", { name: "New ticket" }).click()
  // Per-key gaps in ms: a fast typist (about 60 ms average, longer after spaces), the most that still fits one
  // minute. The name and email are typed faster, from habit.
  await typeLikeHuman(page.locator("#title"), t.title, [42, 75])
  await typeLikeHuman(page.locator("#description"), t.description, [42, 75])
  await typeLikeHuman(page.locator("#customer_name"), t.name, [28, 50])
  await typeLikeHuman(page.locator("#customer_email"), t.email, [28, 50])
  await page.locator("#submission_channel").click()
  await page.getByRole("option", { name: t.channel }).click()
  await sleep(250)
  await page.getByRole("button", { name: "Save ticket" }).click()
  await page.getByRole("button", { name: "Run Jev + LLM" }).waitFor()
  await sleep(300)
  await page.getByRole("button", { name: "Run Jev + LLM" }).click()
  await page
    .getByRole("status")
    .filter({ hasText: /Agree on|partial comparison|Neither provider/ })
    .waitFor({ timeout: 120_000 })
  const run = await readRun(page)
  results.push(run)
  mark(`${t.caption} done ${JSON.stringify(run)}`)
  await sleep(1200) // hold on the result so it can be read
}

const sum = (key) => results.reduce((a, r) => a + (r[key] ?? 0), 0)
const total = {
  jevSeconds: sum("jevSeconds"),
  llmSeconds: sum("llmSeconds"),
  jevTokens: sum("jevTokens"),
  llmTokens: sum("llmTokens"),
}
// Plain numbers, no adjectives: whatever the runs produced is what the caption says. Tokens are left out on
// purpose: the local Jev adapter asks in two steps and used MORE tokens than the LLM in rehearsal.
await caption(
  page,
  `3 tickets, server time: Jev ${total.jevSeconds.toFixed(1)} s · LLM ${total.llmSeconds.toFixed(1)} s`,
)
mark(`totals ${JSON.stringify(total)}`)
// With the recorder running (record.sh), keep the last frame on screen until the fixed-length recording
// ends, so the file does not finish on the desktop. Without it, a short hold.
const recordMs = Number(process.env.DEMO_RECORD_SECONDS ?? 0) * 1000
const elapsedMs = Date.now() - started
if (recordMs && elapsedMs > recordMs - 3000) console.log("WARNING: too slow, the closing caption may be cut. Retake.")
await sleep(recordMs ? Math.max(0, recordMs - elapsedMs) : 2500)
await browser.close()
mark("finished")
