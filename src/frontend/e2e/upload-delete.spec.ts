import { test, expect } from '@playwright/test'
import { mockAllApis } from './helpers'
import { MOCK_JOBS, MOCK_UPLOAD_RESPONSE } from './fixtures'

test.beforeEach(async ({ page }) => {
  await mockAllApis(page)
})

test.describe('Upload Flow', () => {
  test('upload button opens file picker and navigates on success', async ({ page }) => {
    await page.goto('/')

    // The upload button should be visible in sidebar
    const uploadBtn = page.getByTestId('sidebar').getByRole('button', { name: /upload pdf/i })
    await expect(uploadBtn).toBeVisible()

    // Set up file chooser listener before clicking
    const fileChooserPromise = page.waitForEvent('filechooser')
    await uploadBtn.click()
    const fileChooser = await fileChooserPromise

    // Verify it accepts PDF
    expect(fileChooser.isMultiple()).toBe(false)

    // Mock the job list to include the new upload after the upload completes
    const updatedJobs = {
      ...MOCK_JOBS,
      total: 4,
      items: [
        {
          ...MOCK_UPLOAD_RESPONSE,
          job_id: MOCK_UPLOAD_RESPONSE.job_id,
          filename: MOCK_UPLOAD_RESPONSE.filename,
          status: 'pending',
          page_count: null,
          languages_detected: [],
          doc_title: null,
          element_count: null,
          chunk_count: null,
          has_equations: null,
          has_code: null,
          error_message: null,
          updated_at: MOCK_UPLOAD_RESPONSE.created_at,
        },
        ...MOCK_JOBS.items,
      ],
    }

    // Re-mock the jobs list to include new upload
    await page.route('**/api/jobs?*', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(updatedJobs) }),
    )
    // Mock the new job endpoint
    await page.route(`**/api/jobs/${MOCK_UPLOAD_RESPONSE.job_id}`, route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...MOCK_UPLOAD_RESPONSE,
          page_count: null,
          languages_detected: [],
          doc_title: null,
          element_count: null,
          chunk_count: null,
          error_message: null,
          updated_at: MOCK_UPLOAD_RESPONSE.created_at,
        }),
      }),
    )

    // Choose a mock PDF file
    await fileChooser.setFiles({
      name: 'new_upload.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.0 mock'),
    })

    // Should navigate to the new job
    await expect(page).toHaveURL(new RegExp(`/jobs/${MOCK_UPLOAD_RESPONSE.job_id}`))
  })
})

test.describe('Delete Flow', () => {
  test('delete with confirmation removes document from sidebar', async ({ page }) => {
    await page.goto('/')
    const docList = page.getByTestId('sidebar-doc-list')

    // Hover over the first completed doc to see delete button
    const firstItem = docList.getByTestId('sidebar-doc-item').first()
    await firstItem.hover()

    // Click delete button (first click shows confirmation)
    const deleteBtn = firstItem.getByTitle('Delete document')
    await deleteBtn.click()

    // Confirmation should appear
    await expect(firstItem.getByText('Del')).toBeVisible()

    // Confirm delete
    await firstItem.getByText('Del').click()

    // The item should be removed from the list
    await expect(docList.getByText('resume_kr.pdf')).not.toBeVisible()
  })

  test('cancel delete keeps document in list', async ({ page }) => {
    await page.goto('/')
    const docList = page.getByTestId('sidebar-doc-list')

    const firstItem = docList.getByTestId('sidebar-doc-item').first()
    await firstItem.hover()
    await firstItem.getByTitle('Delete document').click()

    // Click No to cancel
    await firstItem.getByText('No').click()

    // Document should still be there
    await expect(docList.getByText('resume_kr.pdf')).toBeVisible()
  })
})
