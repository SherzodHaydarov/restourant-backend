"""
Utility functions for the application
"""
import uuid
from datetime import datetime
from decimal import Decimal


def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"ORD-{timestamp}-{random_suffix}"


def calculate_discount_price(price: Decimal, discount_percent: float) -> Decimal:
    """Calculate discounted price"""
    if discount_percent <= 0:
        return None
    discount_amount = price * Decimal(str(discount_percent / 100))
    return (price - discount_amount).quantize(Decimal("0.01"))


def format_currency(amount: Decimal, currency: str = "UZS") -> str:
    """Format amount as currency"""
    return f"{amount:,.2f} {currency}"


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    # Remove spaces and dashes
    cleaned = phone.replace(" ", "").replace("-", "")
    # Should start with + or country code
    return cleaned.startswith("+") and len(cleaned) >= 10


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def paginate(items: list, skip: int, limit: int) -> list:
    """Paginate items"""
    return items[skip : skip + limit]


def get_total_price(items: list) -> Decimal:
    """Calculate total from order items"""
    total = Decimal("0.00")
    for item in items:
        if isinstance(item.get("subtotal"), Decimal):
            total += item["subtotal"]
        else:
            total += Decimal(str(item.get("subtotal", 0)))
    return total.quantize(Decimal("0.01"))


def seconds_to_hms(seconds: int) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_delivery_time_display(minutes: int) -> str:
    """Get readable delivery time"""
    if minutes < 60:
        return f"{minutes} минут"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} соат"
        return f"{hours} соат {mins} минут"
