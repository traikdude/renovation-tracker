#!/usr/bin/env python3
"""
Moving Guide Text Parser
Parses the comprehensive moving guide text into structured tasks for Task Tracker sheet
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd


class MovingGuideParser:
    """Parse moving guide text into structured task records"""

    # Valid rooms (matching dropdown options)
    VALID_ROOMS = [
        "Kitchen", "Dining Room", "Florida Room", "Living Room",
        "Laundry Room", "Master Bedroom", "Mom's Bedroom", "Erik's Bedroom",
        "Bathroom", "Garage", "Closet", "Pantry", "General"
    ]

    # Valid priorities (matching dropdown options with emojis)
    VALID_PRIORITIES = {
        "high": "🔥 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low"
    }

    # Valid statuses
    VALID_STATUSES = [
        "Not Started", "In Progress", "Completed", "On Hold", "Blocked"
    ]

    def __init__(self, moving_day_date: Optional[str] = None):
        """
        Initialize the moving guide parser

        Args:
            moving_day_date: Target moving day (YYYY-MM-DD format).
                           If None, assumes 14 days from today.
        """
        if moving_day_date:
            self.moving_day = datetime.strptime(moving_day_date, "%Y-%m-%d")
        else:
            # Default: assume moving day is 2 weeks from now
            self.moving_day = datetime.now() + timedelta(days=14)

        # Timeline to days offset (relative to moving day)
        self.timeline_mappings = {
            "4 weeks before": 28,
            "3-4 weeks out": 25,
            "3 weeks before": 21,
            "2-4 weeks": 21,
            "2 weeks before": 14,
            "2 weeks out": 14,
            "1-2 weeks out": 10,
            "1 week before": 7,
            "week of move": 3,
            "moving day": 0,
            "day after move": -1,
            "week 1 after move": -7,
            "weeks 2-4 after move": -14,
            "arrival day": 0,
            "first 2 hours": 0,
            "day 1-2": -1,
            "week 1-2": -7,
        }

        # Room keyword mappings
        self.room_keywords = {
            "Kitchen": ["kitchen", "dishes", "appliances", "coffee maker", "canned goods"],
            "Living Room": ["living room", "living areas", "furniture"],
            "Master Bedroom": ["bedroom", "bed frames", "mattress"],
            "Bathroom": ["bathroom", "toiletries"],
            "Garage": ["garage", "truck", "dolly", "hand truck", "tools"],
            "General": ["supplies", "boxes", "packing", "moving", "utilities"]
        }

        # Priority keywords
        self.priority_keywords = {
            "high": [
                "essential", "critical", "first", "immediate", "safety",
                "urgent", "must", "priority 1", "important"
            ],
            "medium": [
                "priority 2", "day 1", "verify", "confirm", "update"
            ],
            "low": [
                "priority 3", "week 1-2", "explore", "final"
            ]
        }

    def parse_guide(self, text: str) -> pd.DataFrame:
        """
        Parse the complete moving guide text into structured tasks

        Args:
            text: Raw moving guide text

        Returns:
            DataFrame with Task Tracker columns
        """
        tasks = []
        lines = text.split('\n')

        current_section = None
        current_timeline = None
        current_priority = "medium"

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Detect section headers and extract timeline
            section_info = self._extract_section_info(line)
            if section_info:
                current_section = section_info['section']
                current_timeline = section_info.get('timeline')
                current_priority = section_info.get('priority', 'medium')
                continue

            # Extract checklist items (lines starting with [ ])
            checklist_task = self._extract_checklist_item(line)
            if checklist_task:
                task = self._create_task_record(
                    checklist_task,
                    current_section or "General",
                    current_timeline,
                    current_priority
                )
                tasks.append(task)
                continue

            # Extract action steps
            action_step = self._extract_action_step(line, i, lines)
            if action_step:
                task = self._create_task_record(
                    action_step,
                    current_section or "General",
                    current_timeline,
                    current_priority
                )
                tasks.append(task)

        if not tasks:
            return self._create_empty_dataframe()

        df = pd.DataFrame(tasks)
        return df

    def _extract_section_info(self, line: str) -> Optional[Dict]:
        """Extract section name and timeline from header lines"""
        line_lower = line.lower()

        # Check for timeline patterns in the line
        timeline = None
        priority = "medium"

        # Pattern 1: "🗓️ WEEKS 3-4 BEFORE MOVING DAY"
        if re.search(r'weeks?\s+\d+-?\d*\s+before', line_lower):
            match = re.search(r'weeks?\s+(\d+)-?(\d*)\s+before', line_lower)
            if match:
                week_num = int(match.group(1))
                timeline = f"{week_num} weeks before"
                priority = "medium" if week_num >= 2 else "high"

        # Pattern 2: "WEEK OF MOVE"
        elif 'week of move' in line_lower:
            timeline = "week of move"
            priority = "high"

        # Pattern 3: "MOVING DAY"
        elif 'moving day' in line_lower and 'before' not in line_lower:
            timeline = "moving day"
            priority = "high"

        # Pattern 4: "DAY AFTER MOVE" or "WEEK 1 AFTER MOVE"
        elif re.search(r'(day|week\s+\d+)\s+after\s+move', line_lower):
            match = re.search(r'(day|week\s+\d+)\s+after\s+move', line_lower)
            timeline = match.group(0)
            priority = "high" if 'day' in timeline else "medium"

        # Pattern 5: "ARRIVAL DAY"
        elif 'arrival' in line_lower:
            timeline = "arrival day"
            priority = "high"

        if timeline or any(indicator in line_lower for indicator in ['checklist', 'phase', 'guide', 'reference']):
            return {
                'section': line.strip('🗓️📅💪🚚🏠🆘🏷️✅ ').strip(':').strip(),
                'timeline': timeline,
                'priority': priority
            }

        return None

    def _extract_checklist_item(self, line: str) -> Optional[str]:
        """Extract task from checklist format [ ] item"""
        # Match checkbox patterns: [ ] or [X] or [x]
        match = re.match(r'^\[\s*[xX✓✔]?\s*\]\s+(.+)$', line)
        if match:
            task_text = match.group(1).strip()
            # Remove quantity placeholders and dates
            task_text = re.sub(r'\s+-\s+(Qty|Date|Dates|Platform|Drop-off scheduled|Rolls):?\s*_+', '', task_text)
            task_text = re.sub(r'\s+-\s+Reserved/Purchased:?\s*_+', '', task_text)

            # Only return if substantial task (not just a category)
            if len(task_text) > 5:
                return task_text

        return None

    def _extract_action_step(self, line: str, index: int, all_lines: List[str]) -> Optional[str]:
        """Extract action steps from 'Action Step X:' sections"""
        # Look for "Action Step X:" patterns
        if re.match(r'^Action\s+Step\s+\d+:', line, re.IGNORECASE):
            # Get the action title (rest of the line after "Action Step X:")
            action_match = re.search(r'^Action\s+Step\s+\d+:\s*(.+)$', line, re.IGNORECASE)
            if action_match:
                return action_match.group(1).strip()

        return None

    def _create_task_record(
        self,
        task_text: str,
        section: str,
        timeline: Optional[str],
        priority_level: str
    ) -> Dict:
        """
        Create a complete task record with all required columns

        Task Tracker Columns:
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
        # Infer room from task text
        room = self._infer_room(task_text)

        # Determine priority
        priority = self._determine_priority(task_text, priority_level)

        # Calculate due date based on timeline
        due_date = self._calculate_due_date(timeline)

        # Build notes with section and timeline
        notes_parts = []
        if section:
            notes_parts.append(f"Section: {section}")
        if timeline:
            notes_parts.append(f"Timeline: {timeline}")
        notes = " | ".join(notes_parts)

        return {
            'Source File': 'moving_guide.txt',
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

    def _calculate_due_date(self, timeline: Optional[str]) -> Optional[str]:
        """Calculate due date based on timeline relative to moving day"""
        if not timeline:
            return None

        timeline_lower = timeline.lower()

        # Try exact match first
        if timeline_lower in self.timeline_mappings:
            days_offset = self.timeline_mappings[timeline_lower]
            due_date = self.moving_day - timedelta(days=days_offset)
            return due_date.strftime("%Y-%m-%d")

        # Try pattern matching
        for pattern, days_offset in self.timeline_mappings.items():
            if pattern in timeline_lower:
                due_date = self.moving_day - timedelta(days=days_offset)
                return due_date.strftime("%Y-%m-%d")

        return None

    def _infer_room(self, task_text: str) -> str:
        """Infer room from task description"""
        task_lower = task_text.lower()

        for room, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in task_lower:
                    return room

        return "General"

    def _determine_priority(self, task_text: str, base_priority: str) -> str:
        """Determine priority from task text and context"""
        task_lower = task_text.lower()

        # Check for priority keywords in task text
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in task_lower:
                    return self.VALID_PRIORITIES[priority]

        # Use base priority from section
        return self.VALID_PRIORITIES.get(base_priority, "🟡 Medium")

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with correct column structure"""
        return pd.DataFrame(columns=[
            'Source File', 'Date Added', 'Room', 'Task Description',
            'Priority', 'Status', 'Assigned To', 'Start Date', 'Due Date',
            'Completion Date', 'Estimated Cost', 'Actual Cost', 'Notes'
        ])


def main():
    """Main function to parse moving guide and output to CSV/Excel"""
    import sys

    # Read the moving guide text from file or stdin
    if len(sys.argv) > 1:
        # Read from file
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            guide_text = f.read()
    else:
        print("Please provide the moving guide text file as an argument")
        print("Usage: python moving_guide_parser.py <text_file>")
        sys.exit(1)

    # Optional: specify moving day
    moving_day = sys.argv[2] if len(sys.argv) > 2 else None

    # Parse the guide
    parser = MovingGuideParser(moving_day_date=moving_day)
    tasks_df = parser.parse_guide(guide_text)

    # Output results
    print(f"\n{'='*120}")
    print(f"Moving Guide Parser Results")
    print(f"{'='*120}")
    print(f"Moving Day: {parser.moving_day.strftime('%Y-%m-%d')}")
    print(f"Total Tasks Extracted: {len(tasks_df)}")
    print(f"{'='*120}\n")

    # Display sample tasks
    if len(tasks_df) > 0:
        print("Sample Tasks (first 10):")
        print(tasks_df.head(10).to_string(index=False))
        print(f"\n... and {len(tasks_df) - 10} more tasks\n")

    # Save to files
    output_csv = "extracted_data/moving_guide_tasks.csv"
    output_excel = "extracted_data/moving_guide_tasks.xlsx"

    tasks_df.to_csv(output_csv, index=False, encoding='utf-8')
    tasks_df.to_excel(output_excel, index=False, engine='openpyxl')

    print(f"✅ Tasks saved to:")
    print(f"   - CSV: {output_csv}")
    print(f"   - Excel: {output_excel}")
    print(f"\nNext step: Upload to Google Sheets using:")
    print(f"   python google_sheets_integration.py --upload-tasks moving_guide_tasks.csv")


if __name__ == "__main__":
    main()
