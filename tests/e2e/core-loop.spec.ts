import { expect, test } from "@playwright/test";

test("real action to persisted inventory Core Loop", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "Demo" }).click();
  await page.getByLabel("Demo hunter name").fill(`e2e-hunter-${Date.now()}`);
  await page.getByRole("button", { name: "ENTER THE SYSTEM" }).click();

  await expect(page.getByRole("heading", { name: "QUEST BOARD" })).toBeVisible();
  await page.getByRole("button", { name: /Trial of Focus/ }).click();
  await page.getByRole("button", { name: "ACCEPT QUEST" }).click();
  await expect(page.getByText(/QUEST ACCEPTED/)).toBeVisible();
  await expect(page.getByRole("button", { name: /Echoes of the Mind/ })).toBeDisabled();
  await expect(page.getByRole("heading", { name: "Trial of Focus" })).toBeVisible();

  await page.getByLabel("Observed value").fill("30");
  await page.getByLabel("Image evidence (optional)").setInputFiles({
    name: "proof.png",
    mimeType: "image/png",
    buffer: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64"),
  });
  await page.getByRole("button", { name: "SUBMIT PROOF" }).click();
  await page.getByRole("button", { name: "VERIFY EVIDENCE" }).click();

  await expect(page.getByText("PASS", { exact: true })).toBeVisible();
  await expect(page.getByText(/\+132 EXP/)).toBeVisible();
  await expect(page.getByText("32 / 255 XP")).toBeVisible();
  await expect(page.getByLabel("Level 2 progress")).toHaveAttribute("value", "32");
  await page.getByRole("button", { name: "OPEN PERSISTED CHEST" }).click();
  await expect(page.getByText("CHEST OPENED — Focus Band persisted in inventory.")).toBeVisible();
  await expect(page.getByRole("listitem").getByText("Focus Band")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "HUNTER STATUS" })).toBeVisible();
  await expect(page.getByRole("listitem").getByText("Focus Band")).toBeVisible();
});

test("completion quest accepts an explicit demo self-report", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "Demo" }).click();
  await page.getByLabel("Demo hunter name").fill(`journal-e2e-${Date.now()}`);
  await page.getByRole("button", { name: "ENTER THE SYSTEM" }).click();
  await page.getByRole("button", { name: /Echoes of the Mind/ }).click();
  await page.getByRole("button", { name: "ACCEPT QUEST" }).click();
  await page.getByLabel(/I completed the stated objective/).check();
  await page.getByRole("button", { name: "SUBMIT PROOF" }).click();
  await page.getByRole("button", { name: "VERIFY EVIDENCE" }).click();
  await expect(page.getByText("PASS", { exact: true })).toBeVisible();
  await expect(page.getByText(/QUEST CLEAR/)).toBeVisible();
});
