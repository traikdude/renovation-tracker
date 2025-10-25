#!/usr/bin/env python3
"""
Upload Moving Guide Tasks to Google Sheets Task Tracker
"""

import pandas as pd
from google_sheets_integration import GoogleSheetsManager


def main():
    """Upload tasks from CSV to Task Tracker worksheet"""

    print("\n" + "="*80)
    print("Moving Guide Tasks → Google Sheets Upload")
    print("="*80 + "\n")

    # Load the parsed tasks
    tasks_file = "extracted_data/moving_guide_tasks.csv"
    print(f"📂 Loading tasks from: {tasks_file}")
    tasks_df = pd.read_csv(tasks_file)

    # Replace NaN values with empty strings (required for Google Sheets API)
    tasks_df = tasks_df.fillna('')

    print(f"✓ Loaded {len(tasks_df)} tasks\n")

    # Display summary
    print("Task Summary:")
    print(f"  • Total Tasks: {len(tasks_df)}")
    print(f"  • High Priority: {len(tasks_df[tasks_df['Priority'] == '🔥 High'])}")
    print(f"  • Medium Priority: {len(tasks_df[tasks_df['Priority'] == '🟡 Medium'])}")
    print(f"  • Low Priority: {len(tasks_df[tasks_df['Priority'] == '🟢 Low'])}")
    print()

    # Initialize Google Sheets manager
    print("🔐 Authenticating with Google Sheets...")
    gs_manager = GoogleSheetsManager()

    # Get Task Tracker worksheet
    worksheet_name = "Task Tracker"
    print(f"📊 Connecting to worksheet: {worksheet_name}")
    worksheet = gs_manager.get_worksheet(worksheet_name)

    # Upload the data
    print(f"\n⬆️  Uploading {len(tasks_df)} tasks to '{worksheet_name}'...")
    print("   (This may take a moment...)\n")

    result = gs_manager.upload_dataframe(
        df=tasks_df,
        worksheet_name=worksheet_name,
        mode='append',  # Append to existing data
        add_timestamp=False  # We already have Date Added column
    )

    if result:
        print("\n" + "="*80)
        print("✅ SUCCESS! Tasks uploaded to Google Sheets")
        print("="*80)
        print(f"\n📋 {len(tasks_df)} tasks added to '{worksheet_name}' worksheet")
        print(f"\n🔗 View your sheet at:")
        print(f"   https://docs.google.com/spreadsheets/d/{gs_manager.config['google_sheets']['spreadsheet_id']}/edit")
        print()
    else:
        print("\n❌ Upload failed. Check the logs for details.\n")


if __name__ == "__main__":
    main()
