import { readFileSync } from "node:fs"

import { expect, type Page, test } from "@playwright/test"

const API = "http://127.0.0.1:8001"

async function createTicket(page: Page, title: string): Promise<string> {
  const response = await page.request.post(`${API}/api/tickets`, {
    data: {
      title,
      description: `Synthetic test ticket: ${title}.`,
      customer_name: "Test Customer",
      customer_email: "test.customer@example.test",
      submission_channel: "Email",
    },
  })
  expect(response.ok()).toBeTruthy()
  return (await response.json()).ticket_id
}

test("full journey: create, classify, compare, choose final, export, delete", async ({
  page,
}) => {
  const title = `Refund still missing ${Date.now()}`
  const ticketId = await createTicket(page, title)

  await page.goto(`/compare?ticket=${ticketId}`)
  await page.getByRole("button", { name: "Run Jev + LLM" }).click()
  await expect(page.getByText(/Agree on \d of 5 fields/)).toBeVisible({
    timeout: 30_000,
  })
  await expect(page.getByText("Agree", { exact: true }).first()).toBeVisible()

  await page.getByRole("link", { name: ticketId }).click()
  await expect(page).toHaveURL(`/tickets/${ticketId}`)
  await expect(page.getByText("Not chosen yet")).toBeVisible()
  await page.getByRole("button", { name: /Use Jev's answer/ }).click()
  await page.getByRole("button", { name: "Save final classification" }).click()
  await expect(page.getByText("AI answer, unchanged")).toBeVisible()

  await page.goto("/tickets")
  const download = page.waitForEvent("download")
  await page.getByRole("link", { name: "Tickets CSV" }).click()
  const csv = readFileSync(await (await download).path(), "utf-8")
  expect(csv).toContain(ticketId)
  expect(csv.toLowerCase()).not.toContain("api_key")

  await page.goto(`/tickets/${ticketId}`)
  await page.getByRole("button", { name: "Delete" }).click()
  await page.getByRole("button", { name: "Delete ticket" }).click()
  await expect(page).toHaveURL("/tickets")
  await page.goto(`/tickets/${ticketId}`)
  await expect(page.getByText(`Ticket ${ticketId} not found`)).toBeVisible()
})

test("a failing side does not erase the other side's result", async ({ page }) => {
  const ticketId = await createTicket(page, `[mock-fail] Broken ${Date.now()}`)
  await page.request.post(`${API}/api/tickets/${ticketId}/runs/gpt`)

  await page.goto(`/tickets/${ticketId}`)

  await expect(page.getByText(/LLM · .* · Failed/)).toBeVisible()
  await expect(page.getByRole("button", { name: /Use LLM's answer/ })).toHaveCount(0)
})

test("the form refuses invalid input and explains why", async ({ page }) => {
  await page.goto("/tickets/new")
  await page.getByRole("button", { name: "Create ticket" }).click()

  await expect(page).toHaveURL("/tickets/new")
  await expect(page.getByText("Enter a title")).toBeVisible()
  await expect(page.getByLabel("Title", { exact: true })).toHaveAttribute("aria-invalid", "true")
})

test("filters narrow the list, live in the URL and can be cleared", async ({ page }) => {
  const word = `zebra${Date.now()}`
  const ticketId = await createTicket(page, `Parcel ${word}`)

  await page.goto("/tickets")
  await page.getByRole("searchbox", { name: "Search tickets" }).last().fill(word)
  await page.getByRole("searchbox", { name: "Search tickets" }).last().press("Enter")
  await expect(page).toHaveURL(new RegExp(`q=${word}`))
  await expect(page.locator("tbody tr")).toHaveCount(1)
  await expect(page.getByRole("link", { name: ticketId })).toBeVisible()

  await page.goto(`/tickets?q=nothing-matches-${word}`)
  await expect(page.getByText("No tickets match these filters")).toBeVisible()
  await page.getByRole("button", { name: "Clear filters" }).click()
  await expect(page.locator("tbody tr").first()).toBeVisible()
})

test("when the backend is down, pages say so and offer a retry", async ({ page }) => {
  await page.route(`${API}/api/tickets*`, (route) => route.abort())

  await page.goto("/tickets")

  await expect(page.getByRole("alert")).toContainText("Cannot reach the TicketLens backend", {
    timeout: 20_000,
  })
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible()
})

test("settings never offer an API key field", async ({ page }) => {
  await page.goto("/settings")

  await expect(page.getByText(/Prompt \(version/)).toBeVisible()
  await expect(page.getByLabel(/api key/i)).toHaveCount(0)
  await expect(page.getByText("backend/.env")).toBeVisible()
})
