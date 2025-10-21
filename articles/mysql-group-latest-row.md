
---
title: "MySQL 8で『グループごとに最新1件だけ』を取得する：ROW_NUMBERでシンプルに書く"
emoji: "📊"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["mysql", "sql", "database", "tips"]
published: false
---

SQLを書いていると、  
「**何かしらのIDでグループ化して、その中で最新の1件だけ欲しい**」  
という場面、よくありませんか？

たとえば──

- 各ユーザーの**最新ログイン履歴**  
- 各注文の**最新ステータス**  
- 各記事の**最新編集内容**

など、ユースケースはいろいろですが、  
やりたいことは共通していて「**グループごとに最新1件を取る**」ことです。

---

## 💡 想定する例：記事の更新履歴テーブル

今回は例として、ブログ記事の更新履歴テーブルを題材にします。  
やりたいことは「**記事ごとに最新の編集履歴だけを取得したい**」。

```sql
CREATE TABLE article_histories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  article_id INT NOT NULL,             -- 記事を識別するID
  version INT NOT NULL,                -- バージョン番号
  content TEXT,                        -- 記事内容
  updated_at DATETIME(6) NOT NULL,     -- 更新日時
  KEY idx_article_updated (article_id, updated_at DESC)
);
```

### サンプルデータ

```sql
INSERT INTO article_histories (article_id, version, content, updated_at) VALUES
(1, 1, '初回投稿', '2025-10-01 09:00:00.000000'),
(1, 2, 'タイトル修正', '2025-10-05 12:34:56.123456'),
(2, 1, '初回投稿', '2025-10-03 08:00:00.000000'),
(2, 2, '本文追記', '2025-10-06 18:20:10.000000'),
(3, 1, '初回投稿', '2025-10-02 10:00:00.000000');
```

---

## 🧮 方法1：`ROW_NUMBER()`で最新1件を取る（MySQL 8以降）

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

### ✅ ポイント
- `PARTITION BY article_id` で記事ごとにグループ化。  
- `ORDER BY updated_at DESC` で新しい順に並べ、行番号を振る。  
- `WHERE rn = 1` で各グループの1番目＝最新行のみ抽出。  

タイブレーク用に `id DESC` を追加しておくと、同時刻更新があっても安定します。

---

## 🔁 方法2：`MAX()` と `JOIN` で書く（古典的なやり方）

MySQL 5系などウィンドウ関数が使えない環境では、  
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

この方法でも同様に「各 `article_id` の最新1件」を取得できます。  
ただし、**同時刻に複数レコードがあると重複**して返るので注意。

---

## ⚙️ パフォーマンスのためのインデックス

今回のように「グループ化＋最新順ソート」をする場合は  
次のような複合インデックスが効きます。

```sql
CREATE INDEX idx_article_updated ON article_histories (article_id, updated_at DESC);
```

---

## 📘 まとめ

| 方法 | 特徴 | MySQL対応 |
|------|------|------------|
| `ROW_NUMBER()` | シンプル・拡張性高い・一意にできる | 8.0以降 |
| `MAX()`＋`JOIN` | 古典的で広く対応・重複の可能性あり | 5系〜 |

「グループごとに最新の1件を取る」  
── これは**ログ、履歴、ステータス管理などあらゆる場面で再登場するSQLパターン**です。

MySQL 8 以降を使えるなら、まずは `ROW_NUMBER()` で書いてみましょう。  
きっとクエリがすっきり見通し良くなります。
