import csv
import os
import pytest
import requests_mock
from main import fetch_country_overview, save_to_csv, main
from etl_utils.const import COUNTRIES

def test_fetch_country_overview_success(requests_mock):
    """Test fetching country overview with successful response."""
    url = "https://www.bergfex.at/test-country/schneewerte/"
    html_content = """
    <table class="snow">
        <tr><th>Resort</th><th>Valley</th><th>Mountain</th><th>New</th><th>Lifts</th><th>Update</th></tr>
        <tr>
            <td>
                <div class="h1"><a href="/test-country/test-resort/">Test Resort</a></div>
            </td>
            <td data-value="10">10</td>
            <td data-value="20">20</td>
            <td data-value="5">5</td>
            <td>1/2</td>
            <td data-value="Heute, 10:00">Heute, 10:00</td>
        </tr>
    </table>
    """
    requests_mock.get(url, text=html_content)
    
    data = fetch_country_overview("Test Country", "/test-country/schneewerte/")
    
    assert len(data) == 1
    assert data[0]["country"] == "Test Country"
    assert data[0]["resort_name"] == "Test Resort"
    assert "scraped_at" in data[0]

def test_fetch_country_overview_failure(requests_mock):
    """Test fetching country overview with 404 error."""
    url = "https://www.bergfex.at/test-country/schneewerte/"
    requests_mock.get(url, status_code=404)
    
    data = fetch_country_overview("Test Country", "/test-country/schneewerte/")
    
    assert data == []

def test_save_to_csv(tmp_path):
    """Test saving data to CSV."""
    data = [
        {"country": "AT", "resort_name": "Resort A", "status": "Open", "scraped_at": "2025-01-01"},
        {"country": "DE", "resort_name": "Resort B", "status": "Closed", "scraped_at": "2025-01-01"},
    ]
    output_file = tmp_path / "test_output.csv"
    
    save_to_csv(data, str(output_file))
    
    assert output_file.exists()
    
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["country"] == "AT"
        assert rows[1]["resort_name"] == "Resort B"

def test_main_execution(requests_mock, tmp_path):
    """Test the main function orchestration (with mocked network)."""
    # Mock specific country URLs used in main.py
    # This assumes main.py uses COUNTRIES from const.py
    for country, path in COUNTRIES.items():
        url = "https://www.bergfex.at" + path
        requests_mock.get(url, text="<table class='snow'></table>") # Empty table for simplicity

    # We need to monkeypatch save_to_csv or just check the output if main uses a fixed filename?
    # main.py writes to "bergfex_data.csv" in CWD.
    # To avoid overwriting real data, we should probably modify main to accept a filename or run in tmpdir.
    # But main() doesn't accept arguments. 
    # For this test, we can just run it and check if it runs without error, 
    # but we should be careful about the output file.
    # Let's mock save_to_csv instead to verify it's called.
    
    from unittest.mock import patch, MagicMock
    import argparse
    
    # Mock parse_args directly to bypass sys.argv issues
    with patch("main.save_to_csv") as mock_save, \
         patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
             
        mock_parse_args.return_value = argparse.Namespace(smoke_test=False, force=False)
        main()
        
        assert mock_save.called
        # Check that it gathered data from all countries (even if empty)
        # In this mock, each country returns empty list, so passed data is empty list
        args, _ = mock_save.call_args
        assert args[0] == [] 
