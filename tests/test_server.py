from unittest.mock import patch
import pytest
from mcp.server.fastmcp import FastMCP
from nist_mcp.server import (
    search_compound,
    get_thermodynamic_properties,
    get_phase_change_data,
    ToolError
)
from nist_mcp.scraper import ScraperError

def test_server_search_compound_success():
    mock_result = {
        "name": "Water",
        "cas": "7732-18-5",
        "formula": "H2O",
        "molecular_weight": 18.0153,
        "available_data": ["thermochemical_gas", "phase_change"]
    }
    with patch("nist_mcp.scraper.search_compound", return_value=mock_result) as mock_search:
        res = search_compound("water", "name")
        assert res == mock_result
        mock_search.assert_called_once_with("water", "name")

def test_server_search_compound_error():
    with patch("nist_mcp.scraper.search_compound", side_effect=ScraperError("Ambiguous search")) as mock_search:
        with pytest.raises(ToolError) as exc_info:
            search_compound("hexane", "name")
        assert "Ambiguous search" in str(exc_info.value)

def test_server_get_thermodynamic_properties_success():
    mock_result = {
        "compound": {
            "name": "Water",
            "cas": "7732-18-5",
            "formula": "H2O",
            "molecular_weight": 18.0153
        },
        "shomate": [
            {
                "phase": "gas",
                "T_min": 500.0, "T_max": 1700.0,
                "A": 30.092, "B": 6.832, "C": 6.793,
                "D": -2.534, "E": 0.082, "F": -250.881,
                "G": 223.396, "H": -241.826,
                "units": "J/(mol*K)",
                "equation": "Cp° = A + B*t + C*t² + D*t³ + E/t²  (t = T/1000)"
            }
        ],
        "standard_state": {
            "Hf_kJ_per_mol": -241.826,
            "Gf_kJ_per_mol": None,
            "S298_J_per_mol_K": 188.835,
            "Cp298_J_per_mol_K": None
        },
        "phase_change": {
            "T_boil_K": 373.15,
            "T_fus_K": 273.15,
            "dHvap_kJ_per_mol": 40.65,
            "dHfus_kJ_per_mol": 6.01
        }
    }
    with patch("nist_mcp.scraper.get_thermodynamic_properties", return_value=mock_result) as mock_get:
        res = get_thermodynamic_properties("7732-18-5")
        assert res == mock_result
        mock_get.assert_called_once_with("7732-18-5")

def test_server_get_thermodynamic_properties_error():
    with patch("nist_mcp.scraper.get_thermodynamic_properties", side_effect=ScraperError("No Shomate data")) as mock_get:
        with pytest.raises(ToolError) as exc_info:
            get_thermodynamic_properties("123-45-6")
        assert "No Shomate data" in str(exc_info.value)

def test_server_get_phase_change_data_success():
    mock_result = {
        "phase_change": {
            "T_boil_K": 351.5,
            "T_fus_K": 159.0,
            "dHvap_kJ_per_mol": 42.3,
            "dHfus_kJ_per_mol": 4.973
        },
        "antoine": [
            {
                "T_min": 364.8, "T_max": 513.91,
                "A": 4.925, "B": 1432.526, "C": -61.819
            }
        ]
    }
    with patch("nist_mcp.scraper.get_phase_change_data", return_value=mock_result) as mock_get:
        res = get_phase_change_data("64-17-5")
        assert res == mock_result
        mock_get.assert_called_once_with("64-17-5")
