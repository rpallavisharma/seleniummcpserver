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

- `navigate(url)`: open a URL.
- `get_page_title()`: read the current page title.
- `get_page_text()`: read visible page text.
- `click_element(strategy, selector)`: click the first matching element.
- `type_text(strategy, selector, text, clear=true)`: type into the first matching
  element, clearing it by default.
- `take_screenshot()`: return a PNG screenshot.
- `close_browser()`: close the active session.

Supported locator strategies are `id`, `name`, `css`, `xpath`, `tag`, `class`,
`link_text`, and `partial_link_text`.

## Test

```sh
python -m unittest discover -s tests
```
