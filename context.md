# Context handoff — NIST WebBook MCP Server project

## Who I am

Sriraj, undergraduate Chemical Engineering student at IIT Delhi (2025CH71058). Switched from Linux Mint to Windows recently. Comfortable with Python (OOP, NumPy, matplotlib, wrote a Matrix class, worked on algorithmic problems). Experience writing LaTeX reports and generating Python figures for a real multiphysics simulation project (hemodynamics drug transport, COMSOL). No prior MCP or web scraping experience.

---

## What we're building and why

**Project:** An MCP (Model Context Protocol) server for the NIST Chemistry WebBook.

**The gap:** The NIST Chemistry WebBook (webbook.nist.gov) is the canonical public database for thermodynamic and physical property data — heat capacity, enthalpy of formation, vapor pressure, Shomate coefficients, Antoine parameters, fluid properties. Every chemistry and chemical engineering researcher uses it constantly. It has no official API. It is a website designed in the late 1990s that has never changed. The only programmatic access that exists is a janky 2019 Scrapy scraper and an unmaintained Python library. No MCP server exists for it.

**Why this matters (the YC framing):** We've been working through YC's 2026 RFS, specifically the "Software for Agents" prompt — the idea that AI agents are the next trillion users of the internet, and they need machine-readable interfaces, not human-facing UIs. The NIST WebBook is a perfect example: the data exists, it's public, it's authoritative, but it's completely inaccessible to agents. An MCP server fixes that for every agent doing chemistry, chemical engineering, or materials simulation work.

**Why no one has built it yet:** The big simulation software MCPs (COMSOL, Aspen Plus, MATLAB/Simulink, OpenFOAM) all got built in 2025-2026. The NIST cybersecurity framework MCPs exist. But the NIST *Chemistry* WebBook — the thermodynamic data side — has been missed entirely.

---

## Confirmed research

- NIST WebBook URL structure is well-documented and simple:
  - `webbook.nist.gov/cgi/cbook.cgi?Name=ethanol&Units=SI&Mask=2` → thermochemical data
  - `Mask=4` → phase change / Antoine / vapor pressure
  - `Mask=1` → basic compound info
  - Can also search by CAS number: `?ID=64-17-5&Units=SI`

- **`nistchempy`** exists on PyPI — an unofficial Python API that handles search by name, formula, CAS, InChI/InChIKey, and bypasses the WebBook's 400-compound search limit. This is our scraping foundation — we build on top of it, not from scratch.

- The JSON shape we want to output already exists as a reference from the old Scrapy project (water example):
  ```json
  {
    "name": "Water",
    "cas": "7732185",
    "formula": "H2O",
    "molecular_weight": 18.0153,
    "enthalpy_formation_gas": { "value": -241.826, "units": "kJ/mol" },
    "heat_capacity_shomate_equation_gas": [
      { "temperatures": [500.0, 1700.0], "A": 30.092, "B": 6.832514, ... }
    ],
    "antoine_parameters": [
      { "T_range": [379.0, 573.0], "A": 8.07131, "B": 1730.63, "C": 233.426 }
    ]
  }
  ```

- **MCP itself:** Open standard from Anthropic (now Linux Foundation governed). Python SDK available (`mcp` on PyPI, use FastMCP for simplicity). Three primitives: Tools (callable functions), Resources (read-only data), Prompts (templates). Works with Claude, ChatGPT, Cursor, VS Code, and anything else MCP-compatible.

---

## Architecture

```
Claude / Gemini / any AI agent
        ↓ MCP tool call
nist-webbook-mcp  (Python, FastMCP)
        ↓ uses
nistchempy (PyPI) + requests + BeautifulSoup
        ↓ scrapes
webbook.nist.gov
        ↓ returns
clean structured JSON back up the chain
```

Three files for v1:
- `server.py` — MCP server, tool definitions
- `scraper.py` — all WebBook fetching and parsing logic
- `pyproject.toml` — dependencies

---

## Target tools for v1

These are the four highest-value tools covering what ChE researchers need most:

```python
search_compound(query: str, search_by: str = "name")
# Returns: name, CAS, formula, molecular weight, available data types
# search_by options: "name", "cas", "formula", "inchi"

get_thermodynamic_properties(compound: str, phase: str = "gas")
# Returns: Hf, Gf, entropy, Shomate coefficients (A-H) with temperature ranges
# phase options: "gas", "liquid", "solid"

get_vapor_pressure(compound: str)
# Returns: Antoine equation parameters (A, B, C) with temperature validity ranges
# Includes: normal boiling point, critical point if available

get_fluid_properties(compound: str, temperature: float, pressure: float)
# Returns: density, viscosity, thermal conductivity, Cp at given T (K) and P (Pa)
# Uses NIST's REFPROP-backed fluid property pages
```

---

## What good output looks like

An AI agent should be able to do this:

> "What is the heat capacity of ethanol as a function of temperature between 300-500K?"

And get back Shomate coefficients it can immediately plug into `Cp = A + B*t + C*t² + D*t³ + E/t²` (where `t = T/1000`) — no scraping, no HTML parsing, no copy-pasting from a 1990s webpage.

---

## Things to watch out for

- NIST WebBook has no rate limiting documentation, but be respectful — add a small delay between requests (0.5–1s), cache results where possible
- Some compounds have multiple phases with separate Shomate coefficient sets for different temperature ranges — the output must preserve all ranges, not just return one
- Antoine parameters are empirical and only valid within their stated temperature range — always return the range alongside A, B, C
- `nistchempy` covers basic properties and spectra well but may need supplementing with direct BeautifulSoup scraping for Shomate coefficients and fluid properties
- NIST says it "reserves the right to charge for access in the future" — worth noting in the README

---

## Stack

- Python 3.10+
- `mcp[cli]` (FastMCP) — MCP server framework
- `nistchempy` — WebBook search and basic extraction
- `requests` + `beautifulsoup4` — supplementary scraping for data nistchempy doesn't cover
- `uv` — package manager (standard for MCP projects)

---

## Immediate next step

Write the three files: `server.py`, `scraper.py`, `pyproject.toml`. Start with `search_compound` and `get_thermodynamic_properties` working end-to-end before adding the other two tools. Test with MCP Inspector before connecting to any AI client.

The GitHub repo should be named something like `nist-webbook-mcp`. README should clearly explain the problem (no agent-native interface to NIST data), the solution, installation, and example tool calls.
