from pathlib import Path
from custom_components.bergfex.parser import parse_resort_page


def test_parse_open_pistes_hintertux():
    """Test parsing of open pistes for Hintertux (hintertux.html)."""
    fixture_path = Path(__file__).parent / "fixtures" / "hintertux.html"
    with open(fixture_path, "r") as f:
        html = f.read()

    data = parse_resort_page(html, lang="at")

    assert "open_pistes" in data
    assert isinstance(data["open_pistes"], list)
    assert len(data["open_pistes"]) > 0

    # Check for some specific open slopes from hintertux.html
    open_pistes = data["open_pistes"]
    names = [s["name"] for s in open_pistes]
    assert "1 schwarze Pfanne - beschneit" in names  # icon-status2
    assert "2 Spannagelabfahrt beschneit" in names  # icon-status1

    # Check details for one slope
    p3 = next(s for s in open_pistes if s["name"] == "3")
    assert p3["difficulty"]["id"] == "1"  # leicht (blue) in Hintertux

    # Check that closed slopes are NOT in the list
    assert "1a Waldabfahrt" not in names  # icon-status0
    assert "2b" not in names  # icon-status0


def test_parse_open_pistes_ankogel():
    """Test parsing of open pistes for Ankogel (ankogel.html)."""
    fixture_path = Path(__file__).parent / "fixtures" / "ankogel.html"
    with open(fixture_path, "r") as f:
        html = f.read()

    data = parse_resort_page(html, lang="at")

    # It should not have open_pistes if the table is missing
    assert "open_pistes" not in data


def test_parse_open_pistes_airolo():
    """Test parsing of open pistes for Airolo (airolo.html)."""
    fixture_path = Path(__file__).parent / "fixtures" / "airolo.html"
    with open(fixture_path, "r") as f:
        html = f.read()

    data = parse_resort_page(html, lang="it")

    assert "open_pistes" in data
    open_pistes = data["open_pistes"]
    assert len(open_pistes) > 0

    # Check Comasnè details
    # Comasnè has number 11, difficulty mittel (2)
    comasne = next((s for s in open_pistes if s["name"] == "Comasnè"), None)
    assert comasne is not None
    assert comasne["number"] == "11"
    assert comasne["difficulty"]["id"] == "2"
    assert comasne["difficulty"]["description"] == "mittel"

    # Check a blue slope (easy)
    pescium = next((s for s in open_pistes if s["name"] == "Pesciüm"), None)
    assert pescium is not None
    assert pescium["number"] == "12"
    assert pescium["difficulty"]["id"] == "1"
    assert pescium["difficulty"]["description"] == "leicht"

    # Check length for Winter Wanderwege
    wanderwege = next(
        (s for s in open_pistes if "Winter Wanderwege" in s["name"]), None
    )
    assert wanderwege is not None
    assert wanderwege["length"] == "3.000 m"
    assert wanderwege["difficulty"]["id"] == "9"
