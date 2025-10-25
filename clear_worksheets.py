#!/usr/bin/env python3
"""
Clear incorrect OCR data from Google Sheets worksheets
"""

from google_sheets_integration import GoogleSheetsManager


def clear_worksheet_data(worksheet_name: str, keep_headers: bool = True):
    """
    Clear data from a worksheet

    Args:
        worksheet_name: Name of worksheet to clear
        keep_headers: If True, only clear rows 2+ (keep header row)
    """
    try:
        manager = GoogleSheetsManager()
        worksheet = manager.get_worksheet(worksheet_name)

        if keep_headers:
            # Get all values
            all_values = worksheet.get_all_values()

            if len(all_values) > 1:
                # Clear everything except row 1 (headers)
                num_rows = len(all_values)
                if num_rows > 1:
                    # Delete rows 2 through end
                    range_to_clear = f"A2:Z{num_rows}"
                    worksheet.batch_clear([range_to_clear])
                    print(f"✓ Cleared {num_rows - 1} data rows from '{worksheet_name}' (kept headers)")
            else:
                print(f"  '{worksheet_name}' has no data to clear")
        else:
            # Clear entire worksheet
            worksheet.clear()
            print(f"✓ Cleared entire '{worksheet_name}' worksheet")

        return True

    except Exception as e:
        print(f"✗ Failed to clear '{worksheet_name}': {e}")
        return False


def main():
    """Clear incorrect data from OCR-populated worksheets"""

    print("\n" + "=" * 70)
    print("Clear Incorrect OCR Data from Google Sheets")
    print("=" * 70 + "\n")

    # Worksheets to clear
    worksheets_to_clear = [
        "Budget & Expenses",
        "Task Tracker",
        "Property Layout"
    ]

    print("This will clear data from the following worksheets:")
    for ws in worksheets_to_clear:
        print(f"  - {ws}")

    confirm = input("\nProceed? (yes/no): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    print("\nClearing worksheets...\n")

    for worksheet_name in worksheets_to_clear:
        clear_worksheet_data(worksheet_name, keep_headers=True)

    print("\n" + "=" * 70)
    print("✓ Worksheets cleared successfully!")
    print("=" * 70)
    print("\nYou can now run the revised OCR pipeline to upload properly formatted data.")


if __name__ == "__main__":
    main()
