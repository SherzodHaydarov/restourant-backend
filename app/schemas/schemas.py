from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ==================== ENUM SCHEMAS ====================


class RoleSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserAuthSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLoginSchema(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshSchema(BaseModel):
    refresh_token: str


# ==================== USER SCHEMAS ====================


class UserBaseSchema(BaseModel):
    username: str
    email: str
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(UserBaseSchema):
    id: int
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    role: RoleSchema
    created_at: datetime


class UserDetailSchema(UserResponseSchema):
    addresses: List["UserAddressResponseSchema"] = []


# ==================== ADDRESS SCHEMAS ====================


class UserAddressBaseSchema(BaseModel):
    label: Optional[str] = None
    address_line: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: bool = False


class UserAddressCreateSchema(UserAddressBaseSchema):
    pass


class UserAddressResponseSchema(UserAddressBaseSchema):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== RESTAURANT SCHEMAS ====================


class RestaurantBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    phone: str
    email: str
    address: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None


class RestaurantCreateSchema(RestaurantBaseSchema):
    pass


class RestaurantResponseSchema(RestaurantBaseSchema):
    id: int
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== CATEGORY SCHEMAS ====================


class CategoryBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0


class CategoryCreateSchema(CategoryBaseSchema):
    pass


class CategoryResponseSchema(CategoryBaseSchema):
    id: int
    restaurant_id: int
    icon_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== SUBCATEGORY SCHEMAS ====================


class SubCategoryBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0


class SubCategoryCreateSchema(SubCategoryBaseSchema):
    pass


class SubCategoryResponseSchema(SubCategoryBaseSchema):
    id: int
    category_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PRODUCT SCHEMAS ====================


class ProductBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    discount_percent: float = 0
    ingredients: Optional[List[str]] = None
    calories: Optional[int] = None
    preparation_time: Optional[int] = None
    display_order: int = 0


class ProductCreateSchema(ProductBaseSchema):
    category_id: int
    subcategory_id: Optional[int] = None


class ProductResponseSchema(ProductBaseSchema):
    id: int
    restaurant_id: int
    category_id: int
    subcategory_id: Optional[int] = None
    discount_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    qr_code_url: Optional[str] = None
    is_available: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== TABLE SCHEMAS ====================


class TableBaseSchema(BaseModel):
    table_number: int
    capacity: int


class TableCreateSchema(TableBaseSchema):
    pass


class TableResponseSchema(TableBaseSchema):
    id: int
    restaurant_id: int
    qr_code_data: str
    qr_code_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableQRSchema(BaseModel):
    table_id: int
    qr_code_url: str
    qr_code_data: str


# ==================== ORDER SCHEMAS ====================


class OrderItemBaseSchema(BaseModel):
    product_id: int
    quantity: int
    notes: Optional[str] = None


class OrderItemCreateSchema(OrderItemBaseSchema):
    pass


class OrderItemResponseSchema(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    discount_percent: float
    subtotal: Decimal
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreateSchema(BaseModel):
    order_type: str  # "dine_in", "takeaway", "delivery"
    table_id: Optional[int] = None
    delivery_address_id: Optional[int] = None
    items: List[OrderItemCreateSchema]
    notes: Optional[str] = None


class OrderResponseSchema(BaseModel):
    id: int
    order_number: str
    restaurant_id: int
    user_id: Optional[int]
    table_id: Optional[int]
    order_type: str
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    items: List[OrderItemResponseSchema]
    notes: Optional[str] = None
    estimated_delivery_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderDetailSchema(OrderResponseSchema):
    payment: Optional["PaymentResponseSchema"] = None
    delivery: Optional["DeliveryResponseSchema"] = None


# ==================== PAYMENT SCHEMAS ====================


class TransactionResponseSchema(BaseModel):
    id: int
    transaction_id: str
    amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentCreateSchema(BaseModel):
    method: str  # "payme", "click", "uzum", "cash"


class PaymentResponseSchema(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    method: str
    status: str
    payment_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    payment_link: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    transactions: List[TransactionResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)


class PaymentWebhookSchema(BaseModel):
    """Base schema for payment webhooks"""
    pass


# ==================== DELIVERY SCHEMAS ====================


class DeliveryResponseSchema(BaseModel):
    id: int
    order_id: int
    courier_id: Optional[int] = None
    yandex_delivery_id: Optional[str] = None
    status: str
    estimated_time: Optional[int] = None
    actual_delivery_time: Optional[datetime] = None
    courier_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryCreateSchema(BaseModel):
    order_id: int
    delivery_address: str
    latitude: Decimal
    longitude: Decimal


# ==================== ANALYTICS SCHEMAS ====================


class DailySalesSchema(BaseModel):
    date: str
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    completed_orders: int


class MonthlySalesSchema(BaseModel):
    month: str
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal


class TopProductSchema(BaseModel):
    product_id: int
    product_name: str
    quantity_sold: int
    revenue: Decimal


class DashboardStatsSchema(BaseModel):
    today_revenue: Decimal
    today_orders: int
    active_orders: int
    total_customers: int
    average_order_value: Decimal
    top_products: List[TopProductSchema]
    daily_sales_last_7_days: List[DailySalesSchema]


# ==================== PAGINATION SCHEMAS ====================


class PaginationParamsSchema(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class PaginatedResponseSchema(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[dict]


# Update forward references
UserDetailSchema.model_rebuild()
OrderDetailSchema.model_rebuild()
