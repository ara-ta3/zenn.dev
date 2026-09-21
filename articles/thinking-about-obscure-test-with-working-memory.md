---
title: "Obscure Test を Working Memory から考える"
emoji: "🔍"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: ["test", "testing", "vitest"]
published: false
---

## はじめに

テストコードを読んでいて、なんか読みづらいなと感じることがありました。

例えば、次のような Parameterized Test です。

```js
test.each([
  ["未成年の利用者", 17, "active", "card", false],
  ["退会済みの利用者", 20, "withdrawn", "card", false],
])("%s は申し込みできるか", (_, age, status, paymentMethod, expected) => {
  const user = { age, status, paymentMethod };

  expect(canApply(user)).toBe(expected);
});
```

ケースを追加しやすく、コード量も少ないので便利です。ただ、parameter が増えてくると、各値が何を表しているのか、どの条件によって期待結果が決まるのかがぱっと見では分からなくなります。

具体的なテストケースを理解するためには、配列の要素を仮引数へ対応づけ、`user` を組み立て、最後に assertion へ代入する必要があります。テストは読めるものの、読むために少し頑張る必要がある、という感じです。

この読みづらさをうまく説明できないか考えていたところ、xUnit Test Patterns の Obscure Test と、『プログラマー脳』の Working Memory の話がつながりそうだと感じました。

この記事では、複数の parameter を持つ Parameterized Test を Obscure Test と Working Memory の観点から考えます。

## Parameterized Test の何を読みづらいと感じたのか

もう少しケースを増やして考えます。この記事のコード例では Vitest を使います。

```js
test.each([
  ["未成年の利用者", 17, "active", "card", false],
  ["退会済みの利用者", 20, "withdrawn", "card", false],
  ["利用停止中の利用者", 20, "suspended", "card", false],
  ["支払い方法が未登録の利用者", 20, "active", null, false],
  ["条件を満たす利用者", 20, "active", "card", true],
])("%s は申し込みできるか", (_, age, status, paymentMethod, expected) => {
  const user = { age, status, paymentMethod };

  expect(canApply(user)).toBe(expected);
});
```

繰り返しの制御はテストフレームワークが引き受けるため、ループの現在位置や終了条件を追う必要はなくなりました。ケースを追加しやすく、コードの重複も減っています。

### テーブルとテスト本体を頭の中で組み立てる

一方、「退会済みの利用者」のケースが何を保証しているのか理解するには、次のような作業が必要です。

1. テーブルから対象の行を取り出す
2. 配列の各要素を `label`、`age`、`status`、`paymentMethod`、`expected` へ対応づける
3. 対応を保持したまま `user` を組み立て、テスト本体へ値を当てはめる
4. どの値が期待結果を決めているのか探す
5. 「退会済みの利用者は申し込みできない」という仕様を読み取る

頭の中で具体化すると、次のテストになります。

```js
expect(
  canApply({ age: 20, status: "withdrawn", paymentMethod: "card" }),
).toBe(false);
```

テーブルとテスト本体を結合しないと、具体的なテストケースが見えてきません。

### 複数の条件が1つのテーブルに含まれている

さらに、このテーブルには「申し込める」と「申し込めない」の両方があります。「申し込めない」ケースにも複数の条件があります。

- 未成年の利用者は申し込めない
- 退会済みの利用者は申し込めない
- 利用停止中の利用者は申し込めない
- 支払い方法が未登録の利用者は申し込めない
- 条件を満たす利用者は申し込める

このテーブルでは、年齢、アカウントの状態、支払い方法という別々の条件を確かめています。引数の形が同じという理由でまとめた結果、どの条件を確かめているのかがデータの並びへ押し込まれています。

## 読みづらさを Obscure Test として捉える

xUnit Test Patterns では、**Obscure Test** を次のように定義しています。

> It is difficult to understand the test at a glance.

一目見ただけでは、そのテストを理解するのが難しい状態です。

https://xunitpatterns.com/Obscure%20Test.html

テストは実行可能な仕様です。同時に、実行するための詳細を持つコードでもあります。その詳細から何を保証しているのか読み取れなくなると、Tests as Documentation としての役割を果たしにくくなります。

Obscure Test は特定の構文を指すものではありません。必要な情報がテストの外に隠れている場合もあれば、反対に情報が多すぎて意図が埋もれている場合もあります。

今回注目したいのは、テーブルとテスト本体を頭の中で組み合わせなければ、具体的な前提と期待結果が見えてこない状態です。

Parameterized Test 自体が Obscure Test なのではありません。ただ、今回の例は一目見ただけでは前提と期待結果の関係を理解できず、行ごとに具体的なテストへ復元する必要があります。そのため、Obscure Test になっていると考えています。

## Working Memory が関係しているのか考える

### 『プログラマー脳』の Working Memory

『プログラマー脳』では、コードを読むときに Long-Term Memory、Short-Term Memory、Working Memory という3つの認知プロセスが関わると説明されています。このうち Working Memory は、情報を一時的に保持しながら処理する役割を持ちます。

https://www.felienne.com/book

日本語版は、フェリエンヌ・ヘルマンス著、水野貴明訳、水野いずみ監訳の『プログラマー脳〜優れたプログラマーになるための認知科学に基づくアプローチ』として、2023年に秀和システムから出版されています。

[Amazon - プログラマー脳 ～優れたプログラマーになるための認知科学に基づくアプローチ](https://link.amazon/B0aAnswB5)

:::message
2026年9月21日時点では、日本語版を新品で購入するのは難しくなっているようです。発行元の秀和システムは2025年7月4日に[破産手続開始決定を受けています](https://diamond.jp/articles/-/376387)。出版事業は[秀和システム新社へ譲渡されています](https://prtimes.jp/main/html/rd/p/000000001.000169048.html)が、『プログラマー脳』が同社から再刊されたことは確認できませんでした。上記の Amazon の商品リンクも現在は開けないため、読みたい場合は中古書店や図書館を探すことになりそうです。
:::

### Program Tracing と Working Memory

今回の Parameterized Test を読むときは、テーブルの値と仮引数の対応を保持しながら、テスト本体へ値を当てはめます。これは、具体的な入力に対してプログラムを頭の中で実行する Program Tracing に近い作業です。

2021年の *The Role of Working Memory in Program Tracing* は、プログラムを頭の中で実行するとき、変数と値の組み合わせなどの状態を Working Memory へ保持する必要があると説明しています。実験では、Working Memory の負荷によって、変数と値の組み合わせを忘れるだけでなく、別の組み合わせと取り違えることも確認されています。

https://arxiv.org/abs/2101.06305

:::message
この研究は Parameterized Test の書き方を比較したものではありません。そのため、複数の parameter を持つことによる認知負荷が直接実証されたわけではありません。
:::

ただ、テストを理解するまでに保持する情報を減らす、という判断には使えそうです。

## 個別のテストに展開して読み比べる

Parameterized Test を個別のテストへ展開すると、次のようになります。

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

コード量は増えました。ただ、それぞれのテストだけを読めば、前提、操作、期待結果が分かります。配列と仮引数の対応を Working Memory へ保持する必要もありません。

コードの重複と、年齢やアカウントの状態、支払い方法のような別々の条件を1つへまとめることは、分けて考えたいです。多少のコードが重複しても、仕様を直接読めるなら個別のテストを選びます。

## Parameterized Test が読みやすい場合もある

Parameterized Test を完全に使わないわけではありません。テーブル自体を1つの仕様として読める場合には、個別に展開したコードより読みやすくなることもあります。

### 年齢区分の境界値を並べる

```js
test.each([
  { age: 0, expected: "child" },
  { age: 12, expected: "child" },
  { age: 13, expected: "adult" },
  { age: 64, expected: "adult" },
  { age: 65, expected: "senior" },
])("$age歳の年齢区分は$expectedになる", ({ age, expected }) => {
  expect(toAgeGroup(age)).toBe(expected);
});
```

このテーブルで変わるのは `age` と、それに対応する `expected` だけです。年齢区分という1つの仕様に対する代表値と境界値を並べており、入力と期待値の対応をテーブルからそのまま読めます。

『プログラマー脳』では、複数の情報を意味のあるまとまりとして扱う Chunking も紹介されています。この例なら、テーブル全体を「年齢区分の境界値」という1つのまとまりで読めそうです。

### 使う基準

今のところ、Parameterized Test を使うなら、少なくとも次の条件を満たしたいです。

- すべての行が同じ仕様を確かめている
- 独立した仕様軸が1つに収まっている
- 入力と期待値の対応がそのまま仕様として読める
- 1行ずつテスト本体へ代入しなくても、テーブルの意味を理解できる

## まとめ

私は、複数の parameter を持つ Parameterized Test を読みづらいと感じることがありました。テーブルの値と仮引数の対応を保持し、具体的なテストへ復元する作業に Working Memory を使うことが、その理由の1つなのかもしれません。

Parameterized Test 自体は便利なので、入力と期待値の対応がそのまま読めるようなシンプルなケースでは、これからも使っていきたいです。一方、parameter が増え、テスト本体へ値を当てはめないと仕様を理解できない場合は、多少コードが重複しても個別のテストへ展開しようと思います。
