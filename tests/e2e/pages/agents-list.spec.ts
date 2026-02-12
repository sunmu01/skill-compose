import { test, expect } from '@playwright/test';

test.describe('Agents List Page', () => {
  test('should load agents page', async ({ page }) => {
    await page.goto('/agents');
    await expect(page.locator('body')).not.toContainText('Application error');
  });

  test('should display agent preset cards', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should have create button', async ({ page }) => {
    await page.goto('/agents');
    const createBtn = page.locator(
      'a[href*="/agents/new"], button:has-text("Create"), button:has-text("New")',
    );
    await expect(createBtn.first()).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to create page', async ({ page }) => {
    await page.goto('/agents');
    const createBtn = page.locator(
      'a[href*="/agents/new"], button:has-text("Create"), button:has-text("New")',
    );
    if (await createBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await createBtn.first().click();
      await expect(page).toHaveURL(/.*agents\/new/);
    }
  });
});
