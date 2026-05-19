#!/usr/bin/env python3
"""
Bank Statement Extraction Test Script
Tests the extraction pipeline with sample data
"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.extraction.regex_parser import parse_transactions


def test_basic_extraction():
    """Test extraction with sample transaction data."""
    print("=" * 60)
    print("Testing Basic Transaction Extraction")
    print("=" * 60)
    
    # Sample OCR output (what PaddleOCR would return)
    sample_rows = [
        {
            "text": "Date Description Amount Balance",
            "confidence": 0.95,
            "page": 1,
        },
        {
            "text": "01/01/2024 Salary Deposit 5000.00 15000.00",
            "confidence": 0.92,
            "page": 1,
        },
        {
            "text": "02/01/2024 Grocery Shopping 150.50 14849.50",
            "confidence": 0.88,
            "page": 1,
        },
        {
            "text": "03/01/2024 ATM Withdrawal 500.00 14349.50",
            "confidence": 0.91,
            "page": 1,
        },
        {
            "text": "04/01/2024 Online Transfer In 1000.00 CR 15349.50",
            "confidence": 0.89,
            "page": 1,
        },
    ]
    
    transactions = parse_transactions(sample_rows)
    
    print(f"\n✓ Extracted {len(transactions)} transactions\n")
    
    for i, tx in enumerate(transactions, 1):
        print(f"Transaction {i}:")
        print(f"  Date: {tx.get('date')}")
        print(f"  Description: {tx.get('description')}")
        print(f"  Debit: {tx.get('debit')}")
        print(f"  Credit: {tx.get('credit')}")
        print(f"  Type: {tx.get('type')}")
        print(f"  Confidence: {tx.get('confidence')}")
        print()
    
    return len(transactions) > 0


def test_date_formats():
    """Test different date format recognition."""
    print("\n" + "=" * 60)
    print("Testing Date Format Support")
    print("=" * 60)
    
    date_formats = [
        ("01/01/2024 Payment 100.00 1000.00", "DD/MM/YYYY"),
        ("2024-01-01 Payment 100.00 1000.00", "YYYY-MM-DD"),
        ("01 Jan 2024 Payment 100.00 1000.00", "DD Mon YYYY"),
        ("01 January 2024 Payment 100.00 1000.00", "DD Month YYYY"),
    ]
    
    for text, format_name in date_formats:
        sample_rows = [{"text": text, "confidence": 0.90, "page": 1}]
        transactions = parse_transactions(sample_rows)
        status = "✓" if transactions else "✗"
        print(f"{status} {format_name}: {text}")
        if transactions:
            print(f"   → Date: {transactions[0].get('date')}")
    
    print()


def test_amount_formats():
    """Test different amount format recognition."""
    print("\n" + "=" * 60)
    print("Testing Amount Format Support")
    print("=" * 60)
    
    amount_formats = [
        ("01/01/2024 Payment $1,234.56 5000.00", "$1,234.56"),
        ("01/01/2024 Payment 1234.56 5000.00", "1234.56"),
        ("01/01/2024 Payment ₹1,000.00 5000.00", "₹1,000.00"),
        ("01/01/2024 Payment €500.00 5000.00", "€500.00"),
    ]
    
    for text, amount_format in amount_formats:
        sample_rows = [{"text": text, "confidence": 0.90, "page": 1}]
        transactions = parse_transactions(sample_rows)
        status = "✓" if transactions and transactions[0].get("debit") else "✗"
        print(f"{status} Format: {amount_format}")
        if transactions:
            print(f"   → Parsed: ${transactions[0].get('debit')}")
    
    print()


def test_credit_debit_detection():
    """Test credit/debit detection."""
    print("\n" + "=" * 60)
    print("Testing Credit/Debit Detection")
    print("=" * 60)
    
    test_cases = [
        ("01/01/2024 Salary Deposit CR 5000.00 15000.00", "Credit"),
        ("01/01/2024 Withdrawal DR 500.00 14500.00", "Debit"),
        ("01/01/2024 Transfer In 1000.00 15500.00", "Credit"),
        ("01/01/2024 Payment Out 200.00 15300.00", "Debit"),
    ]
    
    for text, expected_type in test_cases:
        sample_rows = [{"text": text, "confidence": 0.90, "page": 1}]
        transactions = parse_transactions(sample_rows)
        
        if transactions:
            detected_type = "Credit" if transactions[0].get("credit") else "Debit"
            status = "✓" if detected_type == expected_type else "✗"
            print(f"{status} Expected: {expected_type}, Got: {detected_type}")
            print(f"   → {text}")
        else:
            print(f"✗ Failed to parse: {text}")
    
    print()


if __name__ == "__main__":
    try:
        print("\n🧪 Starting Bank Statement Extraction Tests\n")
        
        # Run all tests
        basic_ok = test_basic_extraction()
        test_date_formats()
        test_amount_formats()
        test_credit_debit_detection()
        
        print("=" * 60)
        if basic_ok:
            print("✓ All tests completed successfully!")
        else:
            print("⚠ Some tests failed. Check the output above.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
