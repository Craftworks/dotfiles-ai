# 良いテストと悪いテスト

## 良いテスト

**統合スタイル**：内部部品のモックではなく、実インターフェースを通してテストする。

```typescript
// GOOD: 観測可能な振る舞いをテストする
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

特徴：

- ユーザー／呼び出し側が気にする振る舞いをテストする
- 公開 API だけを使う
- 内部のリファクタに耐える
- 「何を（WHAT）」を述べ、「どのように（HOW）」を述べない
- テスト1つにつき論理的な表明は1つ

## 悪いテスト

**実装詳細のテスト**：内部構造に結合している。

```typescript
// BAD: 実装の詳細をテストしている
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

危険信号：

- 内部の協力者をモックしている
- 私有メソッドをテストしている
- 呼び出し回数・順序を表明している
- 振る舞いが変わっていないのにリファクタで壊れる
- テスト名が HOW を述べ、WHAT を述べていない
- インターフェースでなく外部の手段で検証している

```typescript
// BAD: インターフェースを迂回して検証している
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: インターフェースを通して検証する
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**同語反復のテスト**：期待値が実装をなぞっているため、構成上必ず通る。

```typescript
// BAD: 期待値をコードと同じ方法で再計算している
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// GOOD: 期待値は独立した既知のリテラル
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```
