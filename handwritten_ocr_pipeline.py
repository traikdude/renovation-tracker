#!/usr/bin/env python3
"""
Handwritten OCR Pipeline for Renovation Tracking
Processes handwritten renovation images and extracts text data
"""

import cv2
import pytesseract
from PIL import Image
import pandas as pd
import numpy as np
import os
import argparse
from datetime import datetime
from google_sheets_integration import GoogleSheetsManager

# Configuration
IMAGE_FOLDER = "./images"
OUTPUT_FOLDER = "./extracted_data"
IMAGE_FILES = [
    "property_layout.jpg",
    "financial_notes.jpg",
    "task_checklist.jpg"
]

# Tesseract configuration for handwritten text
# PSM 6 = Assume a single uniform block of text
# PSM 11 = Sparse text. Find as much text as possible in no particular order
TESSERACT_CONFIG = '--psm 6 --oem 3'

def preprocess_image(image_path):
    """
    Preprocess image to improve OCR accuracy for handwritten text
    """
    print(f"Preprocessing: {image_path}")

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while keeping edges sharp
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)

    # Apply adaptive thresholding for better contrast
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # Optional: Apply morphological operations to clean up
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return cleaned

def extract_text_from_image(image_path, config=TESSERACT_CONFIG):
    """
    Extract text from preprocessed image using Tesseract OCR
    """
    print(f"Extracting text from: {os.path.basename(image_path)}")

    # Preprocess the image
    processed_img = preprocess_image(image_path)

    # Convert numpy array to PIL Image for pytesseract
    pil_img = Image.fromarray(processed_img)

    # Extract text
    text = pytesseract.image_to_string(pil_img, config=config)

    # Also get detailed data (word-level bounding boxes and confidence)
    data = pytesseract.image_to_data(pil_img, config=config, output_type=pytesseract.Output.DICT)

    return text, data

def save_results(filename, text, data, output_folder):
    """
    Save OCR results to text file and structured Excel file
    """
    base_name = os.path.splitext(filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save raw text
    text_file = os.path.join(output_folder, f"{base_name}_{timestamp}.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  Saved text to: {text_file}")

    # Save structured data to Excel
    df = pd.DataFrame(data)
    # Filter out empty detections
    df = df[df['text'].str.strip() != '']

    excel_file = os.path.join(output_folder, f"{base_name}_{timestamp}.xlsx")
    df.to_excel(excel_file, index=False)
    print(f"  Saved structured data to: {excel_file}")

    return text_file, excel_file, df


def upload_to_sheets(filename, text, data, sheets_manager):
    """
    Upload OCR results to Google Sheets

    Args:
        filename: Name of the image file
        text: Extracted text
        data: OCR data dictionary from pytesseract
        sheets_manager: GoogleSheetsManager instance

    Returns:
        bool: True if upload successful
    """
    try:
        print(f"  Uploading to Google Sheets...")
        success = sheets_manager.upload_ocr_results(filename, text, data)
        if success:
            print(f"  ✓ Data uploaded to Google Sheets")
        return success
    except Exception as e:
        print(f"  ✗ Failed to upload to Google Sheets: {e}")
        return False

def process_pipeline(image_files, image_folder, output_folder, upload_to_google_sheets=False):
    """
    Main pipeline to process all images

    Args:
        image_files: List of image filenames to process
        image_folder: Folder containing images
        output_folder: Folder to save OCR results
        upload_to_google_sheets: Whether to upload results to Google Sheets

    Returns:
        List of processing results
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Initialize Google Sheets manager if upload requested
    sheets_manager = None
    if upload_to_google_sheets:
        try:
            print("Initializing Google Sheets connection...")
            sheets_manager = GoogleSheetsManager()
            print("✓ Connected to Google Sheets\n")
        except Exception as e:
            print(f"✗ Failed to connect to Google Sheets: {e}")
            print("Continuing with local file storage only...\n")

    results = []

    print(f"\n{'='*60}")
    print(f"Starting OCR Pipeline")
    print(f"{'='*60}\n")

    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)

        # Check if file exists
        if not os.path.exists(image_path):
            print(f"WARNING: Image not found: {image_path}")
            print(f"  Skipping...\n")
            continue

        try:
            # Extract text
            text, data = extract_text_from_image(image_path)

            # Save results locally
            text_file, excel_file, df = save_results(
                image_file, text, data, output_folder
            )

            # Upload to Google Sheets if enabled
            uploaded = False
            if sheets_manager:
                uploaded = upload_to_sheets(image_file, text, data, sheets_manager)

            # Store results
            results.append({
                'image': image_file,
                'text_file': text_file,
                'excel_file': excel_file,
                'word_count': len([w for w in text.split() if w]),
                'confidence_avg': np.mean([c for c in data['conf'] if c != -1]),
                'uploaded_to_sheets': uploaded
            })

            print(f"  Words extracted: {results[-1]['word_count']}")
            print(f"  Average confidence: {results[-1]['confidence_avg']:.2f}%\n")

        except Exception as e:
            print(f"ERROR processing {image_file}: {str(e)}\n")
            continue

    print(f"{'='*60}")
    print(f"Pipeline Complete")
    print(f"{'='*60}\n")

    # Create summary report
    if results:
        summary_df = pd.DataFrame(results)
        summary_file = os.path.join(
            output_folder,
            f"ocr_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        summary_df.to_excel(summary_file, index=False)
        print(f"Summary report saved to: {summary_file}\n")

        print("Results Summary:")
        print(summary_df.to_string(index=False))

    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Handwritten OCR Pipeline for Renovation Tracker'
    )
    parser.add_argument(
        '--upload-to-sheets',
        action='store_true',
        help='Upload OCR results to Google Sheets'
    )
    parser.add_argument(
        '--images',
        nargs='+',
        help='Specific image files to process (default: all configured images)'
    )

    args = parser.parse_args()

    print("\nHandwritten OCR Pipeline - Renovation Tracker")
    print("=" * 60)

    # Determine which images to process
    images_to_process = args.images if args.images else IMAGE_FILES

    # Display configuration
    print(f"\nConfiguration:")
    print(f"  Image folder: {IMAGE_FOLDER}")
    print(f"  Output folder: {OUTPUT_FOLDER}")
    print(f"  Tesseract config: {TESSERACT_CONFIG}")
    print(f"  Images to process: {len(images_to_process)}")
    print(f"  Upload to Google Sheets: {'Yes' if args.upload_to_sheets else 'No'}")

    # Process all images
    results = process_pipeline(
        images_to_process,
        IMAGE_FOLDER,
        OUTPUT_FOLDER,
        upload_to_google_sheets=args.upload_to_sheets
    )

    print(f"\nProcessed {len(results)} images successfully!")

    if args.upload_to_sheets:
        uploaded_count = sum(1 for r in results if r.get('uploaded_to_sheets', False))
        print(f"Uploaded to Google Sheets: {uploaded_count}/{len(results)}")
