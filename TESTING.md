# Quick Start Guide - Testing Document Extraction

## Prerequisites
- Backend running (`npm run dev`)
- OCR service running (Docker or standalone)
- Frontend running (`npm run dev`)

---

## Step 1: Verify Services Are Running

### Check OCR Service
```bash
curl http://localhost:8000/ocr/health
```

Expected response:
```json
{"success": true, "status": "ok", "engine": "PaddleOCR"}
```

### Check Backend Health
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status": "OK", "message": "Server is running"}
```

### Run Backend Diagnostics
```bash
cd backend
npm run diagnose
```

---

## Step 2: Test Extraction with Python Script

Before testing in the UI, validate the extraction logic:

```bash
cd ocr-service
python test_extraction.py
```

This tests:
- ✓ Basic transaction extraction
- ✓ Multiple date formats
- ✓ Multiple amount formats
- ✓ Credit/Debit detection

---

## Step 3: Prepare Real Test Document

### Option A: Use Your Bank Statement
1. Get a recent bank statement PDF or photo
2. Ensure document is:
   - Clear and legible
   - Proper orientation (not rotated)
   - 200+ DPI resolution for scans
   - Good contrast

### Option B: Create Test Document
```
BANK STATEMENT
Account: 1234567890
Period: 01/01/2024 - 31/01/2024

Date        Description              Debit    Credit   Balance
01/01/2024  Opening Balance                           15000.00
02/01/2024  Salary Deposit                  5000.00  20000.00
03/01/2024  Grocery Store             150.50          19849.50
05/01/2024  ATM Withdrawal            500.00          19349.50
08/01/2024  Online Transfer In                1000.00 20349.50
```

Then:
- Scan with printer/scanner, or
- Take clear photo, or
- Convert to PDF

---

## Step 4: Upload in UI

1. Open http://localhost:3000
2. Click "Continue as guest" (or login)
3. Navigate to Upload section
4. Upload your test file
5. Wait for processing (2-15 seconds depending on document size)

---

## Step 5: Check Response

### In Frontend
- Should show extracted transactions in table
- Check "Summary" section for:
  - Transaction count
  - Average confidence score
  - Pages processed
  - Status (should be "complete" if transactions found)

### Via API (curl)
```bash
curl -X POST http://localhost:5000/api/uploads/upload \
  -F "file=@/path/to/statement.pdf"
```

Response structure:
```json
{
  "fileId": "upload-12345-...",
  "status": "processed",
  "originalName": "statement.pdf",
  "summary": {
    "transaction_count": 5,
    "average_confidence": 0.87,
    "status": "complete"
  },
  "transactions": [
    {
      "id": "txn-0001",
      "date": "01/01/2024",
      "description": "Salary Deposit",
      "debit": null,
      "credit": 5000.00,
      "balance": 20000.00,
      "type": "Credit",
      "confidence": 0.92
    },
    ...
  ],
  "rawText": "...",  // OCR extracted text
  "pages": [
    {
      "page": 1,
      "line_count": 25,
      "status": "processed"
    }
  ]
}
```

---

## Troubleshooting

### 1. No Transactions Extracted

**Check:**
```bash
# Look for date patterns
grep -E "[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}" <<< "$raw_text"

# Look for amounts
grep -E "\$?[0-9,]+" <<< "$raw_text"
```

**Fix Options:**
1. Ensure dates match supported format (see EXTRACTION_DEBUG.md)
2. Check `rawText` in response to see what was recognized
3. Try a clearer document scan

### 2. Partial Transactions

**Check:**
- Missing debit/credit amounts?
- Check if amounts were recognized in raw_text
- Look at confidence scores

**Fix:**
- Ensure amounts have consistent formatting
- Try different document quality
- Check EXTRACTION_DEBUG.md for format examples

### 3. Wrong Credit/Debit Detection

**Check:**
- Does transaction description contain "credit/deposit" or "debit/withdrawal"?
- Does it have CR/DR indicators?

**Fix:**
- Verify bank statement uses standard terminology
- May need custom regex pattern for your bank

### 4. OCR Service Errors

```bash
# Check OCR logs
docker logs -f difm_ocr

# Or if running locally:
export LOG_LEVEL=DEBUG
python ocr-service/app/main.py
```

---

## Performance Benchmarks

| Document Type | Size | Time | Notes |
|---|---|---|---|
| Single page scan | 1-2MB | 2-5s | Fastest |
| Multi-page PDF | 10-30MB | 5-15s | Normal |
| Large PDF | 50MB+ | 15-30s | May timeout |
| High-res scan | 5MB+ | 10-20s | Best accuracy |

---

## Next Steps

1. **After verification:**
   - Test with 3-5 different bank statements
   - Document any issues in GitHub
   - Note specific banks/formats that fail

2. **For production:**
   - Set up proper database (currently using PostgreSQL)
   - Configure Redis for queuing
   - Set up proper authentication
   - Enable HTTPS/SSL

3. **To improve accuracy:**
   - Fine-tune preprocessing settings in `.env`
   - Add bank-specific regex patterns
   - Collect training data for custom models

---

## Useful Commands

```bash
# Reset extraction pipeline
npm run diagnose

# View OCR service logs in real-time
docker logs -f difm_ocr

# Test OCR with image file
curl -X POST http://localhost:8000/ocr/extract \
  -F "file=@document.pdf"

# View upload history
curl http://localhost:5000/api/uploads

# Check backend config
cat backend/.env | grep -v "PASSWORD"
```

---

For detailed troubleshooting, see [EXTRACTION_DEBUG.md](EXTRACTION_DEBUG.md)
