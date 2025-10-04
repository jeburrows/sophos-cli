"""Utility functions for the Sophos CLI"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def export_to_csv(data: List[Dict], filename: str, fieldnames: List[str]) -> str:
    """
    Export data to a CSV file

    Args:
        data: List of dictionaries containing the data
        filename: Base filename for the CSV (without extension)
        fieldnames: List of field names for the CSV columns

    Returns:
        str: The full path to the created CSV file
    """
    # Add timestamp to filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{filename}_{timestamp}.csv"

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / csv_filename

    # Write to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return str(filepath)
