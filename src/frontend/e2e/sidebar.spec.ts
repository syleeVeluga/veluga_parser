import { test, expect } from '@playwright/test'
import { mockAllApis } from './helpers'

test.beforeEach(async ({ page }) => {
  await mockAllApis(page)
})

test.describe('Sidebar', () => {
  test('renders sidebar with document list on app load', async ({ page }) => {
    await page.goto('/')
    const sidebar = page.getByTestId('sidebar')
    await expect(sidebar).toBeVisible()

    // Should show app title
    await expect(sidebar.getByText('Veluga PDF Parser')).toBeVisible()

    // Upload button visible
    await expect(sidebar.getByRole('button', { name: /upload pdf/i })).toBeVisible()

    // Document list shows items
    const docList = page.getByTestId('sidebar-doc-list')
    await expect(docList).toBeVisible()
    await expect(docList.getByText('resume_kr.pdf')).toBeVisible()
    await expect(docList.getByText('report_en.pdf')).toBeVisible()
    await expect(docList.getByText('analysis_jp.pdf')).toBeVisible()
  })

  test('shows status badges for each document', async ({ page }) => {
    await page.goto('/')
    const docList = page.getByTestId('sidebar-doc-list')
    await expect(docList.getByText('Completed').first()).toBeVisible()
    await expect(docList.getByText('Running')).toBeVisible()
  })

  test('collapse/expand via toggle button', async ({ page }) => {
    await page.goto('/')
    const sidebar = page.getByTestId('sidebar')

    // Initially expanded — should have full width content
    await expect(sidebar.getByText('Veluga PDF Parser')).toBeVisible()

    // Click collapse
    await sidebar.getByRole('button', { name: /collapse sidebar/i }).click()

    // After collapse, the app title should not be visible
    await expect(page.getByText('Veluga PDF Parser')).not.toBeVisible()

    // Expand button should be visible
    await page.getByRole('button', { name: /expand sidebar/i }).click()
    await expect(page.getByText('Veluga PDF Parser')).toBeVisible()
  })

  test('collapse/expand via Ctrl+B keyboard shortcut', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Veluga PDF Parser')).toBeVisible()

    await page.keyboard.press('Control+b')
    await expect(page.getByText('Veluga PDF Parser')).not.toBeVisible()

    await page.keyboard.press('Control+b')
    await expect(page.getByText('Veluga PDF Parser')).toBeVisible()
  })

  test('sidebar state persists in localStorage', async ({ page }) => {
    await page.goto('/')
    // Collapse sidebar
    await page.getByRole('button', { name: /collapse sidebar/i }).click()
    await expect(page.getByText('Veluga PDF Parser')).not.toBeVisible()

    // Reload page
    await page.reload()
    await mockAllApis(page)

    // Sidebar should remain collapsed after reload
    await expect(page.getByText('Veluga PDF Parser')).not.toBeVisible()
  })
})
