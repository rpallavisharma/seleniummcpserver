# Use Selenium MCP Server with Claude Desktop on macOS

This guide connects Claude Desktop to the Selenium MCP server in this
repository. After setup, you can ask Claude to browse and inspect pages using
plain-language prompts.

## What you need

- Claude Desktop installed and running on macOS
- Python 3.10 or later
- Chrome, Firefox, Edge, or Safari installed
- An internet connection the first time Selenium Manager sets up a browser driver

The server controls a real browser on your Mac. Chrome is selected by default,
and the browser runs headlessly unless you turn headless mode off.

## 1. Download the project

Open Terminal and clone the repository:

```sh
git clone https://github.com/rpallavisharma/seleniummcpserver.git
cd seleniummcpserver
```

If you already downloaded the repository, use `cd` to move into the folder that
contains `requirements.txt` and the `selenium_mcp_server` directory.

## 2. Create an environment and install dependencies

Check that Python is new enough:

```sh
python3 --version
```

If the version is below 3.10, install a newer Python before continuing. Then,
from the repository directory, run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Keep the virtual environment in the repository. Claude will use its Python
executable in the next step.

## 3. Copy the full repository path

In the same Terminal window, run:

```sh
pwd
```

Copy the printed path. It should be the directory containing both
`requirements.txt` and `selenium_mcp_server/`. For example:

```text
/Users/yourname/Documents/seleniummcpserver
```

## 4. Configure Claude Desktop

In Claude Desktop, open **Settings → Developer → Edit Config**. This opens
`claude_desktop_config.json`. If the file already contains settings, preserve
them and add the `selenium` entry inside its existing `mcpServers` object.

Add or update the configuration below, replacing both occurrences of
`/Users/yourname/Documents/seleniummcpserver` with the exact path you copied:

```json
{
  "mcpServers": {
    "selenium": {
      "command": "/Users/yourname/Documents/seleniummcpserver/.venv/bin/python",
      "args": ["-m", "selenium_mcp_server"],
      "env": {
        "PYTHONPATH": "/Users/yourname/Documents/seleniummcpserver",
        "SELENIUM_BROWSER": "chrome",
        "SELENIUM_HEADLESS": "false"
      }
    }
  }
}
```

`PYTHONPATH` tells Python where to find the project package. Make sure both
paths point to the repository root, not to the `selenium_mcp_server` subfolder.
Use valid JSON: double quotes, commas between entries, and no comments.

To keep the browser hidden, change `SELENIUM_HEADLESS` to `"true"` or remove
that setting. To use another installed browser, change `SELENIUM_BROWSER` to
`"firefox"`, `"edge"`, or `"safari"`. Safari is only available on macOS and
requires enabling automation in Safari's Develop menu.

## 5. Restart and check the connection

Save the config, fully quit Claude Desktop with **Cmd+Q**, then reopen it. Go
to **Settings → Developer** and check that the Selenium server is running. If
Claude asks permission to use a tool in a chat, review the request and allow it
when appropriate.

## 6. Try a first browser task

Start with a simple public page:

> Open https://example.com and tell me the page title and the main text.

Claude should use the Selenium tools to navigate to the page and inspect it.
With `"SELENIUM_HEADLESS": "false"`, you should also see the browser window.

## 7. Try more tasks

For example:

- “Open https://example.com and list its links.”
- “Take a screenshot of the current page.”
- “Find the heading on this page and tell me its text.”
- “Wait for the element with CSS selector `#results` to appear, then read its
  text.”
- “Go back one page and tell me the current URL.”

You can ask Claude to use a specific locator when you know one, such as a CSS
selector or an element ID. Otherwise, describe the element and Claude can
inspect the page to choose a locator.

## Troubleshooting

### `No module named selenium_mcp_server`

Check that `PYTHONPATH` is the exact repository path from `pwd` and that the
path contains the `selenium_mcp_server` directory. Also confirm that the
`command` path points to `.venv/bin/python` inside that same repository.
After editing the config, quit and reopen Claude Desktop.

You can check the package and interpreter directly in Terminal:

```sh
/full/path/to/seleniummcpserver/.venv/bin/python -c "import selenium_mcp_server; print('Package found')"
```

Replace `/full/path/to/seleniummcpserver` with your actual repository path.

### `Could not find a version` while installing

Check `python3 --version`; the project requires Python 3.10 or later. If
Python is recent enough, check that your network, VPN, or proxy allows access
to PyPI, then retry the install command.

### Claude reports that the server disconnected

Open **Settings → Developer** and inspect the server logs. Check for invalid
JSON, incorrect paths, and dependency installation errors. Make sure you
restarted Claude Desktop after changing its config.

### The browser does not open

Confirm the selected browser is installed. On first use, Selenium Manager may
need internet access to obtain a compatible driver. Safari requires macOS and
Safari automation enabled in the Develop menu.

## Use browser access carefully

The server can click, type into forms, read page content, and execute
JavaScript. Start with public, non-sensitive pages; review actions before
allowing them, and avoid using it with private accounts or sensitive data
unless you understand and trust the requested browser actions.
