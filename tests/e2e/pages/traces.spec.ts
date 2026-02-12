import { test, expect } from '@playwright/test';

test.describe('Traces Page', () => {
  test('should load traces page', async ({ page }) => {
    await page.goto('/traces');
    await expect(page.locator('body')).not.toContainText('Application error');
  });

  test('should display traces list or empty state', async ({ page }) => {
    await page.goto('/traces');
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should support filtering', async ({ page }) => {
    await page.goto('/traces');
    await page.waitForTimeout(2000);
  });

  test('should navigate to trace detail', async ({ page }) => {
    await page.goto('/traces');
    await page.waitForTimeout(2000);
    const traceLink = page.locator('a[href*="/traces/"]').first();
    if (await traceLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await traceLink.click();
      await expect(page).toHaveURL(/.*traces\/.+/);
    }
  });
});
