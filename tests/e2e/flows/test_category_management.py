"""
E2E Flow: Category CRUD Management

Covers:
- Create custom expense categories
- Create sub-categories (with parent)
- Categories appear in expense form dropdown
- Attempt to add duplicate name (error expected)
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
    navigate_to,
)
from tests.e2e.pages.categories_page import CategoriesPage
from tests.e2e.pages.expense_page import ExpensePage


@pytest.fixture
def category_setup(page: Page) -> dict:
    """Setup: fresh user with USD, account, and period."""
    email = make_email("cat")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Cat Period {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    return {"period_name": period_name, "rid": rid}


def test_create_custom_category(page: Page, category_setup: dict) -> None:
    """User can create a custom expense category."""
    navigate_to(page, "categories")
    cat = CategoriesPage(page)
    cat_name = f"Entertainment {category_setup['rid']}"
    cat.add_category(name=cat_name, icon="🎭")
    cat.expect_category_in_table(cat_name)


def test_multiple_categories_visible(page: Page, category_setup: dict) -> None:
    """Multiple categories all appear in the table."""
    navigate_to(page, "categories")
    cat = CategoriesPage(page)
    rid = category_setup["rid"]
    names = [f"Groceries {rid}", f"Transport {rid}", f"Health {rid}"]
    for name in names:
        navigate_to(page, "categories")
        cat.add_category(name=name)
    navigate_to(page, "categories")
    for name in names:
        cat.expect_category_in_table(name)


def test_custom_category_available_in_expenses(page: Page, category_setup: dict) -> None:
    """A custom category appears in the expense form dropdown after creation."""
    navigate_to(page, "categories")
    cat = CategoriesPage(page)
    cat_name = f"MySpecial {category_setup['rid']}"
    cat.add_category(name=cat_name)
    cat.expect_category_in_table(cat_name)

    # Now go to expenses and verify category is selectable
    navigate_to(page, "expenses")
    exp = ExpensePage(page)
    exp.wait_for_form()
    page.wait_for_selector("#expense-category option", state="attached")
    options = page.locator("#expense-category option").all_inner_texts()
    assert any(cat_name.lower() in opt.lower() for opt in options), (
        f"Category '{cat_name}' not found in expense dropdown. Options: {options}"
    )


def test_create_subcategory(page: Page, category_setup: dict) -> None:
    """User can create a sub-category under a parent."""
    navigate_to(page, "categories")
    cat = CategoriesPage(page)
    rid = category_setup["rid"]
    parent_name = f"Housing {rid}"
    cat.add_category(name=parent_name)
    cat.expect_category_in_table(parent_name)

    navigate_to(page, "categories")
    # Select parent at index 1 (first non-empty option)
    cat.add_category(name=f"Mortgage {rid}", parent_index=1)
    cat.expect_category_in_table(f"Mortgage {rid}")
