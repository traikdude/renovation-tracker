# Handwritten OCR Pipeline for Renovation Tracking

A Python-based OCR (Optical Character Recognition) pipeline that processes handwritten renovation notes, task lists, and financial documents, then intelligently uploads the extracted data to Google Sheets for easy tracking and management.

## Features

- **Intelligent OCR Processing**: Uses Tesseract OCR with optimized preprocessing for handwritten text
- **Smart Data Parsing**: Automatically categorizes and structures data based on content type:
  - Financial transactions (Budget & Expenses)
  - Task checklists (Task Tracker)
  - Property layout information (Property Layout)
- **Google Sheets Integration**: Seamlessly uploads parsed data to designated worksheets
- **Automated Backup**: Saves extracted data locally as Excel files before uploading
- **Confidence Scoring**: Tracks OCR accuracy with confidence metrics
- **Batch Processing**: Process multiple images in a single run

## Prerequisites

- Python 3.8+
- Tesseract OCR installed on your system
- Google Cloud Project with Sheets API and Drive API enabled
- Google Service Account credentials

### Installing Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/renovation-tracker.git
   cd renovation-tracker
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Set up Google Cloud Credentials

1. Create a Google Cloud Project at [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API and Google Drive API
3. Create a Service Account and download the JSON credentials file
4. Save the credentials file as `credentials.json` in the project root
5. Share your Google Sheet with the service account email (found in credentials.json)

### 2. Configure the Application

Edit `config.yaml` to customize settings:

```yaml
google_sheets:
  # Replace with your Google Sheet ID (from the URL)
  spreadsheet_id: "YOUR_SPREADSHEET_ID_HERE"

  credentials_file: "./credentials.json"

  worksheets:
    budget: "Budget & Expenses"
    tasks: "Task Tracker"
    layout: "Property Layout"

ocr:
  image_folder: "./images"
  output_folder: "./extracted_data"

  # Map image files to specific worksheets
  image_mappings:
    financial_notes.jpg: "Budget & Expenses"
    task_checklist.jpg: "Task Tracker"
    property_layout.jpg: "Property Layout"
```

### 3. Prepare Your Images

Place your handwritten notes, receipts, or documents in the `./images` folder.

## Usage

### Basic Usage (Local Processing Only)

Process images and save results locally:

```bash
python3 handwritten_ocr_pipeline.py
```

### Upload to Google Sheets

Process images and upload to Google Sheets:

```bash
python3 handwritten_ocr_pipeline.py --upload-to-sheets
```

### Process Specific Images

Process only specific image files:

```bash
python3 handwritten_ocr_pipeline.py --images image1.jpg image2.jpg --upload-to-sheets
```

### Test Google Sheets Connection

Verify your Google Sheets setup:

```bash
python3 google_sheets_integration.py
```

### Set Up Google Sheets Structure

Create required worksheets in your spreadsheet:

```bash
python3 setup_google_sheets.py
```

## Project Structure

```
renovation-tracker/
├── handwritten_ocr_pipeline.py    # Main OCR pipeline
├── google_sheets_integration.py   # Google Sheets API wrapper
├── transaction_parser.py          # Parse financial transactions
├── task_parser.py                 # Parse task checklists
├── layout_parser.py               # Parse property layouts
├── setup_google_sheets.py         # Initialize Google Sheets structure
├── clear_worksheets.py            # Utility to clear worksheets
├── config.yaml                    # Configuration file
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
├── images/                        # Input images (not tracked)
├── extracted_data/                # Output files (not tracked)
└── logs/                          # Application logs (not tracked)
```

## Intelligent Parsers

### Transaction Parser
Extracts financial data from receipts and expense notes:
- Date, Description, Amount, Category
- Payment Method, Vendor
- Automatically uploaded to "Budget & Expenses" worksheet

### Task Parser
Extracts tasks and checklists:
- Task Name, Status, Priority
- Due Date, Category
- Automatically uploaded to "Task Tracker" worksheet

### Layout Parser
Extracts property information:
- Room/Area Name, Dimensions, Notes
- Automatically uploaded to "Property Layout" worksheet

## Output

### Local Files
- **Text files**: Raw OCR text output
- **Excel files**: Structured data with confidence scores
- **Summary report**: Overview of all processed images

### Google Sheets
- Parsed data uploaded to appropriate worksheets
- Timestamp tracking for all uploads
- Automatic data validation and formatting

## Troubleshooting

### OCR Quality Issues
- Ensure images are well-lit and high resolution
- Adjust Tesseract config in `config.yaml` if needed
- Try different PSM (Page Segmentation Mode) values

### Google Sheets API Errors
- Verify credentials file exists and is valid
- Ensure the spreadsheet is shared with the service account
- Check that APIs are enabled in Google Cloud Console

### Permission Errors
- Make sure the service account has edit access to the spreadsheet
- Verify the spreadsheet ID in config.yaml is correct

## Security Notes

- **NEVER commit `credentials.json`** to version control
- The `.gitignore` file is configured to exclude sensitive files
- Keep your `config.yaml` secure if it contains sensitive spreadsheet IDs
- Review all data before uploading to shared spreadsheets

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [gspread](https://github.com/burnash/gspread) - Google Sheets Python API
- [OpenCV](https://opencv.org/) - Image preprocessing

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Built with Python for efficient renovation project management**
