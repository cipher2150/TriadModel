import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

const growth2025 = (page: Page) => page.getByLabel('Revenue growth, 2025 (percent)')

async function figure(page: Page, line: string, year: number): Promise<string> {
  const button = page.getByRole('button', { name: new RegExp(`^${line} ${year}: `) })
  const label = (await button.getAttribute('aria-label')) ?? ''
  return label.replace(new RegExp(`^${line} ${year}: `), '').split('.')[0]
}

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Demo data')).toBeVisible()
})

test('demo loads labelled as demo data with all checks passing', async ({ page }) => {
  await expect(page.getByText('All checks pass.')).toBeVisible()
  await expect(page.getByRole('tab', { name: /base/i })).toHaveAttribute('aria-selected', 'true')
})

test('changing one assumption propagates through all three statements', async ({ page }) => {
  const revenueBefore = await figure(page, 'Revenue', 2025)
  const netIncomeBefore = await figure(page, 'Net income', 2025)

  await growth2025(page).fill('20')
  await expect(page.getByText('Recalculating…')).toBeHidden()
  await expect.poll(() => figure(page, 'Revenue', 2025)).not.toBe(revenueBefore)
  expect(await figure(page, 'Net income', 2025)).not.toBe(netIncomeBefore)

  await page.getByRole('tab', { name: 'Balance sheet' }).click()
  const cash = await figure(page, 'Cash', 2025)
  await page.getByRole('tab', { name: 'Cash flow' }).click()
  await page.getByRole('button', { name: /^Net income 2025: / }).waitFor()
  const statements = page.getByRole('region', { name: 'Financial statements' })
  // Columns after the row header: 3 historical years, then 2025.
  await expect(
    statements
      .getByRole('row', { name: /^Ending cash/ })
      .getByRole('cell')
      .nth(3),
  ).toHaveText(cash)
  await expect(page.getByText('All checks pass.')).toBeVisible()
})

test('a cash shortfall is flagged with its year', async ({ page }) => {
  await page.getByLabel('Capex % of revenue, 2025 (percent)').fill('50')
  await page.getByLabel('Revolver limit, 2025').fill('10')
  const flags = page.getByRole('list').filter({ hasText: 'Cash shortfall' })
  await expect(flags).toBeVisible()
  await expect(flags).toContainText('2025')
  await expect(flags).toContainText('Negative cash')
  await expect(page.getByText('All checks pass.')).toBeHidden()
})

test('a figure can be traced to its formula and inputs', async ({ page }) => {
  await page.getByRole('button', { name: /^Revenue 2025: / }).click()
  const panel = page.getByRole('region', { name: /how a number was calculated/i })
  await expect(panel).toContainText('revenue@1')
  await expect(panel).toContainText('revenue@0')
})

test('scenario switch shows that scenario’s assumptions', async ({ page }) => {
  await page.getByRole('tab', { name: /downside/i }).click()
  await expect(page.getByRole('heading', { name: /Assumptions — downside/ })).toBeVisible()
  await expect(growth2025(page)).toHaveValue('2')
})

test('a saved model survives reload via its link; without the token it is view-only', async ({ page, context }) => {
  await growth2025(page).fill('12')
  await expect(page.getByText('Not saved')).toBeVisible()
  await page.getByRole('button', { name: 'Save model' }).click()
  await expect(page.getByText('Saved · v1')).toBeVisible()
  const link = page.url()
  expect(link).toMatch(/#\/m\/[0-9a-f-]{36}$/)

  await page.reload()
  await expect(page.getByText('Saved · v1')).toBeVisible()
  await expect(growth2025(page)).toHaveValue('12')

  await growth2025(page).fill('13')
  await page.getByRole('button', { name: 'Save changes' }).click()
  await expect(page.getByText('Saved · v2')).toBeVisible()

  const stranger = await context.browser()!.newContext()
  const other = await stranger.newPage()
  await other.goto(link)
  await expect(other.getByText('Saved · view only')).toBeVisible()
  await expect(other.getByRole('button', { name: 'Save changes' })).toBeDisabled()
  await expect(other.getByLabel('Revenue growth, 2025 (percent)')).toHaveValue('13')
  await stranger.close()
})

test('importing a file that is not JSON shows a clear error', async ({ page }) => {
  await page.getByLabel('Import model JSON file').setInputFiles({
    name: 'bad.json',
    mimeType: 'application/json',
    buffer: Buffer.from('this is not json'),
  })
  await expect(page.getByText('not valid JSON for a TriadModel export')).toBeVisible()
})

test('importing a model with an unbalanced history is rejected by the server with the year', async ({ page }) => {
  const demo = await (await page.request.get('/api/demo')).json()
  demo.historicals[1].balance_sheet.cash = '999999'
  await page.getByLabel('Import model JSON file').setInputFiles({
    name: 'unbalanced.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(demo)),
  })
  await expect(page.getByRole('alert')).toContainText('does not balance')
  await expect(page.getByRole('alert')).toContainText('2023')
})

test('an unknown saved-model link shows a not-found error with a way out', async ({ page }) => {
  await page.goto('/#/m/00000000-0000-4000-8000-000000000000')
  await page.reload()
  await expect(page.getByRole('alert')).toContainText('Model not found')
  await page.getByRole('button', { name: /load the demo/i }).click()
  await expect(page.getByText('Demo data')).toBeVisible()
})

test('the main page has no serious or critical accessibility violations', async ({ page }) => {
  const results = await new AxeBuilder({ page }).analyze()
  const serious = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
  expect(serious.map((v) => `${v.id}: ${v.help}`)).toEqual([])
})

test('responses carry security headers', async ({ page }) => {
  const response = await page.request.get('/')
  const headers = response.headers()
  expect(headers['x-content-type-options']).toBe('nosniff')
  expect(headers['content-security-policy']).toContain("default-src 'self'")
})
