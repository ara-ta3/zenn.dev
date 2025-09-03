---
title: "MySQLで中央値を取得するSQLを書く"
emoji: "📑"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["mysql"]
published: false
---

# MySQLで文字数の中央値を求める方法

MySQLで文字列の長さを求めるときは `CHAR_LENGTH()` を使います。  
例えば、商品の名前の文字数の「中央値」を出したいとき、直接 `MEDIAN()` 関数はないため工夫が必要です。  
この記事では、サンプルテーブルを用意して実際にクエリを動かしながら解説します。

---

## サンプルテーブルの作成とデータ投入

まずは `products` テーブルを作ります。

```sql
CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);
```

適当に日本語のデータを入れます。  
今回は「めちゃくちゃ長い名前」のふざけたデータも追加してみます。

```sql
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

これで以下のようなデータになります。

| id | name                                                                                      |
|----|-------------------------------------------------------------------------------------------|
|  1 | ペン                                                                                      |
|  2 | ノート                                                                                    |
|  3 | えんぴつ                                                                                  |
|  4 | 消しゴム                                                                                  |
|  5 | 机                                                                                        |
|  6 | 椅子                                                                                      |
|  7 | 参考書                                                                                    |
|  8 | 定規                                                                                      |
|  9 | コピー用紙                                                                                |
| 10 | ホワイトボードマーカー                                                                    |
| 11 | これは本当に存在するのか誰もわからないけれど世界一長い商品名として登録されてしまったとんでもなくふざけた商品サンプルデータですよろしくお願いします1234567890 |

---

## 各商品の文字数を確認する

`CHAR_LENGTH()` を使えば文字数がわかります。

```sql
SELECT id, name, CHAR_LENGTH(name) AS len
FROM products;
```

結果イメージ:

| id | name                                                                                      | len |
|----|-------------------------------------------------------------------------------------------|-----|
|  1 | ペン                                                                                      | 2   |
|  2 | ノート                                                                                    | 3   |
|  3 | えんぴつ                                                                                  | 4   |
|  4 | 消しゴム                                                                                  | 4   |
|  5 | 机                                                                                        | 1   |
|  6 | 椅子                                                                                      | 2   |
|  7 | 参考書                                                                                    | 3   |
|  8 | 定規                                                                                      | 2   |
|  9 | コピー用紙                                                                                | 5   |
| 10 | ホワイトボードマーカー                                                                    | 11  |
| 11 | これは本当に存在するのか誰もわからないけれど世界一長い商品名として登録されてしまったとんでもなくふざけた商品サンプルデータですよろしくお願いします1234567890 | 93  |

---

## 方法1: LIMIT + OFFSET で中央値を求める

シンプルに「ソートして真ん中を取る」方法です。  

```sql
SELECT
  AVG(sub.len) AS median_length
FROM (
  SELECT CHAR_LENGTH(name) AS len
  FROM products
  ORDER BY len
  LIMIT 2 - (SELECT COUNT(*) FROM products) % 2    -- 偶数なら2件、奇数なら1件
  OFFSET (SELECT (COUNT(*) - 1) / 2 FROM products) -- 真ん中の位置
) AS sub;
```

この場合、結果は:

```
+---------------+
| median_length |
+---------------+
| 3.0           |
+---------------+
```

つまり中央値は「3文字」です。

---

## 方法2: ウィンドウ関数を使う (MySQL 8.0以上)

より柔軟に書く方法として、ウィンドウ関数 `ROW_NUMBER()` と `COUNT(*) OVER ()` を使います。

```sql
WITH ordered AS (
  SELECT
    CHAR_LENGTH(name) AS len,
    ROW_NUMBER() OVER (ORDER BY CHAR_LENGTH(name)) AS rn,
    COUNT(*) OVER () AS total_count
  FROM products
)
SELECT
  CASE
    WHEN total_count % 2 = 1 THEN
      MAX(CASE WHEN rn = (total_count + 1) / 2 THEN len END)
    ELSE
      AVG(CASE WHEN rn IN (total_count / 2, total_count / 2 + 1) THEN len END)
  END AS median_length
FROM ordered;
```

結果:

```
+---------------+
| median_length |
+---------------+
| 3.0           |
+---------------+
```

---

## まとめ

- `CHAR_LENGTH()` で文字数を取得できる  
- MySQLには `MEDIAN()` 関数がないので工夫が必要  
- 行数が少なければ **LIMIT + OFFSET** でシンプルに  
- MySQL 8.0 以上なら **ウィンドウ関数**でスマートに書ける  

中央値は統計的に便利な指標なので、ぜひ覚えておくと役立ちます！
