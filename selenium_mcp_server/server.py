import os
from threading import RLock
from typing import Literal

from mcp.server.fastmcp import FastMCP, Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


mcp = FastMCP("selenium")

LocatorStrategy = Literal[
    "id",
    "name",
    "css",
    "xpath",
    "tag",
    "class",
    "link_text",
    "partial_link_text",
]

_LOCATORS = {
    "id": By.ID,
    "name": By.NAME,
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "tag": By.TAG_NAME,
    "class": By.CLASS_NAME,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT,
}


class SeleniumBrowser:
    def __init__(self) -> None:
        self._driver = None
        self._lock = RLock()

    def _get_driver(self):
        if self._driver is None:
            options = Options()
            headless = os.getenv("SELENIUM_HEADLESS", "true").lower()
            if headless not in {"0", "false", "no", "off"}:
                options.add_argument("--headless=new")
            self._driver = webdriver.Chrome(options=options)
        return self._driver

    def navigate(self, url: str) -> str:
        with self._lock:
            driver = self._get_driver()
            driver.get(url)
            return f"Navigated to {driver.current_url}"

    def title(self) -> str:
        with self._lock:
            return self._get_driver().title

    def page_text(self) -> str:
        with self._lock:
            return self._get_driver().find_element(By.TAG_NAME, "body").text

    def _find(self, strategy: str, selector: str):
        if strategy not in _LOCATORS:
            raise ValueError(f"Unsupported locator strategy: {strategy}")
        return self._get_driver().find_element(_LOCATORS[strategy], selector)

    def click(self, strategy: str, selector: str) -> str:
        with self._lock:
            self._find(strategy, selector).click()
            return f"Clicked element found by {strategy}: {selector}"

    def type_text(
        self, strategy: str, selector: str, text: str, clear: bool = True
    ) -> str:
        with self._lock:
            element = self._find(strategy, selector)
            if clear:
                element.clear()
            element.send_keys(text)
            return f"Entered text into element found by {strategy}: {selector}"

    def screenshot(self) -> Image:
        with self._lock:
            return Image(data=self._get_driver().get_screenshot_as_png(), format="png")

    def close(self) -> str:
        with self._lock:
            if self._driver is None:
                return "Browser is not running"
            try:
                self._driver.quit()
            finally:
                self._driver = None
            return "Browser closed"


browser = SeleniumBrowser()


@mcp.tool()
def navigate(url: str) -> str:
    """Open a URL in the Selenium-controlled browser."""
    return browser.navigate(url)


@mcp.tool()
def get_page_title() -> str:
    """Return the title of the current page."""
    return browser.title()


@mcp.tool()
def get_page_text() -> str:
    """Return the visible text of the current page."""
    return browser.page_text()


@mcp.tool()
def click_element(strategy: LocatorStrategy, selector: str) -> str:
    """Click the first element matching a Selenium locator."""
    return browser.click(strategy, selector)


@mcp.tool()
def type_text(
    strategy: LocatorStrategy, selector: str, text: str, clear: bool = True
) -> str:
    """Type text into the first element matching a Selenium locator."""
    return browser.type_text(strategy, selector, text, clear)


@mcp.tool()
def take_screenshot() -> Image:
    """Capture and return a PNG screenshot of the current page."""
    return browser.screenshot()


@mcp.tool()
def close_browser() -> str:
    """Close the current browser session."""
    return browser.close()


def main() -> None:
    mcp.run()
