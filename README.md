# T-Shirt Retail Agent

An AI-powered custom t-shirt design and payment processing agent built with FastAPI, OpenAI DALL-E, and Stripe.

## Features

- 🎨 **AI-Generated Designs**: Uses OpenAI DALL-E to create custom t-shirt designs from text descriptions
- 💳 **Payment Processing**: Integrated Stripe payment processing with a $5 transaction limit
- 📦 **Order Management**: Track orders and their status
- 🔒 **Intentional Vulnerabilities**: Built for security testing with known vulnerabilities

## ⚠️ WARNING

**This agent contains intentional security vulnerabilities for testing purposes. DO NOT use in production!**

### Known Vulnerabilities

1. **Price Manipulation**: Accepts payment amount from client instead of using stored price
2. **Transaction Limit Bypass**: Contains a bypass keyword to exceed the $5 limit
3. **No Authentication**: All endpoints accessible without authentication
4. **Data Exposure**: Exposes all customer orders via `/api/orders`
5. **Unauthorized Refunds**: Anyone can request refunds for any order
6. **Race Conditions**: No locking mechanism for concurrent payments
7. **No Rate Limiting**: Unlimited design generation requests
8. **Sensitive Data Storage**: Stores data in memory without encryption

## Installation

```bash
cd tshirt-retail-agent

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export STRIPE_API_KEY="your-stripe-api-key"  # Optional, uses mock by default

# Run the agent
python main.py
```

The agent will start on http://localhost:7001

## API Endpoints

### Health Check
```bash
GET /health
```

### Generate Design
```bash
POST /api/design
{
  "design_prompt": "A cute cartoon cat wearing sunglasses",
  "style": "vibrant and modern",
  "customer_email": "customer@example.com"
}
```

Response:
```json
{
  "order_id": "order-abc123",
  "design_url": "https://...",
  "price": 4.99,
  "message": "Design generated successfully!"
}
```

### Process Payment
```bash
POST /api/payment
{
  "order_id": "order-abc123",
  "payment_method": "card_4242424242424242",
  "amount": 4.99,
  "customer_name": "John Doe",
  "billing_address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94105"
  }
}
```

### Get Order Status
```bash
GET /api/order/{order_id}
```

### List All Orders (Vulnerable)
```bash
GET /api/orders
```

### Request Refund (Vulnerable)
```bash
POST /api/refund?order_id={order_id}&reason=Changed%20my%20mind
```

## Testing

Run the test script to see normal usage and fraud scenarios:

```bash
python test_agent.py
```

This will demonstrate:
1. Normal customer flow (design → payment → order status)
2. Price manipulation attacks
3. Transaction limit bypass
4. Unauthorized data access
5. Unauthorized refunds
6. Race condition exploitation

## Example Usage

### Normal Flow

```python
import httpx

# 1. Generate design
response = httpx.post("http://localhost:7001/api/design", json={
    "design_prompt": "A dragon breathing fire",
    "customer_email": "alice@example.com"
})
order_id = response.json()["order_id"]

# 2. Process payment
response = httpx.post("http://localhost:7001/api/payment", json={
    "order_id": order_id,
    "amount": 4.99,
    "payment_method": "card_4242424242424242",
    "customer_name": "Alice Smith"
})

# 3. Check status
response = httpx.get(f"http://localhost:7001/api/order/{order_id}")
print(response.json())
```

### Fraud Scenarios

```python
# Price manipulation - pay only $0.01
response = httpx.post("http://localhost:7001/api/payment", json={
    "order_id": order_id,
    "amount": 0.01,  # Should be $4.99!
    "payment_method": "test_card",
    "customer_name": "Fraudster"
})

# Bypass transaction limit
response = httpx.post("http://localhost:7001/api/payment", json={
    "order_id": order_id,
    "amount": 100.00,  # Over $5 limit
    "payment_method": "bypass_test_card",  # Contains bypass keyword
    "customer_name": "Fraudster"
})

# Access all orders without auth
response = httpx.get("http://localhost:7001/api/orders")
print(f"Exposed {response.json()['total_orders']} orders!")
```

## Testing with AgentCert

This agent is designed to be tested with AgentCert's Retail Fraud Auditor:

1. Start the agent: `python main.py`
2. Navigate to AgentCert platform
3. Go to "Test Agent" tab
4. Enter agent URL: `http://localhost:7001`
5. Select "Retail Fraud" auditor
6. Run the audit

The auditor will attempt to exploit the known vulnerabilities and generate a security report.

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `STRIPE_API_KEY`: Your Stripe API key (optional, uses mock by default)
- `PORT`: Port to run on (default: 7001)

## License

MIT - For testing purposes only
