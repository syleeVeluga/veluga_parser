import { test, expect } from '@playwright/test'
import { mockAllApis } from './helpers'

test.beforeEach(async ({ page }) => {
  await mockAllApis(page)
})

test.describe('EngineSelector', () => {
  test('renders three engine cards with correct labels', async ({ page }) => {
    await page.goto('/')
    const sidebar = page.getByTestId('sidebar')
    await expect(sidebar.getByText('Docling')).toBeVisible()
    await expect(sidebar.getByText('PaddleOCR 3')).toBeVisible()
    await expect(sidebar.getByText('Gemini Flash')).toBeVisible()
  })

  test('Docling card is selected by default', async ({ page }) => {
    await page.goto('/')
    const doclingCard = page.locator('[data-engine="docling"]')
    await expect(doclingCard).toBeVisible()
    await expect(doclingCard).toHaveAttribute('aria-checked', 'true')
  })

  test('clicking PaddleOCR 3 selects it', async ({ page }) => {
    await page.goto('/')
    const paddleCard = page.locator('[data-engine="paddleocr"]')
    await paddleCard.click()
    await expect(paddleCard).toHaveAttribute('aria-checked', 'true')

    // Docling should now be unselected
    const doclingCard = page.locator('[data-engine="docling"]')
    await expect(doclingCard).toHaveAttribute('aria-checked', 'false')
  })

  test('Gemini card has aria-disabled when not configured', async ({ page }) => {
    // Default mock returns gemini_configured: false
    await page.goto('/')
    await page.waitForTimeout(300) // wait for getApiKeyStatus fetch
    const geminiCard = page.locator('[data-engine="gemini"]')
    await expect(geminiCard).toHaveAttribute('aria-disabled', 'true')
  })

  test('Gemini card shows Settings link when not configured', async ({ page }) => {
    await page.goto('/')
    await page.waitForTimeout(300)
    const settingsLink = page.getByTestId('gemini-settings-link')
    await expect(settingsLink).toBeVisible()
    await expect(settingsLink).toHaveAttribute('href', '/settings')
  })

  test('Settings nav link is visible in sidebar', async ({ page }) => {
    await page.goto('/')
    const settingsLink = page.getByTestId('settings-nav-link')
    await expect(settingsLink).toBeVisible()
  })

  test('navigating to /settings renders the API key form', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.locator('#gemini-api-key')).toBeVisible()
    await expect(page.getByText('Gemini API Key').first()).toBeVisible()
    await expect(page.getByRole('button', { name: /save/i })).toBeVisible()
  })

  test('upload sends engine form field to API', async ({ page }) => {
    // Capture upload request and verify engine field
    let capturedEngine = ''
    await page.route('**/api/upload', async route => {
      const body = route.request().postData() ?? ''
      const match = body.match(/Content-Disposition: form-data; name="engine"[\r\n]+[\r\n]+([^\r\n]+)/)
      if (match) capturedEngine = match[1]
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: '{"job_id":"test-123","filename":"test.pdf","status":"pending","created_at":"2026-03-29T00:00:00Z"}',
      })
    })

    await page.goto('/')

    // Select PaddleOCR
    const paddleCard = page.locator('[data-engine="paddleocr"]')
    await paddleCard.click()
    await expect(paddleCard).toHaveAttribute('aria-checked', 'true')

    // Upload a PDF via file input
    const input = page.locator('input[type="file"]').first()
    await input.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 test'),
    })

    await page.waitForTimeout(500)
    expect(capturedEngine).toBe('paddleocr')
  })
})
