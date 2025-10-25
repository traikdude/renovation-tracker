#!/usr/bin/env python3
"""
Enhanced Moving Guide Parser - Extracts ALL tasks including checkboxes
"""

import re
from datetime import datetime, timedelta
import pandas as pd


def preprocess_text(text):
    """Split checkbox items that are on the same line"""
    # Replace "[ ]" with newline + "[ ]" to separate checkbox items
    text = re.sub(r'(\[ \])', r'\n\1', text)
    return text


def parse_moving_guide(text, moving_day_str=None):
    """Parse the complete moving guide into tasks"""

    # Set moving day
    if moving_day_str:
        moving_day = datetime.strptime(moving_day_str, "%Y-%m-%d")
    else:
        moving_day = datetime.now() + timedelta(days=14)  # Default: 2 weeks from now

    # Timeline mappings (days before moving day)
    timeline_map = {
        "3-4 weeks": 25,
        "1-2 weeks": 10,
        "week of move": 3,
        "moving day": 0,
        "day after": -1,
        "week 1 after": -7,
        "weeks 2-4 after": -14,
    }

    # Preprocess to split checkbox items
    text = preprocess_text(text)
    lines = text.split('\n')

    tasks = []
    current_section = ""
    current_timeline = None
    current_priority = "🟡 Medium"

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Detect section headers
        if re.search(r'(WEEKS?\s+\d+-?\d*\s+(BEFORE|AFTER)|MOVING DAY|ARRIVAL|DAY AFTER|WEEK \d+)', line, re.IGNORECASE):
            current_section = line.strip('🗓️📅💪🚚🏠🆘🏷️✅ ').strip(':').strip()

            # Extract timeline
            line_lower = line.lower()
            if '3-4 weeks' in line_lower or '4 weeks' in line_lower:
                current_timeline = "3-4 weeks"
                current_priority = "🟡 Medium"
            elif '1-2 weeks' in line_lower or '2 weeks' in line_lower:
                current_timeline = "1-2 weeks"
                current_priority = "🔥 High"
            elif 'week of move' in line_lower:
                current_timeline = "week of move"
                current_priority = "🔥 High"
            elif 'moving day' in line_lower and 'before' not in line_lower:
                current_timeline = "moving day"
                current_priority = "🔥 High"
            elif 'day after' in line_lower:
                current_timeline = "day after"
                current_priority = "🔥 High"
            elif 'week 1 after' in line_lower:
                current_timeline = "week 1 after"
                current_priority = "🟡 Medium"
            elif 'weeks 2-4 after' in line_lower:
                current_timeline = "weeks 2-4 after"
                current_priority = "🟢 Low"
            continue

        # Extract checkbox items
        checkbox_match = re.match(r'^\[\s*[xX✓✔]?\s*\]\s+(.+)$', line)
        if checkbox_match:
            task_text = checkbox_match.group(1).strip()

            # Clean up quantity/date placeholders
            task_text = re.sub(r'\s*-\s*(Qty|Date|Dates|Platform|Drop-off scheduled|Rolls|Reserved/Purchased):?\s*_+.*$', '', task_text)

            if len(task_text) > 5:  # Only substantial tasks
                task = create_task(task_text, current_section, current_timeline, current_priority, moving_day, timeline_map)
                tasks.append(task)
            continue

        # Extract Action Steps
        if re.match(r'^Action\s+Step\s+\d+:', line, re.IGNORECASE):
            action_match = re.search(r'^Action\s+Step\s+\d+:\s*(.+)$', line, re.IGNORECASE)
            if action_match:
                task_text = action_match.group(1).strip()
                # Also get the next line for context
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not re.match(r'(Action|WEEK|MOVING|DAY|^\[)', next_line):
                        task_text += " " + next_line

                task = create_task(task_text, current_section, current_timeline, current_priority, moving_day, timeline_map)
                tasks.append(task)

    # Create DataFrame
    df = pd.DataFrame(tasks)
    return df


def create_task(task_text, section, timeline, priority, moving_day, timeline_map):
    """Create a task record"""

    # Calculate due date
    due_date = ""
    if timeline and timeline in timeline_map:
        days_offset = timeline_map[timeline]
        date_obj = moving_day - timedelta(days=days_offset)
        due_date = date_obj.strftime("%Y-%m-%d")

    # Infer room from task text
    room = infer_room(task_text)

    # Enhance priority based on keywords
    final_priority = enhance_priority(task_text, priority)

    # Build notes
    notes = f"Section: {section}"
    if timeline:
        notes += f" | Timeline: {timeline}"

    return {
        'Source File': 'moving_guide.txt',
        'Date Added': datetime.now().strftime("%Y-%m-%d"),
        'Room': room,
        'Task Description': task_text[:500],  # Limit to 500 chars
        'Priority': final_priority,
        'Status': 'Not Started',
        'Assigned To': '',
        'Start Date': '',
        'Due Date': due_date,
        'Completion Date': '',
        'Estimated Cost': '',
        'Actual Cost': '',
        'Notes': notes
    }


def infer_room(text):
    """Infer room from task description"""
    text_lower = text.lower()

    room_keywords = {
        "Kitchen": ["kitchen", "dishes", "appliances", "coffee maker", "canned goods", "kitchenware"],
        "Living Room": ["living room", "living areas", "furniture"],
        "Master Bedroom": ["bedroom", "bed", "mattress"],
        "Bathroom": ["bathroom", "toiletries"],
        "Garage": ["garage", "truck", "dolly", "hand truck", "loading", "transport"],
        "General": []
    }

    for room, keywords in room_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return room

    return "General"


def enhance_priority(text, base_priority):
    """Enhance priority based on keywords in text"""
    text_lower = text.lower()

    high_keywords = ["essential", "critical", "first", "immediate", "safety", "urgent", "must", "important", "priority 1"]
    low_keywords = ["priority 3", "explore", "final", "optional"]

    for keyword in high_keywords:
        if keyword in text_lower:
            return "🔥 High"

    for keyword in low_keywords:
        if keyword in text_lower:
            return "🟢 Low"

    return base_priority


# Main execution
if __name__ == "__main__":
    import sys

    # Read input file
    if len(sys.argv) < 2:
        print("Usage: python parse_moving_guide.py <input_file> [moving_day_YYYY-MM-DD]")
        sys.exit(1)

    input_file = sys.argv[1]
    moving_day = sys.argv[2] if len(sys.argv) > 2 else None

    with open(input_file, 'r', encoding='utf-8') as f:
        guide_text = f.read()

    # Parse
    tasks_df = parse_moving_guide(guide_text, moving_day)

    # Display results
    print(f"\n{'='*120}")
    print(f"Moving Guide Parser - Complete Results")
    print(f"{'='*120}")
    if moving_day:
        print(f"Moving Day: {moving_day}")
    else:
        print(f"Moving Day: {(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')} (default: 2 weeks from today)")
    print(f"Total Tasks Extracted: {len(tasks_df)}")
    print(f"{'='*120}\n")

    # Show breakdown by timeline
    print("Task Breakdown by Timeline:")
    print(tasks_df.groupby('Notes').size().to_string())
    print()

    # Show breakdown by priority
    print("\nTask Breakdown by Priority:")
    print(tasks_df['Priority'].value_counts().to_string())
    print()

    # Show sample tasks
    print("\nSample Tasks (first 15):")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 60)
    print(tasks_df[['Room', 'Task Description', 'Priority', 'Due Date', 'Notes']].head(15).to_string(index=False))

    # Save to files
    tasks_df.to_csv("extracted_data/moving_guide_tasks.csv", index=False, encoding='utf-8')
    tasks_df.to_excel("extracted_data/moving_guide_tasks.xlsx", index=False, engine='openpyxl')

    print(f"\n{'='*120}")
    print("✅ Tasks saved to:")
    print("   - CSV: extracted_data/moving_guide_tasks.csv")
    print("   - Excel: extracted_data/moving_guide_tasks.xlsx")
    print(f"{'='*120}\n")

    print("Next steps:")
    print("1. Review the CSV/Excel file to verify tasks")
    print("2. Upload to Google Sheets Task Tracker using google_sheets_integration.py")
