import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.repository import (
    OrderRepository,
    PaymentRepository,
    UserRepository,
    TableRepository,
)
from app.services.service import OrderService, PaymentService, QRCodeService
from app.schemas.schemas import OrderCreateSchema, OrderResponseSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new order"""
    try:
        order_repo = OrderRepository(db)
        payment_repo = PaymentRepository(db)

        order_service = OrderService(order_repo, payment_repo)

        # Create order
        items = []
        for item in order_data.items:
            items.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": 15000,  # Should fetch from product
                }
            )

        result = await order_service.create_order(
            restaurant_id=1,  # Should come from context
            user_id=current_user["user_id"],
            order_type=order_data.order_type,
            items=items,
            table_id=order_data.table_id,
            delivery_address_id=order_data.delivery_address_id,
            notes=order_data.notes,
        )

        return {
            "status": "success",
            "message": "Order created successfully",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Create order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )


@router.get("/{order_id}", response_model=dict)
async def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get order details"""
    try:
        order_repo = OrderRepository(db)
        order = await order_repo.get_order_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # Check access
        if order.user_id != current_user["user_id"] and current_user["role"] not in [
            "admin",
            "manager",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return {
            "status": "success",
            "data": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "order_type": order.order_type,
                "subtotal": str(order.subtotal),
                "tax_amount": str(order.tax_amount),
                "delivery_fee": str(order.delivery_fee),
                "total_amount": str(order.total_amount),
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                        "subtotal": str(item.subtotal),
                    }
                    for item in order.items
                ],
                "created_at": order.created_at,
                "updated_at": order.updated_at,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order",
        )


@router.get("", response_model=dict)
async def get_user_orders(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get user orders"""
    try:
        order_repo = OrderRepository(db)
        orders, total = await order_repo.get_user_orders(
            current_user["user_id"], skip, limit
        )

        return {
            "status": "success",
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": str(order.total_amount),
                    "created_at": order.created_at,
                }
                for order in orders
            ],
        }
    except Exception as e:
        logger.error(f"Get user orders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders",
        )


@router.post("/{order_id}/pay", response_model=dict)
async def pay_order(
    order_id: int,
    payment_method: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate payment for order"""
    try:
        order_repo = OrderRepository(db)
        payment_repo = PaymentRepository(db)

        order = await order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # Check access
        if order.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        payment_service = PaymentService(payment_repo)

        # Create payment record
        payment = await payment_service.create_payment(
            order_id=order_id,
            amount=order.total_amount,
            method=payment_method,
        )

        return {
            "status": "success",
            "message": "Payment initiated",
            "data": payment,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment",
        )


@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel order"""
    try:
        order_repo = OrderRepository(db)
        order = await order_repo.get_order_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # Check access
        if order.user_id != current_user["user_id"] and current_user["role"] not in [
            "admin",
            "manager",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        if order.status not in ["new", "confirmed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be cancelled in current status",
            )

        order_service = OrderService(order_repo, PaymentRepository(db))
        result = await order_service.update_order_status(order_id, "cancelled")

        return {
            "status": "success",
            "message": "Order cancelled",
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order",
        )


@router.post("/table/{table_id}/order", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dine_in_order(
    table_id: int,
    order_data: OrderCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    """Create order from table QR code (no auth required)"""
    try:
        table_repo = TableRepository(db)
        order_repo = OrderRepository(db)

        # Verify table exists
        table = await table_repo.get_table_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found",
            )

        order_data.table_id = table_id
        order_data.order_type = "dine_in"

        order_service = OrderService(order_repo, PaymentRepository(db))

        items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": 15000,
            }
            for item in order_data.items
        ]

        result = await order_service.create_order(
            restaurant_id=table.restaurant_id,
            user_id=None,
            order_type="dine_in",
            items=items,
            table_id=table_id,
            notes=order_data.notes,
        )

        return {
            "status": "success",
            "message": "Table order created",
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create table order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )
