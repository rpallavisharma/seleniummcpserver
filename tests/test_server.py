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
    def test_close_quits_and_resets_driver(self, chrome):
        chrome.return_value = self.driver
        self.browser.title()

        self.assertEqual(self.browser.close(), "Browser closed")
        self.driver.quit.assert_called_once()
        self.assertIsNone(self.browser._driver)


if __name__ == "__main__":
    unittest.main()
