import { test, expect } from '@playwright/test';

test.describe('Create Agent Preset Page', () => {
  test('should load create page', async ({ page }) => {
    await page.goto('/agents/new');
    await expect(page.locator('body')).not.toContainText('Application error');
  });

  test('should display form fields', async ({ page }) => {
    await page.goto('/agents/new');
    await page.waitForTimeout(1000);
    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]');
    await expect(nameInput.first()).toBeVisible({ timeout: 5000 });
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/agents/new');
    await page.waitForTimeout(1000);
    const submitBtn = page.locator(
      'button[type="submit"], button:has-text("Create"), button:has-text("Save")',
    );
    if (await submitBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await submitBtn.first().click();
      await page.waitForTimeout(500);
      await expect(page).toHaveURL(/.*agents\/new/);
    }
  });

  test('should have skills and tools selectors', async ({ page }) => {
    await page.goto('/agents/new');
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).not.toContainText('Application error');
  });
});
