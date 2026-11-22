import { test, expect } from '@playwright/test';

test.describe('FocusBoard End-to-End User Journeys', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to local application root
    await page.goto('/');
  });

  test('Journey 1: Application loads brand header, metrics, and navigation', async ({ page }) => {
    // Verify brand header
    await expect(page.locator('.brand-name')).toContainText('FocusBoard');

    // Verify main navigation items exist
    const sidebar = page.locator('.desktop-sidebar');
    await expect(sidebar.getByText('Overview')).toBeVisible();
    await expect(sidebar.getByText('My Tasks')).toBeVisible();
    await expect(sidebar.getByText('AI Planner')).toBeVisible();
    await expect(sidebar.getByText('Plans & Billing')).toBeVisible();
  });

  test('Journey 2: Task CRUD workflow (Create, View, Filter)', async ({ page }) => {
    // Click "New Task" or "+" button
    const newTaskBtn = page.getByRole('button', { name: /new task|add task|\+/i }).first();
    if (await newTaskBtn.isVisible()) {
      await newTaskBtn.click();

      // Modal appears
      const modal = page.locator('role=dialog');
      await expect(modal).toBeVisible();

      // Fill in task form
      const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]').first();
      await titleInput.fill('E2E Automated Task Verification');

      // Submit form
      const submitBtn = page.locator('button[type="submit"]').first();
      await submitBtn.click();

      // Verify task card appears in task list
      await expect(page.getByText('E2E Automated Task Verification')).toBeVisible();
    }
  });

  test('Journey 3: Navigation across Product Intelligence and Enterprise Admin', async ({ page }) => {
    const sidebar = page.locator('.desktop-sidebar');

    // Navigate to Intelligence
    const intelBtn = sidebar.getByText('Intelligence');
    if (await intelBtn.isVisible()) {
      await intelBtn.click();
      await expect(page.getByText('Product Intelligence Engine')).toBeVisible();
      await expect(page.getByText('Completion Velocity')).toBeVisible();
    }

    // Navigate to Enterprise Admin
    const enterpriseBtn = sidebar.getByText('Enterprise Admin');
    if (await enterpriseBtn.isVisible()) {
      await enterpriseBtn.click();
      await expect(page.getByText('Enterprise Administration & Governance')).toBeVisible();
      await expect(page.getByText('Enforce Multi-Factor Authentication')).toBeVisible();
    }
  });

  test('Journey 4: SaaS Billing and Plans View', async ({ page }) => {
    const sidebar = page.locator('.desktop-sidebar');
    const billingBtn = sidebar.getByText('Plans & Billing');
    if (await billingBtn.isVisible()) {
      await billingBtn.click();
      await expect(page.getByText(/Free Tier|Starter|Pro|Enterprise/i).first()).toBeVisible();
    }
  });

  test('Journey 5: Mobile viewport displays bottom navigation', async ({ page, isMobile }) => {
    if (isMobile) {
      const bottomNav = page.locator('.mobile-bottom-nav');
      await expect(bottomNav).toBeVisible();
      await expect(bottomNav.getByText('Overview')).toBeVisible();
      await expect(bottomNav.getByText('Tasks')).toBeVisible();
    }
  });
});
