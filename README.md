# Restaurant Backend API

Production-ready backend for restaurant management system built with FastAPI, PostgreSQL, and modern Python technologies.

## Features

- **Authentication System**: JWT-based with role-based access control (Admin, Manager, Cashier, Courier, User)
- **Menu Management**: Categories, subcategories, products with pricing and discounts
- **Table QR System**: Unique QR codes for each table with automatic order placement
- **Order Management**: Support for dine-in, takeaway, and delivery orders
- **Payment Integration**: Payme, Click, Uzum payment gateways
- **Delivery Integration**: Yandex Delivery API integration
- **Admin Analytics**: Dashboard with sales stats, revenue tracking, order management
- **Caching**: Redis-based caching for performance optimization
- **Background Jobs**: Celery for async tasks (email, payment status check, etc.)
- **Logging**: Comprehensive logging with audit trails
- **Docker**: Complete Docker and docker-compose setup

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.12
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0 async ORM
- **Migrations**: Alembic
- **Cache**: Redis 7
- **Task Queue**: Celery 5
- **Authentication**: JWT with bcrypt hashing
- **API Documentation**: OpenAPI/Swagger
- **Web Server**: Nginx
- **Containerization**: Docker

## Project Structure

```
app/
├── api/              # API route handlers
│   ├── auth.py      # Authentication routes
│   ├── menu.py      # Menu management routes
│   ├── orders.py    # Order management routes
│   └── admin.py     # Admin panel analytics routes
├── core/            # Core utilities
│   ├── config.py    # Configuration
│   ├── security.py  # JWT and password utilities
│   ├── database.py  # Database connection
│   ├── cache.py     # Redis cache utilities
│   └── logging_config.py
├── models/          # SQLAlchemy ORM models
│   └── models.py
├── schemas/         # Pydantic request/response schemas
│   └── schemas.py
├── services/        # Business logic layer
│   └── service.py
├── repositories/    # Data access layer
│   └── repository.py
├── integrations/    # External integrations
│   ├── payment.py   # Payment gateway integration
│   └── delivery.py  # Delivery service integration
├── workers/         # Background tasks
│   └── celery_app.py
└── main.py         # FastAPI application entry point
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Docker (optional)

### Local Development Setup

1. **Clone repository and setup environment**
```bash
cd restaurant-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Setup database**
```bash
alembic upgrade head
```

4. **Run development server**
```bash
python -m uvicorn app.main:app --reload
```

Access API docs at `http://localhost:8000/docs`

### Docker Setup

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache
- FastAPI app
- Celery worker
- Nginx reverse proxy

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Menu
- `GET /api/menu/products` - Get products with filtering
- `GET /api/menu/products/{id}` - Get product details
- `POST /api/menu/products` - Create product (Manager/Admin)
- `PUT /api/menu/products/{id}` - Update product (Manager/Admin)

### Orders
- `POST /api/orders` - Create new order
- `GET /api/orders` - Get user orders
- `GET /api/orders/{id}` - Get order details
- `POST /api/orders/{id}/pay` - Initiate payment
- `POST /api/orders/{id}/cancel` - Cancel order
- `POST /api/orders/table/{table_id}/order` - Create order from table QR

### Admin
- `GET /admin` - Lightweight admin panel page with endpoint shortcuts
- `GET /api/admin/dashboard` - Dashboard analytics
- `GET /api/admin/sales/daily` - Daily sales report
- `GET /api/admin/sales/monthly` - Monthly sales report
- `GET /api/admin/orders/active` - Active orders
- `POST /api/admin/orders/{id}/status` - Update order status

## Database Schema

### Key Tables
- **users** - User accounts with roles
- **roles** - Role definitions (admin, manager, etc.)
- **restaurants** - Restaurant information
- **categories** - Product categories
- **products** - Menu items
- **restaurant_tables** - Dine-in tables with QR codes
- **orders** - Order records
- **order_items** - Items in each order
- **payments** - Payment records
- **delivery_orders** - Delivery tracking
- **audit_logs** - Admin activity logs

## Security Features

- JWT token-based authentication
- Bcrypt password hashing
- Role-based access control
- SQL injection protection (ORM)
- CORS configuration
- Rate limiting (Nginx)
- HTTPS-ready
- Secure headers
- Audit logging

## Payment Integration

### Supported Providers
1. **Payme** - Popular in Uzbekistan
2. **Click** - UzCard payment system
3. **Uzum** - Digital wallet payments

### Payment Flow
1. Create order
2. Initiate payment with selected method
3. User redirected to payment gateway
4. Webhook updates payment status
5. Order status updates on completion

## Delivery Integration

### Yandex Delivery
- Create delivery orders
- Track courier location in real-time
- Get delivery cost estimation
- Handle delivery status updates via webhooks

## Background Tasks (Celery)

- Email notifications
- Payment status checking
- Delivery tracking
- Report generation
- Session cleanup

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest app/tests/test_auth.py
```

## Monitoring & Logging

- **Application logs**: `logs/app.log`
- **Audit logs**: `logs/audit.log`
- **Log level**: Configure in `.env`
- **Celery logs**: See docker logs or worker output

## Performance Optimization

- Redis caching for frequently accessed data
- Database query optimization with indexes
- Async operations throughout
- Connection pooling
- Pagination for large datasets
- CDN-ready image serving

## Production Deployment

### Recommendations

1. **Environment**
   - Use HTTPS/TLS
   - Set `ENVIRONMENT=production`
   - Use strong `SECRET_KEY`
   - Set proper database URL

2. **Database**
   - Use managed PostgreSQL service
   - Enable backups
   - Use connection pooling

3. **Cache**
   - Use managed Redis
   - Enable TTL cleanup
   - Monitor memory usage

4. **Monitoring**
   - Setup error tracking (Sentry)
   - Monitor API response times
   - Track database queries
   - Alert on critical errors

5. **Scaling**
   - Use load balancer
   - Run multiple app instances
   - Separate Celery workers
   - Database read replicas

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (change in production!)
- `REDIS_URL` - Redis connection string
- `ALLOWED_ORIGINS` - CORS allowed origins

## Contributing

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues and questions, please create an issue in the repository.
