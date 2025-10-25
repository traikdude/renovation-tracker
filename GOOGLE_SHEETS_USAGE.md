# Google Sheets Integration - Usage Guide

Complete guide for using the automated Google Sheets integration with your Renovation Tracker OCR Pipeline.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Running the OCR Pipeline](#running-the-ocr-pipeline)
3. [Configuration](#configuration)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Prerequisites
- ✓ Google Cloud Project created
- ✓ Google Sheets API enabled
- ✓ Service account credentials (credentials.json)
- ✓ Google Sheet shared with service account email
- ✓ All dependencies installed

### Verify Setup

Run the setup script to verify everything is configured correctly:

```bash
./venv/bin/python3 setup_google_sheets.py
```

This will:
- Check credentials file
- Test Google Sheets connection
- Verify worksheets exist
- Upload test data

---

## Running the OCR Pipeline

### Basic Usage (Local Files Only)

Process images and save results locally without uploading to Google Sheets:

```bash
./venv/bin/python3 handwritten_ocr_pipeline.py
```

**Output:**
- Text files in `extracted_data/`
- Excel files in `extracted_data/`
- Summary report

### With Google Sheets Upload

Process images AND automatically upload to Google Sheets:

```bash
./venv/bin/python3 handwritten_ocr_pipeline.py --upload-to-sheets
```

**Output:**
- Local files (backup)
- Data uploaded to appropriate Google Sheets worksheets
- Summary report with upload status

### Process Specific Images

Process only specific images:

```bash
# Single image
./venv/bin/python3 handwritten_ocr_pipeline.py --upload-to-sheets --images property_layout.jpg

# Multiple images
./venv/bin/python3 handwritten_ocr_pipeline.py --upload-to-sheets --images financial_notes.jpg task_checklist.jpg
```

---

## Configuration

### config.yaml

The `config.yaml` file controls all settings:

```yaml
google_sheets:
  spreadsheet_id: "YOUR_SHEET_ID"
  credentials_file: "./credentials.json"
  worksheets:
    budget: "Budget & Expenses"
    tasks: "Task Tracker"
    layout: "Property Layout"

ocr:
  image_mappings:
    property_layout.jpg: "Property Layout"
    financial_notes.jpg: "Budget & Expenses"
    task_checklist.jpg: "Task Tracker"

upload:
  mode: "append"  # or "replace"
  add_timestamp: true
  max_retries: 3
```

### Updating Google Sheet URL

If you change your Google Sheet:

1. Extract the Sheet ID from the new URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```

2. Update `config.yaml`:
   ```yaml
   spreadsheet_id: "NEW_SHEET_ID"
   ```

3. Share the new sheet with your service account email

4. Test connection:
   ```bash
   ./venv/bin/python3 setup_google_sheets.py
   ```

### Image to Worksheet Mapping

To change which images go to which worksheets, edit the `image_mappings` section in `config.yaml`:

```yaml
ocr:
  image_mappings:
    my_custom_image.jpg: "My Custom Worksheet"
```

---

## Troubleshooting

### Error: "Failed to connect to Google Sheets"

**Possible causes:**
1. Credentials file missing or invalid
2. Google Sheets API not enabled
3. Sheet not shared with service account

**Solutions:**
- Run `./venv/bin/python3 setup_google_sheets.py` to diagnose
- Check that `credentials.json` exists
- Verify service account email has Editor access to your sheet
- Ensure Google Sheets API is enabled in Google Cloud Console

### Error: "Worksheet not found"

**Solution:**
- Check worksheet names in your Google Sheet match `config.yaml`
- Run setup script to create missing worksheets:
  ```bash
  ./venv/bin/python3 setup_google_sheets.py
  ```

### Error: "Permission denied" or "403 Forbidden"

**Solution:**
- Your service account doesn't have access to the sheet
- Share the Google Sheet with the service account email (found in credentials.json):
  ```
  renovation-ocr-service@renovation-tracker-ocr.iam.gserviceaccount.com
  ```

### Data Not Appearing in Sheet

**Check:**
1. Look for upload success messages in console output
2. Verify correct worksheet name in `config.yaml`
3. Check if data was appended to bottom of sheet (scroll down)
4. Look for errors in console output

### Rate Limiting / Quota Exceeded

**Solution:**
- Google Sheets API has usage quotas
- Wait a few minutes and try again
- Process images in smaller batches
- Increase `retry_delay` in `config.yaml`

---

## Advanced Usage

### Append vs Replace Mode

**Append Mode** (default):
- Adds new data to the end of the worksheet
- Preserves existing data
- Good for ongoing tracking

```yaml
upload:
  mode: "append"
```

**Replace Mode**:
- Clears worksheet and replaces with new data
- Use with caution!
- Good for single complete updates

```yaml
upload:
  mode: "replace"
```

### Batch Processing

Process all images in a folder:

```bash
# Find all .jpg files and process them
for img in images/*.jpg; do
  ./venv/bin/python3 handwritten_ocr_pipeline.py --upload-to-sheets --images $(basename $img)
done
```

### Viewing Logs

Check detailed logs for debugging:

```bash
tail -f logs/ocr_pipeline.log
```

### Testing Without Uploading

To test OCR without uploading to Google Sheets:

```bash
# Omit the --upload-to-sheets flag
./venv/bin/python3 handwritten_ocr_pipeline.py
```

Results will be saved locally in `extracted_data/` folder.

---

## Data Format

### What Gets Uploaded

For each image processed, the following data is uploaded to Google Sheets:

| Column | Description |
|--------|-------------|
| Upload_Timestamp | When the data was uploaded |
| Source_Image | Original image filename |
| Extracted_Text | First 500 characters of extracted text |
| level | OCR hierarchy level |
| page_num | Page number (always 1 for images) |
| block_num | Text block number |
| par_num | Paragraph number |
| line_num | Line number |
| word_num | Word number |
| left, top, width, height | Bounding box coordinates |
| conf | OCR confidence score (0-100) |
| text | Extracted text for each word |

### Filtering Data

Only non-empty text entries are uploaded (blank detections are filtered out).

---

## Worksheet Structure

Your Google Sheet should have these worksheets:

1. **Dashboard** - Overview and calculations
2. **Budget & Expenses** - Financial tracking (receives data from `financial_notes.jpg`)
3. **Task Tracker** - Task management (receives data from `task_checklist.jpg`)
4. **Property Layout** - Layout notes (receives data from `property_layout.jpg`)
5. **Settings** - Configuration

The OCR pipeline will create a new worksheet for each image if it doesn't exist.

---

## Security Best Practices

1. **Never commit credentials.json to Git**
   - Already added to `.gitignore`
   - Keep it secure and private

2. **Limit service account permissions**
   - Only share specific sheets, not entire Drive
   - Use Editor permission (not Owner)

3. **Rotate credentials periodically**
   - Generate new service account keys every 90 days
   - Delete old keys from Google Cloud Console

---

## Support

For issues or questions:

1. Run the setup script: `./venv/bin/python3 setup_google_sheets.py`
2. Check console output for error messages
3. Verify your configuration in `config.yaml`
4. Check Google Sheets API quota in Google Cloud Console

---

## File Locations

- **Credentials:** `./credentials.json`
- **Configuration:** `./config.yaml`
- **Images:** `./images/`
- **Output:** `./extracted_data/`
- **Logs:** `./logs/`

---

**Last Updated:** 2025-10-22
