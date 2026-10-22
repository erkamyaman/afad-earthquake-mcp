# afad-earthquake-mcp

An MCP server that gives Claude live earthquake data for Türkiye from the [AFAD](https://deprem.afad.gov.tr) public event API. No API key needed.

## Tools

| Tool | What it does | Parameters |
|---|---|---|
| `last_earthquakes` | Latest earthquakes in and around Türkiye | `hours` (default 24), `min_magnitude`, `limit` (default 10) |
| `city_earthquakes` | Recent earthquakes in one province | `city`, `days` (default 7), `min_magnitude`, `limit` (default 20) |

Both return a Markdown table with time (Türkiye time, UTC+3), magnitude, depth and location. City names ignore case and Turkish letters, so `izmir`, `İZMİR` and `Istanbul` all work.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone https://github.com/erkamyaman/afad-earthquake-mcp.git
cd afad-earthquake-mcp
uv sync
```

## Use with Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), replacing the path with where you cloned the repo:

```json
{
  "mcpServers": {
    "afad-earthquake": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/afad-earthquake-mcp", "afad-earthquake-mcp"]
    }
  }
}
```

Quit Claude Desktop fully and reopen it, then ask something like "Son 24 saatteki depremler neler?" or "İzmir'de bu hafta deprem oldu mu?"

## Notes

- AFAD assigns offshore and some foreign earthquakes to the nearest province, so city results can include quakes at sea or across the border.
- AFAD cannot filter by province, so `city_earthquakes` fetches every quake in the time window and filters locally.
