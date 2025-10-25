#!/usr/bin/env python3
"""
Google Sheets Integration Module for Renovation Tracker OCR Pipeline
Handles authentication, data upload, and worksheet management
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
import yaml


class GoogleSheetsManager:
    """Manages Google Sheets API connections and data operations"""

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize Google Sheets Manager

        Args:
            config_path: Path to YAML configuration file
        """
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.client = None
        self.spreadsheet = None
        self._authenticate()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('GoogleSheetsManager')
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise

    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            creds_file = self.config['google_sheets']['credentials_file']
            self.logger.info(f"Authenticating with credentials: {creds_file}")

            creds = Credentials.from_service_account_file(
                creds_file,
                scopes=self.SCOPES
            )

            self.client = gspread.authorize(creds)
            self.logger.info("✓ Successfully authenticated with Google Sheets API")

            # Open the spreadsheet
            spreadsheet_id = self.config['google_sheets']['spreadsheet_id']
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            self.logger.info(f"✓ Opened spreadsheet: {self.spreadsheet.title}")

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

    def get_worksheet(self, worksheet_name: str):
        """
        Get or create a worksheet by name

        Args:
            worksheet_name: Name of the worksheet

        Returns:
            gspread.Worksheet object
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            self.logger.info(f"✓ Found worksheet: {worksheet_name}")
            return worksheet
        except gspread.WorksheetNotFound:
            self.logger.warning(f"Worksheet '{worksheet_name}' not found, creating...")
            worksheet = self.spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=1000,
                cols=20
            )
            self.logger.info(f"✓ Created worksheet: {worksheet_name}")
            return worksheet

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        worksheet_name: str,
        mode: str = "append",
        add_timestamp: bool = True
    ) -> bool:
        """
        Upload pandas DataFrame to Google Sheets

        Args:
            df: Pandas DataFrame to upload
            worksheet_name: Target worksheet name
            mode: "append" or "replace"
            add_timestamp: Whether to add timestamp column

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info(f"Uploading data to worksheet: {worksheet_name}")
            self.logger.info(f"  Mode: {mode}")
            self.logger.info(f"  Rows: {len(df)}, Columns: {len(df.columns)}")

            worksheet = self.get_worksheet(worksheet_name)

            # Add timestamp if requested
            if add_timestamp:
                df = df.copy()
                df.insert(0, 'Upload_Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Convert DataFrame to list of lists
            data = [df.columns.values.tolist()] + df.values.tolist()

            if mode == "replace":
                # Clear existing data and write new data
                worksheet.clear()
                self._upload_with_retry(worksheet, data)
                self.logger.info(f"✓ Replaced data in {worksheet_name}")

            elif mode == "append":
                # Get existing data to check if headers exist
                existing_data = worksheet.get_all_values()

                if not existing_data or len(existing_data) == 0:
                    # No existing data, write headers + data
                    self._upload_with_retry(worksheet, data)
                else:
                    # Append only data rows (skip header)
                    self._upload_with_retry(worksheet, data[1:], append=True)

                self.logger.info(f"✓ Appended {len(df)} rows to {worksheet_name}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to upload data: {e}")
            return False

    def _upload_with_retry(
        self,
        worksheet,
        data: List[List],
        append: bool = False,
        max_retries: int = 3
    ):
        """
        Upload data with retry logic

        Args:
            worksheet: gspread worksheet object
            data: List of lists to upload
            append: Whether to append or replace
            max_retries: Maximum number of retry attempts
        """
        retry_delay = self.config.get('upload', {}).get('retry_delay', 2)

        for attempt in range(max_retries):
            try:
                if append:
                    worksheet.append_rows(data)
                else:
                    worksheet.update('A1', data)
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Upload attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                else:
                    raise

    def upload_ocr_results(
        self,
        image_filename: str,
        extracted_text: str,
        ocr_data: Dict[str, Any]
    ) -> bool:
        """
        Upload OCR results to appropriate worksheet based on image filename
        Uses intelligent parsing for financial documents

        Args:
            image_filename: Name of the processed image
            extracted_text: Raw extracted text
            ocr_data: Dictionary containing OCR data from pytesseract

        Returns:
            bool: True if successful
        """
        try:
            from transaction_parser import TransactionParser
            from task_parser import TaskParser
            from layout_parser import LayoutParser

            # Get target worksheet from image mappings
            image_mappings = self.config['ocr']['image_mappings']
            worksheet_name = image_mappings.get(image_filename)

            if not worksheet_name:
                self.logger.warning(
                    f"No worksheet mapping found for {image_filename}. "
                    f"Using default 'OCR Results'"
                )
                worksheet_name = "OCR Results"

            # Use intelligent parser for Budget & Expenses worksheet
            if worksheet_name == "Budget & Expenses":
                parser = TransactionParser()
                df = parser.parse_transactions(extracted_text, image_filename)

                if len(df) == 0:
                    self.logger.warning("No transactions found in text")
                    return False

                self.logger.info(f"Parsed {len(df)} transactions from {image_filename}")

                # Upload without timestamp (already has Date Added column)
                success = self.upload_dataframe(
                    df,
                    worksheet_name,
                    mode='append',
                    add_timestamp=False
                )

                return success

            # Use intelligent parser for Task Tracker worksheet
            elif worksheet_name == "Task Tracker":
                parser = TaskParser()
                df = parser.parse_tasks(extracted_text, image_filename)

                if len(df) == 0:
                    self.logger.warning("No tasks found in text")
                    return False

                self.logger.info(f"Parsed {len(df)} tasks from {image_filename}")

                # Upload without timestamp (already has Date Added column)
                success = self.upload_dataframe(
                    df,
                    worksheet_name,
                    mode='append',
                    add_timestamp=False
                )

                return success

            # Use intelligent parser for Property Layout worksheet
            elif worksheet_name == "Property Layout":
                parser = LayoutParser()
                df = parser.parse_layout(extracted_text, image_filename)

                if len(df) == 0:
                    self.logger.warning("No layout records found in text")
                    return False

                self.logger.info(f"Parsed {len(df)} layout records from {image_filename}")

                # Upload without timestamp (already has Date Added column)
                success = self.upload_dataframe(
                    df,
                    worksheet_name,
                    mode='append',
                    add_timestamp=False
                )

                return success

            else:
                # For other worksheets, store as simple text record
                df = pd.DataFrame([{
                    'Source File': image_filename,
                    'Date': datetime.now().strftime("%Y-%m-%d"),
                    'Extracted Text': extracted_text
                }])

                success = self.upload_dataframe(
                    df,
                    worksheet_name,
                    mode='append',
                    add_timestamp=False
                )

                return success

        except Exception as e:
            self.logger.error(f"Failed to upload OCR results: {e}")
            return False

    def verify_connection(self) -> bool:
        """
        Verify connection to Google Sheets

        Returns:
            bool: True if connection is valid
        """
        try:
            self.logger.info("Verifying Google Sheets connection...")

            # Try to access spreadsheet metadata
            title = self.spreadsheet.title
            sheet_count = len(self.spreadsheet.worksheets())

            self.logger.info(f"✓ Connected to: {title}")
            self.logger.info(f"✓ Total worksheets: {sheet_count}")

            return True

        except Exception as e:
            self.logger.error(f"Connection verification failed: {e}")
            return False

    def list_worksheets(self) -> List[str]:
        """
        List all worksheets in the spreadsheet

        Returns:
            List of worksheet names
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            names = [ws.title for ws in worksheets]
            self.logger.info(f"Found {len(names)} worksheets: {', '.join(names)}")
            return names
        except Exception as e:
            self.logger.error(f"Failed to list worksheets: {e}")
            return []

    def create_missing_worksheets(self) -> bool:
        """
        Create any missing worksheets defined in config

        Returns:
            bool: True if successful
        """
        try:
            required_sheets = self.config['google_sheets']['worksheets'].values()
            existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]

            for sheet_name in required_sheets:
                if sheet_name not in existing_sheets:
                    self.logger.info(f"Creating missing worksheet: {sheet_name}")
                    self.spreadsheet.add_worksheet(
                        title=sheet_name,
                        rows=1000,
                        cols=20
                    )

            self.logger.info("✓ All required worksheets exist")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create worksheets: {e}")
            return False


def test_connection(config_path: str = "config.yaml") -> bool:
    """
    Test Google Sheets connection

    Args:
        config_path: Path to config file

    Returns:
        bool: True if connection successful
    """
    try:
        manager = GoogleSheetsManager(config_path)
        return manager.verify_connection()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Google Sheets Integration - Connection Test")
    print("=" * 60 + "\n")

    success = test_connection()

    if success:
        print("\n✓ Google Sheets integration is working correctly!")
    else:
        print("\n✗ Google Sheets integration failed. Check credentials and config.")
