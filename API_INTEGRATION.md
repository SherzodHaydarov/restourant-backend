# API Integration Guide

## Table of Contents
1. [Authentication](#authentication)
2. [Menu Management](#menu-management)
3. [Order Management](#order-management)
4. [Payment Processing](#payment-processing)
5. [Delivery Integration](#delivery-integration)
6. [Error Handling](#error-handling)

## Authentication

### Register User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "phone": "+998901234567",
  "first_name": "John",
  "last_name": "Doe"
}

Response (201):
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user"
  }
}
```

### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}

Response (200):
{
  "status": "success",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user"
    }
  }
}
```

### Refresh Token
```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response (200):
{
  "status": "success",
  "data": {
    "access_token": "new_access_token...",
    "token_type": "bearer"
  }
}
```

### Get Current User
```bash
GET /api/auth/me
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_verified": true,
    "phone": "+998901234567",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Menu Management

### Get Products
```bash
GET /api/menu/products?restaurant_id=1&category_id=2&skip=0&limit=20
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "total": 45,
  "skip": 0,
  "limit": 20,
  "data": [
    {
      "id": 1,
      "name": "Pizza Margherita",
      "description": "Classic Italian pizza",
      "price": "15000.00",
      "discount_percent": 10,
      "discount_price": "13500.00",
      "image_url": "https://api.restaurant.uz/uploads/pizza1.jpg",
      "qr_code_url": "data:image/png;base64,...",
      "is_available": true,
      "preparation_time": 20
    },
    ...
  ]
}
```

### Get Product Details
```bash
GET /api/menu/products/1
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Pizza Margherita",
    "description": "Classic Italian pizza",
    "price": "15000.00",
    "discount_percent": 10,
    "discount_price": "13500.00",
    "image_url": "https://api.restaurant.uz/uploads/pizza1.jpg",
    "qr_code_url": "data:image/png;base64,...",
    "ingredients": ["tomato", "mozzarella", "basil", "olive oil"],
    "calories": 800,
    "preparation_time": 20,
    "is_available": true
  }
}
```

## Order Management

### Create Order
```bash
POST /api/orders
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "order_type": "dine_in",
  "table_id": 5,
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "notes": "No onions"
    },
    {
      "product_id": 3,
      "quantity": 1,
      "notes": ""
    }
  ],
  "notes": "Extra napkins please"
}

Response (201):
{
  "status": "success",
  "message": "Order created successfully",
  "data": {
    "id": 1,
    "order_number": "ORD-20240115101530-ABC123",
    "total_amount": "32500.00",
    "status": "new"
  }
}
```

### Get Order Details
```bash
GET /api/orders/1
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "data": {
    "id": 1,
    "order_number": "ORD-20240115101530-ABC123",
    "status": "confirmed",
    "order_type": "dine_in",
    "subtotal": "30000.00",
    "tax_amount": "2400.00",
    "delivery_fee": "0.00",
    "total_amount": "32500.00",
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "unit_price": "15000.00",
        "subtotal": "30000.00"
      }
    ],
    "created_at": "2024-01-15T10:15:30Z",
    "updated_at": "2024-01-15T10:16:45Z"
  }
}
```

### Get User Orders
```bash
GET /api/orders?skip=0&limit=10
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "total": 15,
  "skip": 0,
  "limit": 10,
  "data": [
    {
      "id": 1,
      "order_number": "ORD-20240115101530-ABC123",
      "status": "completed",
      "total_amount": "32500.00",
      "created_at": "2024-01-15T10:15:30Z"
    },
    ...
  ]
}
```

## Payment Processing

### Initiate Payment
```bash
POST /api/orders/1/pay?payment_method=payme
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "message": "Payment initiated",
  "data": {
    "id": 1,
    "order_id": 1,
    "amount": "32500.00",
    "method": "payme",
    "status": "pending",
    "payment_id": null,
    "qr_code_url": "data:image/png;base64,...",
    "payment_link": "https://checkout.paycom.uz/...",
    "created_at": "2024-01-15T10:16:45Z"
  }
}
```

### Payment Status Webhook (Payme)
```bash
POST /webhooks/payme
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "TransactionCompleted",
  "params": {
    "paymentId": "625ffac3ee5d8920a84ab2e4",
    "state": 3,
    "time": 1650540291000,
    "reason": 0,
    "external_order_id": 1
  }
}

Response (200):
{
  "status": "success",
  "message": "Payment confirmed"
}
```

## Delivery Integration

### Create Delivery Order
```bash
POST /api/deliveries
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "order_id": 1,
  "delivery_address": "123 Customer Street, Apt 5, Tashkent",
  "latitude": "41.3775",
  "longitude": "69.2797"
}

Response (201):
{
  "status": "success",
  "data": {
    "id": 1,
    "order_id": 1,
    "courier_id": null,
    "yandex_delivery_id": "yandex_12345",
    "status": "pending",
    "estimated_time": 45,
    "created_at": "2024-01-15T10:16:45Z"
  }
}
```

### Track Delivery
```bash
GET /api/deliveries/1/track
Authorization: Bearer {access_token}

Response (200):
{
  "status": "success",
  "data": {
    "id": 1,
    "order_id": 1,
    "status": "on_the_way",
    "courier": {
      "name": "Ali Karimov",
      "phone": "+998901234567"
    },
    "location": {
      "latitude": "41.3800",
      "longitude": "69.2820"
    },
    "estimated_arrival": "15 minutes"
  }
}
```

## Admin Endpoints

### Dashboard Analytics
```bash
GET /api/admin/dashboard?restaurant_id=1
Authorization: Bearer {admin_token}

Response (200):
{
  "status": "success",
  "data": {
    "today_revenue": "2500000.00",
    "today_orders": 45,
    "active_orders": 8,
    "total_customers": 120,
    "average_order_value": "55555.55",
    "completed_orders": 37
  }
}
```

### Active Orders (Management)
```bash
GET /api/admin/orders/active?restaurant_id=1
Authorization: Bearer {manager_token}

Response (200):
{
  "status": "success",
  "total": 8,
  "data": [
    {
      "id": 1,
      "order_number": "ORD-20240115101530-ABC123",
      "status": "cooking",
      "order_type": "dine_in",
      "total_amount": "32500.00",
      "created_at": "2024-01-15T10:15:30Z",
      "items_count": 2
    },
    ...
  ]
}
```

### Update Order Status
```bash
POST /api/admin/orders/1/status?status=ready
Authorization: Bearer {manager_token}

Response (200):
{
  "status": "success",
  "message": "Order status updated to ready",
  "data": {
    "id": 1,
    "order_number": "ORD-20240115101530-ABC123",
    "status": "ready"
  }
}
```

## Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
  "status": "error",
  "message": "Invalid request data",
  "details": {
    "field": "email",
    "error": "Invalid email format"
  }
}
```

**401 Unauthorized**
```json
{
  "status": "error",
  "message": "Invalid or expired token"
}
```

**403 Forbidden**
```json
{
  "status": "error",
  "message": "Insufficient permissions"
}
```

**404 Not Found**
```json
{
  "status": "error",
  "message": "Resource not found"
}
```

**500 Internal Server Error**
```json
{
  "status": "error",
  "message": "Internal server error"
}
```

## Rate Limiting

Rate limits are applied by Nginx:
- **Auth endpoints**: 10 requests per minute
- **API endpoints**: 100 requests per minute
- **Retry-After header** included in 429 responses

## Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (HttpOnly cookies recommended)
3. **Refresh tokens before expiry** (30 minutes default)
4. **Implement proper error handling** on frontend
5. **Validate input** on both client and server
6. **Use pagination** for large datasets
7. **Cache menu items** on client side (1 hour)
8. **Implement retry logic** for payment webhooks
