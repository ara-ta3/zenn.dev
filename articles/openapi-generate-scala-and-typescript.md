---
title: "OpenAPI generatorでTypeScriptとScalaのコードを生成してデータのやりとりをする"
emoji: "💨"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["openapi", "swagger", "scala", "typescript", "scalatra"]
published: true
---

# 概要

OpenAPIでSwaggerを使ってドキュメントは書いているのですが、自動生成までは試したことがなく、一度向き合ってみるかと思って試してみました。  
フロントエンドは特に何も考えずTypeScript React、バックエンドにはScalaのマイクロフレームワークのScalatraを使っています。  
(本当はKotlin Ktorをバックエンドにしようと思ったんですが、gradleにハマっているのかopenapi generatorにハマっているのかわからなかったので、それなりに書けるScalaにしたという背景があります。  
API経由でデータのやり取りをする以外にReactやScalatra固有の何かは特段使っていません。  

検証したコードはこちら  

https://github.com/ara-ta3/api-scheme-definiton-getting-started

おおよそのやっていることはこんなイメージです。  
(mermaidちょっと書きたかっただけな気持ちはある  

```mermaid
graph LR
    A[openapi.yml] --> B[sbt-openapi-generator]
    B --> C[backend/openapi-generated/src]
    D[scalatra backend/src] -->|利用| C 

    A --> E[@openapitools/openapi-generator-cli]
    E --> F[frontend/src/openapi]
    H[frontend/src/Hooks.ts] -->|利用| F 

    D <--> |Web APIを叩く| H

    subgraph TypeScript
        E
        F
        H
    end
    subgraph Scala
        B
        C
        D
    end

```

# 1. 準備

とりあえず雑にGETとPOSTのエンドポイントを用意したopenapiのyamlファイルを用意します。  
めんどくさかったのでそれっぽいものをchagptに生成してもらっています。  

```yml
openapi: 3.0.1
info:
  title: User API
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: Get all users
      responses:
        '200':
          description: A list of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Add a new user
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '200':
          description: The created user
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
          example: 1
        name:
          type: string
          example: Foo
        email:
          type: string
          example: foo@example.com
      required:
        - id
        - name
        - email
    CreateUser:
      type: object
      properties:
        name:
          type: string
          example: Alice
        email:
          type: string
          example: alice@example.com
      required:
        - name
        - email

```

# 2. フロントエンドのTypeScriptのコードを自動生成する

## @openapitools/openapi-generator-cliの設定

とりあえずopenapi-generatorのwrapperらしい `@openapitools/openapi-generator-cli` を利用します。  
こっちは特にハマるところもなくフロントエンドのコードが生成されました。  

```zsh
$cd path/to/frontend
$npx openapi-generator-cli generate -i ../openapi.yml -g typescript-fetch -o src/openapi
```

## 出力されたコード

```zsh
$tree src/openapi                                                                                                                                                                                                                               main
src/openapi
├── apis
│   ├── DefaultApi.ts
│   └── index.ts
├── index.ts
├── models
│   ├── CreateUser.ts
│   ├── User.ts
│   └── index.ts
└── runtime.ts

3 directories, 7 files
```

## Hooksから利用するコード

これを元にHooksの実装など外部との遣り取りをする役割のコードでクライアントコードを利用します。  

frontend/src/Hooks.ts

```ts
import { useState } from "react";
import { Configuration, DefaultApi } from "./openapi";

interface User {
    id: number;
    name: string;
    email: string;
};

const apiClient = new DefaultApi(
    new Configuration(
        {
            basePath: "http://localhost:8080"
        }
    )
);

export const useFetchUsers = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const fetchUsers = async () => {
        setLoading(true);
        setError(null);

        try {
            const users = await apiClient.apiUsersGet();
            setUsers(users);
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setLoading(false);
        }
    };

    return { users, loading, error, fetchUsers };
};
```

ボタンを押したらなんか取ってきてもらいましょう。  

frontend/src/App.ts

```ts
import React, { useState } from "react";

import { useFetchUsers } from "./Hooks";

const App: React.FC = () => {
  const { users, loading, error, fetchUsers } = useFetchUsers();
  return (
    <div>
      <button onClick={fetchUsers}>Fetch Users</button>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <ul>
        {users.map((user) => <li key={user.id}>{user.name} ({user.email})</li>)}
      </ul>
    </div>
  );
};

export default App;
```

frontend/src/index.ts

```ts
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

これでバックエンドがlocalhost:8080で起動していればデータを取得できます。  

# 3. バックエンドのScalaのコードを自動生成する

## sbt-openapi-generatorとbuild.sbtの設定

sbt-openapi-generatorというのがあって、3 weeks agoにもリリースがあったのでメンテされそうと思ってこれを使いました。  

https://github.com/OpenAPITools/sbt-openapi-generator

一つのプロジェクトに混在させることも可能ですが、分かれていたほうが触ってもいいか触らないほうがいいかがわかりやすいと思うので、プロジェクトを分ける設定にしました。  

backend/build.sbt

```scala
lazy val openapi = project.in(file("openapi-generated"))
  .enablePlugins(OpenApiGeneratorPlugin)
  .settings(
    scalaVersion := ScalaVersion,
    openApiGeneratorName := "scalatra",
    openApiOutputDir := "openapi-generated",
    openApiInputSpec := "../openapi.yml",
    openApiModelPackage := "com.example.api.model",
    openApiValidateSpec := SettingDisabled,
    openApiGenerateModelTests := SettingEnabled,
    openApiIgnoreFileOverride := "./openapi-ignore-file",
  )
```

### 設定について

#### openApiConfigFile による設定内容の別ファイルへの出力

この設定は `openApiConfigFile := "config.yaml"` のようにyaml形式のファイルに書いたうえでそのパスを指定することも可能です。  
が、分ける理由も特にないかなと思って分けていません。  

#### openApiIgnoreFileOverride と openapi-ignore-file

生成するコマンドを何も設定せずに実行するとプロジェクトを丸ごと出力し、build.sbtも新たに生成されます。  
そのため、 `openapi-ignore-file` というファイルにgitignoreのような記述を追加し、 `openApiIgnoreFileOverride` で指定してコードのみを出力するようにしました。  
コードも、Request/Responseをbindできるcase classのみで良いかと思いmodelのクラスのみを出力しています。  

backend/openapi-ignore-file

```ignore
*
**/*
!**/src/main/scala/com/example/api/**/*
```

#### openApiModelPackageによるModelのpackage名変更

Modelのpackage名をデフォルトから変更するべく `openApiModelPackage := "com.example.api.model"` の設定も追加しています。  
余談ですが、 `openApiPackageName` や `openApiApiPackage` の設定項目と間違えていて、Modelのpackageが変わらねぇなってのをしばらく繰り返したりしていたことをここに懺悔します。  

## 出力されたコード

結果として `backend/openapi-generated/src/main/scala/com/example/api/` にコードが生成されました。  

```zsh
$tree openapi-generated/src                                                                                                                                                                                                                     main
openapi-generated/src
└── main
    └── scala
        └── com
            └── example
                └── api
                    └── model
                        ├── CreateUser.scala
                        └── User.scala
```

CreateUser.scala

```scala
/**
 * User API
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 1.0.0
 * Contact: team@openapitools.org
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 */

package com.example.api.model

case class CreateUser(
  name: String,

  email: String

 )
```

User.scala

```scala
/**
 * User API
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 1.0.0
 * Contact: team@openapitools.org
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 */

package com.example.api.model

case class User(
  id: 
Int,

  name: String,

  email: String

 )
```

## Scalatraのプロジェクトから利用するコード

まず利用するべくbuild.sbtにdependsOnの設定をしておきます。  

```scala
lazy val rootProject = project
  .in(file("."))
  .settings(
    scalaVersion := ScalaVersion,
    libraryDependencies ++= Seq(
      "org.scalatra" %% "scalatra-jakarta" % ScalatraVersion,
      "org.scalatra"   %% "scalatra-json-jakarta" % ScalatraVersion,
      "jakarta.servlet" % "jakarta.servlet-api"   % "6.0.0" % "provided",
      "org.json4s" %% "json4s-jackson" % "4.0.6",
      "org.eclipse.jetty" % "jetty-server" % "11.0.15",
      "org.slf4j" % "slf4j-api" % "2.0.9",
      "ch.qos.logback" % "logback-classic" % "1.4.11",

    ),
    excludeDependencies ++= Seq(
      "openapi" % "openapi_3",
      "openapi" % "openapi_2.13"
    )
  )
  .dependsOn(openapi)
```

scalatra-jsonを使っていればcase classをjsonに変えてくれるので、scalatra自体の話は省略します。  
実際のコードはこちらです。  

https://github.com/ara-ta3/api-scheme-definiton-getting-started/blob/main/backend/src/main/scala/com/example/Scalatra.scala


## sbt compile時にopenapiの依存が取得できないと怒られて困った話

これはScalaのバージョンを2.13にしているときのメッセージですが、下記のように怒られてしまいました。  
正直原因がわかってないのですが、アプリケーションコードはopenapiに依存はしていないと思っているので、 `excludeDependencies` に設定を追加して事なきを得ました。  

```
[error]   not found: /path/to/home/.ivy2/localopenapi/openapi_2.13/0.1.0-SNAPSHOT/ivys/ivy.xml
[error]   not found: https://repo1.maven.org/maven2/openapi/openapi_2.13/0.1.0-SNAPSHOT/openapi_2.13-0.1.0-SNAPSHOT.pom
```

backend/build.sbt

```scala
lazy val rootProject = project
  .in(file("."))
  .settings(
    scalaVersion := ScalaVersion,
    libraryDependencies ++= Seq(
      "org.scalatra" %% "scalatra-jakarta" % ScalatraVersion,
      "org.scalatra"   %% "scalatra-json-jakarta" % ScalatraVersion,
      "jakarta.servlet" % "jakarta.servlet-api"   % "6.0.0" % "provided",
      "org.json4s" %% "json4s-jackson" % "4.0.6",
      "org.eclipse.jetty" % "jetty-server" % "11.0.15",
      "org.slf4j" % "slf4j-api" % "2.0.9",
      "ch.qos.logback" % "logback-classic" % "1.4.11",

    ),
    // ↓の部分
    excludeDependencies ++= Seq(
      "openapi" % "openapi_3",
      "openapi" % "openapi_2.13"
    )
  )
  .dependsOn(openapi)
```

Scalaのバージョンが3系統なら `"openapi" % "openapi_3",` を追加しています。  

# まとめ

- openapi.ymlからまずはWebAPIのインタフェースを生成してデータのやり取りをできるようにしました
- もうちょっと使い込むと困りごととか出てくる気はするので使い込みたい

## 参考

- https://github.com/softwaremill/sttp-openapi-example/tree/master
- https://github.com/OpenAPITools/openapi-generator/tree/master/docs/generators
