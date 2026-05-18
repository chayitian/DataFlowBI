import { test, expect } from "@playwright/test";
import path from "path";

test("upload and render analytics", async ({ page }) => {
  await page.goto("/");

  const filePath = path.join(process.cwd(), "e2e", "fixtures", "sample.csv");
  await page.setInputFiles('input[type="file"]', filePath);

  await page.getByRole("button", { name: /开始解析|Parse data/ }).click();
  await page.locator(".selection-overlay .primary-btn").first().click();

  await expect(page.locator(".hero-card")).toBeVisible();
  await expect(page.locator(".chart-canvas")).toBeVisible();

  await page.getByRole("button", { name: /数据筛选|Data Filter/ }).click();
  await page.locator(".selection-overlay .primary-btn").first().click();

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: /导出 Word|Export Word/ }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/\.docx$/);
});
