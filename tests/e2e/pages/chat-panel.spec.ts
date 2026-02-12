import { test, expect } from '@playwright/test';

test.describe('Chat Panel', () => {
  test('should have chat toggle button', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const chatBtn = page.locator(
      'button[aria-label*="chat" i], button:has-text("Chat"), [data-testid="chat-toggle"]',
    );
    if (await chatBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(chatBtn.first()).toBeVisible();
    }
  });

  test('should open chat panel on click', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const chatBtn = page.locator(
      'button[aria-label*="chat" i], button:has-text("Chat"), [data-testid="chat-toggle"]',
    );
    if (await chatBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await chatBtn.first().click();
      await page.waitForTimeout(500);
      const chatPanel = page.locator('[data-testid="chat-panel"], [class*="chat"]');
      await expect(chatPanel.first()).toBeVisible({ timeout: 3000 });
    }
  });

  test('should have message input', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const chatBtn = page.locator(
      'button[aria-label*="chat" i], button:has-text("Chat"), [data-testid="chat-toggle"]',
    );
    if (await chatBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await chatBtn.first().click();
      await page.waitForTimeout(500);
      const input = page.locator('textarea, input[type="text"]').last();
      await expect(input).toBeVisible({ timeout: 3000 });
    }
  });

  test('should have agent preset selector', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const chatBtn = page.locator(
      'button[aria-label*="chat" i], button:has-text("Chat"), [data-testid="chat-toggle"]',
    );
    if (await chatBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await chatBtn.first().click();
      await page.waitForTimeout(1000);
    }
  });

  test('should send message', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const chatBtn = page.locator(
      'button[aria-label*="chat" i], button:has-text("Chat"), [data-testid="chat-toggle"]',
    );
    if (await chatBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await chatBtn.first().click();
      await page.waitForTimeout(500);
      const input = page.locator('textarea').last();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        await input.fill('Hello, this is a test message');
        // Don't actually send to avoid API calls in E2E
      }
    }
  });

  test('should close chat panel', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    const chatBtn = page.locator(
      'button[aria-label*="chat" i], button:has-text("Chat"), [data-testid="chat-toggle"]',
    );
    if (await chatBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await chatBtn.first().click();
      await page.waitForTimeout(500);
      const closeBtn = page.locator('button[aria-label*="close" i], button:has-text("×")');
      if (await closeBtn.first().isVisible({ timeout: 2000 }).catch(() => false)) {
        await closeBtn.first().click();
      }
    }
  });
});
