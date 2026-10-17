import { test, expect } from '@playwright/test';

test('editor loads and exposes core editing controls', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto('/');
  await expect(page).toHaveTitle(/PitchPerfect AI Studio/);
  await expect(page.getByRole('heading', { name: /VIDEO PREVIEW/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /Choose video/i })).toBeVisible();
  await expect(page.locator('#startTime')).toHaveValue('0');
  await expect(page.locator('#aspect')).toHaveValue('16:9');
  await expect(page.getByRole('button', { name: /Render & download MP4/i })).toBeDisabled();
  await expect(page.getByRole('button', { name: /Scan for exciting moments/i })).toBeDisabled();
  expect(pageErrors).toEqual([]);
});

test('invalid file is rejected with a helpful message', async ({ page }) => {
  await page.goto('/');
  await page.locator('#fileInput').setInputFiles({
    name: 'notes.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('not a video')
  });
  await expect(page.locator('#exportStatus')).toContainText(/choose an MP4, MOV or WebM/i);
  await expect(page.locator('#video')).toHaveClass(/hidden/);
});

test('responsive layout and settings remain usable on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /EXPORT SETTINGS/i })).toBeVisible();
  await expect(page.locator('#aspect')).toBeVisible();
  await expect(page.locator('#resolution')).toBeVisible();
  const bodyWidth = await page.locator('body').evaluate(el => el.scrollWidth);
  expect(bodyWidth).toBeLessThanOrEqual(390);
});
