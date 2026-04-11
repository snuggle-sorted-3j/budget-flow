"""Page Object Model for the Templates tab."""
from playwright.sync_api import Page, expect


class TemplatesPage:
    """Interactions with /dashboard/templates."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def create_template(
        self,
        name: str,
        template_type: str = "FULL",
        source_period_fragment: str = "",
        is_default: bool = False,
    ) -> None:
        """Fill and submit the Create Template form."""
        self.page.wait_for_selector("#tpl-name", state="visible", timeout=10_000)
        self.page.fill("#tpl-name", name)
        self.page.locator(f"input[value='{template_type}']").check()
        if source_period_fragment:
            self.page.wait_for_timeout(500)
            options = self.page.locator("#tpl-source-period option").all_inner_texts()
            target = next(
                (o for o in options if source_period_fragment.lower() in o.lower()), None
            )
            if target:
                self.page.select_option("#tpl-source-period", label=target)
        if is_default:
            self.page.locator("#tpl-is-default").check()
        self.page.click("#tpl-save-btn")
        self.page.wait_for_timeout(1_500)

    def expect_template_in_library(self, name: str) -> None:
        expect(
            self.page.locator("#tpl-library-container").get_by_text(name)
        ).to_be_visible(timeout=10_000)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#tpl-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def apply_template(
        self,
        template_name: str,
        target_period_fragment: str,
    ) -> None:
        """Click Apply on a template card and apply to a period."""
        self.page.locator("#tpl-library-container").get_by_text(
            template_name
        ).first.locator("xpath=ancestor::*[contains(@class,'card')]").get_by_role(
            "button", name="Apply"
        ).click()
        self.page.wait_for_selector("#tpl-apply-target-period", state="visible", timeout=5_000)
        self.page.wait_for_timeout(500)
        options = self.page.locator("#tpl-apply-target-period option").all_inner_texts()
        target = next(
            (o for o in options if target_period_fragment.lower() in o.lower()), None
        )
        if target:
            self.page.select_option("#tpl-apply-target-period", label=target)
        self.page.click("#tpl-apply-confirm")
        self.page.wait_for_timeout(2_000)

    def delete_template(self, template_name: str) -> None:
        """Delete a template from the library."""
        self.page.locator("#tpl-library-container").get_by_text(
            template_name
        ).first.locator("xpath=ancestor::*[contains(@class,'card')]").get_by_role(
            "button", name="Delete"
        ).click()
        self.page.wait_for_selector("#tpl-delete-confirm", state="visible", timeout=5_000)
        self.page.click("#tpl-delete-confirm")
        self.page.wait_for_timeout(1_000)
