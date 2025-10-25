#!/usr/bin/env python3
"""
Setup and Test Script for Google Sheets Integration
Validates credentials, tests connection, and creates required worksheets
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
from google_sheets_integration import GoogleSheetsManager


def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def check_credentials():
    """Check if credentials file exists and is valid"""
    print_header("STEP 1: Checking Credentials")

    creds_file = "credentials.json"

    if not os.path.exists(creds_file):
        print(f"✗ ERROR: Credentials file not found: {creds_file}")
        print("\nPlease ensure you have:")
        print("  1. Created a Google Cloud Project")
        print("  2. Enabled Google Sheets API")
        print("  3. Created a service account")
        print("  4. Downloaded the JSON credentials file")
        print("  5. Saved it as 'credentials.json' in this directory")
        return False

    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)

        required_fields = ['client_email', 'private_key', 'project_id']
        for field in required_fields:
            if field not in creds:
                print(f"✗ ERROR: Missing field '{field}' in credentials file")
                return False

        print(f"✓ Credentials file found: {creds_file}")
        print(f"✓ Service Account: {creds['client_email']}")
        print(f"✓ Project ID: {creds['project_id']}")

        print("\n⚠ IMPORTANT: Make sure you've shared your Google Sheet with:")
        print(f"   {creds['client_email']}")
        print("   (with Editor permissions)")

        return True

    except json.JSONDecodeError:
        print(f"✗ ERROR: Invalid JSON in {creds_file}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Failed to read credentials: {e}")
        return False


def check_config():
    """Check if config.yaml exists and is valid"""
    print_header("STEP 2: Checking Configuration")

    config_file = "config.yaml"

    if not os.path.exists(config_file):
        print(f"✗ ERROR: Configuration file not found: {config_file}")
        return False

    print(f"✓ Configuration file found: {config_file}")

    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Check required sections
        if 'google_sheets' not in config:
            print("✗ ERROR: Missing 'google_sheets' section in config")
            return False

        if 'spreadsheet_id' not in config['google_sheets']:
            print("✗ ERROR: Missing 'spreadsheet_id' in config")
            return False

        spreadsheet_id = config['google_sheets']['spreadsheet_id']
        print(f"✓ Spreadsheet ID: {spreadsheet_id}")

        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"✓ Sheet URL: {sheet_url}")

        return True

    except Exception as e:
        print(f"✗ ERROR: Failed to read config: {e}")
        return False


def test_connection():
    """Test connection to Google Sheets"""
    print_header("STEP 3: Testing Google Sheets Connection")

    try:
        manager = GoogleSheetsManager()

        print("✓ Authentication successful")
        print("✓ Connected to spreadsheet")

        # Verify connection
        if manager.verify_connection():
            print("✓ Connection verified")
            return manager
        else:
            print("✗ Connection verification failed")
            return None

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPossible issues:")
        print("  1. Credentials file is invalid")
        print("  2. Google Sheets API is not enabled")
        print("  3. Spreadsheet is not shared with service account")
        print("  4. Spreadsheet ID is incorrect")
        return None


def check_worksheets(manager):
    """Check existing worksheets and create missing ones"""
    print_header("STEP 4: Checking Worksheets")

    try:
        # List existing worksheets
        worksheets = manager.list_worksheets()
        print(f"\nExisting worksheets ({len(worksheets)}):")
        for ws in worksheets:
            print(f"  - {ws}")

        # Create missing worksheets
        print("\nChecking for required worksheets...")
        manager.create_missing_worksheets()

        # List again after creation
        worksheets = manager.list_worksheets()
        print(f"\n✓ Total worksheets: {len(worksheets)}")

        return True

    except Exception as e:
        print(f"✗ Failed to check worksheets: {e}")
        return False


def run_test_upload(manager):
    """Run a test data upload"""
    print_header("STEP 5: Test Data Upload")

    try:
        # Create test DataFrame
        test_data = pd.DataFrame({
            'Test_Column_1': ['Setup Test', 'Connection Verified'],
            'Test_Column_2': ['Row 1', 'Row 2'],
            'Status': ['Success', 'Success']
        })

        print("Creating test data:")
        print(test_data.to_string(index=False))

        # Try to upload to a test worksheet
        test_worksheet = "Setup_Test"
        print(f"\nUploading to worksheet: {test_worksheet}")

        success = manager.upload_dataframe(
            test_data,
            test_worksheet,
            mode="replace",
            add_timestamp=True
        )

        if success:
            print(f"✓ Test data uploaded successfully to '{test_worksheet}'")
            print("\n⚠ Please check your Google Sheet to verify the data appeared correctly")
            return True
        else:
            print("✗ Test upload failed")
            return False

    except Exception as e:
        print(f"✗ Test upload failed: {e}")
        return False


def main():
    """Main setup and test workflow"""
    print("\n" + "=" * 70)
    print("  Google Sheets Integration - Setup & Test")
    print("  Renovation Tracker OCR Pipeline")
    print("=" * 70)

    # Step 1: Check credentials
    if not check_credentials():
        print("\n✗ Setup failed: Credentials check failed")
        sys.exit(1)

    # Step 2: Check config
    if not check_config():
        print("\n✗ Setup failed: Configuration check failed")
        sys.exit(1)

    # Step 3: Test connection
    manager = test_connection()
    if not manager:
        print("\n✗ Setup failed: Connection test failed")
        sys.exit(1)

    # Step 4: Check worksheets
    if not check_worksheets(manager):
        print("\n✗ Setup failed: Worksheet check failed")
        sys.exit(1)

    # Step 5: Test upload
    if not run_test_upload(manager):
        print("\n✗ Setup failed: Test upload failed")
        sys.exit(1)

    # Success!
    print_header("✓ SETUP COMPLETE")
    print("All checks passed! Your Google Sheets integration is ready.")
    print("\nNext steps:")
    print("  1. Verify test data appears in your Google Sheet")
    print("  2. Add your handwritten images to the 'images/' folder")
    print("  3. Run the OCR pipeline with: ./venv/bin/python3 handwritten_ocr_pipeline.py --upload-to-sheets")
    print()


if __name__ == "__main__":
    main()
