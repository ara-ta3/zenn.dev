---
title: "MySQLでCollationの設定がコンフリクトしてエラーが出て困った話"
emoji: "😸"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["MySQL", "SQL"]
published: false
---

# 起きたエラー

```
ERROR 1267 (HY000) at line 179: Illegal mix of collations (utf8_unicode_ci,IMPLICIT) and (utf8_general_ci,IMPLICIT) for operation '='
```

- サンプルSQL

```sql

```


# なぜ起きたか


# どの設定か

```sql
# これはsession内部
SHOW VARIABLES LIKE 'collation_connection';

# server設定
SHOW VARIABLES LIKE 'collation_server';

# テーブル設定
SHOW CREATE TABLE foo;
```

## circleciのdocker image

```
docker run -ti -e MYSQL_ROOT_PASSWORD=mypassword -e MYSQL_DATABASE=foo -e MYSQL_USER=user -e MYSQL_PASSWORD=mypassword -p 3307:3306  circleci/mysql:5.7
```

## mysql公式docker image

```
docker run -e MYSQL_ROOT_PASSWORD=mypassword -e MYSQL_DATABASE=foo -e MYSQL_USER=user -e MYSQL_PASSWORD=mypassword -p 3308:3306  mysql:5.7
```




