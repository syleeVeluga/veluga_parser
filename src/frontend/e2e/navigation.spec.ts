import { test, expect } from '@playwright/test'
import { mockAllApis } from './helpers'

test.beforeEach(async ({ page }) => {
  await mockAllApis(page)
})

test.describe('URL Sync & Navigation', () => {
  test('empty state shown when no document selected', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('No document selected')).toBeVisible()
    await expect(page.getByText('Select a document from the sidebar')).toBeVisible()
  })

  test('clicking document updates URL', async ({ page }) => {
    await page.goto('/')
    await page.getByText('resume_kr.pdf').click()
    await expect(page).toHaveURL(/\/jobs\/job-001/)
  })

  test('direct navigation to /jobs/:id loads document', async ({ page }) => {
    await page.goto('/jobs/job-001')

    // Metadata bar should show
    await expect(page.getByTestId('metadata-bar')).toBeVisible()
    await expect(page.getByTestId('metadata-bar').getByText('resume_kr.pdf')).toBeVisible()

    // Sidebar should highlight the active document
    const sidebar = page.getByTestId('sidebar')
    await expect(sidebar.getByText('resume_kr.pdf')).toBeVisible()
  })

  test('switching between documents without page reload', async ({ page }) => {
    await page.goto('/jobs/job-001')
    await expect(page.getByTestId('metadata-bar').getByText('resume_kr.pdf')).toBeVisible()

    // Click second document
    await page.getByText('report_en.pdf').click()
    await expect(page).toHaveURL(/\/jobs\/job-002/)
    await expect(page.getByTestId('metadata-bar').getByText('report_en.pdf')).toBeVisible()
  })
})

test.describe('Responsive: Mobile Drawer', () => {
  test('sidebar becomes overlay drawer on narrow viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')

    // Sidebar should be hidden on mobile by default
    await expect(page.getByTestId('sidebar')).not.toBeVisible()

    // Empty state should be visible
    await expect(page.getByText('No document selected')).toBeVisible()

    // FAB button should be visible to open sidebar
    const openBtn = page.getByRole('button', { name: /open sidebar/i })
    await expect(openBtn).toBeVisible()
    await openBtn.click()

    // Sidebar should now be visible as overlay
    await expect(page.getByTestId('sidebar')).toBeVisible()
    await expect(page.getByText('resume_kr.pdf')).toBeVisible()
  })

  test('clicking document on mobile closes drawer', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')

    // Open sidebar
    await page.getByRole('button', { name: /open sidebar/i }).click()
    await expect(page.getByTestId('sidebar')).toBeVisible()

    // Click a document
    await page.getByText('resume_kr.pdf').click()

    // Sidebar should close and URL should update
    await expect(page).toHaveURL(/\/jobs\/job-001/)
    await expect(page.getByTestId('sidebar')).not.toBeVisible()
  })
})
