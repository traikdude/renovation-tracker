#!/usr/bin/env python3
"""
Transaction Parser for OCR-extracted Renovation Data
Intelligently parses financial transaction information from OCR text
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd


class TransactionParser:
    """Parse OCR text into structured transaction records"""

    # Valid categories (matching dropdown options)
    VALID_CATEGORIES = [
        "Materials",
        "Labor",
        "Utilities",
        "Property Tax",
        "Insurance",
        "Permits",
        "Equipment Rental",
        "Other"
    ]

    # Valid status values (matching dropdown options)
    VALID_STATUSES = [
        "Pending",
        "Paid",
        "Reimbursed",
        "Disputed"
    ]

    def __init__(self):
        """Initialize the transaction parser"""
        self.category_keywords = {
            "Materials": ["cabinets", "flooring", "tile", "paint", "supplies", "materials", "lumber", "hardware"],
            "Labor": ["labor", "contractor", "installation", "plumber", "electrician", "worker"],
            "Utilities": ["electric", "water", "gas", "utility", "utilities"],
            "Property Tax": ["tax", "property tax"],
            "Insurance": ["insurance"],
            "Permits": ["permit", "permits", "license"],
            "Equipment Rental": ["rental", "rent", "equipment"],
        }

        self.status_keywords = {
            "Paid": ["paid", "completed", "done"],
            "Pending": ["pending", "due", "outstanding"],
            "Reimbursed": ["reimbursed", "refunded"],
            "Disputed": ["disputed", "issue", "problem"]
        }

    def parse_transactions(self, text: str, source_file: str) -> pd.DataFrame:
        """
        Parse OCR text into structured transaction records

        Args:
            text: Raw OCR extracted text
            source_file: Source image filename

        Returns:
            DataFrame with columns matching Budget & Expenses sheet structure
        """
        transactions = []

        # Split text into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Try to identify transaction blocks
        current_transaction = {}
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for date patterns
            date_match = self._extract_date(line)
            if date_match and not current_transaction.get('transaction_date'):
                current_transaction['transaction_date'] = date_match

            # Check for item/description
            if re.search(r'item:|description:', line, re.IGNORECASE):
                desc = self._extract_value_after_label(line, ['item:', 'description:'])
                if desc:
                    current_transaction['description'] = desc

            # Check for cost/amount
            if re.search(r'cost:|amount:|price:', line, re.IGNORECASE):
                amount = self._extract_amount(line)
                if amount:
                    current_transaction['amount'] = amount
            # Also check for standalone dollar amounts
            elif not current_transaction.get('amount'):
                amount = self._extract_amount(line)
                if amount:
                    current_transaction['amount'] = amount

            # Check for vendor
            if re.search(r'vendor:|store:|from:', line, re.IGNORECASE):
                vendor = self._extract_value_after_label(line, ['vendor:', 'store:', 'from:'])
                if vendor:
                    current_transaction['vendor'] = vendor

            # Check for status
            if re.search(r'status:', line, re.IGNORECASE):
                status = self._extract_status(line)
                if status:
                    current_transaction['status'] = status

            # Check if we've completed a transaction (found empty line or new item starts)
            if (i < len(lines) - 1 and not lines[i + 1].strip()) or \
               (i == len(lines) - 1) or \
               (re.search(r'item:|description:', lines[i + 1], re.IGNORECASE) and current_transaction.get('description')):

                if current_transaction.get('description') or current_transaction.get('amount'):
                    # Complete the transaction
                    transaction = self._create_transaction_record(current_transaction, source_file)
                    transactions.append(transaction)
                    current_transaction = {}

            i += 1

        # If we still have an incomplete transaction, add it
        if current_transaction.get('description') or current_transaction.get('amount'):
            transaction = self._create_transaction_record(current_transaction, source_file)
            transactions.append(transaction)

        # Create DataFrame with proper column structure
        if not transactions:
            # Return empty DataFrame with correct structure
            return self._create_empty_dataframe()

        df = pd.DataFrame(transactions)
        return df

    def _create_transaction_record(self, data: Dict, source_file: str) -> Dict:
        """
        Create a complete transaction record with all required columns

        Columns (matching Budget & Expenses sheet):
        A: Source File
        B: Date Added
        C: Transaction Date
        D: Category
        E: Description
        F: Amount
        G: Payment Method
        H: Vendor
        I: Status
        J: Notes
        K: Receipt Link
        """
        return {
            'Source File': source_file,
            'Date Added': datetime.now().strftime("%Y-%m-%d"),
            'Transaction Date': data.get('transaction_date', ''),
            'Category': self._infer_category(data.get('description', '')),
            'Description': data.get('description', ''),
            'Amount': data.get('amount', ''),
            'Payment Method': data.get('payment_method', ''),
            'Vendor': data.get('vendor', ''),
            'Status': data.get('status', 'Pending'),
            'Notes': data.get('notes', ''),
            'Receipt Link': f"./images/{source_file}"
        }

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with correct column structure"""
        return pd.DataFrame(columns=[
            'Source File', 'Date Added', 'Transaction Date', 'Category',
            'Description', 'Amount', 'Payment Method', 'Vendor',
            'Status', 'Notes', 'Receipt Link'
        ])

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        # Pattern: Month DD, YYYY or MM/DD/YYYY or YYYY-MM-DD
        patterns = [
            r'(\w+ \d{1,2},? \d{4})',  # October 24, 2025
            r'(\d{1,2}/\d{1,2}/\d{4})',  # 10/24/2025
            r'(\d{4}-\d{2}-\d{2})'  # 2025-10-24
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract dollar amount from text"""
        # Pattern: $X,XXX.XX or $XXX.XX
        match = re.search(r'\$[\d,]+\.?\d*', text)
        if match:
            return match.group(0)
        return None

    def _extract_value_after_label(self, text: str, labels: List[str]) -> Optional[str]:
        """Extract value that comes after a label"""
        for label in labels:
            pattern = rf'{label}\s*(.+?)(?:\||$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove trailing colons, commas, etc.
                value = re.sub(r'[,:;]+$', '', value)
                return value
        return None

    def _extract_status(self, text: str) -> str:
        """Extract and validate status from text"""
        text_lower = text.lower()
        for status, keywords in self.status_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return status
        return "Pending"  # Default status

    def _infer_category(self, description: str) -> str:
        """Infer category from description text"""
        if not description:
            return "Other"

        desc_lower = description.lower()

        # Check each category's keywords
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category

        return "Other"  # Default category

    def parse_text_document(self, text: str, source_file: str, doc_type: str = "financial") -> pd.DataFrame:
        """
        Parse different types of documents (financial, tasks, layout)

        Args:
            text: OCR extracted text
            source_file: Source image filename
            doc_type: Type of document (financial, tasks, layout)

        Returns:
            DataFrame with appropriate structure
        """
        if doc_type == "financial":
            return self.parse_transactions(text, source_file)
        else:
            # For non-financial documents, create a simplified record
            return self._create_simple_record(text, source_file, doc_type)

    def _create_simple_record(self, text: str, source_file: str, doc_type: str) -> pd.DataFrame:
        """Create a simple record for non-financial documents"""
        # Extract any dollar amounts found
        amounts = re.findall(r'\$[\d,]+\.?\d*', text)

        # Create a single record with the text summary
        record = {
            'Source File': source_file,
            'Date Added': datetime.now().strftime("%Y-%m-%d"),
            'Transaction Date': self._extract_date(text) or '',
            'Category': 'Other',
            'Description': f"OCR from {doc_type} document: {text[:100]}...",
            'Amount': amounts[0] if amounts else '',
            'Payment Method': '',
            'Vendor': '',
            'Status': 'Pending',
            'Notes': text[:500],  # Store full text in notes
            'Receipt Link': f"./images/{source_file}"
        }

        return pd.DataFrame([record])


def test_parser():
    """Test the transaction parser with sample text"""
    sample_text = """Budget & Expenses
Date: October 24, 2025

Item: Kitchen Cabinets
Cost: $3,500.00
Vendor: Home Depot
Status: Paid

Item: Tile Flooring
Cost: $1,200.00
Vendor: Lowe's
Status: Pending

Item: Paint Supplies
Cost: $450.00
Vendor: Sherwin Williams
Status: Paid"""

    parser = TransactionParser()
    df = parser.parse_transactions(sample_text, "financial_notes.jpg")

    print("Parsed Transactions:")
    print("=" * 80)
    print(df.to_string(index=False))
    print("\n" + "=" * 80)
    print(f"Total transactions parsed: {len(df)}")


if __name__ == "__main__":
    test_parser()
