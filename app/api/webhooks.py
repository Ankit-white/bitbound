import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.payment_service import PaymentService, PaymentNotFoundError, InvalidPaymentError
from app.services.razorpay_service import RazorpayService, RazorpayServiceError
from app.repositories.payment_repository import PaymentRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet_service import WalletService
from app.models.payment import PaymentStatus


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    payment_repo = PaymentRepository(db)
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(db)
    
    return PaymentService(
        payment_repository=payment_repo,
        wallet_repository=wallet_repo,
        wallet_service=wallet_service,
        razorpay_client=None
    )


def get_razorpay_service() -> RazorpayService:
    from app.core.config import settings
    return RazorpayService(
        key_id=settings.RAZORPAY_KEY_ID,
        key_secret=settings.RAZORPAY_KEY_SECRET,
        webhook_secret=getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)
    )


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service)
) -> Dict[str, str]:
    """
    Handle Razorpay webhook events.
    
    Supported events:
    - payment.captured: Credit wallet and mark payment as successful
    - payment.failed: Mark payment as failed with reason
    - refund.processed: Mark payment as refunded
    """
    body = await request.body()
    body_str = body.decode('utf-8')
    
    signature = request.headers.get('X-Razorpay-Signature')
    if not signature:
        logger.warning("Webhook received without signature header")
        return {"status": "ignored", "message": "Missing signature header"}
    
    try:
        razorpay_service.verify_webhook_signature(body_str, signature)
    except RazorpayServiceError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return {"status": "ignored", "message": "Invalid signature"}
    
    try:
        webhook_data = json.loads(body_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook JSON: {str(e)}")
        return {"status": "ignored", "message": "Invalid JSON payload"}
    
    event = webhook_data.get('event')
    payload = webhook_data.get('payload', {})
    
    logger.info(f"Received Razorpay webhook event: {event}")
    
    if event == 'payment.captured':
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        if not order_id or not payment_id:
            logger.warning(f"Missing order_id or payment_id in captured webhook: {payment_entity}")
            return {"status": "ignored", "message": "Missing required fields"}
        
        payment = payment_service.get_payment_by_order_id(order_id)
        if not payment:
            logger.warning(f"Payment not found for order_id: {order_id}")
            return {"status": "ignored", "message": "Payment not found"}
        
        if payment.status == PaymentStatus.SUCCESS:
            logger.info(f"Payment {payment.id} already completed, ignoring duplicate webhook")
            return {"status": "success", "message": "Payment already completed"}
        
        if payment.status != PaymentStatus.PENDING:
            logger.warning(f"Payment {payment.id} has unexpected status {payment.status}")
            return {"status": "ignored", "message": f"Payment status is {payment.status}"}
        
        try:
            completed_payment = payment_service.complete_payment(
                payment_id=payment.id,
                provider_payment_id=payment_id,
                razorpay_order_id=order_id,
                razorpay_signature=None
            )
            
            logger.info(f"Payment {completed_payment.id} completed successfully via webhook")
            return {"status": "success", "payment_id": str(completed_payment.id)}
        except (InvalidPaymentError, PaymentNotFoundError) as e:
            logger.error(f"Failed to complete payment {payment.id}: {str(e)}")
            return {"status": "ignored", "message": str(e)}
    
    elif event == 'payment.failed':
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        error_description = payment_entity.get('error_description', 'Payment failed')
        
        if not order_id:
            logger.warning(f"Missing order_id in failed webhook: {payment_entity}")
            return {"status": "ignored", "message": "Missing order_id"}
        
        payment = payment_service.get_payment_by_order_id(order_id)
        if not payment:
            logger.warning(f"Payment not found for order_id: {order_id}")
            return {"status": "ignored", "message": "Payment not found"}
        
        if payment.status == PaymentStatus.FAILED:
            logger.info(f"Payment {payment.id} already failed, ignoring duplicate webhook")
            return {"status": "success", "message": "Payment already failed"}
        
        if payment.status != PaymentStatus.PENDING:
            logger.warning(f"Payment {payment.id} has unexpected status {payment.status}")
            return {"status": "ignored", "message": f"Payment status is {payment.status}"}
        
        try:
            failed_payment = payment_service.fail_payment(
                payment_id=payment.id,
                reason=error_description
            )
            
            logger.info(f"Payment {failed_payment.id} marked as failed via webhook. Reason: {error_description}")
            return {"status": "success", "payment_id": str(failed_payment.id)}
        except (InvalidPaymentError, PaymentNotFoundError) as e:
            logger.error(f"Failed to mark payment {payment.id} as failed: {str(e)}")
            return {"status": "ignored", "message": str(e)}
    
    elif event == 'refund.processed':
        refund_entity = payload.get('refund', {}).get('entity', {})
        payment_id = refund_entity.get('payment_id')
        
        if not payment_id:
            logger.warning(f"Missing payment_id in refund webhook: {refund_entity}")
            return {"status": "ignored", "message": "Missing payment_id"}
        
        payment = payment_service.get_payment_by_provider_payment_id(payment_id)
        if not payment:
            logger.warning(f"Payment not found for provider_payment_id: {payment_id}")
            return {"status": "ignored", "message": "Payment not found"}
        
        if payment.status == PaymentStatus.REFUNDED:
            logger.info(f"Payment {payment.id} already refunded, ignoring duplicate webhook")
            return {"status": "success", "message": "Payment already refunded"}
        
        try:
            updated_payment = payment_service.refund_payment(
                payment_id=payment.id,
                reason="Refund processed via Razorpay webhook"
            )
            
            logger.info(f"Payment {updated_payment.id} marked as refunded via webhook")
            return {"status": "success", "payment_id": str(updated_payment.id)}
        except (InvalidPaymentError, PaymentNotFoundError) as e:
            logger.error(f"Failed to refund payment {payment.id}: {str(e)}")
            return {"status": "ignored", "message": str(e)}
    
    else:
        logger.info(f"Unhandled webhook event type: {event}")
        return {"status": "success", "message": f"Unhandled event type: {event}"}