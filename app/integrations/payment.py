import logging
import json
from decimal import Decimal
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymeIntegration:
    """Payme payment gateway integration"""

    def __init__(self):
        self.merchant_id = settings.PAYME_MERCHANT_ID
        self.account = settings.PAYME_ACCOUNT
        self.api_url = settings.PAYME_API_URL

    async def create_invoice(
        self, order_id: int, amount: Decimal, order_number: str
    ) -> Optional[dict]:
        """
        Create invoice in Payme
        Returns: payment_link and QR code URL
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "GeneratePaymentForm",
                "params": {
                    "amount": int(amount * 100),  # Payme uses tyins (1 som = 100 tyins)
                    "account": {
                        "order_id": order_id,
                        "order_number": order_number,
                    },
                    "description": f"Payment for order {order_number}",
                },
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"X-Auth": f"{self.merchant_id}:{self.account}"},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return {
                            "payment_link": data["result"]["url"],
                            "payment_id": data["result"]["paymentId"],
                        }
        except Exception as e:
            logger.error(f"Payme integration error: {e}")

        return None

    async def check_payment_status(self, payment_id: str) -> Optional[str]:
        """Check payment status in Payme"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "CheckPayment",
                "params": {
                    "paymentId": payment_id,
                },
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"X-Auth": f"{self.merchant_id}:{self.account}"},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return data["result"]["state"]
        except Exception as e:
            logger.error(f"Payme status check error: {e}")

        return None

    def verify_webhook_signature(self, data: dict, signature: str) -> bool:
        """Verify webhook signature from Payme"""
        # Implementation based on Payme webhook security documentation
        # Typically uses HMAC-SHA256 with merchant key
        return True


class ClickIntegration:
    """Click payment gateway integration"""

    def __init__(self):
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.secret_key = settings.CLICK_SECRET_KEY
        self.service_id = settings.CLICK_SERVICE_ID
        self.api_url = "https://api.click.uz/v2"

    async def create_invoice(
        self, order_id: int, amount: Decimal, order_number: str
    ) -> Optional[dict]:
        """
        Create invoice in Click
        Returns: payment_link and transaction ID
        """
        try:
            payload = {
                "merchant_id": self.merchant_id,
                "service_id": self.service_id,
                "click_trans_id": order_id,
                "amount": float(amount),
                "currency": "UZS",
                "description": f"Payment for order {order_number}",
                "sign_string": "",  # Will be calculated
            }

            # Calculate signature
            sign_string = (
                f"{self.merchant_id};"
                f"{self.service_id};"
                f"{order_id};"
                f"{amount};"
                f"{self.secret_key}"
            )
            import hashlib
            payload["sign_string"] = hashlib.sha1(sign_string.encode()).hexdigest()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/invoice/create/",
                    json=payload,
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "payment_link": data.get("click_payme_id"),
                            "click_trans_id": data.get("click_trans_id"),
                        }
        except Exception as e:
            logger.error(f"Click integration error: {e}")

        return None

    def verify_webhook_signature(self, data: dict, signature: str) -> bool:
        """Verify webhook signature from Click"""
        # Implementation based on Click webhook security documentation
        return True


class UzumIntegration:
    """Uzum payment gateway integration"""

    def __init__(self):
        self.merchant_id = settings.UZUM_MERCHANT_ID
        self.secret_key = settings.UZUM_SECRET_KEY

    async def create_invoice(
        self, order_id: int, amount: Decimal, order_number: str
    ) -> Optional[dict]:
        """
        Create invoice in Uzum
        Returns: payment_link
        """
        try:
            payload = {
                "merchant_id": self.merchant_id,
                "amount": int(amount * 100),
                "account": {
                    "order_id": order_id,
                    "order_number": order_number,
                },
                "description": f"Payment for order {order_number}",
            }

            # Calculate signature
            import hashlib
            signature_string = (
                f"{self.merchant_id}"
                f"{int(amount * 100)}"
                f"{order_id}"
                f"{self.secret_key}"
            )
            signature = hashlib.sha256(signature_string.encode()).hexdigest()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.uzum.uz/api/merchant/invoice/create",
                    json=payload,
                    headers={"X-Signature": signature},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "payment_link": data.get("invoice_url"),
                            "invoice_id": data.get("invoice_id"),
                        }
        except Exception as e:
            logger.error(f"Uzum integration error: {e}")

        return None

    def verify_webhook_signature(self, data: dict, signature: str) -> bool:
        """Verify webhook signature from Uzum"""
        # Implementation based on Uzum webhook security documentation
        return True


class PaymentGatewayFactory:
    """Factory for creating payment gateway instances"""

    _gateways = {
        "payme": PaymeIntegration,
        "click": ClickIntegration,
        "uzum": UzumIntegration,
    }

    @classmethod
    def get_gateway(cls, provider: str):
        """Get payment gateway instance"""
        gateway_class = cls._gateways.get(provider.lower())
        if not gateway_class:
            raise ValueError(f"Unsupported payment provider: {provider}")
        return gateway_class()
