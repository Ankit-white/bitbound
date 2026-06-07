import razorpay
from razorpay.errors import BadRequestError, SignatureVerificationError
from typing import Dict, Any, Optional
import json

from app.core.config import settings


class RazorpayServiceError(Exception):
    """Raised when Razorpay API operations fail."""
    pass


class RazorpayService:
    def __init__(self, key_id: str, key_secret: str, webhook_secret: Optional[str] = None):
        self.key_id = key_id
        self.key_secret = key_secret
        self.webhook_secret = webhook_secret
        self.client = razorpay.Client(auth=(key_id, key_secret))

    def create_order(
        self,
        amount: float,
        receipt: str,
        currency: str = "INR",
        payment_capture: int = 1
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order.
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            receipt: Receipt ID (usually payment record ID)
            currency: Currency code (default: INR)
            payment_capture: 1 for auto-capture, 0 for manual
        
        Returns:
            Dictionary with order_id, amount, currency, status
        """
        try:
            amount_in_paise = int(round(amount * 100))
            
            order_data = {
                'amount': amount_in_paise,
                'currency': currency,
                'receipt': receipt,
                'payment_capture': payment_capture
            }
            
            order = self.client.order.create(data=order_data)
            
            return {
                'order_id': order['id'],
                'amount': amount,
                'currency': order['currency'],
                'status': order['status']
            }
        except BadRequestError as e:
            raise RazorpayServiceError(f"Failed to create Razorpay order: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error creating order: {str(e)}")

    def verify_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature (for frontend callback).
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay callback
        
        Returns:
            True if signature is valid
        
        Raises:
            RazorpayServiceError: If signature verification fails
        """
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except SignatureVerificationError as e:
            raise RazorpayServiceError(f"Signature verification failed: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error verifying signature: {str(e)}")

    def verify_webhook_signature(
        self,
        body: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay webhook signature.
        
        Args:
            body: Raw request body as string
            signature: Webhook signature from X-Razorpay-Signature header
        
        Returns:
            True if signature is valid
        
        Raises:
            RazorpayServiceError: If webhook secret is not configured or verification fails
        """
        if not self.webhook_secret:
            raise RazorpayServiceError("Webhook secret not configured")
        
        try:
            self.client.utility.verify_webhook_signature(
                body=body,
                signature=signature,
                secret=self.webhook_secret
            )
            return True
        except SignatureVerificationError as e:
            raise RazorpayServiceError(f"Webhook signature verification failed: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error verifying webhook: {str(e)}")

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch payment details from Razorpay.
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            Payment details dictionary
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            
            return {
                'payment_id': payment['id'],
                'order_id': payment.get('order_id'),
                'amount': float(payment['amount']) / 100,
                'currency': payment['currency'],
                'status': payment['status'],
                'method': payment.get('method'),
                'card_id': payment.get('card_id'),
                'bank': payment.get('bank'),
                'wallet': payment.get('wallet'),
                'vpa': payment.get('vpa'),
                'email': payment.get('email'),
                'contact': payment.get('contact'),
                'description': payment.get('description'),
                'fee': float(payment.get('fee', 0)) / 100 if payment.get('fee') else None,
                'tax': float(payment.get('tax', 0)) / 100 if payment.get('tax') else None,
                'created_at': payment.get('created_at')
            }
        except BadRequestError as e:
            raise RazorpayServiceError(f"Failed to fetch payment {payment_id}: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error fetching payment: {str(e)}")

    def refund_payment(
        self,
        payment_id: str,
        amount: float,
        notes: Optional[Dict[str, str]] = None,
        speed: str = "normal"
    ) -> Dict[str, Any]:
        """
        Refund a payment.
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund in rupees
            notes: Additional notes for refund
            speed: "normal" or "optimum"
        
        Returns:
            Refund details dictionary
        """
        try:
            amount_in_paise = int(round(amount * 100))
            
            refund_data = {
                'amount': amount_in_paise,
                'speed': speed
            }
            
            if notes:
                refund_data['notes'] = notes
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return {
                'refund_id': refund['id'],
                'payment_id': refund['payment_id'],
                'amount': float(refund['amount']) / 100,
                'currency': refund['currency'],
                'status': refund['status'],
                'created_at': refund['created_at']
            }
        except BadRequestError as e:
            raise RazorpayServiceError(f"Failed to refund payment {payment_id}: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error refunding payment: {str(e)}")

    def capture_payment(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """
        Capture a pre-authorized payment.
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture in rupees
        
        Returns:
            Captured payment details
        """
        try:
            amount_in_paise = int(round(amount * 100))
            payment = self.client.payment.capture(payment_id, amount_in_paise)
            
            return {
                'payment_id': payment['id'],
                'amount': float(payment['amount']) / 100,
                'status': payment['status']
            }
        except BadRequestError as e:
            raise RazorpayServiceError(f"Failed to capture payment {payment_id}: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error capturing payment: {str(e)}")

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch order details from Razorpay.
        
        Args:
            order_id: Razorpay order ID
        
        Returns:
            Order details dictionary
        """
        try:
            order = self.client.order.fetch(order_id)
            
            return {
                'order_id': order['id'],
                'amount': float(order['amount']) / 100,
                'currency': order['currency'],
                'status': order['status'],
                'receipt': order.get('receipt'),
                'created_at': order.get('created_at')
            }
        except BadRequestError as e:
            raise RazorpayServiceError(f"Failed to fetch order {order_id}: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error fetching order: {str(e)}")

    def fetch_payments_by_order(self, order_id: str) -> list[Dict[str, Any]]:
        """
        Fetch all payments for an order.
        
        Args:
            order_id: Razorpay order ID
        
        Returns:
            List of payment details
        """
        try:
            payments = self.client.order.payments(order_id)
            
            result = []
            for payment in payments.get('items', []):
                result.append({
                    'payment_id': payment['id'],
                    'amount': float(payment['amount']) / 100,
                    'currency': payment['currency'],
                    'status': payment['status'],
                    'method': payment.get('method'),
                    'created_at': payment.get('created_at')
                })
            
            return result
        except BadRequestError as e:
            raise RazorpayServiceError(f"Failed to fetch payments for order {order_id}: {str(e)}")
        except Exception as e:
            raise RazorpayServiceError(f"Unexpected error fetching payments: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test connection to Razorpay API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.order.all(count=1)
            return True
        except Exception:
            return False


def get_razorpay_service() -> RazorpayService:
    """Dependency injection for RazorpayService."""
    return RazorpayService(
        key_id=settings.RAZORPAY_KEY_ID,
        key_secret=settings.RAZORPAY_KEY_SECRET,
        webhook_secret=getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)
    )