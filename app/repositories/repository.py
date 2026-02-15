import logging
from typing import Optional, List, Any
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import User, Role, Category, Product, Order, RestaurantTable, Payment, UserAddress
from app.core.security import SecurityService

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository for common operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self):
        """Commit changes"""
        await self.session.commit()

    async def rollback(self):
        """Rollback changes"""
        await self.session.rollback()


class UserRepository(BaseRepository):
    """Repository for user database operations"""

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Create new user"""
        user = User(
            username=username,
            email=email,
            phone=phone,
            password_hash=SecurityService.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role_id=5,  # User role
        )
        self.session.add(user)
        await self.commit()
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with role"""
        stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username).options(selectinload(User.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email).options(selectinload(User.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone"""
        stmt = select(User).where(User.phone == phone).options(selectinload(User.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 10) -> tuple[List[User], int]:
        """Get active users with pagination"""
        stmt = select(User).where(User.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(User).where(User.deleted_at.is_(None))

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all(), total # pyright: ignore[reportReturnType]

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and key != "password_hash":
                setattr(user, key, value)

        await self.commit()
        return user

    async def enable_user(self, user_id: int, email: str) -> Optional[User]:
        """Mark user as verified"""
        user = await self.get_user_by_id(user_id)
        if user:
            user.is_verified = True
            await self.commit()
        return user


class RoleRepository(BaseRepository):
    """Repository for role database operations"""

    async def create_default_roles(self) -> None:
        """Create default roles if not exist"""
        for role_data in Role.get_default_roles():
            existing = await self.session.scalar(
                select(Role).where(Role.name == role_data["name"])
            )
            if not existing:
                role = Role(**role_data)
                self.session.add(role)

        await self.commit()

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        stmt = select(Role).where(Role.id == role_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        stmt = select(Role).where(Role.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ProductRepository(BaseRepository):
    """Repository for product database operations"""

    async def create_product(self, **kwargs) -> Product:
        """Create new product"""
        product = Product(**kwargs)
        self.session.add(product)
        await self.commit()
        return product

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_products_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Product], int]:
        """Get products by category with pagination"""
        stmt = select(Product).where(
            (Product.category_id == category_id) & (Product.is_active == True)
        )
        count_stmt = select(func.count()).select_from(Product).where(
            (Product.category_id == category_id) & (Product.is_active == True)
        )

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(stmt.order_by(Product.display_order).offset(skip).limit(limit))
        return result.scalars().all(), total

    async def get_available_products(
        self, restaurant_id: int, skip: int = 0, limit: int = 50
    ) -> tuple[List[Product], int]:
        """Get available products"""
        stmt = select(Product).where(
            (Product.restaurant_id == restaurant_id) &
            (Product.is_available == True) &
            (Product.is_active == True)
        )
        count_stmt = select(func.count()).select_from(Product).where(
            (Product.restaurant_id == restaurant_id) &
            (Product.is_available == True) &
            (Product.is_active == True)
        )

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(stmt.order_by(Product.display_order).offset(skip).limit(limit))
        return result.scalars().all(), total

    async def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """Update product"""
        product = await self.get_product_by_id(product_id)
        if not product:
            return None

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        await self.commit()
        return product


class OrderRepository(BaseRepository):
    """Repository for order database operations"""

    async def create_order(self, **kwargs) -> Order:
        """Create new order"""
        order = Order(**kwargs)
        self.session.add(order)
        await self.commit()
        return order

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID with items"""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(Order.items[0].product),
                selectinload(Order.payment).selectinload(Order.payment.transactions),
                selectinload(Order.delivery),
                selectinload(Order.table),
                selectinload(Order.user),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        stmt = select(Order).where(Order.order_number == order_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_orders(
        self, user_id: int, skip: int = 0, limit: int = 10
    ) -> tuple[List[Order], int]:
        """Get user orders with pagination"""
        stmt = select(Order).where(Order.user_id == user_id)
        count_stmt = select(func.count()).select_from(Order).where(Order.user_id == user_id)

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(
            stmt.order_by(desc(Order.created_at)).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def get_restaurant_active_orders(self, restaurant_id: int) -> List[Order]:
        """Get active orders for restaurant"""
        stmt = select(Order).where(
            (Order.restaurant_id == restaurant_id) &
            (Order.status.in_(["new", "confirmed", "cooking", "ready", "delivering"]))
        ).order_by(desc(Order.created_at))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_restaurant_orders_by_date(
        self, restaurant_id: int, date: str, skip: int = 0, limit: int = 100
    ) -> tuple[List[Order], int]:
        """Get restaurant orders by date"""
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        next_day = date_obj + timedelta(days=1)

        stmt = select(Order).where(
            (Order.restaurant_id == restaurant_id) &
            (Order.created_at >= date_obj) &
            (Order.created_at < next_day)
        )
        count_stmt = select(func.count()).select_from(Order).where(
            (Order.restaurant_id == restaurant_id) &
            (Order.created_at >= date_obj) &
            (Order.created_at < next_day)
        )

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(
            stmt.order_by(desc(Order.created_at)).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """Update order status"""
        order = await self.get_order_by_id(order_id)
        if order:
            order.status = status
            await self.commit()
        return order


class PaymentRepository(BaseRepository):
    """Repository for payment database operations"""

    async def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID"""
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_payment_by_order(self, order_id: int) -> Optional[Payment]:
        """Get payment by order ID"""
        stmt = select(Payment).where(Payment.order_id == order_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_payment(self, **kwargs) -> Payment:
        """Create new payment"""
        payment = Payment(**kwargs)
        self.session.add(payment)
        await self.commit()
        return payment

    async def update_payment(self, payment_id: int, **kwargs) -> Optional[Payment]:
        """Update payment"""
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            return None

        for key, value in kwargs.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        await self.commit()
        return payment


class TableRepository(BaseRepository):
    """Repository for table database operations"""

    async def get_table_by_id(self, table_id: int) -> Optional[RestaurantTable]:
        """Get table by ID"""
        stmt = select(RestaurantTable).where(RestaurantTable.id == table_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_table_by_qr_code(self, qr_code_data: str) -> Optional[RestaurantTable]:
        """Get table by QR code data"""
        stmt = select(RestaurantTable).where(RestaurantTable.qr_code_data == qr_code_data)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_restaurant_tables(self, restaurant_id: int) -> List[RestaurantTable]:
        """Get all tables for restaurant"""
        stmt = select(RestaurantTable).where(
            RestaurantTable.restaurant_id == restaurant_id
        ).order_by(RestaurantTable.table_number)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_table(self, **kwargs) -> RestaurantTable:
        """Create new table"""
        table = RestaurantTable(**kwargs)
        self.session.add(table)
        await self.commit()
        return table


class UserAddressRepository(BaseRepository):
    """Repository for user address database operations"""

    async def get_address_by_id(self, address_id: int) -> Optional[UserAddress]:
        """Get address by ID"""
        stmt = select(UserAddress).where(UserAddress.id == address_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_addresses(self, user_id: int) -> List[UserAddress]:
        """Get user addresses"""
        stmt = select(UserAddress).where(
            (UserAddress.user_id == user_id) &
            (UserAddress.is_active == True)
        ).order_by(desc(UserAddress.is_default))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_address(self, **kwargs) -> UserAddress:
        """Create new address"""
        address = UserAddress(**kwargs)
        self.session.add(address)
        await self.commit()
        return address

    async def update_address(self, address_id: int, **kwargs) -> Optional[UserAddress]:
        """Update address"""
        address = await self.get_address_by_id(address_id)
        if not address:
            return None

        for key, value in kwargs.items():
            if hasattr(address, key):
                setattr(address, key, value)

        await self.commit()
        return address
