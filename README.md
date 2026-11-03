# Selenium MCP Server

A Model Context Protocol (MCP) server that lets an MCP client control a Chrome
browser through Selenium.

## Requirements

- Python 3.10 or later
- Google Chrome or Chromium installed
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
by default.

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
