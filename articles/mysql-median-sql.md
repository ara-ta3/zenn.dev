---
title: "MySQLで中央値を取得するSQLを書く"
emoji: "📑"
type: "tech"
topics: ["mysql", "統計", "中央値"]
published: true
---

# はじめに

MySQLで文字列の長さを求めるときは `CHAR_LENGTH()` を使います。
VARCHAR型のカラムの文字数について、中央値を求めたくなったときの備忘録です。
ここではMySQL 8.0で、文字数を並べて中央の値を取り出してみます。

:::message
以前の版には、`LIMIT` / `OFFSET` に計算式やサブクエリを直接渡す例がありましたが、MySQLではその構文を使えません。
また、ウィンドウ関数の例には、集約されていない `total_count` と集約関数を同じSELECTに置く問題がありました。
以下は、プリペアドステートメントで件数を渡す方法と、中央の行をWHEREで絞ってから集約する方法へ訂正したものです。
:::

# サンプルテーブルを用意する

```sql
CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

INSERT INTO products (name) VALUES
  ('ペン'),
  ('ノート'),
  ('えんぴつ'),
  ('消しゴム'),
  ('机'),
  ('椅子'),
  ('参考書'),
  ('定規'),
  ('コピー用紙'),
  ('ホワイトボードマーカー'),
  ('これは本当に存在するのか誰もわからないけれど世界一長い商品名として登録されてしまったとんでもなくふざけた商品サンプルデータですよろしくお願いします1234567890');
```

文字数を短い順に確認します。バイト数を返す `LENGTH()` ではなく `CHAR_LENGTH()` を使います。

```sql
SELECT id, CHAR_LENGTH(name) AS len
FROM products
ORDER BY len, id;
```

```text
id  len
5   1
1   2
6   2
8   2
2   3
7   3
3   4
4   4
9   5
10  11
11  83
```

11件なので、中央は6番目の `3` です。件数が偶数なら、中央の2件の平均を中央値とします。

# 方法1: LIMIT + OFFSETで中央の行を取得する

件数を `n` とすると、取得件数は `2 - n % 2`、スキップする件数は `FLOOR((n - 1) / 2)` です。
ただし、通常のSELECTでは `LIMIT` / `OFFSET` に計算式やサブクエリを直接書けません。
ここでは計算結果をユーザー変数へ入れ、プリペアドステートメントのパラメーターとして渡します。
件数のパラメーターは整数として渡す必要があるため、`CAST(... AS UNSIGNED)` で型も揃えています。

```sql
SELECT COUNT(*) INTO @total_count FROM products;
SET @take = CAST(2 - MOD(@total_count, 2) AS UNSIGNED);
SET @skip = CAST(GREATEST(0, FLOOR((@total_count - 1) / 2)) AS UNSIGNED);

PREPARE median_query FROM '
  SELECT AVG(middle_rows.len) AS median_length
  FROM (
    SELECT CHAR_LENGTH(name) AS len
    FROM products
    ORDER BY len
    LIMIT ? OFFSET ?
  ) AS middle_rows
';
EXECUTE median_query USING @take, @skip;
DEALLOCATE PREPARE median_query;
```

11件の例では `LIMIT 1 OFFSET 5` として実行され、中央値は `3` になります。
空のテーブルではスキップ件数を0にして、`AVG()` が `NULL` を返すようにしています。

この例は、処理中にデータが変わらない前提です。
行数取得と中央値取得は別のSQLなので、更新が並行する場合は同じスナップショットで読む設計が必要です。
MySQL 8.0以降なら、次の方法で1つのSQLにまとめられます。

# 方法2: ウィンドウ関数を使う（MySQL 8.0以降）

`ROW_NUMBER()` で行番号を、`COUNT(*) OVER ()` で全体の行数を付けます。
その後、中央の行をWHEREで絞ってから、`AVG()` で平均を取ります。

```sql
WITH ordered AS (
  SELECT
    CHAR_LENGTH(name) AS len,
    ROW_NUMBER() OVER (ORDER BY CHAR_LENGTH(name), id) AS rn,
    COUNT(*) OVER () AS total_count
  FROM products
)
SELECT AVG(len) AS median_length
FROM ordered
WHERE rn IN (
  FLOOR((total_count + 1) / 2),
  FLOOR((total_count + 2) / 2)
);
```

11件なら、2つの式はどちらも6になります。WHEREで6番目の1件を選び、その値を返します。
10件なら5と6になるので、中央の2件の平均が返ります。

| 行数 | 選ぶ行番号 | 結果 |
| --- | --- | --- |
| 11件 | 6 | 6番目の値 |
| 10件 | 5、6 | 5番目と6番目の平均 |
| 1件 | 1 | その1件の値 |
| 0件 | なし | `NULL` |

今回の11件では、両方の方法で `3.0000` が返ります。
別の数値カラムに使う場合も、並べた値から中央の行を選ぶ考え方は同じです。
ただし、NULLを除外するなら、CTEの中で除外し、行番号と件数が同じ対象から計算されるようにします。
今回の `name` はNOT NULLなので、その条件は不要です。

# まとめ

MySQLで中央値を求める2つの方法を確認しました。
MySQL 8.0以降なら、ウィンドウ関数で行番号と件数を付け、中央の行だけを平均する方法が読みやすいと感じました。
文字数だけでなく、別の数値の中央値を求めたいときにも使えそうです。

# 参考

- [MySQL: SELECT Statement](https://dev.mysql.com/doc/refman/8.0/en/select.html)
- [MySQL: Window Function Descriptions](https://dev.mysql.com/doc/refman/8.0/en/window-function-descriptions.html)
