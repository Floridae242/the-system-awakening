import { expect, test } from "@playwright/test";

test("account auth uses HttpOnly session and enforces CSRF on logout", async ({ page, request }) => {
  const email = `browser-${Date.now()}@example.com`;
  const loginData = { email, password: `Awakening-${crypto.randomUUID()}!` };
  const registration = await request.post("/api/backend/auth/register", {
    data: { ...loginData, display_name: "Browser Hunter" },
  });
  expect(registration.ok()).toBeTruthy();

  await page.goto("/");
  await page.getByRole("tab", { name: "Account" }).click();
  await page.getByLabel("Email").fill(loginData.email);
  await page.getByLabel("Password").fill(loginData.password);
  await page.getByRole("button", { name: "SIGN IN" }).click();
  await expect(page.getByRole("heading", { name: "QUEST BOARD" })).toBeVisible();

  const cookies = await page.context().cookies();
  const session = cookies.find((cookie) => cookie.name === "awakening_session");
  expect(session?.httpOnly).toBe(true);
  expect(await page.evaluate(() => document.cookie)).not.toContain("awakening_session=");

  const csrf = cookies.find((cookie) => cookie.name === "awakening_csrf")?.value;
  const rejected = await page.request.post("/api/backend/auth/logout");
  expect(rejected.status()).toBe(403);
  const logout = await page.request.post("/api/backend/auth/logout", {
    headers: { "X-CSRF-Token": csrf ?? "" },
  });
  expect(logout.ok()).toBeTruthy();
  expect((await page.context().cookies()).some((cookie) => cookie.name === "awakening_session")).toBe(false);
});
