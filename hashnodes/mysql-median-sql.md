---
title: "How to Calculate the Median in MySQL 8 with Window Functions"
emoji: "📑"
type: "tech"
topics: ["mysql", "sql", "statistics"]
---

## Introduction

I wanted to find the median length of the strings in a MySQL `VARCHAR` column. MySQL 8.0 does not have a built-in `MEDIAN()` aggregate, so I used window functions to select the middle values and average them.

This is an English adaptation of my [Japanese article on Zenn](https://zenn.dev/ara_ta3/articles/mysql-median-sql), incorporating corrections to the original SQL examples.

## Quick answer: number the rows and average the middle values

For a table named `products` with a non-null `name` column:

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

The query requires MySQL 8.0 or later. For an odd number of rows, it selects the single middle row. For an even number, it averages the two middle rows.

## Prepare a small example

```sql
CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

INSERT INTO products (name) VALUES
  ('a'),
  ('bb'),
  ('cc'),
  ('dd'),
  ('eee'),
  ('fff'),
  ('gggg'),
  ('hhhh'),
  ('iiiii'),
  ('jjjjjjjjjjj'),
  ('kkkkkkkkkkkkk');
```

The sorted string lengths are:

```text
1, 2, 2, 2, 3, 3, 4, 4, 5, 11, 13
```

There are 11 rows, so the median is the sixth value: `3`. The query returns `3.0000`.

I use `CHAR_LENGTH()` because I want characters, rather than bytes. This distinction also matters for the Japanese strings in the original article.

## How the middle-row calculation works

The CTE adds two values to each row:

- `rn`: the position when sorted by string length.
- `total_count`: the number of rows in the input.

The two middle positions are calculated as follows:

| Number of rows | First position | Second position | Selected rows |
| --- | --- | --- | --- |
| 11 | `FLOOR(12 / 2) = 6` | `FLOOR(13 / 2) = 6` | Row 6 |
| 10 | `FLOOR(11 / 2) = 5` | `FLOOR(12 / 2) = 6` | Rows 5 and 6 |
| 1 | `FLOOR(2 / 2) = 1` | `FLOOR(3 / 2) = 1` | Row 1 |

Repeating the same position in `IN (...)` does not duplicate a row. That lets `AVG()` handle both odd and even counts without a separate branch.

For an empty table, there are no middle rows and the aggregate returns `NULL`.

The extra `id` ordering makes the row numbering deterministic when lengths tie. It does not affect the median because tied lengths have the same value.

## Check an even number of rows

Remove the first sample product:

```sql
DELETE FROM products WHERE id = 1;
```

The remaining lengths are:

```text
2, 2, 2, 3, 3, 4, 4, 5, 11, 13
```

Run the window-function query again. The fifth and sixth values are `3` and `4`, so the median is `3.5000`.

## Alternative: LIMIT and OFFSET with bound parameters

Another approach sorts all values and retrieves the middle one or two rows directly. For `n` rows:

- Take `2 - n % 2` rows.
- Skip `FLOOR((n - 1) / 2)` rows.

However, MySQL does not accept arbitrary expressions or subqueries directly in the `LIMIT` and `OFFSET` arguments of a normal `SELECT` statement. Use bound parameters in a prepared statement instead:

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

On the remaining 10 rows, this also returns `3.5000`. For an empty table, clamping the offset to zero avoids a negative offset, and the result is `NULL`.

The casts make both bound arguments unsigned integers, as required for the row count and offset.

This example assumes the data does not change between counting and reading it. With concurrent updates, use a consistent snapshot for both statements. The window-function version avoids the separate counting statement.

## Adapting the query to another numeric column

The same pattern works for prices, durations, or another numeric value. Replace `CHAR_LENGTH(name)` with the value you want to measure.

If the column is nullable and you want to ignore `NULL`, filter those rows **inside the CTE**, before both `ROW_NUMBER()` and `COUNT(*) OVER ()` are calculated. The positions and the count must describe the same set of values.

The sample uses `name NOT NULL`, so it does not need that filter.

## Summary

For MySQL 8, I find the window-function version easier to read: sort the values, number the rows, select the middle positions, and average them. It handles odd, even, single-row, and empty inputs with the same query.

## References

- [MySQL: SELECT Statement](https://dev.mysql.com/doc/refman/8.0/en/select.html)
- [MySQL: Window Function Descriptions](https://dev.mysql.com/doc/refman/8.0/en/window-function-descriptions.html)
