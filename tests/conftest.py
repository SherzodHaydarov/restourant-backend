import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.main import app


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def test_user_data():
    """Sample test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!",
        "phone": "+998901234567",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def test_product_data():
    """Sample test product data"""
    return {
        "category_id": 1,
        "name": "Pizza Margherita",
        "description": "Classic Italian pizza",
        "price": "15000.00",
        "discount_percent": 0,
        "ingredients": ["tomato", "mozzarella", "basil"],
        "calories": 800,
        "preparation_time": 20,
    }


@pytest.fixture
def test_order_data():
    """Sample test order data"""
    return {
        "order_type": "dine_in",
        "table_id": 1,
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "notes": "No onions",
            }
        ],
        "notes": "Extra napkins please",
    }
