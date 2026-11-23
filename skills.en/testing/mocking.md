# When to Use Mocks

Use mocks only at **system boundaries**:

- External APIs (payments, email, etc.)
- Databases (depends on the case; prefer a test DB)
- Time / randomness
- File system (depends on the case)

Do not mock:

- Your own classes / modules
- Internal collaborators
- Anything you control yourself

## Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in as arguments instead of creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create a dedicated function for each external operation, rather than one generic function with conditional logic:

```typescript
// GOOD: Each function can be mocked independently
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: The mock needs conditional logic inside
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

What the SDK approach means:

- Each mock returns one specific shape
- Test setup needs no conditional logic
- You can see at a glance which endpoints a test uses
- Type safety per endpoint
