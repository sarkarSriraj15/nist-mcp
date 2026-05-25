# NIST Chemistry WebBook MCP Server

A Model Context Protocol (MCP) server for the **NIST Chemistry WebBook**, providing machine-readable access to thermodynamic and physical chemistry properties.

---

### What was the pain point?
The NIST Chemistry WebBook is the canonical, peer-reviewed public database for thermodynamic, phase change, and chemical property data. Every chemistry and chemical engineering researcher relies on it daily. However:
1. **No Machine Interface**: It has no official API. The site is a late-1990s web portal designed purely for human-facing web browsers.
2. **Unstructured Data Layouts**: The data is locked behind inconsistent HTML layouts, multi-phase tables, and complex **transposed matrices** (such as Shomate coefficients where columns represent temperature ranges and rows represent coefficients).
3. **AI Accessibility Bottleneck**: Autonomous AI agents, material simulators, and automated workflows had to perform slow, brittle, and error-prone web searches or rely on unmaintained, outdated scraping scripts to read thermodynamic figures.

---

### What was the solution?
We built a production-grade **Model Context Protocol (MCP)** server that acts as a secure, local bridge between AI agents and the NIST WebBook. 
* It translates erratic, unstructured HTML pages directly into deterministic, standard-compliant JSON payloads.
* It exposes these properties through three clean MCP tools, allowing any compatible AI client (such as Claude Desktop, Cursor, or VS Code) to query, read, and compute thermodynamic equations natively.

---

### How was that solution achieved?
We engineered a robust scraping, parsing, and caching system in Python using modern tools:
1. **FastMCP Integration**: Leveraged Anthropic's FastMCP SDK over STDIO to define strict tool schemas and capture execution errors as user-friendly `ToolErrors`.
2. **Dual-Tier Search Resolver**: Built a search routine that attempts high-performance lookups with the `nistchempy` library first, and seamlessly falls back to direct `BeautifulSoup4` URL search scraping if nistchempy is throttled or fails.
3. **Transposed Table Parsing**: Developed a custom BeautifulSoup parsing algorithm that zips transposed rows of Shomate coefficients ($A$ through $H$), maps validity temperature ranges, and filters chemical phases (gas, liquid, solid) from adjacent HTML elements.
4. **Local Persistent Cache**: Wrapped fetch requests with a thread-safe `diskcache` layer stored locally (at `~/.cache/nist-mcp`). It honors custom TTL settings to avoid spamming NIST servers and ensure sub-millisecond local responses for cached compounds.
5. **High Test Coverage**: Implemented a comprehensive `pytest` suite mocking all network requests and validating complex float, CAS, standard state, and Antoine table parsing.

---

## 🛠️ Installation & Setup

### Prerequisites
Make sure you have **Python 3.11+** and the modern package manager [**`uv`**](https://github.com/astral-sh/uv) installed.

### 1. Install Project Dependencies
Initialize the environment and sync dependencies:
```bash
uv sync
```
This automatically installs the required dependencies: `mcp[cli]`, `nistchempy`, `requests`, `beautifulsoup4`, and `diskcache`.

---

## ⚙️ Configuration

The server's caching behavior can be configured using environment variables:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `NIST_CACHE_TTL_SECONDS` | Cache expiration time in seconds (e.g. 86400 = 24 hours). | `86400` |
| `NIST_CACHE_DIR` | Absolute path where cache files will be stored. | `~/.cache/nist-mcp` |

---

## 🔌 Connection to MCP Clients (e.g., Claude Desktop)

To use this server with Claude Desktop, add it to your `claude_desktop_config.json` configuration file:

### Windows Configuration
```json
{
  "mcpServers": {
    "nist-webbook": {
      "command": "uv",
      "args": [
        "--directory",
        "D:\\c\\nist-mcp",
        "run",
        "nist-mcp"
      ],
      "env": {
        "NIST_CACHE_TTL_SECONDS": "86400"
      }
    }
  }
}
```
*Note: Replace `D:\\c\\nist-mcp` with the absolute path to your local repository root.*

---

## 🛠️ Developer Operations

### Run in Development / Inspector Mode
To run the interactive MCP inspector for testing and manual tool invocations:
```bash
uv run mcp dev src/nist_mcp/server.py
```

### Run Tests
To run the local unit and mock test suite:
```bash
uv run pytest
```

---

## 📊 Tool Schema Specifications

### `search_compound`
*   **Usage**: Resolves names, formulas, or CAS numbers into canonical compound data.
*   **Arguments**:
    *   `query` (string, required): The search identifier (e.g. `"water"`, `"C2H6O"`, `"64-17-5"`).
    *   `search_by` (string, optional): One of `"name"`, `"formula"`, `"cas"`. Defaults to `"name"`.
*   **Response Schema**:
    ```json
    {
      "name": "Ethanol",
      "cas": "64-17-5",
      "formula": "C2H6O",
      "molecular_weight": 46.068,
      "available_data": ["thermochemical_gas", "thermochemical_condensed", "phase_change"]
    }
    ```

### `get_thermodynamic_properties`
*   **Usage**: Fetch thermodynamic properties, standard state values, and Shomate coefficients by CAS RN.
*   **Arguments**:
    *   `cas` (string, required): The CAS number or compound ID (e.g. `"64-17-5"`).
*   **Response Schema**: Includes compound info, standard state ($Hf^\circ$, $S_{298}^\circ$, etc.), phase changes, and transposed Shomate parameter lists mapping temperature ranges.

### `get_phase_change_data`
*   **Usage**: Retrieve phase changes (boiling/melting points) and empirical Antoine equations.
*   **Arguments**:
    *   `cas` (string, required): The CAS number or compound ID (e.g. `"64-17-5"`).
*   **Response Schema**: Contains boiling point, melting point, enthalpies of vaporization/fusion, and valid Antoine parameters.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) or source headers for permissions. This is an unofficial tool and is not affiliated with the National Institute of Standards and Technology (NIST).
