import re
import logging
import requests
from bs4 import BeautifulSoup
import nistchempy as nist
from nist_mcp.cache import cached

logger = logging.getLogger("nist-mcp")

class ScraperError(Exception):
    """Custom exception for scraper errors that should be surfaced to the user/LLM."""
    pass

def _normalize_cas(cas: str) -> str:
    """Normalize CAS RN by removing hyphens and prepending 'C' if it's numeric."""
    cleaned = cas.replace('-', '').strip()
    if cleaned.isdigit():
        return f"C{cleaned}"
    return cleaned

def _parse_float(text: str) -> float:
    """Safely parse a float from NIST value text, handling ±, trailing dots, etc."""
    if not text:
        return None
    # Extract the main part of the value before the uncertainty ±
    val_part = text.split('±')[0].strip()
    # Strip any non-numeric characters except standard signs, dot, and scientific notation
    cleaned = ""
    for char in val_part:
        if char.isdigit() or char in ['.', '-', '+', 'e', 'E']:
            cleaned += char
    try:
        return float(cleaned)
    except ValueError:
        return None

@cached
def _fetch_nist_page(cas_id: str, mask: int) -> str:
    """Fetch a page from the NIST Chemistry WebBook with a given Mask and cache the HTML string."""
    url = f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas_id}&Units=SI&Mask={mask}"
    logger.info(f"Fetching NIST WebBook URL: {url}")
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            raise ScraperError(f"NIST WebBook returned HTTP {resp.status_code} for CAS/ID {cas_id}.")
        return resp.text
    except requests.RequestException as e:
        raise ScraperError(f"Network error or timeout reaching NIST WebBook: {e}")

def _fallback_url_search(query: str, search_by: str) -> dict:
    """
    Direct scraping fallback when nistchempy returns nothing or fails.
    Returns compound basic details if we land on a single compound page,
    or raises ScraperError if ambiguous or not found.
    """
    if search_by == "name":
        url = f"https://webbook.nist.gov/cgi/cbook.cgi?Name={query}&Units=SI"
    elif search_by == "formula":
        url = f"https://webbook.nist.gov/cgi/cbook.cgi?Formula={query}&Units=SI"
    elif search_by == "cas":
        url = f"https://webbook.nist.gov/cgi/cbook.cgi?ID={query}&Units=SI"
    else:
        raise ScraperError(f"Unsupported search identifier: {search_by}")
        
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            raise ScraperError(f"NIST WebBook search failed with HTTP {resp.status_code}.")
    except requests.RequestException as e:
        raise ScraperError(f"Network error during fallback search: {e}")
        
    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.title.text.strip() if soup.title else ""
    
    if "Search Results" in title:
        # Multiple matches found
        matches = []
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if "/cgi/cbook.cgi?ID=" in href:
                cas_match = re.search(r'ID=(C?\d+)', href)
                if cas_match:
                    matches.append(f"{a.text.strip()} (ID: {cas_match.group(1)})")
        if matches:
            raise ScraperError(f"Ambiguous query '{query}' — multiple matches found: {', '.join(matches[:10])}. Refine your query or use a CAS number.")
        else:
            raise ScraperError(f"No compound found for '{query}' (search_by='{search_by}').")
            
    # Try to extract the CAS ID from structure links on the page if we landed on a compound page
    cas_id = None
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if "Str2File=" in href:
            match = re.search(r'Str2File=(C?\d+)', href)
            if match:
                cas_id = match.group(1)
                break
                
    if not cas_id:
        # Check if URL itself has ID
        url_match = re.search(r'ID=(C?\d+)', resp.url)
        if url_match:
            cas_id = url_match.group(1)
            
    if not cas_id:
        raise ScraperError(f"No compound found for '{query}' (search_by='{search_by}').")
        
    # Extract details from page
    name = soup.find('h1', id='Top')
    name = name.text.strip() if name else title
    
    formula = None
    cas_rn = None
    mol_weight = None
    for li in soup.find_all('li'):
        text = li.text
        if "Formula:" in text:
            formula = text.replace("Formula:", "").strip()
        elif "CAS Registry Number:" in text:
            cas_rn = text.replace("CAS Registry Number:", "").strip()
        elif "Molecular weight:" in text:
            try:
                mol_weight = float(text.replace("Molecular weight:", "").strip().split()[0])
            except:
                pass
                
    # Detect available sections based on links
    available_data = []
    text_content = resp.text
    if "Thermo-Gas" in text_content or "Constant pressure heat capacity of gas" in text_content:
        available_data.append("thermochemical_gas")
    if "Thermo-Condensed" in text_content or "Constant pressure heat capacity of liquid" in text_content:
        available_data.append("thermochemical_condensed")
    if "Thermo-Phase" in text_content or "Antoine Equation Parameters" in text_content:
        available_data.append("phase_change")
    if "IR-Spec" in text_content:
        available_data.append("ir_spectrum")
    if "Mass-Spec" in text_content:
        available_data.append("mass_spectrum")
        
    return {
        "name": name,
        "cas": cas_rn or cas_id,
        "formula": formula,
        "molecular_weight": mol_weight,
        "available_data": available_data
    }

def search_compound(query: str, search_by: str = "name") -> dict:
    """
    Search compound by name, formula, or CAS number.
    Uses nistchempy first, falls back to direct requests scraping.
    """
    search_by_mapped = search_by.lower().strip()
    if search_by_mapped == "cas":
        search_by_mapped = "cas"
    elif search_by_mapped not in ["name", "formula", "inchi"]:
        search_by_mapped = "name"
        
    try:
        results = nist.run_search(query, search_type=search_by_mapped)
        if results and results.success and results.num_compounds > 0:
            if results.num_compounds > 1:
                # Ambiguous matches
                names = [f"{c.name} (CAS: {c.cas_rn})" for c in results.compounds]
                raise ScraperError(f"Ambiguous query '{query}' — {len(names)} matches found: {', '.join(names[:10])}. Refine your query or use a CAS number.")
            
            compound = results.compounds[0]
            # Map available data refs
            available = []
            for k in compound.data_refs:
                if k == 'cTG': available.append("thermochemical_gas")
                elif k == 'cTC': available.append("thermochemical_condensed")
                elif k == 'cTP': available.append("phase_change")
                elif k == 'cIR': available.append("ir_spectrum")
                elif k == 'cMS': available.append("mass_spectrum")
                
            return {
                "name": compound.name,
                "cas": compound.cas_rn,
                "formula": compound.formula,
                "molecular_weight": compound.mol_weight,
                "available_data": available
            }
    except ScraperError:
        raise
    except Exception as e:
        logger.warning(f"nistchempy search encountered error: {e}. Falling back to direct URL search.")
        
    # Fallback to direct scraping search
    return _fallback_url_search(query, search_by_mapped)

def _parse_shomate_tables(soup: BeautifulSoup, cas_id: str) -> list[dict]:
    """Parse transposed Shomate coefficient tables for all phases on the page."""
    shomate_data = []
    
    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        row_headers = {}
        for r in rows:
            th = r.find('th')
            if th:
                # Clean header name
                h_name = th.text.strip().replace(' ', '').replace('(', '').replace(')', '')
                row_headers[h_name] = r
                
        # Shomate table has row headers A, B, C, D, E, F, G, H
        if 'A' in row_headers and 'B' in row_headers and 'C' in row_headers:
            # Determine Phase from headings or aria-label
            phase = "unknown"
            sibling = table.find_previous(['h1', 'h2', 'h3', 'h4'])
            if sibling:
                title = sibling.text.lower()
                if "gas" in title:
                    phase = "gas"
                elif "liquid" in title:
                    phase = "liquid"
                elif "solid" in title or "crystal" in title:
                    phase = "solid"
            
            aria = table.get('aria-label', '').lower()
            if "gas" in aria:
                phase = "gas"
            elif "liquid" in aria:
                phase = "liquid"
            elif "solid" in aria or "crystal" in aria:
                phase = "solid"
                
            # Find temperature row to count columns and parse T ranges
            temp_row = None
            for k in row_headers:
                if "temperature" in k.lower():
                    temp_row = row_headers[k]
                    break
                    
            if temp_row:
                tds = temp_row.find_all('td')
                for i in range(len(tds)):
                    temp_text = tds[i].text.strip()
                    T_min, T_max = None, None
                    if "to" in temp_text:
                        parts = temp_text.split("to")
                        T_min = _parse_float(parts[0])
                        T_max = _parse_float(parts[1])
                        
                    coeffs = {
                        "phase": phase,
                        "T_min": T_min,
                        "T_max": T_max,
                        "units": "J/(mol*K)",
                        "equation": "Cp° = A + B*t + C*t² + D*t³ + E/t²  (t = T/1000)"
                    }
                    
                    for param in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                        if param in row_headers:
                            param_tds = row_headers[param].find_all('td')
                            if len(param_tds) > i:
                                coeffs[param] = _parse_float(param_tds[i].text.strip())
                            else:
                                coeffs[param] = None
                        else:
                            coeffs[param] = None
                            
                    shomate_data.append(coeffs)
                    
    return shomate_data

def _parse_standard_state_tables(soup: BeautifulSoup) -> dict:
    """Parse standard-state thermochemistry data from the page."""
    standard_state = {}
    
    # Helper to parse one dimensional data tables under given headers
    def parse_one_dim_tables(h_id):
        section = soup.find(id=h_id)
        if not section:
            return
        sibling = section.next_sibling
        while sibling:
            if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                break
            if sibling.name == 'table' and 'data' in sibling.get('class', []):
                for row in sibling.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        qty = tds[0].text.strip().replace(' ', '').replace('\n', '').replace('\r', '')
                        val_text = tds[1].text.strip()
                        units = tds[2].text.strip()
                        val = _parse_float(val_text)
                        if val is not None:
                            standard_state[qty] = {
                                "value": val,
                                "units": units
                            }
            sibling = sibling.next_sibling
            
    parse_one_dim_tables('Thermo-Gas')
    parse_one_dim_tables('Thermo-Condensed')
    
    # Map to final output format
    res = {
        "Hf_kJ_per_mol": None,
        "Gf_kJ_per_mol": None,
        "S298_J_per_mol_K": None,
        "Cp298_J_per_mol_K": None
    }
    
    for k, data in standard_state.items():
        val = data["value"]
        # Check Hf (prioritizing gas/liquid appropriately)
        if 'ΔfH°' in k or 'DfH°' in k or 'dfH°' in k:
            res["Hf_kJ_per_mol"] = val
        # Check Gf
        elif 'ΔfG°' in k or 'DfG°' in k or 'dfG°' in k or 'ΔgG°' in k or 'DgG°' in k:
            res["Gf_kJ_per_mol"] = val
        # Check S298
        elif k.startswith('S°') or k.startswith('S298'):
            res["S298_J_per_mol_K"] = val
        # Check Cp298
        elif k.startswith('Cp°') or k.startswith('Cp,'):
            res["Cp298_J_per_mol_K"] = val
            
    return res

def _parse_phase_change_tables(soup: BeautifulSoup) -> dict:
    """Parse phase-change and vapor pressure data."""
    phase_change = {
        "T_boil_K": None,
        "T_fus_K": None,
        "dHvap_kJ_per_mol": None,
        "dHfus_kJ_per_mol": None
    }
    
    # Check main one dimensional table under Thermo-Phase
    phase_tables = {}
    section = soup.find(id='Thermo-Phase')
    if section:
        sibling = section.next_sibling
        while sibling:
            if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                break
            if sibling.name == 'table' and 'data' in sibling.get('class', []):
                for row in sibling.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        qty = tds[0].text.strip().replace(' ', '').replace('\n', '').replace('\r', '')
                        val_text = tds[1].text.strip()
                        val = _parse_float(val_text)
                        if val is not None:
                            phase_tables[qty] = val
            sibling = sibling.next_sibling
            
    for k, val in phase_tables.items():
        if 'Tboil' in k:
            phase_change["T_boil_K"] = val
        elif 'Tfus' in k or 'Tfreeze' in k:
            phase_change["T_fus_K"] = val
        elif 'ΔvapH°' in k or 'DvapH°' in k or 'ΔvapH' in k or 'DvapH' in k:
            phase_change["dHvap_kJ_per_mol"] = val
        elif 'ΔfusH°' in k or 'DfusH°' in k or 'ΔfusH' in k or 'DfusH' in k:
            phase_change["dHfus_kJ_per_mol"] = val
            
    # Check dedicated tables under h3 headings for dHvap and dHfus if not found
    for h3 in soup.find_all('h3'):
        text = h3.text.lower()
        if "enthalpy of vaporization" in text and phase_change["dHvap_kJ_per_mol"] is None:
            table = h3.find_next('table')
            if table:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    tds = rows[1].find_all('td')
                    if tds:
                        val = _parse_float(tds[0].text.strip())
                        if val is not None:
                            phase_change["dHvap_kJ_per_mol"] = val
        elif "enthalpy of fusion" in text and phase_change["dHfus_kJ_per_mol"] is None:
            table = h3.find_next('table')
            if table:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    tds = rows[1].find_all('td')
                    if tds:
                        val = _parse_float(tds[0].text.strip())
                        if val is not None:
                            phase_change["dHfus_kJ_per_mol"] = val
                            
    return phase_change

def _parse_antoine_tables(soup: BeautifulSoup) -> list[dict]:
    """Parse Antoine Equation Parameter tables from the page."""
    antoine_params = []
    
    for h3 in soup.find_all('h3'):
        if "antoine" in h3.text.lower():
            table = h3.find_next('table')
            if table:
                rows = table.find_all('tr')
                if len(rows) > 0:
                    headers = [th.text.strip().lower() for th in rows[0].find_all('th')]
                    if 'a' in headers and 'b' in headers and 'c' in headers:
                        a_idx = headers.index('a')
                        b_idx = headers.index('b')
                        c_idx = headers.index('c')
                        temp_idx = 0  # usually first column
                        for row in rows[1:]:
                            tds = row.find_all('td')
                            if len(tds) > max(a_idx, b_idx, c_idx):
                                temp_text = tds[temp_idx].text.strip()
                                T_min, T_max = None, None
                                if "to" in temp_text:
                                    parts = temp_text.split("to")
                                    T_min = _parse_float(parts[0])
                                    T_max = _parse_float(parts[1])
                                try:
                                    a_val = float(tds[a_idx].text.strip())
                                    b_val = float(tds[b_idx].text.strip())
                                    c_val = float(tds[c_idx].text.strip())
                                    antoine_params.append({
                                        "T_min": T_min,
                                        "T_max": T_max,
                                        "A": a_val,
                                        "B": b_val,
                                        "C": c_val
                                    })
                                except ValueError:
                                    pass
                                    
    return antoine_params

def get_thermodynamic_properties(cas: str) -> dict:
    """
    Retrieve thermodynamic properties for a compound by CAS.
    Returns:
      compound       → basic info
      shomate        → Shomate coefficients
      standard_state → Hf, Gf, S298, Cp298 standard values
      phase_change   → boiling, melting points and phase change enthalpies
    """
    cas_id = _normalize_cas(cas)
    # Fetch with mask=7 to get Gas + Condensed + Phase change sections in one request
    html = _fetch_nist_page(cas_id, mask=7)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Basic compound metadata
    title_el = soup.find('h1', id='Top')
    name = title_el.text.strip() if title_el else "Unknown Compound"
    
    # Extract formula and MW from list elements
    formula = None
    mw = None
    for li in soup.find_all('li'):
        text = li.text
        if "Formula:" in text:
            formula = text.replace("Formula:", "").strip()
        elif "Molecular weight:" in text:
            try:
                mw = float(text.replace("Molecular weight:", "").strip().split()[0])
            except:
                pass
                
    shomate = _parse_shomate_tables(soup, cas_id)
    if not shomate:
        raise ScraperError(f"No Shomate data available for CAS {cas} on NIST WebBook.")
        
    standard_state = _parse_standard_state_tables(soup)
    phase_change = _parse_phase_change_tables(soup)
    
    return {
        "compound": {
            "name": name,
            "cas": cas,
            "formula": formula,
            "molecular_weight": mw
        },
        "shomate": shomate,
        "standard_state": standard_state,
        "phase_change": phase_change
    }

def get_phase_change_data(cas: str) -> dict:
    """
    Retrieve phase change and vapor pressure data for a compound by CAS.
    Returns:
      phase_change   → boiling, melting, dHvap, dHfus
      antoine        → list of Antoine parameters
    """
    cas_id = _normalize_cas(cas)
    # Mask 4 has phase change data and Antoine coefficients
    html = _fetch_nist_page(cas_id, mask=4)
    soup = BeautifulSoup(html, 'html.parser')
    
    phase_change = _parse_phase_change_tables(soup)
    antoine = _parse_antoine_tables(soup)
    
    if not antoine and not any(phase_change.values()):
        raise ScraperError(f"No phase change data available for CAS {cas} on NIST WebBook.")
        
    return {
        "phase_change": phase_change,
        "antoine": antoine
    }
