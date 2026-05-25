from bs4 import BeautifulSoup
import pytest
from nist_mcp.scraper import (
    _parse_float,
    _parse_shomate_tables,
    _parse_standard_state_tables,
    _parse_phase_change_tables,
    _parse_antoine_tables,
    _normalize_cas,
    ScraperError
)

def test_parse_float():
    assert _parse_float("-241.826 ± 0.040") == -241.826
    assert _parse_float("351.5 ± 0.2") == 351.5
    assert _parse_float("159. ± 2.") == 159.0
    assert _parse_float("159.") == 159.0
    assert _parse_float("  4.973  ") == 4.973
    assert _parse_float(None) is None
    assert _parse_float("invalid") is None

def test_normalize_cas():
    assert _normalize_cas("64-17-5") == "C64175"
    assert _normalize_cas("C64175") == "C64175"
    assert _normalize_cas("C64-17-5") == "C64175"
    assert _normalize_cas("water") == "water"

def test_parse_shomate_tables(mock_shomate_html):
    soup = BeautifulSoup(mock_shomate_html, 'html.parser')
    res = _parse_shomate_tables(soup, "C7732185")
    
    assert len(res) == 2
    # Check range 1
    assert res[0]["T_min"] == 500.0
    assert res[0]["T_max"] == 1700.0
    assert res[0]["A"] == 30.09200
    assert res[0]["H"] == -241.8264
    assert res[0]["phase"] == "gas"
    
    # Check range 2
    assert res[1]["T_min"] == 1700.0
    assert res[1]["T_max"] == 6000.0
    assert res[1]["A"] == 41.96426
    assert res[1]["H"] == -241.8264
    assert res[1]["phase"] == "gas"

def test_parse_standard_state_tables(mock_thermo_page_html):
    soup = BeautifulSoup(mock_thermo_page_html, 'html.parser')
    res = _parse_standard_state_tables(soup)
    
    assert res["Hf_kJ_per_mol"] == -241.826
    assert res["S298_J_per_mol_K"] == 188.835
    assert res["Gf_kJ_per_mol"] is None
    assert res["Cp298_J_per_mol_K"] is None

def test_parse_phase_change_tables(mock_phase_page_html):
    soup = BeautifulSoup(mock_phase_page_html, 'html.parser')
    res = _parse_phase_change_tables(soup)
    
    assert res["T_boil_K"] == 351.5
    assert res["T_fus_K"] == 159.0
    assert res["dHvap_kJ_per_mol"] == 42.3
    assert res["dHfus_kJ_per_mol"] == 4.973

def test_parse_antoine_tables(mock_phase_page_html):
    soup = BeautifulSoup(mock_phase_page_html, 'html.parser')
    res = _parse_antoine_tables(soup)
    
    assert len(res) == 1
    assert res[0]["T_min"] == 364.8
    assert res[0]["T_max"] == 513.91
    assert res[0]["A"] == 4.92531
    assert res[0]["B"] == 1432.526
    assert res[0]["C"] == -61.819
