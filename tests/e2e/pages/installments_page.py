"""Page Object Model for the Installments Tracking tab."""
from playwright.sync_api import Page, expect


class InstallmentsPage:
    """Interactions with /dashboard/installments."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def add_installment(
        self,
        name: str,
        total_price: str,
        currency_ticker: str = "USD",
        start_period_fragment: str = "",
        monthly_payment: str = "",
        months: str = "",
        notes: str = "",
    ) -> None:
        """Fill and submit the Add Installment Plan form."""
        self.page.wait_for_selector("#inst-name", state="visible", timeout=10_000)
        self.page.fill("#inst-name", name)
        self.page.fill("#inst-total", total_price)
        self.page.wait_for_selector(
            f"#inst-currency option:has-text('{currency_ticker}')", state="attached"
        )
        self.page.select_option("#inst-currency", label=currency_ticker)
        if start_period_fragment:
            self.page.wait_for_timeout(500)
            options = self.page.locator("#inst-start-period option").all_inner_texts()
            target = next(
                (o for o in options if start_period_fragment.lower() in o.lower()), None
            )
            if target:
                self.page.select_option("#inst-start-period", label=target)
        if monthly_payment:
            self.page.fill("#inst-monthly", monthly_payment)
        if months:
            self.page.fill("#inst-months", months)
        if notes:
            self.page.fill("#inst-notes", notes)
        self.page.click("#add-inst-btn")
        self.page.wait_for_timeout(1_500)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#inst-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def expect_installment_in_active_list(self, name: str) -> None:
        expect(
            self.page.locator("#active-installments-container").get_by_text(name)
        ).to_be_visible(timeout=10_000)

    def expect_installment_paid_off(self, name: str) -> None:
        expect(
            self.page.locator("#paid-off-installments-container").get_by_text(name)
        ).to_be_visible(timeout=10_000)

    def open_payment_modal_for(self, installment_name: str) -> None:
        """Click the 'Pay' button for a given installment."""
        self.page.locator("#active-installments-container").get_by_text(
            installment_name
        ).first.locator("xpath=ancestor::*[contains(@class,'card')]").get_by_role(
            "button", name="Pay"
        ).click()
        self.page.wait_for_selector("#payment-amount", state="visible", timeout=5_000)

    def fill_payment(self, amount: str, date: str) -> None:
        """Fill and submit the payment modal."""
        self.page.fill("#payment-amount", amount)
        self.page.fill("#payment-date", date)
        self.page.click("#payment-save-btn")
        self.page.wait_for_timeout(1_500)

    def delete_installment(self, installment_name: str) -> None:
        """Delete an installment from the active list."""
        self.page.locator("#active-installments-container").get_by_text(
            installment_name
        ).first.locator("xpath=ancestor::*[contains(@class,'card')]").get_by_role(
            "button", name="Delete"
        ).click()
        self.page.locator("#inst-delete-confirm").click()
        self.page.wait_for_timeout(1_000)
