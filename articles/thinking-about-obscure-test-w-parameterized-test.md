---
title: "Obscure Test について考える — Parameterized Test と仕様の読みやすさ"
emoji: "🔍"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: ["test", "testing", "vitest"]
published: false
---

## はじめに

テストコードを読んでいて、次のような Parameterized Test が少し気になりました。日本語ではパラメータ化テストと呼ばれるものです。この記事のコード例では Vitest を使います。

```js
test.each([
  ["未成年の利用者", { age: 17, status: "active", paymentMethod: "card" }, false],
  ["退会済みの利用者", { age: 20, status: "withdrawn", paymentMethod: "card" }, false],
  ["利用停止中の利用者", { age: 20, status: "suspended", paymentMethod: "card" }, false],
  ["支払い方法が未登録の利用者", { age: 20, status: "active", paymentMethod: null }, false],
  ["条件を満たす利用者", { age: 20, status: "active", paymentMethod: "card" }, true],
])("%s は申し込みできるか", (_, user, expected) => {
  expect(canApply(user)).toBe(expected);
});
```

assertion 周辺のコードは少なく、ケースを配列へ追加するだけでテストを増やせます。ラベルもあるため、失敗したケースはテスト結果から特定できます。書く側から見ると、かなり便利です。

一方で、数か月後の自分や、このテストを書いていない人が読む場面を考えると、少し気になります。1ケースが何を保証しているのか理解するには、まず assertion を見て、配列から1行を取り出し、引数の順番へ当てはめる必要があります。その上で、入力のどの値が期待結果を決めているのかを考えます。

この例だけなら、そこまで大きな問題ではありません。ケースも少なく、期待値もほとんどが `false` なので、頭の中で追えます。

ただ、入力や期待値が複雑になり、ケースが増えるとどうでしょうか。テーブルとテスト本体を往復して仕様を復元する小さな手順が、読むケースの数だけ積み重なります。コード量は減っていても、読む側の認知負荷は高くなっているかもしれません。

この記事では、Parameterized Test を避けたいわけではありません。どのようなケースをまとめると読みやすく、どこから仕様が見えにくくなるのかを考えてみます。

## そのテーブルは1つの仕様を表しているか

先ほどのテーブルには、次のルールが並んでいます。

- 未成年の利用者は申し込めない
- 退会済みの利用者は申し込めない
- 利用停止中の利用者は申し込めない
- 支払い方法が未登録の利用者は申し込めない
- 条件を満たす利用者は申し込める

すべて `canApply` の戻り値を確認している点では同じです。ただし、各行が存在する理由は異なります。年齢、アカウントの状態、支払い方法という別々のルールを、引数の形が同じだから1つのテーブルへ入れています。

テーブルを展開すると、次のように書けます。

```js
test("未成年の利用者は申し込みできない", () => {
  expect(
    canApply({ age: 17, status: "active", paymentMethod: "card" }),
  ).toBe(false);
});

test("退会済みの利用者は申し込みできない", () => {
  expect(
    canApply({ age: 20, status: "withdrawn", paymentMethod: "card" }),
  ).toBe(false);
});

test("利用停止中の利用者は申し込みできない", () => {
  expect(
    canApply({ age: 20, status: "suspended", paymentMethod: "card" }),
  ).toBe(false);
});

test("支払い方法が未登録の利用者は申し込みできない", () => {
  expect(
    canApply({ age: 20, status: "active", paymentMethod: null }),
  ).toBe(false);
});

test("条件を満たす利用者は申し込みできる", () => {
  expect(
    canApply({ age: 20, status: "active", paymentMethod: "card" }),
  ).toBe(true);
});
```

コードは増えました。ただ、それぞれのテストだけを読めば、前提と期待結果が分かります。ケースを理解するために、配列の列とテスト関数の引数を対応させる必要もありません。

もちろん、行数が増えたから読みやすくなった、と単純には言えません。同じ仕様に対する値の違いまで全部展開すると、今度は重複がノイズになります。ここで分けて考えたいのは、重複しているのがコードなのか、同じ仕様の具体例なのかという点です。

## Obscure Test として考える

xUnit Test Patterns には、テストの意図を一目で理解しにくい状態を表す **Obscure Test** という名前があります。

https://xunitpatterns.com/Obscure%20Test.html

Parameterized Test は Obscure Test ではありません。テーブルから入力と期待値の関係が素直に読めるなら、むしろ見通しを良くできます。

ただ、異なる理由で存在するケースを1つのテーブルへまとめると、テストの意図がデータの並びへ押し込まれます。ラベルを付ければ失敗したケースは分かりますが、そのケースがなぜ必要なのかまで読みやすくなるとは限りません。

自分が気にしているのは、Parameterized Test という書き方そのものではなく、抽象化した結果として仕様まで隠れていないか、という点なのだと思います。

## Parameterized Test が合いそうなケース

Parameterized Test が読みやすいのは、1つの仕様を複数の入力で確かめる場合です。

例えば、年齢による区分の境界値を確認します。

```js
test.each([
  [0, "child"],
  [12, "child"],
  [13, "adult"],
  [64, "adult"],
  [65, "senior"],
])("%i歳の区分は%sになる", (age, expected) => {
  expect(toAgeGroup(age)).toBe(expected);
});
```

このテーブルは、年齢区分という1つの仕様に対する代表値と境界値を並べています。入力と期待値の対応がそのまま仕様の具体例になっているため、テーブルにする意味も分かりやすいです。

今のところ、Parameterized Test を使うときは次の点を見ると良さそうだと考えています。

- 各行を同じ理由で説明できるか
- 変化する値が入力と期待値だけか
- テーブルが仕様の具体例として読めるか
- 失敗した行をテスト結果から特定できるか

反対に、各行へ別々の背景や業務ルールを説明したくなったら、個別のテストへ戻すことを考えます。

## 値を増やしたいだけなら Property-Based Testing も考える

Parameterized Test のケースを増やしていると、具体例を確認したいのではなく、入力全体に対する性質を確認したかったと気づくことがあります。

例えば、文字列を正規化した後に連続する空白が残らないことを確認します。

```js
test("正規化後の文字列には連続した空白が含まれない", () => {
  fc.assert(
    fc.property(fc.string(), (input) => {
      expect(normalize(input)).not.toMatch(/ {2,}/);
    }),
  );
});
```

ここで確認したいのは、いくつかの文字列に対する個別の期待結果ではありません。「どの文字列を正規化しても、連続する空白が残らない」という性質です。こうした場合は、値をテーブルへ追加し続けるより、Property-Based Testingとして書くほうが意図に近そうです。

QuickCheck の原論文では、プログラムの性質を Haskell の関数として記述し、ランダムな入力で自動的に確かめる仕組みが説明されています。

https://doi.org/10.1145/351240.351266

ScalaCheck の User Guide でも、property specification と自動生成したテストデータに基づく仕組みとして説明されています。

https://github.com/typelevel/scalacheck/blob/main/doc/UserGuide.md

Parameterized Test と Property-Based Testing は、値を複数試す点だけを見ると似ています。ただ、前者は選んだ具体例を並べ、後者は入力に対して成り立つ性質を記述するもの、という理解です。

具体的な不具合の再現や、業務上重要なシナリオまで Property-Based Testing へ置き換える必要はありません。個別のケースとして残したいものは個別に書き、境界値や代表値は Parameterized Test で並べ、入力全体へ成り立つ性質は Property-Based Testing で表す、くらいに分けるのが良さそうです。

## まとめ

- 個別の理由があるケースは、個別のテストとして書くと意図を追いやすい
- 同じ仕様の代表値や境界値は、Parameterized Test にまとめると読みやすい
- 入力全体に対する性質を確認したいなら、Property-Based Testing を検討する
- テストコードの短さだけでなく、何を保証しているかを読める状態にしたい

Parameterized Test は便利なので、今後も使うと思います。ただ、ケースを配列へ追加する前に、その行が同じ仕様の具体例なのか、別の仕様を押し込もうとしているのかは一度考えてみたいです。
