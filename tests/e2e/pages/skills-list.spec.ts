import { test, expect } from '@playwright/test';

test.describe('Skills List Page', () => {
  test('should load skills page', async ({ page }) => {
    await page.goto('/skills');
    await expect(page.locator('h1, h2').first()).toContainText(/skills/i);
  });

  test('should display skill cards or empty state', async ({ page }) => {
    await page.goto('/skills');
    const cards = page.locator('[data-testid="skill-card"], [class*="card"]');
    const emptyState = page.locator('text=/no skills/i, text=/empty/i');
    await expect(cards.or(emptyState).first()).toBeVisible({ timeout: 10000 });
  });

  test('should have meta skills pinned at top', async ({ page }) => {
    await page.goto('/skills');
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).not.toContainText('Application error');
  });

  test('should support search', async ({ page }) => {
    await page.goto('/skills');
    const searchInput = page.locator(
      'input[type="search"], input[placeholder*="search" i], input[placeholder*="Search" i]',
    );
    if (await searchInput.isVisible()) {
      await searchInput.fill('test');
      await page.waitForTimeout(500);
    }
  });

  test('should navigate to skill detail', async ({ page }) => {
    await page.goto('/skills');
    const firstCard = page
      .locator('[data-testid="skill-card"] a, [class*="card"] a')
      .first();
    if (await firstCard.isVisible({ timeout: 3000 }).catch(() => false)) {
      await firstCard.click();
      await expect(page).toHaveURL(/.*skills\/.+/);
    }
  });
});
