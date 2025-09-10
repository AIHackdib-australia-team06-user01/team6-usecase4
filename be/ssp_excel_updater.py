import json
import openpyxl
from typing import List, Dict


def update_ssp_excel(json_path: str, excel_path: str, output_path: str) -> None:
    """
    Update the ASD blueprint SSP Excel template with results from a JSON file.
    Args:
        json_path: Path to the JSON file containing result objects.
        excel_path: Path to the ASD blueprint SSP Excel template (xlsx).
        output_path: Path to save the updated Excel file.
    """
    # Load JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        results: List[Dict[str, str]] = json.load(f)

    # Map ISM control to result and comment
    result_map = {item['ism-control']: item for item in results}

    # Load Excel workbook
    wb = openpyxl.load_workbook(excel_path)
    try:
        ws = wb['Essential Eight']
    except KeyError:
        raise ValueError("Worksheet 'Essential Eight' not found in the Excel file")

    # Iterate through rows and update columns L and M
    for row in ws.iter_rows(min_row=2):  # Assuming first row is header
        ism_control = str(row[1].value).strip()  # Column B (index 1)
        if ism_control in result_map:
            row[11].value = result_map[ism_control]['result']   # Column L (index 11)
            row[12].value = result_map[ism_control]['comment']  # Column M (index 12)

    # Save updated workbook
    wb.save(output_path)
