---
title: "OpenAPI generatorでTypeScriptとScalaのコードを生成してデータのやりとりをする"
emoji: "💨"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["openapi", "swagger", "scala", "typescript", "scalatra"]
published: false
---

https://github.com/ara-ta3/api-scheme-definiton-getting-started

# フロントエンドのTypeScriptのコードを自動生成する

- 特に困らなかった
- 生成したコードをすべてコミットするかは少し悩んだ

# バックエンドのScalaのコードを自動生成する

- sbtのpluginの話
- projectを分けた
- modelのみで良いのでmodelを持ってきた
    - それ以外はignoreで生成しないようにした
    - openApiIgnoreFileOverrideがそれ
- package名の設定
    - modelとapiなどで異なる設定名なので注意
- configでも設定できた
    - が、build.sbtにまとめて分かれていないほうが好みだったのでやめた

```sbt
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

## 困ったこと

- 2.13を使っている時の挙動
- https://repo1.maven.org/maven2/openapi/openapi_2.13/0.1.0-SNAPSHOT/openapi_2.13-0.1.0-SNAPSHOT.pom

↓で怒られる

```
[error]   not found: /path/to/home/.ivy2/localopenapi/openapi_2.13/0.1.0-SNAPSHOT/ivys/ivy.xml
[error]   not found: https://repo1.maven.org/maven2/openapi/openapi_2.13/0.1.0-SNAPSHOT/openapi_2.13-0.1.0-SNAPSHOT.pom
```

- excludeを設定した



# 参考

- https://github.com/softwaremill/sttp-openapi-example/tree/master
