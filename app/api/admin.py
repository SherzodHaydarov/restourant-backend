import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, __main__, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.repositories.repository import OrderRepository, UserRepository
from app.services.service import AnalyticsService
from app.schemas.schemas import DashboardStatsSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard", response_model=dict)
async def get_dashboard(
    restaurant_id: int = Query(...),
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard stats"""
    try:
        order_repo = OrderRepository(db)
        analytics_service = AnalyticsService(order_repo)

        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")

        # Get daily sales
        daily_stats = await analytics_service.get_daily_sales(restaurant_id, today)

        # Get active orders count
        active_orders_count = await analytics_service.get_active_orders_count(
            restaurant_id
        )

        # Get total customers (placeholder)
        user_repo = UserRepository(db)
        active_users, total_customers = await user_repo.get_active_users(limit=1000000)

        return {
            "status": "success",
            "data": {
                "today_revenue": daily_stats["total_revenue"],
                "today_orders": daily_stats["total_orders"],
                "active_orders": active_orders_count,
                "total_customers": total_customers,
                "average_order_value": daily_stats["average_order_value"],
                "completed_orders": daily_stats["completed_orders"],
            },
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data",
        )


@router.get("/sales/daily", response_model=dict)
async def get_daily_sales(
    restaurant_id: int = Query(...),
    date: str = Query(...),
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get daily sales report"""
    try:
        order_repo = OrderRepository(db)
        analytics_service = AnalyticsService(order_repo)

        stats = await analytics_service.get_daily_sales(restaurant_id, date)

        return {
            "status": "success",
            "data": stats,
        }
    except Exception as e:
        logger.error(f"Daily sales error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get daily sales",
        )


@router.get("/sales/monthly", response_model=dict)
async def get_monthly_sales(
    restaurant_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly sales report"""
    try:
        order_repo = OrderRepository(db)

        # Generate date range for the month
        from datetime import datetime
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # TODO: Implement monthly aggregation
        total_orders = 0
        total_revenue = 0

        return {
            "status": "success",
            "data": {
                "month": f"{year}-{month:02d}",
                "total_orders": total_orders,
                "total_revenue": str(total_revenue),
            },
        }
    except Exception as e:
        logger.error(f"Monthly sales error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monthly sales",
        )


@router.get("/orders/active", response_model=dict)
async def get_active_orders(
    restaurant_id: int = Query(...),
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get all active orders"""
    try:
        order_repo = OrderRepository(db)
        orders = await order_repo.get_restaurant_active_orders(restaurant_id)

        return {
            "status": "success",
            "total": len(orders),
            "data": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "order_type": order.order_type,
                    "total_amount": str(order.total_amount),
                    "created_at": order.created_at,
                    "items_count": len(order.items),
                }
                for order in orders
            ],
        }
    except Exception as e:
        logger.error(f"Active orders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active orders",
        )


@router.post("/orders/{order_id}/status", response_model=dict)
async def update_order_status(
    order_id: int,
    status: str = Query(...),
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update order status"""
    try:
        from app.services.service import OrderService, PaymentService
        from app.repositories.repository import PaymentRepository

        order_repo = OrderRepository(db)
        payment_repo = PaymentRepository(db)

        order_service = OrderService(order_repo, payment_repo)
        result = await order_service.update_order_status(order_id, status)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        return {
            "status": "success",
            "message": f"Order status updated to {status}",
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status",
        )
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.admin:router", host="127.0.0.1", port=8000)