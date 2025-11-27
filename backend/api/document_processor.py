import pdfplumber
import re
from decimal import Decimal
from io import BytesIO

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_proforma_data(file):
    """Extract key data from proforma invoice"""
    text = extract_text_from_pdf(file)
    
    data = {
        'vendor': extract_vendor(text),
        'items': extract_items(text),
        'total_amount': extract_amount(text),
        'date': extract_date(text),
        'invoice_number': extract_invoice_number(text),
        'raw_text': text[:500]  # Store first 500 chars
    }
    
    return data

def extract_vendor(text):
    """Extract vendor name from text"""
    patterns = [
        r'(?:Vendor|Supplier|From|Company):\s*([A-Za-z\s&.,]+)',
        r'([A-Z][A-Za-z\s&.,]+)\n.*(?:Address|Tel|Email)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    lines = text.split('\n')
    if lines:
        return lines[0].strip()
    
    return "Unknown Vendor"

def extract_items(text):
    """Extract items from text"""
    items = []
    
    lines = text.split('\n')
    for line in lines:
        if re.search(r'\d+\.\d{2}', line) and len(line.split()) > 2:
            items.append(line.strip())
    
    return items[:10] if items else ["Item details not extracted"]

def extract_amount(text):
    """Extract total amount from text"""
    patterns = [
        r'(?:Total|Amount|Grand Total|Sum):\s*\$?\s*([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except:
                pass
    
    amounts = re.findall(r'\d+\.\d{2}', text)
    if amounts:
        return float(amounts[-1])
    
    return 0.0

def extract_date(text):
    """Extract date from text"""
    patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'\d{1,2}-\d{1,2}-\d{2,4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return "Date not found"

def extract_invoice_number(text):
    """Extract invoice/proforma number"""
    patterns = [
        r'(?:Invoice|Proforma|Ref|No|Number)[\s#:]*([A-Z0-9-]+)',
        r'#([A-Z0-9-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "N/A"

def generate_purchase_order(request):
    """Generate purchase order data from approved request"""
    proforma_data = request.proforma_data or {}
    
    po_data = {
        'po_number': f"PO-{request.id:06d}",
        'request_id': request.id,
        'vendor': proforma_data.get('vendor', 'Unknown'),
        'items': proforma_data.get('items', []),
        'total_amount': str(request.amount),
        'approved_by_level_1': request.level_1_approver.get_full_name() if request.level_1_approver else 'N/A',
        'approved_by_level_2': request.level_2_approver.get_full_name() if request.level_2_approver else 'N/A',
        'status': 'APPROVED',
        'notes': f"Purchase order for: {request.title}"
    }
    
    return po_data

def validate_receipt(receipt_file, purchase_order_data):
    """Validate receipt against purchase order"""
    receipt_text = extract_text_from_pdf(receipt_file)
    receipt_data = {
        'vendor': extract_vendor(receipt_text),
        'amount': extract_amount(receipt_text),
        'items': extract_items(receipt_text),
    }
    
    discrepancies = []
    
    po_vendor = purchase_order_data.get('vendor', '').lower()
    receipt_vendor = receipt_data.get('vendor', '').lower()
    if po_vendor not in receipt_vendor and receipt_vendor not in po_vendor:
        discrepancies.append(f"Vendor mismatch: PO='{purchase_order_data.get('vendor')}' vs Receipt='{receipt_data.get('vendor')}'")
    
    po_amount = float(purchase_order_data.get('total_amount', 0))
    receipt_amount = receipt_data.get('amount', 0)
    if abs(po_amount - receipt_amount) > 0.01:
        discrepancies.append(f"Amount mismatch: PO=${po_amount:.2f} vs Receipt=${receipt_amount:.2f}")
    
    validation_result = {
        'is_valid': len(discrepancies) == 0,
        'discrepancies': discrepancies,
        'receipt_data': receipt_data,
        'message': 'Receipt validated successfully' if len(discrepancies) == 0 else 'Discrepancies found'
    }
    
    return validation_result