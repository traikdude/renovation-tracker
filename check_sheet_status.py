#!/usr/bin/env python3
"""
Check Google Sheet status and verify upload
"""

from google_sheets_integration import GoogleSheetsManager

def main():
    print("\n" + "="*80)
    print("Google Sheet Status Check")
    print("="*80 + "\n")

    # Initialize Google Sheets manager
    gs_manager = GoogleSheetsManager()

    print(f"📊 Spreadsheet: {gs_manager.spreadsheet.title}")
    print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{gs_manager.config['google_sheets']['spreadsheet_id']}/edit")
    print()

    # Get all worksheets
    worksheets = gs_manager.spreadsheet.worksheets()
    print(f"Found {len(worksheets)} worksheets:")
    for i, ws in enumerate(worksheets, 1):
        print(f"  {i}. {ws.title} ({ws.row_count} rows, {ws.col_count} cols)")
    print()

    # Check Task Tracker specifically
    task_tracker = gs_manager.get_worksheet("Task Tracker")
    print("Task Tracker Details:")
    print(f"  - Total rows: {task_tracker.row_count}")
    print(f"  - Total columns: {task_tracker.col_count}")

    # Get all data from Task Tracker
    all_data = task_tracker.get_all_values()
    print(f"  - Rows with data: {len(all_data)}")

    if len(all_data) > 0:
        print(f"\n  Header row: {all_data[0]}")
        print(f"  Total data rows: {len(all_data) - 1}")

        if len(all_data) > 1:
            print(f"\n  Last 5 rows added:")
            for i, row in enumerate(all_data[-5:], start=len(all_data)-4):
                # Show just first few columns
                preview = row[:5] if len(row) >= 5 else row
                print(f"    Row {i}: {preview}")
    else:
        print("  ⚠️ No data found in Task Tracker!")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
