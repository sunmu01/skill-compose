import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Skills/i);
  });

  test('should display navigation links', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('link', { name: /skills/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /agents/i })).toBeVisible();
  });

  test('should navigate to skills page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /skills/i }).click();
    await expect(page).toHaveURL(/.*skills/);
  });
});
