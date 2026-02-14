import logging
import uuid
from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone

import qrcode
from io import BytesIO
import base64
import hashlib

from app.core.config import settings
from app.repositories.repository import (
    UserRepository,
    RoleRepository,
    ProductRepository,
    OrderRepository,
    PaymentRepository,
    TableRepository,
    UserAddressRepository,
)
from app.core.security import SecurityService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication business logic"""

    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> dict:
        """Register new user"""
        existing_user = await self.user_repo.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"Email {email} already registered")

        if await self.user_repo.get_user_by_username(username):
            raise ValueError(f"Username {username} already taken")

        user = await self.user_repo.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
        )

        role = await self.role_repo.get_role_by_id(user.role_id)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role.name if role else "user",
        }

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user and return tokens"""
        user = await self.user_repo.get_user_by_username(username)

        if not user or not SecurityService.verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {username}")
            return None

        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {username}")
            return None

        role = await self.role_repo.get_role_by_id(user.role_id)
        role_name = role.name if role else "user"

        # Create tokens
        access_token = SecurityService.create_access_token(
            data={"sub": user.id, "username": user.username, "role": role_name}
        )
        refresh_token = SecurityService.create_refresh_token(
            data={"sub": user.id, "username": user.username}
        )

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role_name,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        try:
            payload = SecurityService.verify_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = payload.get("sub")
            user = await self.user_repo.get_user_by_id(user_id)

            if not user or not user.is_active:
                return None

            role = await self.role_repo.get_role_by_id(user.role_id)
            role_name = role.name if role else "user"

            access_token = SecurityService.create_access_token(
                data={"sub": user.id, "username": user.username, "role": role_name}
            )
            return access_token
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None


class QRCodeService:
    """QR Code generation service"""

    @staticmethod
    def generate_table_qr(restaurant_id: int, table_id: int) -> tuple[str, str]:
        """
        Generate QR code for table
        Returns: (qr_code_data, qr_code_image_base64)
        """
        qr_data = f"{settings.UPLOAD_DIR}/order?restaurant_id={restaurant_id}&table_id={table_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return qr_data, f"data:image/png;base64,{img_str}"

    @staticmethod
    def generate_product_qr(product_id: int) -> tuple[str, str]:
        """
        Generate QR code for product
        Returns: (qr_code_data, qr_code_image_base64)
        """
        qr_data = f"{settings.UPLOAD_DIR}/product/{product_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return qr_data, f"data:image/png;base64,{img_str}"


class OrderService:
    """Order management business logic"""

    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository):
        self.order_repo = order_repo
        self.payment_repo = payment_repo

    async def create_order(
        self,
        restaurant_id: int,
        user_id: Optional[int],
        order_type: str,
        items: list,
        table_id: Optional[int] = None,
        delivery_address_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Create new order"""
        # Generate unique order number
        order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        # Calculate totals
        subtotal = Decimal("0.00")
        for item in items:
            subtotal += Decimal(str(item["price"])) * Decimal(str(item["quantity"]))

        tax_amount = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"))  # 8% tax
        total_amount = subtotal + tax_amount

        order = await self.order_repo.create_order(
            order_number=order_number,
            restaurant_id=restaurant_id,
            user_id=user_id,
            order_type=order_type,
            table_id=table_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            delivery_address_id=delivery_address_id,
            notes=notes,
        )

        logger.info(f"Order created: {order_number} with total {total_amount}")

        return {
            "id": order.id,
            "order_number": order_number,
            "total_amount": str(total_amount),
            "status": order.status,
        }

    async def get_order(self, order_id: int) -> Optional[dict]:
        """Get order details"""
        order = await self.order_repo.get_order_by_id(order_id)
        if not order:
            return None

        return {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "order_type": order.order_type,
            "total_amount": str(order.total_amount),
            "created_at": order.created_at,
        }

    async def update_order_status(self, order_id: int, status: str) -> Optional[dict]:
        """Update order status"""
        order = await self.order_repo.update_order_status(order_id, status)
        if not order:
            return None

        logger.info(f"Order {order.order_number} status updated to {status}")

        return {
            "id": order.id,
            "order_number": order.order_number,
            "status": status,
        }


class PaymentService:
    """Payment management business logic"""

    def __init__(self, payment_repo: PaymentRepository):
        self.payment_repo = payment_repo

    async def create_payment(
        self, order_id: int, amount: Decimal, method: str
    ) -> dict:
        """Create payment record"""
        payment = await self.payment_repo.create_payment(
            order_id=order_id,
            amount=amount,
            method=method,
        )

        return {
            "id": payment.id,
            "order_id": order_id,
            "amount": str(amount),
            "method": method,
            "status": payment.status,
        }

    async def update_payment_status(
        self,
        payment_id: int,
        status: str,
        payment_provider_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Update payment status"""
        update_data = {"status": status}
        if payment_provider_id:
            update_data["payment_id"] = payment_provider_id

        payment = await self.payment_repo.update_payment(payment_id, **update_data)
        if not payment:
            return None

        return {
            "id": payment.id,
            "status": payment.status,
        }

    @staticmethod
    def verify_payme_signature(data: dict, signature: str) -> bool:
        """Verify Payme payment signature"""
        # Implementation depends on Payme API documentation
        # This is a placeholder
        return True

    @staticmethod
    def verify_click_signature(data: dict, signature: str) -> bool:
        """Verify Click payment signature"""
        # Implementation depends on Click API documentation
        # This is a placeholder
        return True


class AnalyticsService:
    """Analytics and reporting business logic"""

    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    async def get_daily_sales(self, restaurant_id: int, date: str) -> dict:
        """Get daily sales stats"""
        orders, total_count = await self.order_repo.get_restaurant_orders_by_date(
            restaurant_id, date, limit=1000
        )

        total_revenue = Decimal("0.00")
        completed_orders = 0

        for order in orders:
            total_revenue += order.total_amount
            if order.status == "completed":
                completed_orders += 1

        avg_order_value = (
            total_revenue / len(orders) if orders else Decimal("0.00")
        )

        return {
            "date": date,
            "total_orders": len(orders),
            "total_revenue": str(total_revenue),
            "average_order_value": str(avg_order_value),
            "completed_orders": completed_orders,
        }

    async def get_active_orders_count(self, restaurant_id: int) -> int:
        """Get count of active orders"""
        orders = await self.order_repo.get_restaurant_active_orders(restaurant_id)
        return len(orders)
