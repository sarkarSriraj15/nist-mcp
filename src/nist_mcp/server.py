import logging
import sys
import math
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("nist-mcp")

try:
    from mcp.server.fastmcp import ToolError
except ImportError:
    ToolError = Exception

from nist_mcp import scraper

# Initialize FastMCP Server
mcp = FastMCP("nist-webbook")

@mcp.tool()
def search_compound(query: str, search_by: str = "name") -> dict:
    """
    Search the NIST Chemistry WebBook for a compound by Name, Formula, or CAS number.
    
    Args:
        query: The search term (e.g. 'ethanol', 'H2O', or '64-17-5')
        search_by: The identifier type: 'name', 'formula', or 'cas' (default: 'name')
        
    Returns:
        A dictionary containing:
          - name: The canonical name of the compound
          - cas: The CAS Registry Number
          - formula: The chemical formula
          - molecular_weight: The molecular weight in g/mol
          - available_data: A list of available data categories on NIST
    """
    logger.info(f"Tool search_compound called with query='{query}', search_by='{search_by}'")
    try:
        return scraper.search_compound(query, search_by)
    except scraper.ScraperError as e:
        logger.error(f"search_compound failed: {e}")
        raise ToolError(str(e))
    except Exception as e:
        logger.exception("Unexpected error in search_compound")
        raise ToolError(f"Unexpected error: {e}")

@mcp.tool()
def get_thermodynamic_properties(cas: str, phase: str = "all") -> dict:
    """
    Retrieve thermodynamic properties for a compound by CAS number.
    Includes Shomate coefficients, standard state values, and phase changes.
    
    Args:
        cas: The CAS Registry Number or NIST ID (e.g., '64-17-5')
        phase: Optional. 'gas', 'condensed', or 'all' (default: 'all'). Determines which phase's standard state data is returned.
        
    Returns:
        A nested dictionary containing:
          - compound: name, formula, molecular weight, cas
          - shomate: List of objects containing temperature ranges (T_min, T_max), phase, and coefficients (A-H)
          - standard_state: standard enthalpy of formation (Hf), Gibbs energy of formation (Gf), entropy (S298), Cp298. If phase is 'all', keyed by 'gas' and 'condensed'.
          - phase_change: boiling point, melting point, enthalpy of vaporization, enthalpy of fusion
    """
    logger.info(f"Tool get_thermodynamic_properties called for CAS='{cas}', phase='{phase}'")
    try:
        return scraper.get_thermodynamic_properties(cas, phase)
    except scraper.ScraperError as e:
        logger.error(f"get_thermodynamic_properties failed: {e}")
        raise ToolError(str(e))
    except Exception as e:
        logger.exception("Unexpected error in get_thermodynamic_properties")
        raise ToolError(f"Unexpected error: {e}")

@mcp.tool()
def get_phase_change_data(cas: str) -> dict:
    """
    Retrieve phase change and vapor pressure (Antoine parameters) data by CAS number.
    
    Args:
        cas: The CAS Registry Number or NIST ID (e.g., '64-17-5')
        
    Returns:
        A dictionary containing:
          - phase_change: boiling point, melting point, enthalpy of vaporization, enthalpy of fusion
          - antoine: List of Antoine parameters with validity temperature ranges
    """
    logger.info(f"Tool get_phase_change_data called for CAS='{cas}'")
    try:
        return scraper.get_phase_change_data(cas)
    except scraper.ScraperError as e:
        logger.error(f"get_phase_change_data failed: {e}")
        raise ToolError(str(e))
    except Exception as e:
        logger.exception("Unexpected error in get_phase_change_data")
        raise ToolError(f"Unexpected error: {e}")

@mcp.tool()
def get_vapor_pressure(cas: str, temperature_K: float) -> dict:
    """
    Calculate vapor pressure of a compound at a given temperature using Antoine parameters.
    
    Args:
        cas: The CAS Registry Number or NIST ID (e.g., '64-17-5')
        temperature_K: The temperature in Kelvin
        
    Returns:
        A dictionary containing:
          - vapor_pressure_bar: Vapor pressure in bar
          - vapor_pressure_kPa: Vapor pressure in kilopascals (kPa)
          - antoine_used: The Antoine parameters (A, B, C) and range used
    """
    logger.info(f"Tool get_vapor_pressure called for CAS='{cas}', T={temperature_K}K")
    try:
        data = scraper.get_phase_change_data(cas)
        antoine_params = data.get("antoine", [])
        
        valid_param = None
        for param in antoine_params:
            if param.get("T_min") is not None and param.get("T_max") is not None:
                if param["T_min"] <= temperature_K <= param["T_max"]:
                    valid_param = param
                    break
                    
        if not valid_param:
            raise ToolError(f"No valid Antoine parameters found for {cas} at {temperature_K}K.")
            
        A, B, C = valid_param["A"], valid_param["B"], valid_param["C"]
        # log10(P) = A - (B / (T + C)), P in bar
        log10_P = A - (B / (temperature_K + C))
        P_bar = math.pow(10, log10_P)
        P_kPa = P_bar * 100.0
        
        return {
            "vapor_pressure_bar": P_bar,
            "vapor_pressure_kPa": P_kPa,
            "antoine_used": valid_param
        }
    except scraper.ScraperError as e:
        logger.error(f"get_vapor_pressure failed: {e}")
        raise ToolError(str(e))
    except ToolError:
        raise
    except Exception as e:
        logger.exception("Unexpected error in get_vapor_pressure")
        raise ToolError(f"Unexpected error: {e}")

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
