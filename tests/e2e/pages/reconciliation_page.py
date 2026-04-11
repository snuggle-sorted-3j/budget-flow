"""Page Object Model for the Reconciliation tab."""
from playwright.sync_api import Page, expect


class ReconciliationPage:
    """Interactions with /dashboard/reconciliation."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_for_content(self, timeout: int = 10_000) -> None:
        """Wait for the reconciliation content to become visible (period must be selected)."""
        self.page.wait_for_selector(
            "#save-snapshots-btn", state="visible", timeout=timeout
        )

    def fill_snapshot(self, account_index: int, balance: str) -> None:
        """Fill a balance snapshot input at a given index."""
        inputs = self.page.locator("input[id*='snapshot-balance']")
        inputs.nth(account_index).fill(balance)

    def fill_first_snapshot(self, balance: str) -> None:
        """Fill the first snapshot input."""
        self.page.wait_for_selector("input[id*='snapshot-balance']", state="visible")
        self.page.locator("input[id*='snapshot-balance']").first.fill(balance)

    def save_snapshots(self) -> None:
        self.page.click("#save-snapshots-btn")
        self.page.wait_for_timeout(1_000)

    def expect_snapshot_saved(self, timeout: int = 5_000) -> None:
        expect(self.page.locator("#snapshot-message")).to_be_visible(timeout=timeout)

    def expect_recon_balanced(self, timeout: int = 8_000) -> None:
        expect(self.page.locator("#recon-summary-container")).to_contain_text(
            "BALANCED", timeout=timeout
        )

    def expect_recon_unbalanced(self, timeout: int = 8_000) -> None:
        container = self.page.locator("#recon-summary-container")
        expect(container).to_be_visible(timeout=timeout)
        # Look for any non-zero difference indicator
        text = container.inner_text()
        assert "BALANCED" not in text, f"Expected unbalanced, but found BALANCED in: {text}"

    def open_finalize_modal(self) -> None:
        self.page.locator("#open-finalize-modal-btn").click()
        self.page.wait_for_selector("#finalize-confirm-btn", state="visible", timeout=5_000)

    def confirm_finalize(self) -> None:
        self.page.click("#finalize-confirm-btn")
        self.page.wait_for_timeout(2_000)

    def cancel_finalize(self) -> None:
        self.page.click("#finalize-cancel-btn")
        self.page.wait_for_timeout(500)

    def expect_period_finalized(self, timeout: int = 8_000) -> None:
        expect(self.page.locator("#finalize-message")).to_be_visible(timeout=timeout)
        # The global period selector should show FINALIZED
        expect(self.page.locator("#global-period-selector")).to_contain_text(
            "FINALIZED", timeout=timeout
        )
