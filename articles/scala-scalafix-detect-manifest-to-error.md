---
title: "Scala 2.13でscalafix Semantic Ruleを使いManifest使用を検知する"
emoji: "😎"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["scala", "scalafix", "json4s", "scala3"]
published: false
---

## この記事でやること

- Scala 2.13 プロジェクトで `Manifest` / `ClassManifest` を **scalafix カスタム Semantic Rule** で検知して落とす
- import alias や implicit 経由の利用も取りこぼさない
- 検証用リポジトリ（<https://github.com/ara-ta3/scala-validate-manifest-sample>）のコードをベースに解説

CI を使わず、まずはローカルで確実に落ちるところまでをゴールにします。

---

## 背景

歴史の長いコードや `json4s` でシリアライズを書いたコードには、いまだに `scala.reflect.Manifest` / `ClassManifest` が残っていることがあります。

- Scala 3 では非推奨（削除方向）
- `ClassTag` / `TypeTag` への移行を妨げる
- grep や目視レビューでは alias/implicit に埋もれて見落としがち

このため、**ツールで確実に検知しビルドを失敗させたい**というニーズがあります。

---

## なぜ単純検索では見逃すのか

```scala
import scala.reflect.{ Manifest => M }

def decode[A: M](json: String) = ???
```

表面上は `Manifest` という単語が消えています。`Type.Name("Manifest")` の AST マッチや grep ではすり抜けます。  
「それが本当に `scala.reflect.Manifest` か」を import 解決後のシンボルで判定する必要があります。

ここで semanticdb（型・シンボル情報付きのデータベース）を出力し、scalafix の **Semantic Rule** でシンボルマッチを行います。

---

## 検証リポジトリの構成

<https://github.com/ara-ta3/scala-validate-manifest-sample> をそのまま使います。構成は次のとおりです。

```
.
├─ project/plugins.sbt      # sbt-scalafix 0.14.4
├─ build.sbt                # semanticdb とルールの classpath 設定
├─ .scalafix.conf           # ルール有効化
├─ rules/                   # カスタムルール本体
│   └─ src/main/scala/fix/NoManifestRule.scala
└─ example/                 # ルールを当てるサンプル（json4s）
    └─ src/main/scala/Json4sExample.scala
```

### プラグインとビルド設定

`project/plugins.sbt`

```scala
addSbtPlugin("ch.epfl.scala" % "sbt-scalafix" % "0.14.4")
```

`build.sbt`（ポイントのみ抜粋）

```scala
ThisBuild / scalaVersion := "2.13.18"

lazy val rules = project.in(file("rules")).settings(
  libraryDependencies += "ch.epfl.scala" %% "scalafix-core" % "0.14.4"
)

lazy val example = project.in(file("example")).settings(
  semanticdbEnabled := true,
  semanticdbVersion := scalafixSemanticdb.revision,
  scalacOptions += "-Yrangepos",
  libraryDependencies += "org.json4s" %% "json4s-jackson" % "4.0.7",
  scalafixDependencies += {
    val jar = (rules / crossTarget).value / s"${(rules / moduleName).value}_${scalaBinaryVersion.value}-${version.value}.jar"
    ("local" %% "no-manifest-rule" % version.value).intransitive().from(jar.toURI.toString)
  },
  // scalafix 実行前にルール jar を自動ビルド
  Compile / scalafix := (Compile / scalafix).dependsOn(rules / Compile / packageBin).evaluated,
  Test    / scalafix := (Test    / scalafix).dependsOn(rules / Compile / packageBin).evaluated
)
```

- `semanticdbEnabled` と `semanticdbVersion` で semantic 情報を出力
- `scalafixDependencies` で、ローカルでビルドしたルール jar を classpath に載せる
- `Compile / scalafix := ...dependsOn(packageBin)` で、`sbt example/scalafix` 実行時にルールが自動ビルドされる

### カスタムルール本体

`rules/src/main/scala/fix/NoManifestRule.scala`

```scala
package fix

import scalafix.v1._
import scala.meta._

class NoManifestRule extends SemanticRule("NoManifestRule") {
  private val forbidden = List(
    SymbolMatcher.normalized("scala.reflect.Manifest#"),
    SymbolMatcher.normalized("scala.reflect.Manifest."),
    SymbolMatcher.normalized("scala.reflect.ClassManifest#"),
    SymbolMatcher.normalized("scala.reflect.ClassManifest.")
  )

  override def fix(implicit doc: SemanticDocument): Patch =
    doc.tree.collect {
      case name: Name if isForbidden(name) =>
        Patch.lint(
          Diagnostic(
            id = "NoManifest",
            message = s"scala.reflect.${name.value} の使用は禁止されています。",
            position = name.pos
          )
        )
    }.asPatch

  private def isForbidden(name: Name)(implicit doc: SemanticDocument): Boolean =
    name.symbol match {
      case Symbol.None => false
      case sym         => forbidden.exists(_.matches(sym))
    }
}
```

`SymbolMatcher.normalized` で import alias 後のシンボルに対しても確実にマッチさせています。`Patch.lint` を返すことで、検知した瞬間に scalafix が失敗します。

### ルール対象のサンプルコード

`example/src/main/scala/Json4sExample.scala`

```scala
import org.json4s._
import org.json4s.jackson.JsonMethods._
import scala.reflect.Manifest

object Json4sExample {
  implicit val formats: Formats = DefaultFormats

  def decode[A](json: String)(implicit mf: Manifest[A]): A =
    parse(json).extract[A]
}
```

json4s の `extract` に `Manifest` を要求する典型的なケースをあえて残しています。

---

## 動かし方

SemanticDB を出力してから scalafix を `--check` で走らせます。

```bash
sbt example/compile
sbt "example/scalafix --check"
```

2 つ目のコマンドで `NoManifest` の Diagnostic が出て失敗する想定です。出力イメージ:

```
[error] example/src/main/scala/Json4sExample.scala:5:24: NoManifest: scala.reflect.Manifest の使用は禁止されています。
[error] import scala.reflect.Manifest
[error]                        ^
[error] (example / Compile / scalafix) scalafix.sbt.ScalafixFailed: Lint warnings were found
```

これで **ローカルで Manifest が混入した瞬間にコンパイルを落とす** 仕組みが完成します。CI に載せる場合も、同じ `sbt example/scalafix --check` をジョブに追加するだけです。

---

## まとめと拡張アイデア

- semanticdb + scalafix の Semantic Rule で、import alias/implicit 経由でも `Manifest` / `ClassManifest` を確実に検知できる
- ルール jar を自動ビルドする設定にしておくと、ルールの配置を意識せずに使える
- `scalafixOnCompile := true` を足せば通常の `compile` でも即落とせる
- 自動修正したい場合は `Patch.replaceTree` などで `ClassTag` へ書き換えるルールに発展させられる
