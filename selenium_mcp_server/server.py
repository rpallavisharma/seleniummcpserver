import os
from dataclasses import asdict, is_dataclass
from threading import RLock
from typing import Literal

from mcp.server.fastmcp import FastMCP, Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


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

_BROWSERS = {"chrome", "firefox", "edge", "safari"}
_RELATIVE_RELATIONS = {
    "above": "above",
    "below": "below",
    "left": "to_left_of",
    "right": "to_right_of",
    "near": "near",
    "straight_above": "straight_above",
    "straight_below": "straight_below",
    "straight_left": "straight_left_of",
    "straight_right": "straight_right_of",
}
_KEYS = {
    name: getattr(Keys, name)
    for name in (
        "ENTER",
        "RETURN",
        "TAB",
        "ESCAPE",
        "SPACE",
        "BACKSPACE",
        "DELETE",
        "ARROW_UP",
        "ARROW_DOWN",
        "ARROW_LEFT",
        "ARROW_RIGHT",
        "HOME",
        "END",
        "PAGE_UP",
        "PAGE_DOWN",
    )
}


class SeleniumBrowser:
    def __init__(self, browser_name: str | None = None) -> None:
        self._browser_name = (
            browser_name or os.getenv("SELENIUM_BROWSER", "chrome")
        ).strip().lower()
        if self._browser_name not in _BROWSERS:
            supported = ", ".join(sorted(_BROWSERS))
            raise ValueError(
                f"Unsupported browser: {self._browser_name}. Choose from: {supported}"
            )
        self._driver = None
        self._lock = RLock()

    def _get_driver(self):
        if self._driver is None:
            headless = os.getenv("SELENIUM_HEADLESS", "true").lower()
            if self._browser_name == "chrome":
                options = ChromeOptions()
                options.enable_bidi = True
                if headless not in {"0", "false", "no", "off"}:
                    options.add_argument("--headless=new")
                self._driver = webdriver.Chrome(options=options)
            elif self._browser_name == "firefox":
                options = FirefoxOptions()
                options.enable_bidi = True
                if headless not in {"0", "false", "no", "off"}:
                    options.add_argument("-headless")
                self._driver = webdriver.Firefox(options=options)
            elif self._browser_name == "edge":
                options = EdgeOptions()
                options.enable_bidi = True
                if headless not in {"0", "false", "no", "off"}:
                    options.add_argument("--headless=new")
                self._driver = webdriver.Edge(options=options)
            else:
                options = SafariOptions()
                options.enable_bidi = True
                self._driver = webdriver.Safari(options=options)
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

    def page_source(self, max_chars: int = 20000) -> str:
        if not 1 <= max_chars <= 100000:
            raise ValueError("max_chars must be between 1 and 100000")
        with self._lock:
            return self._get_driver().page_source[:max_chars]

    def current_url(self) -> str:
        with self._lock:
            return self._get_driver().current_url

    def navigate_history(self, direction: Literal["back", "forward", "refresh"]) -> str:
        with self._lock:
            driver = self._get_driver()
            {"back": driver.back, "forward": driver.forward, "refresh": driver.refresh}[
                direction
            ]()
            return f"{direction.capitalize()} to {driver.current_url}"

    def _find(self, strategy: str, selector: str):
        if strategy not in _LOCATORS:
            raise ValueError(f"Unsupported locator strategy: {strategy}")
        return self._get_driver().find_element(_LOCATORS[strategy], selector)

    def find_elements(
        self, strategy: str, selector: str, limit: int = 50
    ) -> list[dict]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        with self._lock:
            elements = self._get_driver().find_elements(
                _LOCATORS[self._validate_locator(strategy)], selector
            )[:limit]
            return [
                {
                    "tag": element.tag_name,
                    "text": element.text,
                    "displayed": element.is_displayed(),
                    "enabled": element.is_enabled(),
                    "selected": element.is_selected(),
                }
                for element in elements
            ]

    @staticmethod
    def _validate_locator(strategy: str) -> str:
        if strategy not in _LOCATORS:
            raise ValueError(f"Unsupported locator strategy: {strategy}")
        return strategy

    @staticmethod
    def _element_summary(element) -> dict:
        return {
            "tag": element.tag_name,
            "text": element.text,
            "displayed": element.is_displayed(),
            "enabled": element.is_enabled(),
            "selected": element.is_selected(),
        }

    def shadow_element(
        self,
        host_strategy: str,
        host_selector: str,
        strategy: str,
        selector: str,
    ) -> dict:
        with self._lock:
            host = self._find(host_strategy, host_selector)
            element = host.shadow_root.find_element(
                _LOCATORS[self._validate_locator(strategy)], selector
            )
            return self._element_summary(element)

    def click_shadow_element(
        self, host_strategy: str, host_selector: str, strategy: str, selector: str
    ) -> str:
        with self._lock:
            host = self._find(host_strategy, host_selector)
            element = host.shadow_root.find_element(
                _LOCATORS[self._validate_locator(strategy)], selector
            )
            element.click()
            return "Clicked element in shadow DOM"

    def type_shadow_text(
        self,
        host_strategy: str,
        host_selector: str,
        strategy: str,
        selector: str,
        text: str,
        clear: bool = True,
    ) -> str:
        with self._lock:
            host = self._find(host_strategy, host_selector)
            element = host.shadow_root.find_element(
                _LOCATORS[self._validate_locator(strategy)], selector
            )
            if clear:
                element.clear()
            element.send_keys(text)
            return "Entered text into element in shadow DOM"

    def find_relative_elements(
        self,
        strategy: str,
        selector: str,
        relation: str,
        anchor_strategy: str,
        anchor_selector: str,
        near_distance: int = 50,
        limit: int = 50,
    ) -> list[dict]:
        if relation not in _RELATIVE_RELATIONS:
            raise ValueError(
                f"Unsupported relative relation: {relation}. "
                f"Choose from: {', '.join(_RELATIVE_RELATIONS)}"
            )
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if relation == "near" and near_distance <= 0:
            raise ValueError("near_distance must be positive")
        with self._lock:
            driver = self._get_driver()
            anchor = self._find(anchor_strategy, anchor_selector)
            relative = locate_with(
                _LOCATORS[self._validate_locator(strategy)], selector
            )
            relation_method = getattr(relative, _RELATIVE_RELATIONS[relation])
            if relation == "near":
                relation_method(anchor, near_distance)
            else:
                relation_method(anchor)
            return [
                self._element_summary(element)
                for element in driver.find_elements(relative)[:limit]
            ]

    def element_attribute(self, strategy: str, selector: str, attribute: str) -> str | None:
        with self._lock:
            return self._find(strategy, selector).get_attribute(attribute)

    def element_property(self, strategy: str, selector: str, name: str):
        with self._lock:
            return self._find(strategy, selector).get_property(name)

    def element_css_value(self, strategy: str, selector: str, property_name: str) -> str:
        with self._lock:
            return self._find(strategy, selector).value_of_css_property(property_name)

    def element_rect(self, strategy: str, selector: str) -> dict:
        with self._lock:
            return self._find(strategy, selector).rect

    def element_screenshot(self, strategy: str, selector: str) -> Image:
        with self._lock:
            return Image(
                data=self._find(strategy, selector).screenshot_as_png, format="png"
            )

    def element_state(self, strategy: str, selector: str) -> dict:
        with self._lock:
            element = self._find(strategy, selector)
            return {
                "displayed": element.is_displayed(),
                "enabled": element.is_enabled(),
                "selected": element.is_selected(),
            }

    def click(self, strategy: str, selector: str) -> str:
        with self._lock:
            self._find(strategy, selector).click()
            return f"Clicked element found by {strategy}: {selector}"

    def submit(self, strategy: str, selector: str) -> str:
        with self._lock:
            self._find(strategy, selector).submit()
            return f"Submitted element found by {strategy}: {selector}"

    def clear_element(self, strategy: str, selector: str) -> str:
        with self._lock:
            self._find(strategy, selector).clear()
            return f"Cleared element found by {strategy}: {selector}"

    def type_text(
        self, strategy: str, selector: str, text: str, clear: bool = True
    ) -> str:
        with self._lock:
            element = self._find(strategy, selector)
            if clear:
                element.clear()
            element.send_keys(text)
            return f"Entered text into element found by {strategy}: {selector}"

    def press_key(self, strategy: str, selector: str, key: str) -> str:
        normalized_key = key.strip().upper()
        if normalized_key not in _KEYS:
            raise ValueError(f"Unsupported key: {key}. Choose from: {', '.join(_KEYS)}")
        with self._lock:
            self._find(strategy, selector).send_keys(_KEYS[normalized_key])
            return f"Pressed {normalized_key} in element found by {strategy}: {selector}"

    def select_option(
        self,
        strategy: str,
        selector: str,
        label: str | None = None,
        value: str | None = None,
        index: int | None = None,
    ) -> str:
        if sum(option is not None for option in (label, value, index)) != 1:
            raise ValueError("Provide exactly one of label, value, or index")
        with self._lock:
            select = Select(self._find(strategy, selector))
            if label is not None:
                select.select_by_visible_text(label)
                chosen = f"label '{label}'"
            elif value is not None:
                select.select_by_value(value)
                chosen = f"value '{value}'"
            else:
                select.select_by_index(index)
                chosen = f"index {index}"
            return f"Selected option by {chosen}"

    def hover(self, strategy: str, selector: str) -> str:
        with self._lock:
            element = self._find(strategy, selector)
            ActionChains(self._get_driver()).move_to_element(element).perform()
            return f"Hovered over element found by {strategy}: {selector}"

    def click_action(
        self, strategy: str, selector: str, action: Literal["double", "right"]
    ) -> str:
        with self._lock:
            element = self._find(strategy, selector)
            actions = ActionChains(self._get_driver())
            if action == "double":
                actions.double_click(element)
            else:
                actions.context_click(element)
            actions.perform()
            return f"Performed {action} click on element found by {strategy}: {selector}"

    def drag_and_drop(
        self,
        source_strategy: str,
        source_selector: str,
        target_strategy: str,
        target_selector: str,
    ) -> str:
        with self._lock:
            source = self._find(source_strategy, source_selector)
            target = self._find(target_strategy, target_selector)
            ActionChains(self._get_driver()).drag_and_drop(source, target).perform()
            return "Dragged source element onto target element"

    def scroll_to_element(self, strategy: str, selector: str) -> str:
        with self._lock:
            element = self._find(strategy, selector)
            self._get_driver().execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            return f"Scrolled to element found by {strategy}: {selector}"

    def scroll_page(self, x: int = 0, y: int = 0) -> str:
        with self._lock:
            self._get_driver().execute_script("window.scrollBy(arguments[0], arguments[1]);", x, y)
            return f"Scrolled page by ({x}, {y})"

    def wait_for_element(
        self, strategy: str, selector: str, timeout: float = 10, visible: bool = True
    ) -> str:
        if not 0 < timeout <= 120:
            raise ValueError("timeout must be greater than 0 and at most 120 seconds")
        with self._lock:
            locator = (_LOCATORS[self._validate_locator(strategy)], selector)
            condition = (
                EC.visibility_of_element_located(locator)
                if visible
                else EC.presence_of_element_located(locator)
            )
            WebDriverWait(self._get_driver(), timeout).until(condition)
            return f"Element found by {strategy}: {selector}"

    def wait_for_title(self, title: str, timeout: float = 10) -> str:
        if not 0 < timeout <= 120:
            raise ValueError("timeout must be greater than 0 and at most 120 seconds")
        with self._lock:
            WebDriverWait(self._get_driver(), timeout).until(EC.title_is(title))
            return f"Page title is '{title}'"

    def wait_for_url(self, url_fragment: str, timeout: float = 10) -> str:
        if not 0 < timeout <= 120:
            raise ValueError("timeout must be greater than 0 and at most 120 seconds")
        with self._lock:
            WebDriverWait(self._get_driver(), timeout).until(
                EC.url_contains(url_fragment)
            )
            return f"Current URL contains '{url_fragment}'"

    def execute_script(self, script: str, arguments: list | None = None):
        with self._lock:
            return self._get_driver().execute_script(script, *(arguments or []))

    def execute_async_script(
        self, script: str, arguments: list | None = None, timeout: float = 10
    ):
        if not 0 < timeout <= 120:
            raise ValueError("timeout must be greater than 0 and at most 120 seconds")
        with self._lock:
            driver = self._get_driver()
            driver.set_script_timeout(timeout)
            return driver.execute_async_script(script, *(arguments or []))

    def active_element(self) -> dict:
        with self._lock:
            return self._element_summary(self._get_driver().switch_to.active_element)

    def parent_frame(self) -> str:
        with self._lock:
            self._get_driver().switch_to.parent_frame()
            return "Switched to parent frame"

    def window_handles(self) -> dict:
        with self._lock:
            driver = self._get_driver()
            return {
                "current": driver.current_window_handle,
                "handles": driver.window_handles,
            }

    def open_window(self, window_type: Literal["tab", "window"], url: str | None = None) -> str:
        with self._lock:
            driver = self._get_driver()
            driver.switch_to.new_window(window_type)
            if url:
                driver.get(url)
            return driver.current_window_handle

    def switch_window(self, handle: str) -> str:
        with self._lock:
            driver = self._get_driver()
            if handle not in driver.window_handles:
                raise ValueError("Unknown window handle")
            driver.switch_to.window(handle)
            return f"Switched to window {handle}"

    def close_window(self) -> str:
        with self._lock:
            driver = self._get_driver()
            driver.close()
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[-1])
                return "Closed current window and switched to remaining window"
            self._driver = None
            return "Closed last window; browser session ended"

    def switch_frame(self, strategy: str, selector: str) -> str:
        with self._lock:
            self._get_driver().switch_to.frame(self._find(strategy, selector))
            return f"Switched to frame found by {strategy}: {selector}"

    def default_content(self) -> str:
        with self._lock:
            self._get_driver().switch_to.default_content()
            return "Switched to default content"

    def alert_text(self) -> str:
        with self._lock:
            return self._get_driver().switch_to.alert.text

    def handle_alert(self, action: Literal["accept", "dismiss"], text: str | None = None) -> str:
        with self._lock:
            alert = self._get_driver().switch_to.alert
            if text is not None:
                alert.send_keys(text)
            getattr(alert, action)()
            return f"Alert {action}ed"

    def cookies(self) -> list[dict]:
        with self._lock:
            return self._get_driver().get_cookies()

    def add_cookie(self, cookie: dict) -> str:
        if "name" not in cookie or "value" not in cookie:
            raise ValueError("Cookie must include name and value")
        with self._lock:
            self._get_driver().add_cookie(cookie)
            return f"Added cookie '{cookie['name']}'"

    def delete_cookie(self, name: str | None = None) -> str:
        with self._lock:
            driver = self._get_driver()
            if name is None:
                driver.delete_all_cookies()
                return "Deleted all cookies"
            driver.delete_cookie(name)
            return f"Deleted cookie '{name}'"

    def set_window_size(self, width: int, height: int) -> str:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        with self._lock:
            self._get_driver().set_window_size(width, height)
            return f"Set browser window size to {width}x{height}"

    def window_position(self) -> dict:
        with self._lock:
            return self._get_driver().get_window_position()

    def set_window_position(self, x: int, y: int) -> dict:
        with self._lock:
            return self._get_driver().set_window_position(x, y)

    def maximize_window(self) -> str:
        with self._lock:
            self._get_driver().maximize_window()
            return "Maximized browser window"

    def fullscreen_window(self) -> str:
        with self._lock:
            self._get_driver().fullscreen_window()
            return "Set browser window to fullscreen"

    def set_timeout(self, timeout_type: Literal["implicit", "page_load", "script"], seconds: float) -> str:
        if not 0 <= seconds <= 120:
            raise ValueError("seconds must be between 0 and 120")
        with self._lock:
            driver = self._get_driver()
            if timeout_type == "implicit":
                driver.implicitly_wait(seconds)
            elif timeout_type == "page_load":
                driver.set_page_load_timeout(seconds)
            else:
                driver.set_script_timeout(seconds)
            return f"Set {timeout_type} timeout to {seconds} seconds"

    def _bidi_driver(self):
        driver = self._get_driver()
        if not driver.capabilities.get("webSocketUrl"):
            raise RuntimeError(
                f"WebDriver BiDi is unavailable for {self._browser_name}; "
                "the selected browser and driver must support BiDi."
            )
        return driver

    def bidi_status(self) -> dict:
        with self._lock:
            driver = self._get_driver()
            return {
                "browser": driver.capabilities.get("browserName", self._browser_name),
                "available": bool(driver.capabilities.get("webSocketUrl")),
            }

    def bidi_context_tree(self, max_depth: int = 5) -> list[dict]:
        if not 0 <= max_depth <= 20:
            raise ValueError("max_depth must be between 0 and 20")
        with self._lock:
            contexts = self._bidi_driver().browsing_context.get_tree(
                max_depth=max_depth
            )
            return [asdict(item) if is_dataclass(item) else item for item in contexts]

    def bidi_user_contexts(self) -> list[str]:
        with self._lock:
            return self._bidi_driver().browser.get_user_contexts()

    def bidi_create_user_context(self) -> str:
        with self._lock:
            return self._bidi_driver().browser.create_user_context()

    def bidi_remove_user_context(self, user_context: str) -> str:
        with self._lock:
            self._bidi_driver().browser.remove_user_context(user_context)
            return f"Removed BiDi user context {user_context}"

    def bidi_navigate(self, context: str, url: str) -> dict:
        with self._lock:
            result = self._bidi_driver().browsing_context.navigate(
                context=context, url=url, wait="complete"
            )
            return result if isinstance(result, dict) else {"result": str(result)}

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
def get_page_source(max_chars: int = 20000) -> str:
    """Return the current page HTML source, capped to max_chars."""
    return browser.page_source(max_chars)


@mcp.tool()
def get_current_url() -> str:
    """Return the current browser URL."""
    return browser.current_url()


@mcp.tool()
def navigate_history(direction: Literal["back", "forward", "refresh"]) -> str:
    """Go back, go forward, or refresh the current page."""
    return browser.navigate_history(direction)


@mcp.tool()
def find_elements(strategy: LocatorStrategy, selector: str, limit: int = 50) -> list[dict]:
    """Find matching elements and return basic state, up to 200 results."""
    return browser.find_elements(strategy, selector, limit)


@mcp.tool()
def get_element_attribute(strategy: LocatorStrategy, selector: str, attribute: str) -> str | None:
    """Return an element attribute value."""
    return browser.element_attribute(strategy, selector, attribute)


@mcp.tool()
def get_element_property(strategy: LocatorStrategy, selector: str, name: str):
    """Return a JavaScript property from the matched element."""
    return browser.element_property(strategy, selector, name)


@mcp.tool()
def get_element_css_value(strategy: LocatorStrategy, selector: str, property_name: str) -> str:
    """Return a computed CSS property value from the matched element."""
    return browser.element_css_value(strategy, selector, property_name)


@mcp.tool()
def get_element_rect(strategy: LocatorStrategy, selector: str) -> dict:
    """Return the matched element's position and dimensions."""
    return browser.element_rect(strategy, selector)


@mcp.tool()
def take_element_screenshot(strategy: LocatorStrategy, selector: str) -> Image:
    """Capture a PNG screenshot of the matched element."""
    return browser.element_screenshot(strategy, selector)


@mcp.tool()
def get_element_state(strategy: LocatorStrategy, selector: str) -> dict:
    """Return whether an element is displayed, enabled, and selected."""
    return browser.element_state(strategy, selector)


@mcp.tool()
def find_shadow_element(
    host_strategy: LocatorStrategy,
    host_selector: str,
    strategy: LocatorStrategy,
    selector: str,
) -> dict:
    """Find an element inside the shadow root of a matching host."""
    return browser.shadow_element(host_strategy, host_selector, strategy, selector)


@mcp.tool()
def click_shadow_element(
    host_strategy: LocatorStrategy,
    host_selector: str,
    strategy: LocatorStrategy,
    selector: str,
) -> str:
    """Click an element inside the shadow root of a matching host."""
    return browser.click_shadow_element(host_strategy, host_selector, strategy, selector)


@mcp.tool()
def type_shadow_text(
    host_strategy: LocatorStrategy,
    host_selector: str,
    strategy: LocatorStrategy,
    selector: str,
    text: str,
    clear: bool = True,
) -> str:
    """Type into an element inside the shadow root of a matching host."""
    return browser.type_shadow_text(
        host_strategy, host_selector, strategy, selector, text, clear
    )


@mcp.tool()
def find_relative_elements(
    strategy: LocatorStrategy,
    selector: str,
    relation: Literal[
        "above",
        "below",
        "left",
        "right",
        "near",
        "straight_above",
        "straight_below",
        "straight_left",
        "straight_right",
    ],
    anchor_strategy: LocatorStrategy,
    anchor_selector: str,
    near_distance: int = 50,
    limit: int = 50,
) -> list[dict]:
    """Find elements positioned relative to an anchor element."""
    return browser.find_relative_elements(
        strategy,
        selector,
        relation,
        anchor_strategy,
        anchor_selector,
        near_distance,
        limit,
    )


@mcp.tool()
def click_element(strategy: LocatorStrategy, selector: str) -> str:
    """Click the first element matching a Selenium locator."""
    return browser.click(strategy, selector)


@mcp.tool()
def submit_element(strategy: LocatorStrategy, selector: str) -> str:
    """Submit the form associated with the matched element."""
    return browser.submit(strategy, selector)


@mcp.tool()
def clear_element(strategy: LocatorStrategy, selector: str) -> str:
    """Clear the first matching input or editable element."""
    return browser.clear_element(strategy, selector)


@mcp.tool()
def type_text(
    strategy: LocatorStrategy, selector: str, text: str, clear: bool = True
) -> str:
    """Type text into the first element matching a Selenium locator."""
    return browser.type_text(strategy, selector, text, clear)


@mcp.tool()
def press_key(strategy: LocatorStrategy, selector: str, key: str) -> str:
    """Send a supported keyboard key to the first matching element."""
    return browser.press_key(strategy, selector, key)


@mcp.tool()
def select_option(
    strategy: LocatorStrategy,
    selector: str,
    label: str | None = None,
    value: str | None = None,
    index: int | None = None,
) -> str:
    """Select an option in a <select> by exactly one of label, value, or index."""
    return browser.select_option(strategy, selector, label, value, index)


@mcp.tool()
def hover_element(strategy: LocatorStrategy, selector: str) -> str:
    """Move the pointer over the first matching element."""
    return browser.hover(strategy, selector)


@mcp.tool()
def click_action(
    strategy: LocatorStrategy, selector: str, action: Literal["double", "right"]
) -> str:
    """Double-click or right-click the first matching element."""
    return browser.click_action(strategy, selector, action)


@mcp.tool()
def drag_and_drop(
    source_strategy: LocatorStrategy,
    source_selector: str,
    target_strategy: LocatorStrategy,
    target_selector: str,
) -> str:
    """Drag one matched element onto another."""
    return browser.drag_and_drop(
        source_strategy, source_selector, target_strategy, target_selector
    )


@mcp.tool()
def scroll_to_element(strategy: LocatorStrategy, selector: str) -> str:
    """Scroll the page until the first matching element is centered."""
    return browser.scroll_to_element(strategy, selector)


@mcp.tool()
def scroll_page(x: int = 0, y: int = 0) -> str:
    """Scroll the page by horizontal and vertical pixel offsets."""
    return browser.scroll_page(x, y)


@mcp.tool()
def wait_for_element(
    strategy: LocatorStrategy, selector: str, timeout: float = 10, visible: bool = True
) -> str:
    """Wait for an element to be present or visible; timeout is capped at 120 seconds."""
    return browser.wait_for_element(strategy, selector, timeout, visible)


@mcp.tool()
def wait_for_title(title: str, timeout: float = 10) -> str:
    """Wait for the page title to equal the supplied text."""
    return browser.wait_for_title(title, timeout)


@mcp.tool()
def wait_for_url(url_fragment: str, timeout: float = 10) -> str:
    """Wait until the current URL contains the supplied text."""
    return browser.wait_for_url(url_fragment, timeout)


@mcp.tool()
def execute_javascript(script: str, arguments: list | None = None):
    """Execute JavaScript in the current page with optional JSON-serializable arguments."""
    return browser.execute_script(script, arguments)


@mcp.tool()
def execute_async_javascript(
    script: str, arguments: list | None = None, timeout: float = 10
):
    """Execute async JavaScript; call Selenium's final callback argument with the result."""
    return browser.execute_async_script(script, arguments, timeout)


@mcp.tool()
def get_active_element() -> dict:
    """Return basic information about the currently focused element."""
    return browser.active_element()


@mcp.tool()
def switch_to_parent_frame() -> str:
    """Switch focus from the current frame to its parent frame."""
    return browser.parent_frame()


@mcp.tool()
def get_windows() -> dict:
    """Return the current window handle and all open window handles."""
    return browser.window_handles()


@mcp.tool()
def open_window(window_type: Literal["tab", "window"] = "tab", url: str | None = None) -> str:
    """Open and switch to a new tab or window, optionally navigating to a URL."""
    return browser.open_window(window_type, url)


@mcp.tool()
def switch_window(handle: str) -> str:
    """Switch to an existing window or tab by handle."""
    return browser.switch_window(handle)


@mcp.tool()
def close_window() -> str:
    """Close the current window or tab, ending the session if it was the last."""
    return browser.close_window()


@mcp.tool()
def switch_frame(strategy: LocatorStrategy, selector: str) -> str:
    """Switch into the first matching frame or iframe."""
    return browser.switch_frame(strategy, selector)


@mcp.tool()
def switch_to_default_content() -> str:
    """Return from a frame to the top-level page."""
    return browser.default_content()


@mcp.tool()
def get_alert_text() -> str:
    """Return text from the active JavaScript alert or prompt."""
    return browser.alert_text()


@mcp.tool()
def handle_alert(action: Literal["accept", "dismiss"], text: str | None = None) -> str:
    """Accept or dismiss the active alert; optionally enter text in a prompt."""
    return browser.handle_alert(action, text)


@mcp.tool()
def get_cookies() -> list[dict]:
    """Return cookies for the current page's domain."""
    return browser.cookies()


@mcp.tool()
def add_cookie(cookie: dict) -> str:
    """Add a Selenium cookie dictionary to the current page's domain."""
    return browser.add_cookie(cookie)


@mcp.tool()
def delete_cookies(name: str | None = None) -> str:
    """Delete one named cookie, or all cookies when name is omitted."""
    return browser.delete_cookie(name)


@mcp.tool()
def set_window_size(width: int, height: int) -> str:
    """Set browser window dimensions in pixels."""
    return browser.set_window_size(width, height)


@mcp.tool()
def get_window_position() -> dict:
    """Return the browser window's x and y position."""
    return browser.window_position()


@mcp.tool()
def set_window_position(x: int, y: int) -> dict:
    """Move the browser window to the given screen coordinates."""
    return browser.set_window_position(x, y)


@mcp.tool()
def maximize_window() -> str:
    """Maximize the browser window."""
    return browser.maximize_window()


@mcp.tool()
def fullscreen_window() -> str:
    """Put the browser window into fullscreen mode."""
    return browser.fullscreen_window()


@mcp.tool()
def set_timeout(
    timeout_type: Literal["implicit", "page_load", "script"], seconds: float
) -> str:
    """Set an implicit, page-load, or script timeout (maximum 120 seconds)."""
    return browser.set_timeout(timeout_type, seconds)


@mcp.tool()
def get_bidi_status() -> dict:
    """Report whether the active WebDriver session exposes a BiDi WebSocket."""
    return browser.bidi_status()


@mcp.tool()
def get_bidi_context_tree(max_depth: int = 5) -> list[dict]:
    """Return the BiDi browsing context tree, when supported by the browser."""
    return browser.bidi_context_tree(max_depth)


@mcp.tool()
def get_bidi_user_contexts() -> list[str]:
    """List browser user contexts through WebDriver BiDi."""
    return browser.bidi_user_contexts()


@mcp.tool()
def create_bidi_user_context() -> str:
    """Create an isolated browser user context through WebDriver BiDi."""
    return browser.bidi_create_user_context()


@mcp.tool()
def remove_bidi_user_context(user_context: str) -> str:
    """Remove an isolated browser user context through WebDriver BiDi."""
    return browser.bidi_remove_user_context(user_context)


@mcp.tool()
def bidi_navigate(context: str, url: str) -> dict:
    """Navigate a BiDi browsing context to a URL."""
    return browser.bidi_navigate(context, url)


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
