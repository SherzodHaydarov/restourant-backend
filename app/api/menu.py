import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.repositories.repository import (
    ProductRepository,
    UserRepository,
    RoleRepository,
)
from app.services.service import QRCodeService
from app.schemas.schemas import (
    ProductResponseSchema,
    ProductCreateSchema,
    CategoryResponseSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/menu", tags=["Menu"])


@router.get("/products", response_model=dict)
async def get_products(
    restaurant_id: int = Query(...),
    category_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get products by category"""
    try:
        product_repo = ProductRepository(db)

        if category_id:
            products, total = await product_repo.get_products_by_category(
                category_id, skip, limit
            )
        else:
            products, total = await product_repo.get_available_products(
                restaurant_id, skip, limit
            )

        return {
            "status": "success",
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": str(p.price),
                    "discount_percent": p.discount_percent,
                    "discount_price": str(p.discount_price) if p.discount_price else None,
                    "image_url": p.image_url,
                    "qr_code_url": p.qr_code_url,
                    "is_available": p.is_available,
                    "preparation_time": p.preparation_time,
                }
                for p in products
            ],
        }
    except Exception as e:
        logger.error(f"Get products error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products",
        )


@router.get("/products/{product_id}", response_model=dict)
async def get_product_details(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get product details"""
    try:
        product_repo = ProductRepository(db)
        product = await product_repo.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        ingredients = []
        if product.ingredients:
            import json
            try:
                ingredients = json.loads(product.ingredients)
            except:
                ingredients = []

        return {
            "status": "success",
            "data": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": str(product.price),
                "discount_percent": product.discount_percent,
                "discount_price": str(product.discount_price) if product.discount_price else None,
                "image_url": product.image_url,
                "qr_code_url": product.qr_code_url,
                "ingredients": ingredients,
                "calories": product.calories,
                "preparation_time": product.preparation_time,
                "is_available": product.is_available,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product details error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product details",
        )


@router.post("/products", response_model=dict)
async def create_product(
    product_data: ProductCreateSchema,
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Create new product (Admin/Manager only)"""
    try:
        product_repo = ProductRepository(db)

        # Calculate discount price if discount percent is provided
        discount_price = None
        if product_data.discount_percent:
            discount_price = product_data.price * (
                1 - product_data.discount_percent / 100
            )

        ingredients_json = None
        if product_data.ingredients:
            import json
            ingredients_json = json.dumps(product_data.ingredients)

        # Generate QR code
        qr_data, qr_image = QRCodeService.generate_product_qr(1)  # Will be updated after product creation

        product = await product_repo.create_product(
            restaurant_id=1,  # Should come from current user's restaurant
            category_id=product_data.category_id,
            subcategory_id=product_data.subcategory_id,
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            discount_percent=product_data.discount_percent,
            discount_price=discount_price,
            ingredients=ingredients_json,
            calories=product_data.calories,
            preparation_time=product_data.preparation_time,
            display_order=product_data.display_order,
            qr_code_url=qr_image,
        )

        return {
            "status": "success",
            "message": "Product created successfully",
            "data": {
                "id": product.id,
                "name": product.name,
                "price": str(product.price),
            },
        }
    except Exception as e:
        logger.error(f"Create product error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product",
        )


@router.put("/products/{product_id}", response_model=dict)
async def update_product(
    product_id: int,
    product_data: ProductCreateSchema,
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update product (Admin/Manager only)"""
    try:
        product_repo = ProductRepository(db)

        # Calculate discount price
        discount_price = None
        if product_data.discount_percent:
            discount_price = product_data.price * (
                1 - product_data.discount_percent / 100
            )

        ingredients_json = None
        if product_data.ingredients:
            import json
            ingredients_json = json.dumps(product_data.ingredients)

        product = await product_repo.update_product(
            product_id,
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            discount_percent=product_data.discount_percent,
            discount_price=discount_price,
            ingredients=ingredients_json,
            calories=product_data.calories,
            preparation_time=product_data.preparation_time,
            display_order=product_data.display_order,
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        return {
            "status": "success",
            "message": "Product updated successfully",
            "data": {"id": product.id},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update product error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product",
        )
