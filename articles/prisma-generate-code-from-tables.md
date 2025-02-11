---
title: "Prismaを使って既存のテーブルスキーマからコードを生成する"
emoji: "✨"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["prisma", "mysql"]
published: false
---

# 背景と概要

発端は既存のテーブル構成からORMっぽい役割のコードを生成できないかと思って探していました。  
調べている間にPrismaの名前を見て、前知り合いが発表していたなと思い検証してみました。その時の備忘録です。  
マッピングするクラスはScalaのコードにしたかったので、Scalaのコードを生成してみます。  
後に出てくるコードを見るとわかりますが、JavaScript(TypeScript)で生成するコードを書くので、任意のファイルが生成可能で、Scalaに限った話ではありません。  

イメージは以下のような感じです。  
prisma/scala-generate.jsという部分でコードを生成するのですが、他の言語のコードをここで生成するようにすれば任意の言語のファイルが生成できます。  

```mermaid
flowchart LR
    A[既存のDB MySQL] --> |prisma db pull| B[prisma/schema.prisma]
    B -->|"prisma generate (prisma/scala-generator.js)"| C[Scalaのコード]
```


検証したコードなどはこちらです。  

https://zenn.dev/ara_ta3/scraps/45124487a548ee

https://github.com/ara-ta3/prisma-scala-gettingstarted

# Prismaとは

PrismaはNode.js用のORMですが、schema.prismaという固有のスキーマファイルを生成し、それを元にDBマイグレーションやコード生成などを行えるという特徴があります。  
当然TypeScript / JavaScriptの生成もできるのですが、独自のジェネレータを書くことによって、TypeScript / JavaScript以外の言語のコード生成も可能というのも1つの利点です。  

https://www.prisma.io/

# 事前準備

## MySQLに適当なテーブルを用意する

MySQLに既存のテーブルがあるという前提にするため、適当なテーブルを作成します。  
ECサイトっぽい雰囲気のテーブルを以下のように定義しています。  

```sql
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE current_cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE ordered_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);
```
## Prismaのインストール

Prismaはnpmでインストールしています。  
今回使ったPrismaのバージョンは6.3.0でした。  

package.json

```json
{
  "name": "prisma-generate-scala",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {},
  "author": "",
  "license": "ISC",
  "description": "",
  "dependencies": {
    "@prisma/generator-helper": "^6.3.0",
    "prisma": "^6.3.0"
  }
}
```

# 既存のテーブルからスキーマファイルを生成する

やることは以下の通りです。  

- prisma/schema.prismaに設定を記述
    - 環境変数を使う場合は.envを利用する
- prisma db pullでprisma/schema.prismaを更新する

## prisma/schema.prismaに設定を記述

```prisma
generator scala {
  provider = "node ./prisma/scala-generator.js"
  output   = "../dist"
}

datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}
```

generator scalaの部分は後の部分で使う記述です。  
テーブルからスキーマファイルを生成する場合の最小限はdatabase dbのブロックのみになります。  
env("HOGE")を使うことで.envから取得できるので、パスワードなどセンシティブな情報はそちらに記載しましょう。  
今回はデモ用なのでここにも記載します。  

```env
DATABASE_URL="mysql://root:rootpassword@127.0.0.1:3306/ecsite-samples"
```

## prisma db pullでprisma/schema.prismaを更新する

上記の設定ができていればprisma db pullを実行するだけです。  

```zsh
./node_modules/.bin/prisma db pull
Prisma schema loaded from prisma/schema.prisma
Environment variables loaded from .env
Datasource "db": MySQL database "ecsite-samples" at "127.0.0.1:3306"

✔ Introspected 5 models and wrote them into prisma/schema.prisma in 171ms

Run prisma generate to generate Prisma Client.
```

実行後、prisma/schema.prismaに独自の定義が記述されます。  

prisma/schema.prisma

```
generator scala {
  provider = "node ./prisma/scala-generator.js"
  output   = "../dist"
}

datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}

model current_cart {
  id       Int   @id @default(autoincrement())
  user_id  Int   @unique(map: "user_id")
  item_id  Int
  quantity Int   @default(1)
  users    users @relation(fields: [user_id], references: [id], onDelete: NoAction, onUpdate: NoAction, map: "current_cart_ibfk_1")
  items    items @relation(fields: [item_id], references: [id], onDelete: NoAction, onUpdate: NoAction, map: "current_cart_ibfk_2")

  @@index([item_id], map: "item_id")
}

model items {
  id            Int             @id @default(autoincrement())
  name          String          @db.VarChar(255)
  description   String?         @db.Text
  price         Decimal         @db.Decimal(10, 2)
  stock         Int?            @default(0)
  current_cart  current_cart[]
  ordered_items ordered_items[]
}

model ordered_items {
  id                Int     @id @default(autoincrement())
  order_id          Int
  item_id           Int
  quantity          Int
  price_at_purchase Decimal @db.Decimal(10, 2)
  orders            orders  @relation(fields: [order_id], references: [id], onDelete: NoAction, onUpdate: NoAction, map: "ordered_items_ibfk_1")
  items             items   @relation(fields: [item_id], references: [id], onDelete: NoAction, onUpdate: NoAction, map: "ordered_items_ibfk_2")

  @@index([item_id], map: "item_id")
  @@index([order_id], map: "order_id")
}

model orders {
  id            Int             @id @default(autoincrement())
  user_id       Int
  order_date    DateTime?       @default(now()) @db.Timestamp(0)
  total_amount  Decimal         @db.Decimal(10, 2)
  ordered_items ordered_items[]
  users         users           @relation(fields: [user_id], references: [id], onDelete: NoAction, onUpdate: NoAction, map: "orders_ibfk_1")

  @@index([user_id], map: "user_id")
}

model users {
  id            Int           @id @default(autoincrement())
  username      String        @unique(map: "username") @db.VarChar(255)
  email         String        @unique(map: "email") @db.VarChar(255)
  password_hash String        @db.VarChar(255)
  current_cart  current_cart?
  orders        orders[]
}
```

# スキーマファイルから「テーブルのデータをマッピングするクラス」を生成するコードを書く

やることは以下の通りです。  

- prisma/scala-generator.jsを書く
    - ここのファイル名はなんでもいいです
- prisma/schema.prismaにgeneratorブロックを書く

## prisma/scala-generator.jsを書く

ts-nodeを使ったり、tscでコンパイルするなどすればTypeScriptでもかけますが、今回は簡単にするべくJavaScriptで記載しています。  
ここは頑張って生成するだけっちゃだけですね(それがめんどくさいというのですが)。  

```js
const { writeFileSync, mkdirSync } = require("fs");
const path = require("path");
const { generatorHandler } = require("@prisma/generator-helper");

generatorHandler({
  onManifest: () => ({}),

  onGenerate: async (options) => {
    console.log("Prisma Custom Generator: Running...");

    const outputDir = options.generator.output.value;
    mkdirSync(outputDir, { recursive: true });

    for (const model of options.dmmf.datamodel.models) {
      const className = toPascalCase(model.name);
      const fileName = className + ".scala";

      const fields = model.fields.map((field) => {
        const f = toCamelCase(field.name);
        return `    ${f}: ${
          mapPrismaTypeToScala(field.type, field.isRequired)
        }`;
      }).join(",\n");

      const scalaClass = `
package com.example

case class ${className}(
${fields}
)`;

      const filePath = path.join(outputDir, fileName);
      writeFileSync(filePath, scalaClass);
      console.log(`Generated: ${filePath}`);
    }
  },
});

function mapPrismaTypeToScala(prismaType, isRequired) {
  const typeMapping = {
    Int: "Int",
    String: "String",
    Boolean: "Boolean",
    DateTime: "java.time.LocalDateTime",
    Float: "Double",
    Decimal: "BigDecimal",
  };

  const scalaType = typeMapping[prismaType] || "String";
  return isRequired ? scalaType : `Option[${scalaType}]`;
}

function toPascalCase(str) {
  return str
    .replace(/[_\s]+(.)?/g, (_, c) => c ? c.toUpperCase() : "")
    .replace(/^./, (m) => m.toUpperCase());
}

function toCamelCase(str) {
  return str
    .replace(/[_\s]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ""))
    .replace(/^./, (m) => m.toLowerCase());
}
```

## prisma/schema.prismaにgeneratorブロックを書く

既に上の方で書いてしまっていましたが、prisma/schema.prismaにgeneratorブロックを追加します。  
これで準備は万端なはずです。  

```prisma
generator scala {
  provider = "node ./prisma/scala-generator.js"
  output   = "../dist"
}
```


# 「テーブルデータをマッピングするクラス」を生成してみる

やることはprisma generateを実行するだけです。  

## prisma generateを実行する

```
./node_modules/.bin/prisma generate
Environment variables loaded from .env
Prisma schema loaded from prisma/schema.prisma
Prisma Custom Generator: Running...
Generated: /path/to/prisma-generate-scala/dist/CurrentCart.scala
Generated: /path/to/prisma-generate-scala/dist/Items.scala
Generated: /path/to/prisma-generate-scala/dist/OrderedItems.scala
Generated: /path/to/prisma-generate-scala/dist/Orders.scala
Generated: /path/to/prisma-generate-scala/dist/Users.scala

✔ Generated node ./prisma/scala-generator.js to ./dist in 27ms
```

結果としていくつかファイルを生成できました。  
サンプルとしてUsers.scalaを見てみると以下の通りになっています。  

```scala

package com.example

case class Users(
    id: Int,
    username: String,
    email: String,
    passwordHash: String,
    currentCart: Option[String],
    orders: String
)
```

# まとめ

- 既存DBからテーブル定義を作れて便利
- 独自のテーブル定義から任意のコードを生成できるのでJavaScript/TypeScript以外のプロジェクトでも採用できて便利

# 参考

- https://speakerdeck.com/hoto17296/orm-toxiang-kihe-u
