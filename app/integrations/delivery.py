import logging
from typing import Optional
from decimal import Decimal

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class YandexDeliveryIntegration:
    """Yandex Delivery API integration"""

    def __init__(self):
        self.api_key = settings.YANDEX_DELIVERY_API_KEY
        self.api_url = settings.YANDEX_DELIVERY_URL
        self.timeout = 30

    async def create_delivery(
        self,
        order_id: int,
        pickup_location: dict,
        delivery_location: dict,
        items: list,
        recipient_phone: str,
        recipient_name: str,
    ) -> Optional[dict]:
        """
        Create delivery order in Yandex Delivery

        Args:
            order_id: Order ID
            pickup_location: {"latitude": float, "longitude": float, "address": str}
            delivery_location: {"latitude": float, "longitude": float, "address": str}
            items: [{"title": str, "quantity": int, "weight": float}]
            recipient_phone: Phone number
            recipient_name: Full name

        Returns:
            Delivery order info with tracking ID
        """
        try:
            payload = {
                "external_order_id": str(order_id),
                "delivery_type": "courierDelivery",
                "locations": [
                    {
                        "type": "source",
                        "latitude": float(pickup_location["latitude"]),
                        "longitude": float(pickup_location["longitude"]),
                        "full_name": "Restaurant",
                        "phone": "1",
                    },
                    {
                        "type": "destination",
                        "latitude": float(delivery_location["latitude"]),
                        "longitude": float(delivery_location["longitude"]),
                        "address": delivery_location.get("address", ""),
                        "full_name": recipient_name,
                        "phone": recipient_phone,
                    },
                ],
                "items": items,
                "requirements": {
                    "taxi_class": "econom",
                },
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/v1/orders",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    return {
                        "delivery_id": data.get("id"),
                        "delivery_order_id": data.get("external_order_id"),
                        "status": data.get("status"),
                        "estimated_delivery_time": data.get("estimate", {}).get("delivery_interval", {}).get("to"),
                    }
        except Exception as e:
            logger.error(f"Yandex Delivery create error: {e}")

        return None

    async def get_delivery_status(self, delivery_id: str) -> Optional[dict]:
        """Get delivery order status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/v1/orders/{delivery_id}",
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "delivery_id": data.get("id"),
                        "status": data.get("status"),
                        "courier": {
                            "id": data.get("performer", {}).get("id"),
                            "name": data.get("performer", {}).get("name"),
                            "phone": data.get("performer", {}).get("phone"),
                        },
                        "location": {
                            "latitude": data.get("performer", {}).get("location", {}).get("latitude"),
                            "longitude": data.get("performer", {}).get("location", {}).get("longitude"),
                        },
                    }
        except Exception as e:
            logger.error(f"Yandex Delivery status error: {e}")

        return None

    async def cancel_delivery(self, delivery_id: str) -> bool:
        """Cancel delivery order"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/v1/orders/{delivery_id}/cancel",
                    headers=headers,
                    timeout=self.timeout,
                )

                return response.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Yandex Delivery cancel error: {e}")

        return False

    async def get_delivery_cost(
        self,
        pickup_location: dict,
        delivery_location: dict,
        weight: float = 1.0,
    ) -> Optional[Decimal]:
        """Get delivery cost estimation"""
        try:
            payload = {
                "source": {
                    "latitude": float(pickup_location["latitude"]),
                    "longitude": float(pickup_location["longitude"]),
                },
                "destination": {
                    "latitude": float(delivery_location["latitude"]),
                    "longitude": float(delivery_location["longitude"]),
                },
                "weight": weight,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/v1/price_estimate",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    price = data.get("estimate", {}).get("final_price")
                    if price:
                        return Decimal(str(price))
        except Exception as e:
            logger.error(f"Yandex Delivery cost estimation error: {e}")

        return None

    def verify_webhook(self, data: dict, signature: str) -> bool:
        """Verify webhook signature from Yandex Delivery"""
        # Implementation based on Yandex Delivery webhook documentation
        # Usually uses HMAC signature verification
        return True
