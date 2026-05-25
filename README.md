# NIST Chemistry WebBook MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/mcp-1.0.0-green.svg)](https://modelcontextprotocol.io/)

The NIST Chemistry WebBook is the gold standard public database for thermodynamic and physical chemistry data — the primary reference for chemical engineers running simulations in Aspen, COMSOL, or MATLAB. The interface, designed in the 1990s, has no API and requires tedious manual navigation through inconsistent HTML pages to extract data. Getting Shomate coefficients for a single compound means scrolling through multiple pages, copying numbers by hand, and repeating this for every compound in a simulation. Just finding the coefficients for one compound takes over 2 minutes for a first-time user. This tool does it in a single query.

Built with **Python**, **FastMCP**, **BeautifulSoup4**, and **diskcache**, this server provides robust lookup, multi-phase parsing, and persistent caching of chemical properties.

---

## 🚀 Key Features

*   **🔍 Unified Search (`search_compound`)**: Lookup compounds by Name, Molecular Formula, or CAS RN. Returns canonical data, molecular weight, and available WebBook datasets.
*   **🌡️ Thermochemical Properties (`get_thermodynamic_properties`)**: Fat payload containing:
    *   **Standard State Data**: $H_f^\circ$, $G_f^\circ$, $S_{298}^\circ$, $C_{p,298}^\circ$ (gas/condensed phases).
    *   **Transposed Shomate Coefficient Parsing**: Extracts multi-phase, multi-range Shomate equations ($C_p^\circ = A + B \cdot t + C \cdot t^2 + D \cdot t^3 + E / t^2$, $t = T/1000$) mapping correct associations across complex, transposed HTML layouts.
    *   **Phase Change Properties**: $T_{\text{boil}}$, $T_{\text{fus}}$, $\Delta_{\text{vap}} H^\circ$, and $\Delta_{\text{fus}} H^\circ$.
*   **⚗️ Antoine & Phase Data (`get_phase_change_data`)**: Dedicated endpoint for Antoine parameters ($A$, $B$, $C$ valid ranges) and boiling/melting temperatures.
*   **💾 Smart Persistent Caching**: Employs `diskcache` to cache raw NIST pages locally, saving bandwidth and respecting NIST's server load with restart-proof caching.
*   **🛠️ Robust Multi-tier Search**: Tries high-performance search library `nistchempy` first, with automatic fallback to direct search scraping.

---

## 🛠️ Installation & Setup

### Prerequisites

Ensure you have **Python 3.11+** and the modern package manager [**`uv`**](https://github.com/astral-sh/uv) installed.

### 1. Install Project Dependencies

Clone or place the server inside your workspace, then run:

```bash
uv sync
```

This will automatically create a virtual environment and install all required dependencies: `mcp[cli]`, `nistchempy`, `requests`, `beautifulsoup4`, and `diskcache`.

---

## ⚙️ Configuration

The server's behavior can be customized using environment variables:

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

*Note: Replace `D:\\c\\nist-mcp` with the absolute path to your server's root folder.*

---

## 🧑‍💻 Developer Operations

### Run in Development / Inspector Mode

Inspect and manually call tools inside the interactive MCP inspector:

```bash
uv run mcp dev src/nist_mcp/server.py
```

### Run Tests

Execute the full unit test suite (testing parsing routines, standard state mappings, transposed Shomate table logic, and error handling):

```bash
uv run pytest
```

---

## 📊 Tool Schema Specifications

### `search_compound`
*   **Usage**: Resolves names, formulas, or CAS numbers into authoritative IDs.
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
*   **Usage**: Fetch all thermodynamic properties and Shomate coefficients by CAS RN.
*   **Arguments**:
    *   `cas` (string, required): The CAS number or compound ID (e.g. `"64-17-5"`).
*   **Response Schema**:
    ```json
    {
      "compound": {
        "name": "Water",
        "cas": "7732-18-5",
        "formula": "H2O",
        "molecular_weight": 18.0153
      },
      "shomate": [
        {
          "phase": "gas",
          "T_min": 500.0,
          "T_max": 1700.0,
          "A": 30.092, "B": 6.832514, "C": 6.793435,
          "D": -2.534480, "E": 0.082139, "F": -250.881,
          "G": 223.3967, "H": -241.8264,
          "units": "J/(mol*K)",
          "equation": "Cp° = A + B*t + C*t² + D*t³ + E/t²  (t = T/1000)"
        }
      ],
      "standard_state": {
        "Hf_kJ_per_mol": -241.826,
        "Gf_kJ_per_mol": null,
        "S298_J_per_mol_K": 188.835,
        "Cp298_J_per_mol_K": null
      },
      "phase_change": {
        "T_boil_K": 373.15,
        "T_fus_K": 273.15,
        "dHvap_kJ_per_mol": 40.65,
        "dHfus_kJ_per_mol": 6.01
      }
    }
    ```

### `get_phase_change_data`
*   **Usage**: Retrieve phase transitions and Antoine vapor pressure parameters by CAS RN.
*   **Arguments**:
    *   `cas` (string, required): The CAS number or compound ID (e.g. `"64-17-5"`).
*   **Response Schema**:
    ```json
    {
      "phase_change": {
        "T_boil_K": 351.5,
        "T_fus_K": 159.0,
        "dHvap_kJ_per_mol": 42.3,
        "dHfus_kJ_per_mol": 4.973
      },
      "antoine": [
        {
          "T_min": 364.8,
          "T_max": 513.91,
          "A": 4.92531,
          "B": 1432.526,
          "C": -61.819
        }
      ]
    }
    ```

---

## 📜 License

MIT License. See [LICENSE](LICENSE) or source headers for permissions. This is an unofficial tool and is not affiliated with the National Institute of Standards and Technology (NIST).
