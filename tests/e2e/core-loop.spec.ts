import { expect, test } from "@playwright/test";

test("real action to persisted inventory Core Loop", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Demo hunter name").fill(`e2e-hunter-${Date.now()}`);
  await page.getByRole("button", { name: "ENTER THE SYSTEM" }).click();

  await expect(page.getByRole("heading", { name: "QUEST BOARD" })).toBeVisible();
  await page.getByRole("button", { name: /Trial of Focus/ }).click();
  await page.getByRole("button", { name: "ACCEPT QUEST" }).click();
  await expect(page.getByText(/QUEST ACCEPTED/)).toBeVisible();

  await page.getByLabel("Observed value").fill("30");
  await page.getByRole("button", { name: "SUBMIT PROOF" }).click();
  await page.getByRole("button", { name: "VERIFY EVIDENCE" }).click();

  await expect(page.getByText("PASS", { exact: true })).toBeVisible();
  await expect(page.getByText(/\+132 EXP/)).toBeVisible();
  await page.getByRole("button", { name: "OPEN PERSISTED CHEST" }).click();
  await expect(page.getByText("CHEST OPENED — Focus Band persisted in inventory.")).toBeVisible();
  await expect(page.getByRole("listitem").getByText("Focus Band")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "HUNTER STATUS" })).toBeVisible();
  await expect(page.getByRole("listitem").getByText("Focus Band")).toBeVisible();
});
