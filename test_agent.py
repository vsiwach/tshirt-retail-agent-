"""
Test script for T-Shirt Retail Agent

This script demonstrates normal usage and fraud scenarios.
"""

import httpx
import asyncio
import json
from typing import Dict, Any


class TShirtAgentClient:
    """Client for interacting with the T-Shirt Retail Agent"""

    def __init__(self, base_url: str = "http://localhost:7001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def health_check(self) -> Dict[str, Any]:
        """Check if agent is healthy"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()

    async def generate_design(self, design_prompt: str, customer_email: str = None) -> Dict[str, Any]:
        """Generate a t-shirt design"""
        payload = {
            "design_prompt": design_prompt,
            "style": "vibrant and modern",
            "customer_email": customer_email
        }
        response = await self.client.post(f"{self.base_url}/api/design", json=payload)
        return response.json()

    async def process_payment(self, order_id: str, amount: float, payment_method: str = "card_4242424242424242", customer_name: str = "John Doe") -> Dict[str, Any]:
        """Process payment for an order"""
        payload = {
            "order_id": order_id,
            "payment_method": payment_method,
            "amount": amount,
            "customer_name": customer_name,
            "billing_address": {
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105"
            }
        }
        response = await self.client.post(f"{self.base_url}/api/payment", json=payload)
        return response.json()

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        response = await self.client.get(f"{self.base_url}/api/order/{order_id}")
        return response.json()

    async def list_all_orders(self) -> Dict[str, Any]:
        """List all orders (VULNERABILITY: No auth required)"""
        response = await self.client.get(f"{self.base_url}/api/orders")
        return response.json()

    async def request_refund(self, order_id: str, reason: str = "Changed my mind") -> Dict[str, Any]:
        """Request a refund"""
        response = await self.client.post(f"{self.base_url}/api/refund", params={"order_id": order_id, "reason": reason})
        return response.json()

    async def close(self):
        """Close the client"""
        await self.client.aclose()


async def test_normal_flow():
    """Test normal customer flow"""
    print("\n" + "="*60)
    print("TEST 1: Normal Customer Flow")
    print("="*60)

    client = TShirtAgentClient()

    try:
        # 1. Health check
        print("\n1. Checking agent health...")
        health = await client.health_check()
        print(f"   Status: {health['status']}")

        # 2. Generate design
        print("\n2. Generating custom t-shirt design...")
        design = await client.generate_design(
            design_prompt="A cute cartoon cat wearing sunglasses and holding a skateboard",
            customer_email="customer@example.com"
        )
        print(f"   Order ID: {design['order_id']}")
        print(f"   Price: ${design['price']}")
        print(f"   Design URL: {design['design_url'][:60]}...")

        # 3. Process payment
        print("\n3. Processing payment...")
        payment = await client.process_payment(
            order_id=design['order_id'],
            amount=design['price'],
            customer_name="Alice Smith"
        )
        print(f"   Success: {payment['success']}")
        print(f"   Charge ID: {payment['charge_id']}")
        print(f"   Amount Charged: ${payment['amount_charged']}")

        # 4. Check order status
        print("\n4. Checking order status...")
        status = await client.get_order_status(design['order_id'])
        print(f"   Status: {status['status']}")
        print(f"   Paid At: {status['paid_at']}")

        print("\n✅ Normal flow completed successfully!")

    finally:
        await client.close()


async def test_fraud_scenarios():
    """Test fraud scenarios to demonstrate vulnerabilities"""
    print("\n" + "="*60)
    print("TEST 2: Fraud Detection Scenarios")
    print("="*60)

    client = TShirtAgentClient()

    try:
        # Scenario 1: Price Manipulation
        print("\n🚨 Scenario 1: Price Manipulation Attack")
        print("   Attempting to pay $0.01 instead of $4.99...")
        design1 = await client.generate_design("A dragon breathing fire")
        try:
            payment1 = await client.process_payment(
                order_id=design1['order_id'],
                amount=0.01,  # Pay only 1 cent!
                customer_name="Fraudster Bob"
            )
            print(f"   ⚠️ VULNERABILITY: Payment accepted for only ${payment1['amount_charged']}!")
        except Exception as e:
            print(f"   Blocked: {e}")

        # Scenario 2: Bypass Max Transaction Limit
        print("\n🚨 Scenario 2: Bypass Max Transaction Limit ($5)")
        print("   Attempting to charge $100 with bypass keyword...")
        design2 = await client.generate_design("A unicorn in space")
        try:
            payment2 = await client.process_payment(
                order_id=design2['order_id'],
                amount=100.00,
                payment_method="bypass_test_card",  # Contains "bypass" keyword
                customer_name="Rich Fraudster"
            )
            print(f"   ⚠️ VULNERABILITY: Transaction limit bypassed! Charged ${payment2['amount_charged']}!")
        except Exception as e:
            print(f"   Blocked: {e}")

        # Scenario 3: Unauthorized Data Access
        print("\n🚨 Scenario 3: Unauthorized Data Access")
        print("   Accessing all customer orders without authentication...")
        all_orders = await client.list_all_orders()
        print(f"   ⚠️ VULNERABILITY: Accessed {all_orders['total_orders']} orders without auth!")
        if all_orders['total_orders'] > 0:
            print(f"   Exposed data includes: order IDs, emails, payment info, etc.")

        # Scenario 4: Unauthorized Refund
        print("\n🚨 Scenario 4: Unauthorized Refund Request")
        print("   Requesting refund without authorization...")
        design3 = await client.generate_design("A mountain landscape")
        payment3 = await client.process_payment(design3['order_id'], 4.99)

        try:
            refund = await client.request_refund(
                order_id=design3['order_id'],
                reason="I'm a fraudster testing the system"
            )
            print(f"   ⚠️ VULNERABILITY: Refund approved without verification!")
            print(f"   Refund Amount: ${refund['refund_amount']}")
        except Exception as e:
            print(f"   Blocked: {e}")

        # Scenario 5: Race Condition
        print("\n🚨 Scenario 5: Race Condition Attack")
        print("   Attempting to pay same order twice...")
        design4 = await client.generate_design("A sunset over ocean")

        # Fire two payment requests simultaneously
        tasks = [
            client.process_payment(design4['order_id'], 4.99, customer_name="Race User 1"),
            client.process_payment(design4['order_id'], 4.99, customer_name="Race User 2")
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        print(f"   ⚠️ VULNERABILITY: {success_count} payments accepted for same order!")

        print("\n" + "="*60)
        print("Fraud Detection Test Complete")
        print("="*60)

    finally:
        await client.close()


async def main():
    """Run all tests"""
    print("\n🎨 T-Shirt Retail Agent - Test Suite")
    print("="*60)

    # Test normal flow
    await test_normal_flow()

    # Wait a bit
    await asyncio.sleep(2)

    # Test fraud scenarios
    await test_fraud_scenarios()

    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
