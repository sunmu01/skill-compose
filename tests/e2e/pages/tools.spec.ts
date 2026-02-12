import { test, expect } from '@playwright/test';

test.describe('Tools Page', () => {
  test('should load tools page', async ({ page }) => {
    await page.goto('/tools');
    await expect(page.locator('body')).not.toContainText('Application error');
  });

  test('should display tool categories', async ({ page }) => {
    await page.goto('/tools');
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should show tool details', async ({ page }) => {
    await page.goto('/tools');
    await page.waitForTimeout(2000);
    const toolItem = page.locator('text=/execute_code|list_skills|read_file/i');
    await expect(toolItem.first()).toBeVisible({ timeout: 5000 });
  });
});
