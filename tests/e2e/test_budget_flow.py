import pytest
import time
import re
from playwright.sync_api import Page, expect

# Constants
BASE_URL = "http://localhost:8050"
# Use a dynamic email to avoid collision in local dev if not reset
import random
RAND_ID = random.randint(1000, 9999)
USER_EMAIL = f"test_e2e_{RAND_ID}@example.com"
USER_PASS = "Password123!"
FULL_NAME = "E2E Test User"
PERIOD_NAME = f"Jan 2026 {RAND_ID}"

def test_full_budget_flow(page: Page):
    # 1. Registration
    page.goto(f"{BASE_URL}/register")
    page.fill("#register-email", USER_EMAIL)
    page.fill("#register-fullname", FULL_NAME)
    page.fill("#register-password", USER_PASS)
    page.click("#register-button")
    
    # Wait for redirect to login
    expect(page).to_have_url(f"{BASE_URL}/login", timeout=10000)
    
    # 2. Login
    page.fill("#login-email", USER_EMAIL)
    page.fill("#login-password", USER_PASS)
    page.click("#login-button")
    
    # Wait for dashboard to load
    expect(page).to_have_url(re.compile(f"{BASE_URL}/dashboard(/periods)?"), timeout=10000)
    expect(page.get_by_text(USER_EMAIL)).to_be_visible()

    # 3. Create Currency
    # Click the Currencies tab inside the dashboard-tabs container
    page.locator("#dashboard-tabs").get_by_text("Currencies", exact=True).click()
    page.wait_for_selector("#currency-ticker")
    page.locator("#currency-ticker").press_sequentially("USD", delay=50)
    page.locator("#currency-name").press_sequentially("US Dollar", delay=50)
    # Checkbox check
    page.locator("#currency-default").check()
    page.wait_for_timeout(500)
    page.click("#add-currency-btn")
    expect(page.locator("#currency-message")).to_contain_text("added!")

    # 4. Create Account
    page.locator("#dashboard-tabs").get_by_text("Accounts", exact=True).click()
    page.wait_for_selector("#account-name-input")
    page.locator("#account-name-input").press_sequentially("Main Savings", delay=50)
    page.select_option("#account-type-select", value="BANK")
    # Wait for currency options to load (attached is enough)
    page.wait_for_selector("#account-currency-select option:has-text('USD')", state="attached")
    page.select_option("#account-currency-select", label="USD")
    page.wait_for_timeout(500)
    page.click("#add-account-btn")
    expect(page.locator("#account-message")).to_contain_text("added!")

    # 5. Create Period
    page.locator("#dashboard-tabs").get_by_text("Period Setup", exact=True).click()
    page.wait_for_selector("#period-name-input")
    page.fill("#period-name-input", PERIOD_NAME)
    page.fill("#period-start-date", "2026-01-01")
    page.fill("#period-end-date", "2026-01-31")
    page.click("#create-period-btn")
    expect(page.locator("#period-create-message")).to_contain_text("successfully")

    # 6. Add Income
    page.locator("#dashboard-tabs").get_by_text("Income", exact=True).click()
    page.wait_for_selector("#income-period-selector")
    # Wait for period options to load
    page.wait_for_selector(f"#income-period-selector option:has-text('{PERIOD_NAME}')", state="attached")
    page.select_option("#income-period-selector", label=f"{PERIOD_NAME} (DRAFT)")
    page.wait_for_selector("#income-source-name")
    
    page.locator("#income-source-name").press_sequentially("Salary", delay=50)
    page.locator("#income-amount").press_sequentially("5000", delay=50)
    
    # Wait for currency options to load
    page.wait_for_selector("#income-currency option:has-text('USD')", state="attached")
    page.select_option("#income-currency", label="USD - US Dollar")
    page.wait_for_timeout(500)
    page.click("#add-income-btn")
    expect(page.locator("#income-message")).to_contain_text("added successfully")

    # 7. Add Expense
    page.locator("#dashboard-tabs").get_by_text("Expenses", exact=True).click()
    page.wait_for_selector("#expense-period-selector")
    # Wait for period options to load
    page.wait_for_selector(f"#expense-period-selector option:has-text('{PERIOD_NAME}')", state="attached")
    page.select_option("#expense-period-selector", label=f"{PERIOD_NAME} (DRAFT)")
    page.wait_for_selector("#expense-category")
    # Wait for category options to load
    page.wait_for_selector("#expense-category option", state="attached")
    page.select_option("#expense-category", index=1)
    
    page.locator("#expense-item-name").press_sequentially("Rent", delay=50)
    page.locator("#expense-amount").press_sequentially("1500", delay=50)
    
    # Wait for currency options to load
    page.wait_for_selector("#expense-currency option:has-text('USD')", state="attached")
    page.select_option("#expense-currency", label="USD - US Dollar")
    page.wait_for_timeout(500)
    page.click("#add-expense-btn")
    expect(page.locator("#expense-message")).to_contain_text("added successfully")

    # 8. Reconciliation
    page.locator("#dashboard-tabs").get_by_text("Reconciliation", exact=True).click()
    page.wait_for_selector("#recon-period-selector")
    # Wait for period options to load
    page.wait_for_selector(f"#recon-period-selector option:has-text('{PERIOD_NAME}')", state="attached")
    page.select_option("#recon-period-selector", label=f"{PERIOD_NAME} (DRAFT)")
    
    # Enter snapshots
    # Expected: 5000 - 1500 = 3500
    page.wait_for_selector("input[id*='snapshot-balance']")
    page.locator("input[id*='snapshot-balance']").first.fill("3500")
    page.click("#save-snapshots-btn")
    expect(page.locator("#recon-message")).to_contain_text("saved successfully")

    # Calculate reconciliation
    page.click("#calculate-recon-btn")
    expect(page.locator("#recon-summary-container")).to_contain_text("BALANCED")

    # Finalize period
    page.click("#open-finalize-modal-btn")
    page.click("#finalize-confirm-btn")
    expect(page.locator("#recon-message")).to_contain_text("finalized successfully")
    
    # Verify it says FINALIZED in selector
    expect(page.locator("#recon-period-selector")).to_contain_text("FINALIZED")

if __name__ == "__main__":
    import subprocess
    subprocess.run(["pytest", __file__, "-v", "--headed"])
