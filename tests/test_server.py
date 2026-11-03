import unittest
from unittest.mock import Mock, patch

from selenium.webdriver.common.by import By

from selenium_mcp_server.server import SeleniumBrowser


class SeleniumBrowserTests(unittest.TestCase):
    def setUp(self):
        self.browser = SeleniumBrowser()
        self.driver = Mock()
        self.driver.current_url = "https://example.com/"
        self.driver.title = "Example"
        self.driver.find_element.return_value = Mock(text="Example page")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_navigate_starts_driver_lazily(self, chrome):
        chrome.return_value = self.driver
        self.browser = SeleniumBrowser("chrome")

        result = self.browser.navigate("https://example.com")

        self.assertEqual(result, "Navigated to https://example.com/")
        chrome.assert_called_once()
        self.assertTrue(chrome.call_args.kwargs["options"].enable_bidi)
        self.driver.get.assert_called_once_with("https://example.com")

    @patch("selenium_mcp_server.server.webdriver.Safari")
    def test_safari_starts_without_headless_options(self, safari):
        safari.return_value = self.driver
        browser = SeleniumBrowser("safari")

        browser.title()

        safari.assert_called_once()

    @patch("selenium_mcp_server.server.webdriver.Edge")
    def test_edge_uses_headless_option_by_default(self, edge):
        edge.return_value = self.driver
        browser = SeleniumBrowser("edge")

        browser.title()

        options = edge.call_args.kwargs["options"]
        self.assertIn("--headless=new", options.arguments)

    @patch("selenium_mcp_server.server.webdriver.Firefox")
    def test_firefox_uses_headless_option_by_default(self, firefox):
        firefox.return_value = self.driver
        browser = SeleniumBrowser("firefox")

        browser.title()

        options = firefox.call_args.kwargs["options"]
        self.assertIn("-headless", options.arguments)

    def test_rejects_unsupported_browser(self):
        with self.assertRaisesRegex(ValueError, "Unsupported browser"):
            SeleniumBrowser("internet_explorer")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_page_text_uses_body_element(self, chrome):
        chrome.return_value = self.driver

        self.assertEqual(self.browser.page_text(), "Example page")
        self.driver.find_element.assert_called_once_with(By.TAG_NAME, "body")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_click_and_type_use_requested_locator(self, chrome):
        chrome.return_value = self.driver
        element = self.driver.find_element.return_value

        self.browser.click("id", "submit")
        self.browser.type_text("name", "query", "hello")

        self.assertEqual(
            self.driver.find_element.call_args_list,
            [unittest.mock.call(By.ID, "submit"), unittest.mock.call(By.NAME, "query")],
        )
        element.click.assert_called_once()
        element.clear.assert_called_once()
        element.send_keys.assert_called_once_with("hello")

    def test_rejects_unsupported_locator(self):
        with self.assertRaisesRegex(ValueError, "Unsupported locator strategy"):
            self.browser.click("invalid", "selector")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_navigation_history_and_current_url(self, chrome):
        chrome.return_value = self.driver

        self.assertIn("Back to", self.browser.navigate_history("back"))
        self.assertIn("Forward to", self.browser.navigate_history("forward"))
        self.assertIn("Refresh to", self.browser.navigate_history("refresh"))
        self.assertEqual(self.browser.current_url(), "https://example.com/")
        self.driver.back.assert_called_once()
        self.driver.forward.assert_called_once()
        self.driver.refresh.assert_called_once()

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_page_source_is_capped(self, chrome):
        chrome.return_value = self.driver
        self.driver.page_source = "<html>content</html>"

        self.assertEqual(self.browser.page_source(7), "<html>c")
        with self.assertRaisesRegex(ValueError, "max_chars"):
            self.browser.page_source(0)

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_find_elements_returns_element_state(self, chrome):
        chrome.return_value = self.driver
        element = Mock(
            tag_name="button",
            text="Continue",
        )
        element.is_displayed.return_value = True
        element.is_enabled.return_value = True
        element.is_selected.return_value = False
        self.driver.find_elements.return_value = [element]

        result = self.browser.find_elements("css", "button")

        self.driver.find_elements.assert_called_once_with(By.CSS_SELECTOR, "button")
        self.assertEqual(
            result,
            [
                {
                    "tag": "button",
                    "text": "Continue",
                    "displayed": True,
                    "enabled": True,
                    "selected": False,
                }
            ],
        )

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_select_option_requires_one_selector_mode(self, chrome):
        chrome.return_value = self.driver
        select_patcher = patch("selenium_mcp_server.server.Select")
        select = select_patcher.start()
        self.addCleanup(select_patcher.stop)

        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.browser.select_option("id", "country")
        self.browser.select_option("id", "country", label="Canada")
        select.return_value.select_by_visible_text.assert_called_once_with("Canada")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_window_switch_validates_handle(self, chrome):
        chrome.return_value = self.driver
        self.driver.window_handles = ["one", "two"]

        with self.assertRaisesRegex(ValueError, "Unknown window handle"):
            self.browser.switch_window("missing")
        self.assertEqual(self.browser.switch_window("two"), "Switched to window two")
        self.driver.switch_to.window.assert_called_once_with("two")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_add_cookie_requires_name_and_value(self, chrome):
        chrome.return_value = self.driver

        with self.assertRaisesRegex(ValueError, "name and value"):
            self.browser.add_cookie({"name": "session"})
        self.assertEqual(
            self.browser.add_cookie({"name": "session", "value": "abc"}),
            "Added cookie 'session'",
        )
        self.driver.add_cookie.assert_called_once_with(
            {"name": "session", "value": "abc"}
        )

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_set_timeout_uses_matching_webdriver_command(self, chrome):
        chrome.return_value = self.driver

        self.browser.set_timeout("page_load", 15)

        self.driver.set_page_load_timeout.assert_called_once_with(15)

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_rejects_timeout_above_limit(self, chrome):
        chrome.return_value = self.driver

        with self.assertRaisesRegex(ValueError, "between 0 and 120"):
            self.browser.set_timeout("script", 121)

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_find_shadow_element_uses_host_shadow_root(self, chrome):
        chrome.return_value = self.driver
        shadow_element = Mock(tag_name="button", text="Continue")
        shadow_element.is_displayed.return_value = True
        shadow_element.is_enabled.return_value = True
        shadow_element.is_selected.return_value = False
        self.driver.find_element.return_value.shadow_root.find_element.return_value = (
            shadow_element
        )

        result = self.browser.shadow_element("id", "host", "css", "button")

        self.driver.find_element.return_value.shadow_root.find_element.assert_called_once_with(
            By.CSS_SELECTOR, "button"
        )
        self.assertEqual(result["tag"], "button")
        self.assertEqual(result["text"], "Continue")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_type_shadow_text_clears_and_types(self, chrome):
        chrome.return_value = self.driver
        shadow_element = self.driver.find_element.return_value.shadow_root.find_element.return_value

        result = self.browser.type_shadow_text("css", "my-widget", "id", "query", "term")

        self.assertIn("shadow DOM", result)
        shadow_element.clear.assert_called_once()
        shadow_element.send_keys.assert_called_once_with("term")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_relative_locator_queries_near_anchor(self, chrome):
        chrome.return_value = self.driver
        candidate = Mock(tag_name="button", text="Save")
        candidate.is_displayed.return_value = True
        candidate.is_enabled.return_value = True
        candidate.is_selected.return_value = False
        self.driver.find_elements.return_value = [candidate]

        result = self.browser.find_relative_elements(
            "tag", "button", "near", "id", "reference", near_distance=25
        )

        relative = self.driver.find_elements.call_args.args[0]
        self.assertEqual(relative.filters[0]["kind"], "near")
        self.assertEqual(relative.filters[0]["args"][1], 25)
        self.assertEqual(result[0]["text"], "Save")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_execute_async_script_sets_timeout_and_passes_arguments(self, chrome):
        chrome.return_value = self.driver
        self.driver.execute_async_script.return_value = "done"

        result = self.browser.execute_async_script(
            "arguments[arguments.length - 1]('done')", ["value"], timeout=7
        )

        self.assertEqual(result, "done")
        self.driver.set_script_timeout.assert_called_once_with(7)
        self.driver.execute_async_script.assert_called_once_with(
            "arguments[arguments.length - 1]('done')", "value"
        )

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_active_element_and_parent_frame(self, chrome):
        chrome.return_value = self.driver
        active = self.driver.switch_to.active_element
        active.tag_name = "input"
        active.text = ""
        active.is_displayed.return_value = True
        active.is_enabled.return_value = True
        active.is_selected.return_value = False

        self.assertEqual(self.browser.active_element()["tag"], "input")
        self.assertEqual(self.browser.parent_frame(), "Switched to parent frame")
        self.driver.switch_to.parent_frame.assert_called_once()

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_window_position_get_and_set(self, chrome):
        chrome.return_value = self.driver
        self.driver.get_window_position.return_value = {"x": 1, "y": 2}
        self.driver.set_window_position.return_value = {"x": 30, "y": 40}

        self.assertEqual(self.browser.window_position(), {"x": 1, "y": 2})
        self.assertEqual(
            self.browser.set_window_position(30, 40), {"x": 30, "y": 40}
        )
        self.driver.set_window_position.assert_called_once_with(30, 40)

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_bidi_status_does_not_expose_websocket_url(self, chrome):
        chrome.return_value = self.driver
        self.driver.capabilities = {
            "browserName": "chrome",
            "webSocketUrl": "ws://localhost/private-session",
        }

        result = self.browser.bidi_status()

        self.assertEqual(result, {"browser": "chrome", "available": True})
        self.assertNotIn("webSocketUrl", result)

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_bidi_commands_require_bidi_capability(self, chrome):
        chrome.return_value = self.driver
        self.driver.capabilities = {"browserName": "chrome"}

        with self.assertRaisesRegex(RuntimeError, "BiDi is unavailable"):
            self.browser.bidi_user_contexts()

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_bidi_context_operations(self, chrome):
        chrome.return_value = self.driver
        self.driver.capabilities = {"browserName": "chrome", "webSocketUrl": "ws://"}
        self.driver.browser.get_user_contexts.return_value = ["default", "isolated"]
        self.driver.browser.create_user_context.return_value = "isolated"
        self.driver.browsing_context.navigate.return_value = {"navigation": "done"}

        self.assertEqual(self.browser.bidi_user_contexts(), ["default", "isolated"])
        self.assertEqual(self.browser.bidi_create_user_context(), "isolated")
        self.assertEqual(
            self.browser.bidi_navigate("context-1", "https://example.com"),
            {"navigation": "done"},
        )
        self.driver.browser.remove_user_context.assert_not_called()
        self.assertEqual(
            self.browser.bidi_remove_user_context("isolated"),
            "Removed BiDi user context isolated",
        )
        self.driver.browser.remove_user_context.assert_called_once_with("isolated")

    @patch("selenium_mcp_server.server.webdriver.Chrome")
    def test_close_quits_and_resets_driver(self, chrome):
        chrome.return_value = self.driver
        self.browser.title()

        self.assertEqual(self.browser.close(), "Browser closed")
        self.driver.quit.assert_called_once()
        self.assertIsNone(self.browser._driver)


if __name__ == "__main__":
    unittest.main()
