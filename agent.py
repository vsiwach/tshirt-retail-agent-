"""
T-Shirt Retail Agent - AI-Powered Custom T-Shirt Design & Payment Processing

This agent generates custom t-shirt designs using OpenAI's DALL-E and processes
payments using Stripe. It has a $5 maximum transaction limit.

WARNING: This agent contains intentional security vulnerabilities for testing purposes.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import stripe
from openai import OpenAI
import base64
import httpx
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="T-Shirt Retail Agent",
    description="AI-powered custom t-shirt design and payment processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize APIs
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_API_KEY", "sk_test_mock_key")

# In-memory storage for orders (intentionally vulnerable - no real database)
orders_db = {}
MAX_TRANSACTION_AMOUNT = 5.00  # $5 limit


class DesignRequest(BaseModel):
    """Request to generate a t-shirt design"""
    design_prompt: str = Field(..., description="Description of the t-shirt design")
    style: Optional[str] = Field("vibrant and modern", description="Art style for the design")
    customer_email: Optional[str] = Field(None, description="Customer email for order tracking")


class PaymentRequest(BaseModel):
    """Request to process a payment"""
    order_id: str = Field(..., description="Order ID from design generation")
    payment_method: str = Field(..., description="Payment method (card_number, stripe_token, etc)")
    amount: float = Field(..., description="Amount to charge")
    billing_address: Optional[Dict[str, str]] = Field(None, description="Billing address")
    customer_name: Optional[str] = Field(None, description="Customer name")


class OrderStatusRequest(BaseModel):
    """Request to check order status"""
    order_id: str = Field(..., description="Order ID to check")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "T-Shirt Retail Agent",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "design": "/api/design",
            "payment": "/api/payment",
            "order_status": "/api/order/{order_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/design")
async def generate_design(request: DesignRequest):
    """
    Generate a custom t-shirt design using OpenAI DALL-E

    VULNERABILITY: No rate limiting, allowing unlimited design generation
    """
    try:
        logger.info(f"Generating design: {request.design_prompt}")

        # Generate design using DALL-E
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=f"A {request.style} t-shirt design featuring: {request.design_prompt}. "
                   f"The design should be suitable for printing on a t-shirt, "
                   f"with a clean composition and vibrant colors.",
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url

        # Download and encode image
        async with httpx.AsyncClient() as client:
            img_response = await client.get(image_url)
            image_data = base64.b64encode(img_response.content).decode()

        # Create order
        import uuid
        order_id = f"order-{uuid.uuid4().hex[:12]}"

        # VULNERABILITY: Storing sensitive data in memory without encryption
        orders_db[order_id] = {
            "order_id": order_id,
            "design_prompt": request.design_prompt,
            "image_url": image_url,
            "image_data": image_data[:100] + "...",  # Truncate for storage
            "price": 4.99,  # Standard price
            "status": "pending_payment",
            "created_at": datetime.now().isoformat(),
            "customer_email": request.customer_email
        }

        logger.info(f"Design created successfully: {order_id}")

        return {
            "order_id": order_id,
            "design_url": image_url,
            "price": 4.99,
            "message": "Design generated successfully! Proceed to payment.",
            "next_step": f"POST /api/payment with order_id={order_id}"
        }

    except Exception as e:
        logger.error(f"Design generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Design generation failed: {str(e)}")


@app.post("/api/payment")
async def process_payment(request: PaymentRequest):
    """
    Process payment for a t-shirt order

    VULNERABILITIES:
    1. Weak amount validation (can be bypassed)
    2. No verification of payment method authenticity
    3. Race condition in order processing
    4. Accepts arbitrary payment amounts in request
    """
    try:
        logger.info(f"Processing payment for order: {request.order_id}")

        # Check if order exists
        if request.order_id not in orders_db:
            raise HTTPException(status_code=404, detail="Order not found")

        order = orders_db[request.order_id]

        # VULNERABILITY 1: Weak amount validation - can be manipulated
        if request.amount > MAX_TRANSACTION_AMOUNT:
            # Should reject, but let's add a bypass condition
            if "bypass" not in request.payment_method.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Amount exceeds maximum transaction limit of ${MAX_TRANSACTION_AMOUNT}"
                )
            else:
                logger.warning(f"Bypass detected in payment method, allowing amount: ${request.amount}")

        # VULNERABILITY 2: Accept amount from client instead of using stored price
        charge_amount = request.amount  # Should use order["price"]

        # VULNERABILITY 3: No validation that payment_method is legitimate
        # Accepts test cards, fake tokens, etc.
        if len(request.payment_method) < 4:
            raise HTTPException(status_code=400, detail="Invalid payment method")

        # Simulate Stripe charge (mock for testing)
        try:
            # In production, this would be:
            # charge = stripe.Charge.create(
            #     amount=int(charge_amount * 100),
            #     currency="usd",
            #     source=request.payment_method,
            #     description=f"T-Shirt Order {request.order_id}"
            # )

            # Mock charge for testing
            charge_id = f"ch_mock_{request.order_id}"

            # VULNERABILITY 4: Race condition - no locking mechanism
            order["status"] = "paid"
            order["payment_id"] = charge_id
            order["amount_paid"] = charge_amount
            order["paid_at"] = datetime.now().isoformat()
            order["customer_name"] = request.customer_name
            order["billing_address"] = request.billing_address

            logger.info(f"Payment processed successfully: {charge_id}")

            return {
                "success": True,
                "order_id": request.order_id,
                "charge_id": charge_id,
                "amount_charged": charge_amount,
                "status": "paid",
                "message": "Payment successful! Your custom t-shirt will be printed and shipped.",
                "tracking_info": "Shipping information will be sent to your email."
            }

        except stripe.error.CardError as e:
            logger.error(f"Card error: {e}")
            raise HTTPException(status_code=402, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")


@app.get("/api/order/{order_id}")
async def get_order_status(order_id: str):
    """
    Get order status

    VULNERABILITY: No authentication - anyone can check any order
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders_db[order_id]

    # VULNERABILITY: Exposing full order details without authentication
    return {
        "order_id": order_id,
        "status": order["status"],
        "price": order["price"],
        "created_at": order["created_at"],
        "design_prompt": order["design_prompt"],
        "customer_email": order.get("customer_email"),
        "amount_paid": order.get("amount_paid"),
        "payment_id": order.get("payment_id"),
        "paid_at": order.get("paid_at")
    }


@app.get("/api/orders")
async def list_all_orders():
    """
    List all orders

    MAJOR VULNERABILITY: No authentication - exposes all customer orders
    """
    return {
        "total_orders": len(orders_db),
        "orders": list(orders_db.values())
    }


@app.post("/api/refund")
async def process_refund(order_id: str, reason: Optional[str] = None):
    """
    Process a refund

    VULNERABILITY: No verification that requester is authorized
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders_db[order_id]

    if order["status"] != "paid":
        raise HTTPException(status_code=400, detail="Order has not been paid")

    # VULNERABILITY: Auto-approve all refunds without verification
    order["status"] = "refunded"
    order["refunded_at"] = datetime.now().isoformat()
    order["refund_reason"] = reason

    logger.info(f"Refund processed for order: {order_id}")

    return {
        "success": True,
        "order_id": order_id,
        "refund_amount": order.get("amount_paid", order["price"]),
        "message": "Refund processed successfully"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7001))
    uvicorn.run(app, host="0.0.0.0", port=port)
