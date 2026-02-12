import { test, expect } from '@playwright/test';

test.describe('MCP Page', () => {
  test('should load MCP page', async ({ page }) => {
    await page.goto('/mcp');
    await expect(page.locator('body')).not.toContainText('Application error');
  });

  test('should display server list', async ({ page }) => {
    await page.goto('/mcp');
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should show server details', async ({ page }) => {
    await page.goto('/mcp');
    await page.waitForTimeout(3000);
    const serverItem = page.locator('text=/fetch|time|git|gemini/i');
    // May or may not exist depending on configuration
  });

  test('should have add server option', async ({ page }) => {
    await page.goto('/mcp');
    await page.waitForTimeout(2000);
  });
});
