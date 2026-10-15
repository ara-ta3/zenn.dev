---
title: "How to Get the Latest Row per Group in MySQL 8 Using ROW_NUMBER()"
emoji: "📊"
type: "tech"
topics: ["mysql", "sql", "database"]
---

## Introduction

I sometimes need to get the latest row for each group in MySQL: the most recent login per user, the latest status per order, or the last edit per article.

For MySQL 8.0 and later, `ROW_NUMBER()` makes this straightforward. Partition the rows by their group, sort each partition from newest to oldest, and keep the row numbered `1`.

This is an English adaptation of my [Japanese article on Zenn](https://zenn.dev/ara_ta3/articles/mysql-group-latest-row).

## Quick answer: use ROW_NUMBER()

For an article history table, the query looks like this:

```sql
WITH ranked AS (
  SELECT
    h.*,
    ROW_NUMBER() OVER (
      PARTITION BY article_id
      ORDER BY updated_at DESC, id DESC
    ) AS rn
  FROM article_histories AS h
)
SELECT article_id, version, content, updated_at
FROM ranked
WHERE rn = 1
ORDER BY article_id;
```

`updated_at DESC` puts the newest edit first. `id DESC` breaks ties when two edits have the same timestamp, so the query selects exactly one row per article. Here, the rule is to choose the larger ID when timestamps match; that is a tie-breaking rule, not a claim that IDs always represent event time.

## Create a sample history table

Let's use a table that stores each edit as a separate row:

```sql
CREATE TABLE article_histories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  article_id INT NOT NULL,
  version INT NOT NULL,
  content TEXT,
  updated_at DATETIME(6) NOT NULL
);

INSERT INTO article_histories
  (article_id, version, content, updated_at)
VALUES
  (1, 1, 'First draft', '2025-10-01 09:00:00.000000'),
  (1, 2, 'Updated title', '2025-10-05 12:30:00.000000'),
  (2, 1, 'First draft', '2025-10-02 10:00:00.000000'),
  (2, 2, 'Expanded content', '2025-10-06 18:20:10.000000'),
  (3, 1, 'First draft', '2025-10-02 10:00:00.000000');
```

Running the query above returns:

```text
article_id  version  content           updated_at
1           2        Updated title     2025-10-05 12:30:00.000000
2           2        Expanded content  2025-10-06 18:20:10.000000
3           1        First draft       2025-10-02 10:00:00.000000
```

## How the query works

There are three parts:

1. `PARTITION BY article_id` splits the rows into groups, one per article.
2. `ORDER BY updated_at DESC, id DESC` orders the rows within each group, and `ROW_NUMBER()` assigns numbers starting at `1`.
3. The outer query keeps only `rn = 1`.

A window function keeps the individual rows available. This matters because we want the content and version from the latest row, rather than just its timestamp.

The common table expression (CTE) gives us a separate query level where we can filter the calculated row number. A derived table works too:

```sql
SELECT article_id, version, content, updated_at
FROM (
  SELECT
    h.*,
    ROW_NUMBER() OVER (
      PARTITION BY article_id
      ORDER BY updated_at DESC, id DESC
    ) AS rn
  FROM article_histories AS h
) AS ranked
WHERE rn = 1
ORDER BY article_id;
```

I tend to prefer the CTE when a history query starts getting more complicated.

## What happens when timestamps tie?

Add another edit with the same timestamp as article `1`'s latest edit:

```sql
INSERT INTO article_histories
  (article_id, version, content, updated_at)
VALUES
  (1, 3, 'Corrected title', '2025-10-05 12:30:00.000000');
```

The new row gets ID `6` in this sample. With `ORDER BY updated_at DESC, id DESC`, the query chooses version `3` for article `1`.

If the timestamp is the only ordering column, the query still returns one row per article, but the choice between tied rows is not fully specified. Add a unique tie-breaker that matches the rule you want.

If you want **all rows tied for the latest timestamp**, use `RANK()` with `ORDER BY updated_at DESC` instead. In that case, multiple rows can have rank `1`.

## Alternative: MAX() with JOIN

For environments without window functions, such as MySQL 5.7, a common approach is to find the maximum timestamp and join it back to the table:

```sql
SELECT h.*
FROM article_histories AS h
JOIN (
  SELECT article_id, MAX(updated_at) AS latest_time
  FROM article_histories
  GROUP BY article_id
) AS latest
  ON h.article_id = latest.article_id
  AND h.updated_at = latest.latest_time
ORDER BY h.article_id, h.id;
```

This returns **every row matching the latest timestamp**. With the extra sample row above, it returns both versions `2` and `3` for article `1`. It is useful when you want ties, but it is not equivalent to selecting exactly one row per group.

Also, selecting `MAX(updated_at)` alone does not retrieve the corresponding content. The join is what reconnects the timestamp to its original row.

## Summary

| Approach | Result when timestamps tie | MySQL version |
| --- | --- | --- |
| `ROW_NUMBER()` with a unique tie-breaker | Exactly one chosen row per group | 8.0+ |
| `RANK()` ordered by timestamp only | All rows tied for latest | 8.0+ |
| `MAX()` joined back to the table | All rows tied for latest | Works without window functions |

For history tables where I need exactly one latest row per group, `ROW_NUMBER()` with an explicit tie-breaker is a useful pattern to keep around.

## References

- [MySQL: Window Function Descriptions](https://dev.mysql.com/doc/refman/8.0/en/window-function-descriptions.html)
- [MySQL: The Rows Holding the Group-wise Maximum of a Certain Column](https://dev.mysql.com/doc/refman/8.0/en/example-maximum-column-group-row.html)
