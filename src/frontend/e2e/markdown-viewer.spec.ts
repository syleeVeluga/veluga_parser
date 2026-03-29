import { test, expect } from '@playwright/test'
import { mockAllApis } from './helpers'
import { MOCK_MARKDOWN } from './fixtures'

test.describe('MarkdownTab Pagination', () => {
  test.beforeEach(async ({ page }) => {
    await mockAllApis(page)
    await page.goto('/jobs/job-001')
    // Wait for the paginated nav bar to appear
    await expect(page.getByText('1 / 3')).toBeVisible()
  })

  test('Prev button is disabled on first page', async ({ page }) => {
    const prevBtn = page.locator('button').filter({ hasText: '\u2039' })
    await expect(prevBtn).toBeDisabled()
  })

  test('Next button is enabled on first page', async ({ page }) => {
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    await expect(nextBtn).toBeEnabled()
  })

  test('Next click advances page indicator to 2 / 3', async ({ page }) => {
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    await nextBtn.click()
    await expect(page.getByText('2 / 3')).toBeVisible()
  })

  test('Page content changes after Next click', async ({ page }) => {
    await expect(page.getByText('Sample body text for testing.')).toBeVisible()
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    await nextBtn.click()
    await expect(page.getByText('Content on page two.')).toBeVisible()
  })

  test('Next button is disabled on last page', async ({ page }) => {
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    await nextBtn.click()
    await nextBtn.click()
    await expect(page.getByText('3 / 3')).toBeVisible()
    await expect(nextBtn).toBeDisabled()
  })

  test('Prev button is enabled after advancing past page 1', async ({ page }) => {
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    const prevBtn = page.locator('button').filter({ hasText: '\u2039' })
    await nextBtn.click()
    await expect(page.getByText('2 / 3')).toBeVisible()
    await expect(prevBtn).toBeEnabled()
  })

  test('Prev click after Next returns to page 1 content', async ({ page }) => {
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    const prevBtn = page.locator('button').filter({ hasText: '\u2039' })
    await nextBtn.click()
    await expect(page.getByText('Content on page two.')).toBeVisible()
    await prevBtn.click()
    await expect(page.getByText('Sample body text for testing.')).toBeVisible()
    await expect(page.getByText('1 / 3')).toBeVisible()
  })

  test('Scroll resets to top after page navigation', async ({ page }) => {
    const contentDiv = page.locator('.markdown-body.overflow-y-auto')
    // Scroll down first
    await contentDiv.evaluate(el => { el.scrollTop = 200 })
    // Navigate to next page
    const nextBtn = page.locator('button').filter({ hasText: '\u203a' })
    await nextBtn.click()
    await expect(page.getByText('Content on page two.')).toBeVisible()
    // Assert scroll reset
    const scrollTop = await contentDiv.evaluate(el => el.scrollTop)
    expect(scrollTop).toBe(0)
  })
})

test.describe('MarkdownTab Fallback Mode', () => {
  test('renders full content when pages endpoint returns 404', async ({ page }) => {
    await mockAllApis(page)
    // Override the pages-list endpoint to return 404 for this test
    await page.route('**/api/jobs/job-001/markdown/pages', route =>
      route.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"not found"}' }),
    )
    await page.goto('/jobs/job-001')
    await expect(page.getByText('Parsed Document')).toBeVisible()
    // No page indicator in fallback mode
    await expect(page.getByText(/\d+ \/ \d+/)).not.toBeVisible()
  })

  test('page indicator label reads "1 / 3" before any navigation', async ({ page }) => {
    await mockAllApis(page)
    await page.goto('/jobs/job-001')
    await expect(page.getByText('1 / 3')).toBeVisible()
  })
})

test.describe('MarkdownTab Full Markdown Fallback Content', () => {
  test('MOCK_MARKDOWN contains Parsed Document for legacy fallback', async () => {
    // Ensure the fallback content fixture satisfies document-viewer.spec.ts assertion
    expect(MOCK_MARKDOWN).toContain('Parsed Document')
  })
})
