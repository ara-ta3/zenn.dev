---
title: "MySQLで『グループごとに最新1件だけ』を取得 ~ 8.0以降で使えるウィンドウ関数でシンプルに書く ~"
emoji: "📊"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["mysql", "sql", "database", "tips"]
published: true
---
## はじめに

MySQL で SQL を書いていて「**何かしらでグループ化して、その中で最新の 1 件だけ欲しい**」みたいなパターンに何度か直面しました。  
具体的に浮かぶユースケースとしては履歴を INSERT して記録する設計において、以下のようなケースがあるかと思います。

- 各ユーザーの**最新ログイン履歴**
- 各注文の**最新ステータス**
- 各記事の**最新編集内容**

これらのやりたいことは共通していて「**グループごとに最新 1 件を取る**」ことでした。  
なので今回はこのとき書く SQL を備忘録がてら書いておこうというのが趣旨です。

## 準備: 記事の更新履歴テーブル

今回は例として、ブログ記事の更新履歴テーブルを題材にします。  
やりたいことは「**記事ごとに最新の編集履歴だけを取得したい**」です。

```sql
CREATE TABLE article_histories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  article_id INT NOT NULL,             -- 記事を識別するID
  version INT NOT NULL,                -- バージョン番号
  content TEXT,                        -- 記事内容
  updated_at DATETIME(6) NOT NULL      -- 更新日時
);
```

### サンプルデータ

```sql
INSERT INTO article_histories (article_id, version, content, updated_at) VALUES
(1, 1, '初回投稿', '2025-10-01 09:00:00.000000'),
(1, 2, 'タイトル修正', '2025-10-05 12:30:00.000000'),
(2, 1, '初回投稿', '2025-10-03 08:00:00.000000'),
(2, 2, '本文追記', '2025-10-06 18:20:10.000000'),
(3, 1, '初回投稿', '2025-10-02 10:00:00.000000');
```

## 方法 1: `ROW_NUMBER()`で最新 1 件を取る（MySQL 8 以降）

MySQL 8 以降では、**ウィンドウ関数**を使えば一発です。

```sql
SELECT article_id, version, content, updated_at
FROM (
  SELECT
    t.*,
    ROW_NUMBER() OVER (PARTITION BY article_id ORDER BY updated_at DESC, id DESC) AS rn
  FROM article_histories AS t
) AS ranked
WHERE rn = 1
ORDER BY article_id;
```

```
+------------+---------+--------------------+----------------------------+
| article_id | version | content            | updated_at                 |
+------------+---------+--------------------+----------------------------+
|          1 |       2 | タイトル修正       | 2025-10-05 12:30:00.000000 |
|          2 |       2 | 本文追記           | 2025-10-06 18:20:10.000000 |
|          3 |       1 | 初回投稿           | 2025-10-02 10:00:00.000000 |
+------------+---------+--------------------+----------------------------+
3 rows in set (0.004 sec)
```

### ポイント

- `PARTITION BY article_id` で記事ごとにグループ化。
- `ORDER BY updated_at DESC` で新しい順に並べ、行番号を振る。
- `WHERE rn = 1` で各グループの 1 番目＝最新行のみ抽出。

時間が被ったときように用に `id DESC` を追加しておくと一応安心です。  

### (余談)サブクエリではなくwith句を使う

上のサブクエリを使った書き方は少しネストが深くなるので、MySQL 8以降なら with句(CTE(Common Table Expression))を使って読みやすく書くこともできます。  

```sql
WITH ranked AS (
  SELECT
    t.*,
    ROW_NUMBER() OVER (
      PARTITION BY article_id
      ORDER BY updated_at DESC, id DESC
    ) AS rn
  FROM article_histories AS t
)
SELECT article_id, version, content, updated_at
FROM ranked
WHERE rn = 1
ORDER BY article_id;
```

履歴系やログ系クエリはどうしても複雑になりがちなので、CTE は積極的に使った方がチーム開発でも読みやすさが担保できる印象です。  

## 方法 2: `MAX()` と `JOIN` で書く（一般的な SQL でのやり方）

MySQL 5 系などウィンドウ関数が使えない環境では、  
`MAX()` サブクエリと `JOIN` を組み合わせます。

```sql
SELECT t.*
FROM article_histories AS t
JOIN (
  SELECT article_id, MAX(updated_at) AS max_time
  FROM article_histories
  GROUP BY article_id
) AS latest
  ON t.article_id = latest.article_id
  AND t.updated_at = latest.max_time;
```

```
+----+------------+---------+--------------------+----------------------------+
| id | article_id | version | content            | updated_at                 |
+----+------------+---------+--------------------+----------------------------+
|  2 |          1 |       2 | タイトル修正       | 2025-10-05 12:30:00.000000 |
|  4 |          2 |       2 | 本文追記           | 2025-10-06 18:20:10.000000 |
|  5 |          3 |       1 | 初回投稿           | 2025-10-02 10:00:00.000000 |
+----+------------+---------+--------------------+----------------------------+
3 rows in set (0.002 sec)
```

この方法でも同様に「各 `article_id` の最新 1 件」を取得できます。  
ただし、**同時刻に複数レコードがあると重複**して返るので注意が必要です。  

## まとめ

| 方法            | 特徴                 | MySQL 対応 |
| --------------- | ---------------------| ---------- |
| `ROW_NUMBER()`  | シンプル・拡張性高い | 8.0 以降   |
| `MAX()`＋`JOIN` | SQL的に通常の方法。  | 5 系〜     |

「グループごとに最新の 1 件を取る」これは**ログ、履歴、ステータス管理など様々な場面で登場する SQL パターン**かと思います。  
MySQL 8 以降を使えるなら、まずは `ROW_NUMBER()` で書くのが非常に便利です。  
きっとクエリがすっきり見通し良くなるでしょう。  
