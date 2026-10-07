---
title: "tblsを使ってMySQLの複数テーブルについてのドキュメントを生成する"
emoji: "📝"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["tbls", "mysql", "document"]
published: true
---

今回使ったコードはここに置いてあります。  

https://github.com/ara-ta3/tbls-getting-started

# 例として使うテーブル構成

ECサイトっぽいテーブルを例として作ってみました。  
せっかくなのでtblsで生成したものをmarkdownへのリンクを省いて表で持ってきています。  

| Name | Columns | Comment | Type |
| ---- | ------- | ------- | ---- |
| current_cart | 4 |  | BASE TABLE |
| items | 5 |  | BASE TABLE |
| ordered_items | 5 |  | BASE TABLE |
| orders | 4 |  | BASE TABLE |
| users | 4 |  | BASE TABLE |

![](/images/tbls/schema.png)

# tblsについて

tblsは、データベースのスキーマ構造を自動的にドキュメント化するためのツールです。  
MySQLやPostgreSQLだけではなくSQLiteやBigQueryなどもサポートしているようです。  
それらのDBに接続し、外部キー制約などを見て自動的にテーブル定義やER図なども作成してくれます。  
また、viewpointsという複数テーブルに関する説明を作成できるのが個人的には嬉しいポイントです。  
サービスをやっているとテーブル単体というより複数のテーブルがビジネスロジックに関わってくるので、それらをまとめて説明できるのが便利だなと思っています。  

https://github.com/k1LoW/tbls


# テーブル単位のドキュメントを生成する

まず基本的な生成に関しての設定です。  

やることとしては以下のようなことが必要になります。

1. docker等で接続できるDBを立ち上げる
2. tblsの設定ファイルに接続情報を追加後に実行しドキュメントを生成する

1については開発環境などを使えばいいので割愛します。  
2の設定については最低限だと下記のような設定になります。  
環境変数から取得できるので${}で囲んで環境変数から取得しています。  
docPathについてはコマンドのオプションなどで設定しても構いません。  

tbls.yml

```yml
dsn: "mysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:3306/ecsite-samples"
docPath: dbdocs
```

この状態で`tbls doc`コマンドを叩けばドキュメントがdbdocsディレクトリに生成されます。  
下記URLにあるようにREADME.mdが全体像で、各々のテーブルに関するドキュメントがテーブル名.mdというファイル(users.mdなど)が生成されます。  

https://github.com/ara-ta3/tbls-getting-started/blob/main/dbdocs/README.md

# viewpointsを使って複数テーブルについてのドキュメントを生成する

viewpointsは複数のテーブル郡に関する説明を設定ファイルに記述してそれをドキュメントとして生成できる機能です。  
下記のような設定をtbls.ymlに追加します。  

```yml
viewpoints:
  - name: 注文
    desc: 注文した商品
    tables:
      - orders
      - ordered_items
      - items
      - users
    groups:
      - name: 注文
        desc: 注文した商品
        tables:
          - orders
          - ordered_items
          - items
  - name: 購入前
    desc: 購入前の商品
    tables:
      - items
      - users
      - current_cart
    groups:
      - name: 購入前
        desc: 購入前の商品一覧
        tables:
          - current_cart
          - items
          - users
  - name: ユーザ
    desc: ユーザ一覧
    tables:
      - users
    groups:
      - name: ユーザ
        desc: ユーザ一覧
        tables:
          - users
```

結果として下記URLのようなマークダウン形式のドキュメントが生成されます。  
https://github.com/ara-ta3/tbls-getting-started/blob/main/dbdocs/viewpoint-0.md  
viewpoint毎に生成されるので、上記設定の場合viewpoint-0.md、viewpoint-1.md、viewpoint-2.mdが生成されました。  
Descriptionが主な説明となりますが、Commentsもテーブルやカラムへのコメントがなくても設定ファイルに記述することでコメントをドキュメントに表示できるようなので、それも合わせると良いでしょう。  

# 差分が出たときの対応

ドキュメントはメンテナンスされないことが多々ありますが、CIで差分があった場合やviewpointへの追加がなかった場合にlintでエラーに倒すということが可能です。
なので、それをCIに含めることによりlintとdiffを見て差分がある場合はメンテナンスしましょうという方針にするのが良いでしょう。  

## GitHub Actionsの例

これが先頭にて紹介したサンプルコード上で回しているGitHub Actionsの設定です。  

https://github.com/ara-ta3/tbls-getting-started/tree/main

```yml
name: TBLs Schema Check

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  tbls-check:
    runs-on: ubuntu-latest

    steps:
      - name: checkout
        uses: actions/checkout@v4

      - name: start mysql docker
        run: make start opt=-d

      - name: wait for mysql
        run: make wait-for-mysql

      - name: Install tbls
        run: |
          curl -L https://github.com/k1LoW/tbls/releases/download/v1.79.0/tbls_v1.79.0_linux_amd64.tar.gz | tar xvz
          sudo mv tbls /usr/local/bin/tbls

      - name: Run tbls lint
        run: make lint

      - name: Run tbls diff
        run: make diff
```

## tbls lint

lintでviewpointsに追加していない場合に落とす設定はtbls.ymlに下記のように追加する必要があります。  

```yml
lint:
  requireViewpoints:
    enabled: true
```

これによりもし新しくテーブルが追加された場合、下記のようにエラーに倒すことが出来ます。  
下記はuser_informationというテーブルを新しく追加した場合の例になります。  

https://github.com/ara-ta3/tbls-getting-started/pull/2
https://github.com/ara-ta3/tbls-getting-started/actions/runs/11658871811/job/32458550009

```zsh
$Run make lint
set -o allexport && . ./env && tbls lint
注文 orders
注文 ordered_items
注文 items
注文 users
購入前 items
購入前 users
購入前 current_cart
ユーザ users
user_information: table `user_information` is not included in any viewpoints.
1 detected
make: *** [Makefile:46: lint] Error 1
```

## tbls diff

diffについては特に指定がない場合、現在生成されているドキュメントとDBの設定の差分を見てくれます。  
なので例えばカラムを追加した場合に差分が発生するので、これもCI含めておくとドキュメントの更新し忘れを防ぐことが出来るでしょう。  
下記はusersテーブルにregistered_atというカラムを追加した場合の例になります。  

https://github.com/ara-ta3/tbls-getting-started/pull/1
https://github.com/ara-ta3/tbls-getting-started/actions/runs/11658830171

```diff
diff 'dbdocs/README.md' 'tbls doc ***127.0.0.1:3306/ecsite-samples'
--- dbdocs/README.md
+++ tbls doc ***127.0.0.1:3306/ecsite-samples
@@ -16,7 +16,7 @@
 | [items](items.md) | 5 |  | BASE TABLE |
 | [ordered_items](ordered_items.md) | 5 |  | BASE TABLE |
 | [orders](orders.md) | 4 |  | BASE TABLE |
-| [users](users.md) | 4 |  | BASE TABLE |
+| [users](users.md) | 5 |  | BASE TABLE |
 
 ## Relations
 
diff 'dbdocs/users.md' '***127.0.0.1:3306/ecsite-samples users'
--- dbdocs/users.md
+++ ***127.0.0.1:3306/ecsite-samples users
@@ -11,6 +11,7 @@
   `username` varchar(255) NOT NULL,
   `email` varchar(255) NOT NULL,
   `password_hash` varchar(255) NOT NULL,
+  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`id`),
   UNIQUE KEY `username` (`username`),
   UNIQUE KEY `email` (`email`)
@@ -27,6 +28,7 @@
 | username | varchar(255) |  | false |  |  |  |  |
 | email | varchar(255) |  | false |  |  |  |  |
 | password_hash | varchar(255) |  | false |  |  |  |  |
+| registered_at | datetime | CURRENT_TIMESTAMP | true | DEFAULT_GENERATED |  |  |  |
 
 ## Viewpoints
 
diff 'dbdocs/viewpoint-0.md' '***127.0.0.1:3306/ecsite-samples viewpoint-0'
--- dbdocs/viewpoint-0.md
+++ ***127.0.0.1:3306/ecsite-samples viewpoint-0
@@ -20,7 +20,7 @@
 
 | Name | Columns | Comment | Type |
 | ---- | ------- | ------- | ---- |
-| [users](users.md) | 4 |  | BASE TABLE |
+| [users](users.md) | 5 |  | BASE TABLE |
 
 ## Relations
 
diff 'dbdocs/viewpoint-1.md' '***127.0.0.1:3306/ecsite-samples viewpoint-1'
--- dbdocs/viewpoint-1.md
+++ ***127.0.0.1:3306/ecsite-samples viewpoint-1
@@ -14,7 +14,7 @@
 | ---- | ------- | ------- | ---- |
 | [current_cart](current_cart.md) | 4 |  | BASE TABLE |
 | [items](items.md) | 5 |  | BASE TABLE |
-| [users](users.md) | 4 |  | BASE TABLE |
+| [users](users.md) | 5 |  | BASE TABLE |
 
 ## Relations
 
diff 'dbdocs/viewpoint-2.md' '***127.0.0.1:3306/ecsite-samples viewpoint-2'
--- dbdocs/viewpoint-2.md
+++ ***127.0.0.1:3306/ecsite-samples viewpoint-2
@@ -12,7 +12,7 @@
 
 | Name | Columns | Comment | Type |
 | ---- | ------- | ------- | ---- |
-| [users](users.md) | 4 |  | BASE TABLE |
+| [users](users.md) | 5 |  | BASE TABLE |
 
 ## Relations
 
make: *** [Makefile:49: diff] Error 1
```

# まとめ

- 自動で生成されるのでだいぶ便利
- メンテナンスの仕組みも合わせやすいので便利
- viewpointを利用して複数のテーブルについての説明も書けるので便利
- つまりとても便利

# 参考

https://zenn.dev/micin/articles/8b64c7460d68a8
https://zenn.dev/ara_ta3/scraps/fd7b61abd81438
https://github.com/ara-ta3/tbls-getting-started
