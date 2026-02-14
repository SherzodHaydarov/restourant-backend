#!/usr/bin/env python
"""
Database initialization and management script
"""
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import init_db, engine, async_session
from app.models.models import Role, User, Restaurant, Category, RestaurantTable
from app.core.security import SecurityService


async def create_default_data():
    """Create default data for development"""
    async with async_session() as session:
        try:
            # Create roles
            existing_roles = await session.execute(select(Role))
            if not existing_roles.scalars().first():
                roles = Role.get_default_roles()
                for role_data in roles:
                    role = Role(**role_data)
                    session.add(role)
                await session.commit()
                print("✓ Default roles created")

            # Create demo restaurant
            existing_restaurant = await session.execute(select(Restaurant))
            if not existing_restaurant.scalars().first():
                restaurant = Restaurant(
                    name="Demo Restaurant",
                    description="Demo restaurant for testing",
                    phone="+998901234567",
                    email="demo@restaurant.uz",
                    address="123 Main Street, Tashkent",
                    latitude=41.3775,
                    longitude=69.2797,
                    opening_time="09:00",
                    closing_time="23:00",
                )
                session.add(restaurant)
                await session.commit()
                print("✓ Demo restaurant created")

                # Create demo category
                category = Category(
                    restaurant_id=restaurant.id,
                    name="Appetizers",
                    description="Starter dishes",
                    display_order=1,
                )
                session.add(category)
                await session.commit()
                print("✓ Demo category created")

                # Create demo tables
                for table_num in range(1, 6):
                    table = RestaurantTable(
                        restaurant_id=restaurant.id,
                        table_number=table_num,
                        capacity=4,
                        qr_code_data=f"restaurant.uz/order?table_id={table_num}",
                    )
                    session.add(table)
                await session.commit()
                print("✓ Demo tables created")

            # Create admin user
            existing_admin = await session.execute(
                select(User).where(User.username == "admin")
            )
            if not existing_admin.scalars().first():
                admin = User(
                    username="admin",
                    email="admin@restaurant.uz",
                    password_hash=SecurityService.hash_password("admin123"),
                    first_name="Admin",
                    last_name="User",
                    role_id=1,  # Admin role
                    is_verified=True,
                    is_active=True,
                )
                session.add(admin)
                await session.commit()
                print("✓ Admin user created (username: admin, password: admin123)")

            # Create manager user
            existing_manager = await session.execute(
                select(User).where(User.username == "manager")
            )
            if not existing_manager.scalars().first():
                manager = User(
                    username="manager",
                    email="manager@restaurant.uz",
                    password_hash=SecurityService.hash_password("manager123"),
                    first_name="Manager",
                    last_name="User",
                    role_id=2,  # Manager role
                    is_verified=True,
                    is_active=True,
                )
                session.add(manager)
                await session.commit()
                print("✓ Manager user created (username: manager, password: manager123)")

        except Exception as e:
            print(f"✗ Error creating default data: {e}")
            await session.rollback()
            raise


async def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            print("Initializing database...")
            await init_db()
            print("✓ Database initialized")

        elif command == "create-data":
            print("Creating default data...")
            await init_db()
            await create_default_data()
            print("✓ Default data created")

        elif command == "reset":
            print("Resetting database...")
            async with engine.begin() as conn:
                from app.core.database import Base
                await conn.run_sync(Base.metadata.drop_all)
            print("✓ Database reset")
            print("Creating fresh database...")
            await init_db()
            await create_default_data()
            print("✓ Database reset and initialized")

        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, create-data, reset")
    else:
        print("Usage: python manage.py [command]")
        print("Available commands:")
        print("  init          - Initialize database tables")
        print("  create-data   - Create default data")
        print("  reset         - Reset and reinitialize database")


if __name__ == "__main__":
    asyncio.run(main())
