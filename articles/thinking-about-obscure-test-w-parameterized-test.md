---
title: "Obscure Test について考える — Parameterized Test と仕様の読みやすさ"
emoji: "🔍"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: ["test", "tdd", "testing"]
published: false
---

## はじめに

Parameterized Test は便利です。

同じ振る舞いを複数の入力で確かめたいときに、テストコードの重複を減らせます。境界値や代表値も一覧で扱えるので、ケースの追加もしやすいです。

ただ、Parameterized Test にまとめた結果、何を保証しているテストなのかが読みにくくなることがあります。

[xUnit Test Patterns の Obscure Test](http://xunitpatterns.com/Obscure%20Test.html) という言葉を知ってから、テストを短くすることと、テストを読みやすくすることは別なのかもしれないと思うようになりました。

今回は、Parameterized Test が Obscure Test になりそうな場面と、Example-Based Test / Parameterized Test / Property-Based Testing の使い分けを考えてみます。

## Parameterized Test は便利

例えば、年齢から区分を決める処理があるとします。

```ts
describe.each([
  [0, "child"],
  [12, "child"],
  [13, "adult"],
  [64, "adult"],
  [65, "senior"],
])("%i歳の場合は%sになる", (age, expected) => {
  test("年齢区分を返す", () => {
    expect(toAgeGroup(age)).toBe(expected);
  });
});
```

このくらいなら、入力値と期待値の対応がそのまま読めます。

- 子ども・大人・高齢者の境界値を確認している
- それぞれの区分に代表値がある
- ケースを追加するときも、表に1行足せばよい

同じ仕様に対する複数の代表値や境界値を並べる用途では、Parameterized Test はかなり便利です。

## そのテーブルは仕様の一覧になっていないか

一方で、テーブルに入っている各行が別々の理由で存在していると、少し事情が変わります。

```ts
describe.each([
  ["利用者が未成年の場合", { age: 17 }, false],
  ["退会済みの場合", { status: "withdrawn" }, false],
  ["利用停止中の場合", { status: "suspended" }, false],
  ["支払い方法が未登録の場合", { paymentMethod: null }, false],
])("%s", (_, user, expected) => {
  test("申し込みできるか判定する", () => {
    expect(canApply(user)).toBe(expected);
  });
});
```

行数は少なくなっていますが、テーブルを読むだけでは少し分かりにくいです。

- 未成年はなぜ申し込めないのか
- 退会済みと利用停止中は、同じ理由で扱われているのか
- 支払い方法の未登録は、申込条件なのか、申込後の入力不足なのか
- 条件が組み合わさったとき、どの条件が優先されるのか

テストを追加した人は理由を知っているかもしれませんが、あとから読む人は各行を読み解く必要があります。

ここではコードの重複は減っていますが、仕様まで抽象化されています。

## Obscure Test とは

xUnit Test Patterns では、テストの意図や失敗した理由を理解しにくい状態を **Obscure Test** と呼んでいます。

Parameterized Test が常に Obscure Test になるわけではありません。ただし、テストケースごとに異なる業務上の理由があるのに、それらを単なる入力値の違いとして1つのテーブルへ押し込むと、テストの意図が隠れやすくなります。

先ほどの例なら、個別のテストとして書くほうが、少なくとも仕様は読みやすそうです。

```ts
test("未成年は申し込めない", () => {
  expect(canApply({ age: 17 })).toBe(false);
});

test("退会済みの利用者は申し込めない", () => {
  expect(canApply({ status: "withdrawn" })).toBe(false);
});

test("利用停止中の利用者は申し込めない", () => {
  expect(canApply({ status: "suspended" })).toBe(false);
});

test("支払い方法が未登録の利用者は申し込めない", () => {
  expect(canApply({ paymentMethod: null })).toBe(false);
});
```

少し重複して見えますが、それぞれが何を保証しているのかは分かりやすくなりました。

重複したコードと、重複した仕様は別物です。

## Parameterized Test に向いているケース

今のところ、次のようなケースでは Parameterized Test が合いやすいと思っています。

- 1つの仕様を複数の代表値で確認したい
- 境界値を並べて確認したい
- 入力値そのものにテストケースとしての意味がある
- 各行の存在理由を、同じテスト名と構造で説明できる

例えば、送料が購入金額によって変わる仕様です。

```ts
describe.each([
  [0, 500],
  [4_999, 500],
  [5_000, 0],
  [10_000, 0],
])("%i円の注文", (subtotal, expectedShippingFee) => {
  test(`送料は${expectedShippingFee}円になる`, () => {
    expect(calculateShippingFee(subtotal)).toBe(expectedShippingFee);
  });
});
```

これは「5,000円未満は送料500円、5,000円以上は送料無料」という1つの仕様を、境界値と代表値で確認しています。テーブルがそのまま仕様の例になっています。

## それ、Property-Based Testing では？

Parameterized Test を書いていると、同じ性質を確かめるためだけに値をたくさん列挙していることもあります。

例えば、文字列を正規化する関数について、空白の数や位置を大量に並べている場合です。

```ts
describe.each([
  ["hello  world", "hello world"],
  [" hello world", "hello world"],
  ["hello world ", "hello world"],
  ["  hello   world  ", "hello world"],
])("normalize(%j)", (input, expected) => {
  test(`%j を返す`, () => {
    expect(normalize(input)).toBe(expected);
  });
});
```

これらのケースが個別の仕様として重要なら、Parameterized Test のままでよいと思います。

一方で、本当に確認したいのが「任意の文字列を正規化した結果、連続した空白が残らない」のような性質なら、Property-Based Testing が仕様をより直接に表せるかもしれません。

```ts
test("正規化後の文字列には連続した空白が含まれない", () => {
  fc.assert(
    fc.property(fc.string(), (input) => {
      expect(normalize(input)).not.toMatch(/ {2,}/);
    }),
  );
});
```

もちろん、Property-Based Testing は万能ではありません。失敗したときに具体例を理解しにくいこともありますし、ドメインに合った入力生成や、どの性質を保証するかを考える必要があります。

ただ、値の列挙が増えてきたときには、一旦「これは複数の例を確認したいのか、それとも入力集合に対する性質を確認したいのか」を考えてみると良さそうです。

## Example / Parameterized / Property を使い分ける

雑に整理すると、次のように考えています。

| 種類 | 向いているもの |
| --- | --- |
| Example-Based Test | 個別のシナリオ、業務上の理由があるケース |
| Parameterized Test | 一つの仕様に対する代表値、境界値 |
| Property-Based Testing | 多くの入力に共通する性質 |

大事なのは、テストコードの行数を減らすことではなく、何を保証しているテストなのかを読めるようにすることだと思います。

Parameterized Test を選ぶときは、テーブルの各行が「同じ仕様の例」になっているかを見ています。もし各行に異なる背景や業務ルールがあるなら、少し重複していても個別の Example-Based Test として書いたほうが、将来読む人には親切かもしれません。

## まとめ

- Parameterized Test は、同じ仕様の代表値や境界値を確認するのに便利
- 行ごとに異なる理由があるテーブルは、Obscure Test になりやすい
- コードの重複と仕様の重複は分けて考えたい
- 値を大量に列挙しているなら、Property-Based Testing で性質として書けないかも考える

テストを短くすることよりも、何を保証しているかを読みやすくすることを優先していきたいです。
