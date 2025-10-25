#!/usr/bin/env python3
"""
Layout Parser for OCR-extracted Property Layout Data
Intelligently parses property/room layout information from OCR text
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class LayoutParser:
    """Parse OCR text into structured property layout records"""

    # Valid rooms/areas (matching dropdown options - NO "General" allowed)
    VALID_ROOMS = [
        "Kitchen",
        "Dining Room",
        "Florida Room",
        "Living Room",
        "Laundry Room",
        "Master Bedroom",
        "Mom's Bedroom",
        "Erik's Bedroom",
        "Guest Bathroom",
        "Garage",
        "Linen Closet",
        "Backyard Area",
        "Frontyard Area"
    ]

    def __init__(self):
        """Initialize the layout parser"""
        # Keywords to identify rooms in text
        self.room_keywords = {
            "Kitchen": ["kitchen"],
            "Dining Room": ["dining", "dining room"],
            "Florida Room": ["florida", "florida room", "sunroom"],
            "Living Room": ["living", "living room", "family room"],
            "Laundry Room": ["laundry", "laundry room"],
            "Master Bedroom": ["master", "master bedroom"],
            "Mom's Bedroom": ["mom's", "mom bedroom", "mom's bedroom"],
            "Erik's Bedroom": ["erik's", "erik bedroom", "erik's bedroom"],
            "Guest Bathroom": ["bathroom", "guest bathroom", "bath"],
            "Garage": ["garage"],
            "Linen Closet": ["linen", "linen closet"],
            "Backyard Area": ["backyard", "back yard", "rear yard"],
            "Frontyard Area": ["frontyard", "front yard"]
        }

    def parse_layout(self, text: str, source_file: str) -> pd.DataFrame:
        """
        Parse OCR text into structured property layout records

        Args:
            text: Raw OCR extracted text
            source_file: Source image filename

        Returns:
            DataFrame with columns matching Property Layout sheet structure
        """
        layouts = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        current_room = None
        current_description = []
        current_features = []
        current_measurements = None
        current_adjacent = []
        current_status = None
        current_notes = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line identifies a room
            room = self._extract_room(line)
            if room:
                # Save previous room if exists
                if current_room:
                    layout = self._create_layout_record(
                        current_room,
                        current_description,
                        current_features,
                        current_measurements,
                        current_adjacent,
                        current_status,
                        current_notes,
                        source_file
                    )
                    layouts.append(layout)

                # Start new room
                current_room = room
                current_description = []
                current_features = []
                current_measurements = None
                current_adjacent = []
                current_status = None
                current_notes = []
                i += 1
                continue

            # Extract measurements (dimensions)
            measurement = self._extract_measurements(line)
            if measurement and current_room:
                if not current_measurements:
                    current_measurements = measurement
                else:
                    current_measurements += f", {measurement}"

            # Check for features/updates keywords
            if re.search(r'feature|update|change|layout|includes?:', line, re.IGNORECASE):
                if current_room:
                    # Next few lines might be features
                    feature_text = self._extract_value_after_label(line, ['feature', 'update', 'change', 'layout', 'includes'])
                    if feature_text:
                        current_features.append(feature_text)

            # Check for adjacent/near keywords
            if re.search(r'adjacent|near|next to|beside:', line, re.IGNORECASE):
                if current_room:
                    adjacent_text = self._extract_value_after_label(line, ['adjacent', 'near', 'next to', 'beside'])
                    if adjacent_text:
                        current_adjacent.append(adjacent_text)

            # Check for status keywords
            if re.search(r'status|current|condition:', line, re.IGNORECASE):
                if current_room:
                    status_text = self._extract_value_after_label(line, ['status', 'current', 'condition'])
                    if status_text:
                        current_status = status_text

            # Check for notes keywords
            if re.search(r'note|notes?:|comment:', line, re.IGNORECASE):
                if current_room:
                    note_text = self._extract_value_after_label(line, ['note', 'notes', 'comment'])
                    if note_text:
                        current_notes.append(note_text)

            # Otherwise, treat as description if we have a current room
            if current_room and len(line) > 5:
                # Skip if it's a label line
                if not re.search(r'^(feature|update|dimension|measurement|adjacent|status|note)s?:', line, re.IGNORECASE):
                    current_description.append(line)

            i += 1

        # Save last room if exists
        if current_room:
            layout = self._create_layout_record(
                current_room,
                current_description,
                current_features,
                current_measurements,
                current_adjacent,
                current_status,
                current_notes,
                source_file
            )
            layouts.append(layout)

        # If no structured rooms found, create a general record
        if not layouts:
            layout = self._create_general_record(text, source_file)
            layouts.append(layout)

        # Create DataFrame with proper column structure
        df = pd.DataFrame(layouts)
        return df

    def _extract_room(self, line: str) -> Optional[str]:
        """Extract room name from line"""
        line_lower = line.lower()

        # Check if line starts with "Room:" or similar
        if re.search(r'^room\s*:', line_lower):
            room_text = line.split(':', 1)[1].strip()
            return self._match_room_name(room_text)

        # Check for room keywords
        for room, keywords in self.room_keywords.items():
            for keyword in keywords:
                # Look for standalone room mentions
                if re.search(rf'\b{keyword}\b', line_lower):
                    # Make sure it's not just part of a description
                    if len(line.split()) <= 4:  # Short line, likely a header
                        return room

        return None

    def _match_room_name(self, text: str) -> Optional[str]:
        """Match text to a valid room name"""
        text_lower = text.lower()

        for room, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return room

        return None

    def _extract_measurements(self, line: str) -> Optional[str]:
        """Extract dimension measurements from line"""
        # Pattern: 12' x 15' or 12 x 15 or 12'x15' or 12ft x 15ft
        patterns = [
            r"(\d+[\'\"]?\s*x\s*\d+[\'\"]?)",  # 12' x 15' or 12 x 15
            r"(\d+\s*ft\.?\s*x\s*\d+\s*ft\.?)",  # 12 ft x 15 ft
            r"(\d+\s*feet?\s*x\s*\d+\s*feet?)",  # 12 feet x 15 feet
            r"dimension[s]?:\s*(.+)",  # Dimensions: ...
            r"size:\s*(.+)",  # Size: ...
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_value_after_label(self, text: str, labels: List[str]) -> Optional[str]:
        """Extract value that comes after a label"""
        for label in labels:
            pattern = rf'{label}s?:\s*(.+?)(?:\n|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove trailing punctuation
                value = re.sub(r'[,:;]+$', '', value)
                return value
        return None

    def _create_layout_record(
        self,
        room: str,
        description: List[str],
        features: List[str],
        measurements: Optional[str],
        adjacent: List[str],
        status: Optional[str],
        notes: List[str],
        source_file: str
    ) -> Dict:
        """
        Create a complete layout record with all required columns

        Columns (matching Property Layout sheet):
        A: Source File
        B: Date Added
        C: Room/Area Name
        D: Description
        E: Features
        F: Measurements
        G: Adjacent To
        H: Current Status
        I: Notes
        """
        return {
            'Source File': source_file,
            'Date Added': datetime.now().strftime("%Y-%m-%d"),
            'Room/Area Name': room,
            'Description': ' '.join(description) if description else '',
            'Features': '; '.join(features) if features else '',
            'Measurements': measurements or '',
            'Adjacent To': ', '.join(adjacent) if adjacent else '',
            'Current Status': status or '',
            'Notes': ' '.join(notes) if notes else ''
        }

    def _create_general_record(self, text: str, source_file: str) -> Dict:
        """Create a layout record when no structured rooms found - leaves Room/Area Name blank"""
        # Try to extract any measurements
        measurements = []
        for line in text.split('\n'):
            measurement = self._extract_measurements(line)
            if measurement:
                measurements.append(measurement)

        return {
            'Source File': source_file,
            'Date Added': datetime.now().strftime("%Y-%m-%d"),
            'Room/Area Name': '',  # Leave blank if no valid room identified
            'Description': text[:200] if text else '',  # First 200 chars
            'Features': '',
            'Measurements': ', '.join(measurements) if measurements else '',
            'Adjacent To': '',
            'Current Status': '',
            'Notes': text[:500] if len(text) > 200 else ''  # Store full text in notes
        }

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with correct column structure"""
        return pd.DataFrame(columns=[
            'Source File', 'Date Added', 'Room/Area Name', 'Description',
            'Features', 'Measurements', 'Adjacent To', 'Current Status', 'Notes'
        ])


def test_parser():
    """Test the layout parser with sample text"""
    sample_text = """Property Layout Notes

Room: Kitchen
Dimensions: 12' x 15'

Layout Changes:
- Move sink to island
- Extend counter on east wall
- Add pantry closet
- New lighting fixtures

Room: Master Bathroom
Dimensions: 8' x 10'

Updates:
- Replace tub with walk-in shower
- Double vanity
- Heated floors

Adjacent: Master Bedroom
Status: In progress
"""

    parser = LayoutParser()
    df = parser.parse_layout(sample_text, "layout_notes.jpg")

    print("Parsed Layout Records:")
    print("=" * 120)
    print(df.to_string(index=False))
    print("\n" + "=" * 120)
    print(f"Total records parsed: {len(df)}")


if __name__ == "__main__":
    test_parser()
