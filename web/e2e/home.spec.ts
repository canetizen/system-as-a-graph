import { expect, test } from "@playwright/test";

test("root redirects to the Model screen", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/model$/);
  await expect(page.getByRole("heading", { name: "Model" })).toBeVisible();
});
