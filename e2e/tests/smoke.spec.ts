import { expect, test } from "@playwright/test"

test("create a ticket, then find it in the list and on its detail page", async ({
  page,
}) => {
  const title = `Parcel not delivered ${Date.now()}`
  const description = "My parcel was due on Monday and it still has not arrived."

  await page.goto("/tickets/new")
  await expect(page.getByRole("button", { name: "Create ticket" })).toBeVisible()
  await expect(page).toHaveScreenshot("new-ticket-form.png")

  await page.getByLabel("Title", { exact: true }).fill(title)
  await page.getByLabel("Description").fill(description)
  await page.getByLabel("Customer name").fill("Test Customer")
  await page.getByLabel("Customer email").fill("test.customer@example.com")
  await page.getByLabel("Submission channel").click()
  await page.getByRole("option", { name: "Email" }).click()
  await page.getByRole("button", { name: "Create ticket" }).click()

  const created = page.getByRole("status").filter({ hasText: /Ticket \S+ created/ })
  await expect(created).toBeVisible()
  const ticketId = (await created.textContent())?.match(/Ticket (\S+) created/)?.[1]
  expect(ticketId).toBeTruthy()

  await page.goto("/tickets")
  await expect(page.getByRole("cell", { name: title })).toBeVisible()
  // Rows and the total depend on what earlier tests created, so only the page around them is compared.
  await expect(page).toHaveScreenshot("ticket-list.png", {
    mask: [page.locator("tbody"), page.getByText(/\d+ tickets? · page/)],
  })

  await page.getByRole("link", { name: ticketId! }).click()
  await expect(page).toHaveURL(`/tickets/${ticketId}`)
  await expect(page.getByText(description)).toBeVisible()
})
