# Selenium MCP Server

A Model Context Protocol (MCP) server that lets an MCP client control Chrome,
Firefox, Edge, or Safari through Selenium.

## Requirements

- Python 3.10 or later
- One supported browser installed: Google Chrome/Chromium, Mozilla Firefox,
  Microsoft Edge, or Safari on macOS
- Safari automation enabled in Safari's Develop menu on macOS
- Selenium Manager network access on first use to obtain a compatible driver

## Install and run

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m selenium_mcp_server
```

The server communicates over standard input/output using MCP stdio transport.
Configure your MCP client to launch `python -m selenium_mcp_server` from this
repository's directory. The browser starts on the first browser tool call.

Set `SELENIUM_HEADLESS=false` to show the browser window. Headless mode is enabled
by default for Chrome, Firefox, and Edge. Safari does not support headless mode.

Set `SELENIUM_BROWSER` to `chrome`, `firefox`, `edge`, or `safari` to select the
browser; it defaults to `chrome`. WebDriver setup is handled by Selenium Manager
where supported. Safari requires macOS and Safari's built-in safaridriver.

## Tools

Navigation and page inspection:

- `navigate(url)`, `navigate_history(direction)`: open a URL or go `back`,
  `forward`, or `refresh`.
- `get_current_url()`, `get_page_title()`, `get_page_text()`,
  `get_page_source(max_chars=20000)`: inspect the current page. Source output is
  capped at 100,000 characters.
- `take_screenshot()`: return a PNG screenshot.

Elements and interactions:

- `find_elements(strategy, selector, limit=50)`: list matching elements and
  their tag, text, and displayed/enabled/selected state (limit 1–200).
- `get_element_attribute(strategy, selector, attribute)` and
  `get_element_state(strategy, selector)`.
- `get_element_property(strategy, selector, name)`,
  `get_element_css_value(strategy, selector, property_name)`,
  `get_element_rect(strategy, selector)`, and
  `take_element_screenshot(strategy, selector)`.
- `click_element(strategy, selector)`, `submit_element(strategy, selector)`,
  `clear_element(strategy, selector)`, and
  `type_text(strategy, selector, text, clear=true)`.
- `press_key(strategy, selector, key)`: send a supported key such as `ENTER`,
  `TAB`, `ESCAPE`, or an arrow key.
- `select_option(strategy, selector, label|value|index)`: select one option in a
  `<select>` element using exactly one of the three selection criteria.
- `hover_element(strategy, selector)`, `click_action(strategy, selector, action)`
  for double/right-click, `drag_and_drop(source_strategy,
  source_selector, target_strategy, target_selector)`,
  `scroll_to_element(strategy, selector)`, and `scroll_page(x=0, y=0)`.
- `wait_for_element(strategy, selector, timeout=10, visible=true)`: wait for
  presence or visibility; timeout is limited to 120 seconds.
- `wait_for_title(title, timeout=10)` and `wait_for_url(url_fragment, timeout=10)`.

Browser context and controls:

- `get_windows()`, `open_window(window_type=tab, url)`, `switch_window(handle)`,
  and `close_window()`.
- `switch_frame(strategy, selector)` and `switch_to_default_content()`.
- `get_alert_text()` and `handle_alert(action, text)`: inspect or accept/dismiss
  alerts and enter text in prompts.
- `get_cookies()`, `add_cookie(cookie)`, and `delete_cookies(name)`.
- `set_window_size(width, height)`, `maximize_window()`, and
  `fullscreen_window()`.
- `set_timeout(timeout_type, seconds)`: configure `implicit`, `page_load`, or
  `script` timeout (0–120 seconds).
- `execute_javascript(script, arguments)`: execute JavaScript in the current
  page; arguments must be JSON-serializable.
- `close_browser()`: end the current browser session.

Supported locator strategies are `id`, `name`, `css`, `xpath`, `tag`, `class`,
`link_text`, and `partial_link_text`.

## Test

```sh
python -m unittest discover -s tests
```
