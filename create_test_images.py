#!/usr/bin/env python3
"""
Create test images for OCR testing
Generates sample renovation-related documents with text
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image(filename, title, content_lines, size=(800, 1000)):
    """Create a test image with text content"""

    # Create white background
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a better font, fallback to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Draw title
    y_position = 50
    draw.text((50, y_position), title, fill='black', font=title_font)

    # Draw horizontal line under title
    y_position += 60
    draw.line([(50, y_position), (size[0]-50, y_position)], fill='black', width=2)

    # Draw content lines
    y_position += 40
    line_spacing = 45

    for line in content_lines:
        draw.text((50, y_position), line, fill='black', font=text_font)
        y_position += line_spacing

    # Save image
    img.save(filename)
    print(f"✓ Created: {filename}")

def main():
    """Generate all test images"""

    output_dir = "./images"
    os.makedirs(output_dir, exist_ok=True)

    # Test Image 1: Financial Notes
    create_test_image(
        f"{output_dir}/financial_notes.jpg",
        "Budget & Expenses",
        [
            "Date: October 24, 2025",
            "",
            "Item: Kitchen Cabinets",
            "Cost: $3,500.00",
            "Vendor: Home Depot",
            "Status: Paid",
            "",
            "Item: Tile Flooring",
            "Cost: $1,200.00",
            "Vendor: Lowe's",
            "Status: Pending",
            "",
            "Item: Paint Supplies",
            "Cost: $450.00",
            "Vendor: Sherwin Williams",
            "Status: Paid"
        ]
    )

    # Test Image 2: Task Checklist
    create_test_image(
        f"{output_dir}/task_checklist.jpg",
        "Renovation Tasks",
        [
            "Date: October 24, 2025",
            "",
            "[ X ] Demo old kitchen cabinets",
            "[ X ] Remove old flooring",
            "[ ] Install new cabinets",
            "[ ] Install countertops",
            "[ ] Tile backsplash",
            "[ ] Paint walls",
            "[ ] Install new appliances",
            "[ ] Final inspection",
            "",
            "Notes:",
            "- Plumber scheduled for Monday",
            "- Electrician coming Tuesday",
            "- Inspection on Friday"
        ]
    )

    # Test Image 3: Property Layout
    create_test_image(
        f"{output_dir}/property_layout.jpg",
        "Property Layout Notes",
        [
            "Room: Kitchen",
            "Dimensions: 12' x 15'",
            "",
            "Layout Changes:",
            "- Move sink to island",
            "- Extend counter on east wall",
            "- Add pantry closet",
            "- New lighting fixtures",
            "",
            "Room: Master Bathroom",
            "Dimensions: 8' x 10'",
            "",
            "Updates:",
            "- Replace tub with walk-in shower",
            "- Double vanity",
            "- Heated floors"
        ]
    )

    print("\n" + "="*60)
    print("✓ All test images created successfully!")
    print("="*60)
    print("\nGenerated files:")
    print("  - financial_notes.jpg (Budget & Expenses)")
    print("  - task_checklist.jpg (Task Tracker)")
    print("  - property_layout.jpg (Property Layout)")
    print("\nReady for OCR processing!")

if __name__ == "__main__":
    main()
