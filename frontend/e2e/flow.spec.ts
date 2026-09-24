import { expect, test } from "@playwright/test";

const email = `e2e-${Date.now()}@test.ru`;
const password = "password123";

test("onboarding → search → card → watchlist → theme", async ({ page }) => {
  // register
  await page.goto("/register");
  await page.fill("#display_name", "E2E User");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Создать аккаунт" }).click();
  await expect(page).toHaveURL(/\/welcome/, { timeout: 15_000 });

  // onboarding step 1: pick services
  await expect(page.getByText("Какие сервисы у вас уже есть?")).toBeVisible();
  await page.getByRole("button", { name: /Иви/ }).click();
  await page.getByRole("button", { name: /Okko/ }).click();
  await page.getByRole("button", { name: "Далее" }).click();

  // step 2: genres
  await expect(page.getByText("Что вы любите смотреть?")).toBeVisible();
  await page.getByRole("button", { name: "фантастика" }).click();
  await page.getByRole("button", { name: "Далее" }).click();

  // step 3: value screen -> finish
  await expect(page.getByText("Готово! Вот что можно посмотреть прямо сейчас")).toBeVisible();
  await page.getByRole("button", { name: /Начать смотреть/ }).click();
  await expect(page).toHaveURL(/\/(\?.*)?$/, { timeout: 15_000 });

  // search with typo
  const search = page.getByRole("combobox");
  await search.fill("матриця");
  await page.waitForTimeout(600); // debounce + fetch
  await expect(page.getByRole("listbox")).toBeVisible({ timeout: 10_000 });
  await search.press("Enter");
  await expect(page).toHaveURL(/\/search\?q=/);
  await expect(page.getByText("Матрица").first()).toBeVisible({ timeout: 15_000 });

  // open card
  await page.getByRole("link", { name: /Матрица, 1999/ }).first().click();
  await expect(page.getByRole("heading", { name: "Матрица" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("button", { name: /Смотреть ·/ }).first()).toBeVisible();

  // add to watchlist
  await page.getByRole("button", { name: "В список" }).click();
  await expect(page.getByText("Сохранено в список")).toBeVisible({ timeout: 10_000 });

  // watchlist contains it
  await page.goto("/watchlist");
  await expect(page.getByText("Матрица").first()).toBeVisible({ timeout: 15_000 });

  // theme toggle persists
  await page.getByRole("button", { name: /тема/i }).first().click();
  await expect(page.locator("html")).toHaveClass(/dark|light/);
  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);
});
