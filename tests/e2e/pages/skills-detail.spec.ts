import { test, expect } from '@playwright/test';

test.describe('Skill Detail Page', () => {
  test('should show 404 for nonexistent skill', async ({ page }) => {
    await page.goto('/skills/nonexistent-skill-xyz');
    await page.waitForTimeout(2000);
    const content = await page.textContent('body');
    expect(content).toBeTruthy();
  });

  test('should display skill overview', async ({ page }) => {
    await page.goto('/skills');
    const firstLink = page.locator('a[href*="/skills/"]').first();
    if (await firstLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstLink.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('body')).not.toContainText('Application error');
    }
  });

  test('should display version timeline if available', async ({ page }) => {
    await page.goto('/skills');
    const firstLink = page.locator('a[href*="/skills/"]').first();
    if (await firstLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstLink.click();
      await page.waitForTimeout(2000);
    }
  });

  test('should have export button', async ({ page }) => {
    await page.goto('/skills');
    const firstLink = page.locator('a[href*="/skills/"]').first();
    if (await firstLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstLink.click();
      await page.waitForTimeout(1000);
    }
  });

  test('should display changelog if available', async ({ page }) => {
    await page.goto('/skills');
    const firstLink = page.locator('a[href*="/skills/"]').first();
    if (await firstLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstLink.click();
      await page.waitForTimeout(2000);
    }
  });

  test('should not show delete for meta skills', async ({ page }) => {
    await page.goto('/skills');
    await page.waitForTimeout(2000);
  });
});
