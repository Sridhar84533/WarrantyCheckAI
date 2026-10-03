import re
from datetime import date
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta


def calculate_warranty(
    product_name: str,
    brand: str,
    model_number: str,
    serial_number: str,
    purchase_date: str,
    warranty_years: any
) -> dict:
    """
    Deterministically calculates warranty status, expiry date, and days remaining.
    Does not rely on AI for date calculation.
    """
    clean_product_name = str(product_name or "").strip()
    clean_brand = str(brand or "").strip()
    clean_model_number = str(model_number or "").strip()
    clean_serial_number = str(serial_number or "").strip()
    clean_purchase_date_str = str(purchase_date or "").strip()

    if not clean_product_name:
        raise ValueError("Product name is required.")

    if not clean_purchase_date_str:
        raise ValueError("Purchase date is required.")

    # Parse purchase date
    try:
        parsed_dt = parse_date(clean_purchase_date_str)
        purchase = parsed_dt.date()
    except Exception:
        raise ValueError("Purchase date must be a valid date (YYYY-MM-DD).")

    # Parse warranty years
    years_val = None
    if isinstance(warranty_years, (int, float)):
        years_val = int(warranty_years)
    elif isinstance(warranty_years, str):
        match = re.search(r"\d+", warranty_years)
        if match:
            years_val = int(match.group(0))

    if years_val is None or years_val <= 0:
        raise ValueError("Please select a valid warranty duration (e.g. 1 to 5 years).")

    # Expiry calculation using relativedelta
    expiry_date = purchase + relativedelta(years=years_val)
    today = date.today()

    within_warranty = today <= expiry_date
    days_remaining = max((expiry_date - today).days, 0)
    status_str = "Within Warranty" if within_warranty else "Warranty Expired"

    formatted_purchase = purchase.strftime("%d %B %Y")
    formatted_expiry = expiry_date.strftime("%d %B %Y")
    formatted_today = today.strftime("%d %B %Y")
    duration_str = f"{years_val} Year{'s' if years_val > 1 else ''}"

    return {
        "success": True,
        "status": status_str,
        "is_valid": within_warranty,
        "product_name": clean_product_name,
        "brand": clean_brand,
        "model_number": clean_model_number,
        "serial_number": clean_serial_number,
        "purchase_date": formatted_purchase,
        "purchase_date_raw": purchase.isoformat(),
        "warranty_duration": duration_str,
        "warranty_years": years_val,
        "warranty_expiry": formatted_expiry,
        "expiry_date": formatted_expiry,
        "checked_on": formatted_today,
        "today": formatted_today,
        "days_remaining": days_remaining
    }