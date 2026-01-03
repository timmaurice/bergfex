from etl_utils.parser import parse_resort_page, get_text_from_dd
import requests
from bs4 import BeautifulSoup

def test_parsing():
    url = "https://www.bergfex.at/mayrhofen/schneebericht/"
    print(f"Fetching {url}...")
    resp = requests.get(url)
    resp.raise_for_status()
    
    html = resp.text
    print(f"Fetched {len(html)} bytes.")
    
    # Test helper directly
    soup = BeautifulSoup(html, "lxml")
    print("\n--- Testing get_text_from_dd ---")
    vals = {
        "Schneezustand": get_text_from_dd(soup, "Schneezustand"),
        "Lawinenwarnstufe": get_text_from_dd(soup, "Lawinenwarnstufe"),
        "Pistenzustand": get_text_from_dd(soup, "Pistenzustand")
    }
    for k, v in vals.items():
        print(f"'{k}': {repr(v)}")

    # Test full parser
    print("\n--- Testing parse_resort_page ---")
    data = parse_resort_page(html, "/mayrhofen/")
    
    keys_to_check = ["snow_condition", "avalanche_warning", "slope_condition"]
    for k in keys_to_check:
        print(f"Result '{k}': {data.get(k)}")

if __name__ == "__main__":
    test_parsing()
