#!/usr/bin/env python3
"""
Task Parser for OCR-extracted Checklist Data
Intelligently parses task checklist information from OCR text
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd


class TaskParser:
    """Parse OCR text into structured task records for Task Tracker"""

    # Valid rooms (matching dropdown options)
    VALID_ROOMS = [
        "Kitchen",
        "Dining Room",
        "Florida Room",
        "Living Room",
        "Laundry Room",
        "Master Bedroom",
        "Mom's Bedroom",
        "Erik's Bedroom",
        "Bathroom",
        "Garage",
        "Closet",
        "Pantry",
        "General"
    ]

    # Valid priorities (matching dropdown options with emojis)
    VALID_PRIORITIES = [
        "🔥 High",
        "🟡 Medium",
        "🟢 Low"
    ]

    # Valid statuses (matching dropdown options)
    VALID_STATUSES = [
        "Not Started",
        "In Progress",
        "Completed",
        "On Hold",
        "Blocked"
    ]

    def __init__(self):
        """Initialize the task parser"""
        # Keywords to identify rooms in task descriptions
        self.room_keywords = {
            "Kitchen": ["kitchen", "cabinets", "countertop", "sink", "stove", "oven", "dishwasher"],
            "Dining Room": ["dining", "dining room"],
            "Florida Room": ["florida", "florida room", "sunroom"],
            "Living Room": ["living", "living room"],
            "Laundry Room": ["laundry", "washer", "dryer"],
            "Master Bedroom": ["master", "master bedroom"],
            "Mom's Bedroom": ["mom's", "mom bedroom"],
            "Erik's Bedroom": ["erik's", "erik bedroom"],
            "Bathroom": ["bathroom", "toilet", "shower", "bathtub", "vanity"],
            "Garage": ["garage", "driveway"],
            "Closet": ["closet"],
            "Pantry": ["pantry"],
        }

        # Keywords to identify priority (return values with emojis)
        self.priority_keywords = {
            "🔥 High": ["urgent", "asap", "critical", "important", "high priority", "must", "required"],
            "🟢 Low": ["optional", "later", "eventually", "low priority", "nice to have"],
        }

        # Timeline mappings to due dates
        self.timeline_mappings = {
            "two months before": 60,
            "one month before": 30,
            "three weeks before": 21,
            "two weeks before": 14,
            "one week before": 7,
            "last few days": 3,
            "few days before": 3,
            "moving day": 0,
            "after moving": -7,
            "few days after": -7,
        }

    def parse_tasks(self, text: str, source_file: str) -> pd.DataFrame:
        """
        Parse OCR text into structured task records

        Args:
            text: Raw OCR extracted text
            source_file: Source image filename

        Returns:
            DataFrame with columns matching Task Tracker sheet structure
        """
        tasks = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        current_timeline = None
        current_due_date = None

        for line in lines:
            # Check if this line defines a timeline/section
            timeline = self._extract_timeline(line)
            if timeline:
                current_timeline = timeline
                current_due_date = self._calculate_due_date(timeline)
                continue

            # Check if this looks like a task item
            task_text = self._extract_task_text(line)
            if task_text:
                task = self._create_task_record(
                    task_text,
                    source_file,
                    current_timeline,
                    current_due_date
                )
                tasks.append(task)

        # Create DataFrame with proper column structure
        if not tasks:
            return self._create_empty_dataframe()

        df = pd.DataFrame(tasks)
        return df

    def _extract_timeline(self, line: str) -> Optional[str]:
        """Extract timeline/section header from line"""
        line_lower = line.lower()

        # Check for timeline keywords
        for timeline_key in self.timeline_mappings.keys():
            if timeline_key in line_lower and ("before" in line_lower or "after" in line_lower or "day" in line_lower):
                return timeline_key

        return None

    def _calculate_due_date(self, timeline: str) -> Optional[str]:
        """Calculate due date based on timeline"""
        if not timeline:
            return None

        days_offset = self.timeline_mappings.get(timeline.lower())
        if days_offset is not None:
            # Calculate date relative to today (or you could use a fixed "moving day" date)
            due_date = datetime.now() + timedelta(days=days_offset)
            return due_date.strftime("%Y-%m-%d")

        return None

    def _extract_task_text(self, line: str) -> Optional[str]:
        """Extract task text from line, removing checkboxes and markers"""
        # Remove common checkbox markers
        cleaned = re.sub(r'^[\[\(]?\s*[xX✓✔]?\s*[\]\)]?\s*', '', line)
        cleaned = re.sub(r'^[•\-\*]\s*', '', cleaned)
        cleaned = re.sub(r'^[DQO1Il]\s+', '', cleaned)  # OCR artifacts
        cleaned = cleaned.strip()

        # Only return if it looks like a task (has some substance)
        if len(cleaned) > 5 and not self._is_section_header(cleaned):
            return cleaned

        return None

    def _is_section_header(self, text: str) -> bool:
        """Check if text is a section header rather than a task"""
        text_lower = text.lower()

        # Section headers often contain these words
        section_indicators = [
            "before your move",
            "after moving",
            "moving day",
            "to-do list",
            "checklist"
        ]

        for indicator in section_indicators:
            if indicator in text_lower:
                return True

        return False

    def _create_task_record(
        self,
        task_text: str,
        source_file: str,
        timeline: Optional[str],
        due_date: Optional[str]
    ) -> Dict:
        """
        Create a complete task record with all required columns

        Columns (matching Task Tracker sheet):
        A: Source File
        B: Date Added
        C: Room
        D: Task Description
        E: Priority
        F: Status
        G: Assigned To
        H: Start Date
        I: Due Date
        J: Completion Date
        K: Estimated Cost
        L: Actual Cost
        M: Notes
        """
        # Infer room from task description
        room = self._infer_room(task_text)

        # Infer priority
        priority = self._infer_priority(task_text)

        # Build notes with timeline if available
        notes = f"Timeline: {timeline}" if timeline else ""

        return {
            'Source File': source_file,
            'Date Added': datetime.now().strftime("%Y-%m-%d"),
            'Room': room,
            'Task Description': task_text,
            'Priority': priority,
            'Status': 'Not Started',
            'Assigned To': '',
            'Start Date': '',
            'Due Date': due_date or '',
            'Completion Date': '',
            'Estimated Cost': '',
            'Actual Cost': '',
            'Notes': notes
        }

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with correct column structure"""
        return pd.DataFrame(columns=[
            'Source File', 'Date Added', 'Room', 'Task Description',
            'Priority', 'Status', 'Assigned To', 'Start Date', 'Due Date',
            'Completion Date', 'Estimated Cost', 'Actual Cost', 'Notes'
        ])

    def _infer_room(self, task_description: str) -> str:
        """Infer room from task description"""
        if not task_description:
            return "General"

        desc_lower = task_description.lower()

        # Check each room's keywords
        for room, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return room

        return "General"  # Default room

    def _infer_priority(self, task_description: str) -> str:
        """Infer priority from task description"""
        if not task_description:
            return "🟡 Medium"

        desc_lower = task_description.lower()

        # Check priority keywords
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return priority

        return "🟡 Medium"  # Default priority

    def _extract_cost(self, text: str) -> Optional[str]:
        """Extract dollar amount from text"""
        match = re.search(r'\$[\d,]+\.?\d*', text)
        if match:
            return match.group(0)
        return None


def test_parser():
    """Test the task parser with sample text"""
    sample_text = """
Two Months Before Your Move
Prepare a Budget
Book a Mover
Get insured
Contact Your Kid's School

One Week Before Your Move
Refill Prescriptions
Pack your Suitcase/Emergency Bag
Clean Out Your Safe or Safety Deposit Box
Find Shipping Bolts for Washer and Dryer (if front-loading)

Moving Day
Get Up Early
Prepare a Meal or Get Take Out
Be Ready to Move
Protect Your Property
Start Cleaning
Final Walkthrough
"""

    parser = TaskParser()
    df = parser.parse_tasks(sample_text, "test_checklist.jpg")

    print("Parsed Tasks:")
    print("=" * 120)
    print(df.to_string(index=False))
    print("\n" + "=" * 120)
    print(f"Total tasks parsed: {len(df)}")


if __name__ == "__main__":
    test_parser()
