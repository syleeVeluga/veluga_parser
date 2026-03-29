import { test, expect } from '@playwright/test'
import { mockAllApis } from './helpers'

test.beforeEach(async ({ page }) => {
  await mockAllApis(page)
})

test.describe('Document Viewer', () => {
  test('clicking document in sidebar shows metadata bar', async ({ page }) => {
    await page.goto('/')
    await page.getByText('resume_kr.pdf').click()

    const metadataBar = page.getByTestId('metadata-bar')
    await expect(metadataBar).toBeVisible()
    await expect(metadataBar.getByText('resume_kr.pdf')).toBeVisible()
    await expect(metadataBar.getByText('Completed')).toBeVisible()
    await expect(metadataBar.getByText('3 pages')).toBeVisible()
    await expect(metadataBar.getByText('112 elements')).toBeVisible()
    await expect(metadataBar.getByText('81 chunks')).toBeVisible()
  })

  test('output tabs switch correctly', async ({ page }) => {
    await page.goto('/jobs/job-001')

    // Markdown tab should be default
    await expect(page.getByText('Parsed Document')).toBeVisible()

    // Switch to JSON tab
    await page.getByRole('button', { name: 'JSON' }).click()
    await expect(page.getByText('"schema_version"')).toBeVisible()

    // Switch to Text tab
    await page.getByRole('button', { name: 'Text' }).click()
    await expect(page.getByText('Sample body text for testing.')).toBeVisible()

    // Switch to Structure tab
    await page.getByRole('button', { name: 'Structure' }).click()
    await expect(page.getByText('Introduction')).toBeVisible()

    // Switch to Chunks tab
    await page.getByRole('button', { name: 'Chunks' }).click()
    await expect(page.getByText('Hierarchical')).toBeVisible()

    // Switch to Analysis tab
    await page.getByRole('button', { name: 'Analysis' }).click()
    await expect(page.getByText('85')).toBeVisible() // confidence
  })

  test('download buttons have correct hrefs', async ({ page }) => {
    await page.goto('/jobs/job-001')

    const metadataBar = page.getByTestId('metadata-bar')
    await expect(metadataBar).toBeVisible()

    const jsonLink = metadataBar.getByRole('link', { name: 'JSON', exact: true })
    await expect(jsonLink).toHaveAttribute('href', '/api/jobs/job-001/download/json')

    const mdLink = metadataBar.getByRole('link', { name: 'Markdown', exact: true })
    await expect(mdLink).toHaveAttribute('href', '/api/jobs/job-001/download/markdown')

    const textLink = metadataBar.getByRole('link', { name: 'Plain Text', exact: true })
    await expect(textLink).toHaveAttribute('href', '/api/jobs/job-001/download/text')

    const chunksLink = metadataBar.getByRole('link', { name: 'Chunks JSON', exact: true })
    await expect(chunksLink).toHaveAttribute('href', '/api/jobs/job-001/download/chunks')
  })

  test('reprocess button triggers API call', async ({ page }) => {
    await page.goto('/jobs/job-001')

    const metadataBar = page.getByTestId('metadata-bar')
    const reprocessBtn = metadataBar.getByRole('button', { name: /reprocess/i })
    await expect(reprocessBtn).toBeVisible()

    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('/reprocess') && req.method() === 'POST'),
      reprocessBtn.click(),
    ])
    expect(request).toBeTruthy()
  })
})
