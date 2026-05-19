# Bank Statement Extraction Troubleshooting Guide

## Common Issues & Solutions

### 1. **No Transactions Extracted**

**Symptoms:**
- Upload succeeds but transaction_count is 0
- Status shows "needs_review"

**Root Causes:**
1. **Date format not recognized**
   - Regex patterns may not match your bank's date format
   - Supported: `01/01/2024`, `2024-01-01`, `01 Jan 2024`, `01 January 2024`
   
2. **Amount format not matching**
   - Amounts must be numeric with optional currency symbols
   - Supported: `$1,234.56`, `1234.56`, `₹1,000.00`
   - NOT supported: `One thousand dollars`

3. **Poor OCR confidence**
   - If confidence < 0.5, rows are skipped
   - Check `summary.average_confidence` in response

**How to Fix:**
```bash
# 1. Check OCR service logs
docker logs difm_ocr

# 2. Enable debug logging
export LOG_LEVEL=DEBUG

# 3. Review extracted text
# Check the response's "raw_text" field to see what was recognized

# 4. Improve image quality
# Ensure scanned document is:
# - Clear and readable
# - Properly oriented (not rotated)
# - Good contrast (not too dark/light)
# - At least 200 DPI resolution
```

---

### 2. **Partial Transactions (Missing Amounts)**

**Symptoms:**
- Some transactions extracted, others missing
- Fields like `debit` or `credit` are null

**Root Causes:**
1. **Amount detection too strict**
   - Amounts with unusual formatting not recognized
   - Scientific notation (1E+03) not supported

2. **Description too long**
   - Descriptions longer than 100 chars are truncated
   - May consume space meant for amounts

**How to Fix:**
1. Check the `raw_text` in response to see actual extracted text
2. Look for amounts in different formats
3. Verify date is being extracted correctly

---

### 3. **Wrong Transaction Type (Debit/Credit)**

**Symptoms:**
- Deposits marked as Withdrawals or vice versa
- Balance amounts showing as transactions

**Root Causes:**
1. **Keywords not found**
   - Text doesn't contain "deposit", "credit", "withdrawal", "debit"
   - Bank uses custom terminology

2. **Multiple amounts parsed incorrectly**
   - First amount assumed to be transaction
   - Last amount assumed to be balance

**How to Fix:**
1. Review response's `transactions[].raw_text` field
2. Check if type is correctly identified
3. For custom bank formats, may need regex pattern update

---

### 4. **PDF Processing Fails**

**Symptoms:**
- PDF uploads fail with error
- "Conversion timeout" or "Invalid PDF" errors

**Root Causes:**
1. **Corrupted PDF file**
2. **PDF is scanned image without embedded text**
3. **PDF too large (>50MB)**

**How to Fix:**
```bash
# Convert PDF to images first
pdftoppm -png document.pdf output

# Re-upload as PNG files
```

---

## Debugging Steps

### Step 1: Check OCR Service Health
```bash
curl http://localhost:8000/ocr/health
# Should return: {"success": true, "status": "ok", "engine": "PaddleOCR"}
```

### Step 2: Monitor OCR Service Logs
```bash
docker logs -f difm_ocr --since 1m
```

### Step 3: Test with Sample File
```bash
# Create a simple test bank statement as text
# Scan or export as PDF/Image
# Upload and check response

# Example test format:
# Date: 01/01/2024
# Description: Salary Deposit
# Amount: $5,000.00 CR
# Balance: $15,000.00
```

### Step 4: Analyze Response
```json
{
  "summary": {
    "transaction_count": 0,      // Should be > 0
    "average_confidence": 0.65,  // Should be > 0.6
    "pages_processed": 1,
    "status": "needs_review"     // Should be "complete"
  },
  "raw_text": "...",             // Check if text is recognized
  "transactions": [],            // Should have items
  "pages": [{                    // Check per-page status
    "page": 1,
    "line_count": 25,            // Should be > 0
    "status": "processed"
  }]
}
```

---

## Advanced Configuration

### Adjust Extraction Sensitivity
Edit `ocr-service/.env`:

```env
# Lower = stricter parsing, fewer false positives
MIN_CONFIDENCE_SCORE=0.5

# Higher = faster but less accurate
PADDLE_DEVICE=gpu  # Use GPU if available
```

### Add Custom Date Patterns
Edit `ocr-service/app/extraction/regex_parser.py`:

```python
DATE_PATTERNS = [
    # Add your bank's format here
    r"(?P<date>\d{2}-\d{2}-\d{4})",  # Example: 01-01-2024
]
```

---

## Performance Tips

1. **Smaller files process faster**
   - Single page statements: ~2-5 seconds
   - Multi-page PDFs: ~5-15 seconds

2. **Use high-quality scans**
   - 200-300 DPI minimum
   - Good lighting, minimal skew

3. **Batch processing**
   - Process multiple statements sequentially
   - Redis queue can handle ~3 concurrent jobs

4. **GPU Acceleration** (Optional)
   - Edit Dockerfile to use GPU-enabled PaddleOCR
   - Requires NVIDIA Docker runtime

---

## Backend Integration

### Upload API Response
```bash
POST /api/uploads/upload
```

Success Response:
```json
{
  "fileId": "upload-12345",
  "status": "processed",
  "transactions": [...],
  "summary": {...},
  "document": {
    "fileName": "statement.pdf",
    "fileSize": 1024000,
    "mimeType": "application/pdf"
  }
}
```

Error Response:
```json
{
  "error": "Extraction failed: No transactions found in document",
  "status": "failed"
}
```

---

## Support

For further issues:
1. Enable DEBUG logging: `export LOG_LEVEL=DEBUG`
2. Collect logs: `docker logs difm_ocr > ocr.log`
3. Save test file and response
4. Check GitHub issues or create new issue with logs attached
