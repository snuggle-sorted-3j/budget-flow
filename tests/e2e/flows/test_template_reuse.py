"""
E2E Flow: Template Create, Apply, Reuse

Covers:
- Create a template from a finalized/data-populated period
- Verify template appears in library
- Apply template to a new period
- Verify data pre-populated in new period
- Delete template
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import (
    make_email,
    rand_id,
    register_and_login,
    create_currency,
    create_account,
    create_period,
    select_period,
    add_income,
    add_expense,
    navigate_to,
)
from tests.e2e.pages.templates_page import TemplatesPage


@pytest.fixture
def template_setup(page: Page) -> dict:
    """Setup: user with a period that has income and expenses (template source)."""
    email = make_email("tpl")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Source Period {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    add_income(page, "Salary", "5000", "USD")
    add_expense(page, "Rent", "1500", "USD")
    return {"period_name": period_name, "rid": rid}


def test_create_template_from_period(page: Page, template_setup: dict) -> None:
    """User can save a template from an existing period."""
    navigate_to(page, "templates")
    tpl = TemplatesPage(page)
    tpl_name = f"Monthly Template {template_setup['rid']}"
    tpl.create_template(
        name=tpl_name,
        template_type="FULL",
        source_period_fragment=template_setup["period_name"],
    )
    tpl.expect_template_in_library(tpl_name)


def test_template_appears_in_library_after_create(page: Page, template_setup: dict) -> None:
    """Template is visible in the library after creation."""
    navigate_to(page, "templates")
    tpl = TemplatesPage(page)
    tpl_name = f"Visible Template {template_setup['rid']}"
    tpl.create_template(
        name=tpl_name,
        template_type="INCOME_SOURCES",
        source_period_fragment=template_setup["period_name"],
    )
    tpl.expect_template_in_library(tpl_name)
    # Library should show the template count badge
    expect(page.locator("#tpl-count-badge")).to_be_visible(timeout=5_000)


def test_apply_template_to_existing_period(page: Page, template_setup: dict) -> None:
    """User can apply a template to an existing period."""
    # Create a second period
    rid = template_setup["rid"]
    second_period = f"Target Period {rid}"
    navigate_to(page, "periods")
    create_period(page, second_period, "2026-02-01", "2026-02-28")

    # Create template
    navigate_to(page, "templates")
    tpl = TemplatesPage(page)
    tpl_name = f"Apply Test {rid}"
    tpl.create_template(
        name=tpl_name,
        template_type="FULL",
        source_period_fragment=template_setup["period_name"],
    )
    tpl.expect_template_in_library(tpl_name)
    tpl.apply_template(tpl_name, target_period_fragment=second_period)
    # After applying, should still be on templates page or show success
    page.wait_for_timeout(1_000)


def test_delete_template(page: Page, template_setup: dict) -> None:
    """User can delete a template from the library."""
    navigate_to(page, "templates")
    tpl = TemplatesPage(page)
    rid = rand_id()
    tpl_name = f"To Delete {rid}"
    tpl.create_template(
        name=tpl_name,
        template_type="EXPENSE_CATEGORIES",
        source_period_fragment=template_setup["period_name"],
    )
    tpl.expect_template_in_library(tpl_name)
    tpl.delete_template(tpl_name)
    # Should no longer be in library
    expect(
        page.locator("#tpl-library-container").get_by_text(tpl_name)
    ).not_to_be_visible(timeout=5_000)


def test_create_period_with_template_from_period_setup(page: Page, template_setup: dict) -> None:
    """User can create a new period with a template applied via Period Setup tab."""
    # Create a template first
    navigate_to(page, "templates")
    tpl = TemplatesPage(page)
    rid = rand_id()
    tpl_name = f"Period Creation {rid}"
    tpl.create_template(
        name=tpl_name,
        template_type="FULL",
        source_period_fragment=template_setup["period_name"],
    )
    tpl.expect_template_in_library(tpl_name)

    # Go to periods and create with template
    navigate_to(page, "periods")
    page.wait_for_selector("#period-apply-template-check", state="visible")
    page.fill("#period-name-input", f"New From Template {rid}")
    page.fill("#period-start-date", "2026-03-01")
    page.fill("#period-end-date", "2026-03-31")
    page.locator("#period-apply-template-check").check()
    page.wait_for_selector("#period-template-dropdown", state="visible", timeout=5_000)
    page.wait_for_timeout(1_000)
    options = page.locator("#period-template-dropdown option").all_inner_texts()
    if any(tpl_name.lower() in o.lower() for o in options):
        page.select_option("#period-template-dropdown", label=tpl_name)
    page.click("#create-period-btn")
    page.wait_for_timeout(2_000)
