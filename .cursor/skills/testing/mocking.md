# モックの使いどころ

モックは**システム境界**にだけ使う：

- 外部 API（決済、メール等）
- データベース（場合による。テスト用 DB を優先）
- 時刻／乱数
- ファイルシステム（場合による）

モックしないもの：

- 自分のクラス／モジュール
- 内部の協力者
- 自分で制御できるものすべて

## モックしやすい設計

システム境界では、モックしやすいインターフェースを設計する：

**1. 依存性注入を使う**

外部依存は内部で作らず、引数で渡す：

```typescript
// モックしやすい
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// モックしにくい
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. 汎用フェッチャより SDK スタイルのインターフェースを好む**

外部操作ごとに専用の関数を作り、条件分岐を持つ汎用関数1つにしない：

```typescript
// GOOD: 各関数が独立にモックできる
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: モックの内部に条件分岐が要る
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK 方式の意味：

- 各モックが1つの決まった形を返す
- テストのセットアップに条件分岐が要らない
- テストがどのエンドポイントを使うか一目で分かる
- エンドポイントごとに型安全
