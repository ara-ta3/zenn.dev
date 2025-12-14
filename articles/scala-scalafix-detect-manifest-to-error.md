---
title: "Scala 2.13でscalafix Semantic Ruleを使いManifest使用を検知する"
emoji: "😎"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["scala", "scalafix", "json4s", "scala3"]
published: false
---

## はじめに

Scala 2.13 プロジェクトで json4s を使っているんですが、ライブラリを使う部分で `Manifest` に依存している部分があり、それを機械的に検知したくなりました。  
grep などでも一定の範囲では出来ますが、コード全体で確かに全てを解消できたかの保証が欲しいと感じ、 **scalafix カスタム Rule** で検知することにしました。  
今回はそのカスタムルールをプロジェクトに取り入れてコマンドでエラーに落とすところまでの流れをサンプルコードと共に示すのがゴールです。

書いたコードはこちらに置きました。

https://github.com/ara-ta3/scala-validate-manifest-sample

すぐ試すなら以下の 2 コマンドです。
2 本目のコマンドで Manifest 検出のエラーが出ます。

```bash
sbt example/compile
sbt "example/scalafix --check"
```

## 検証リポジトリの構成

構成は次のとおりです。

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

設定で触るファイルは主に次の 4 つです。

- `project/plugins.sbt`: sbt-scalafix プラグインを入れる
- `build.sbt`: semanticdb 有効化とルール jar を classpath に載せる設定
- `.scalafix.conf`: 使うルールを宣言
- `rules/src/main/scala/fix/NoManifestRule.scala`: ルール実装本体

### 対象コード

サンプルコードとして json4s で String を extract する関数を用意しました。  
以下に対して scalafix を実行し検知することをゴールとします。

```scala
import org.json4s._
import org.json4s.jackson.JsonMethods._
import scala.reflect.Manifest

object Json4sExample {
  implicit val formats: Formats = DefaultFormats

  def decode[A](json: String)(implicit mf: Manifest[A]): A =
    parse(json).extract[A]

  def main(args: Array[String]): Unit = {
    val json = """{"name":"example","value":1}"""
    val result = decode[Map[String, Any]](json)
    println(result)
  }
}
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

ルートの `.scalafix.conf` でルールを有効化しています。

```hocon
rules = [
  NoManifestRule
]
```

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

このルールは「文字列」ではなく「シンボル」で判定することで、alias や implicit 経由でも確実に拾う、という意図です。

---

## 動かし方

以下のコマンドで走らせます。

```bash
sbt example/compile
sbt "example/scalafix --check"
```

2 つ目のコマンドで `NoManifest` の Diagnostic が出て失敗する想定です。出力イメージ:

```
sbt:root> example/scalafix
[info] Running scalafix on 1 Scala sources
[error] /path/to/github.com/ara-ta3/scala-validate-manifest-sample/example/src/main/scala/Json4sExample.scala:3:22: error: [NoManifestRule.NoManifest] scala.reflect.Manifest の使用は禁止されています。
[error] import scala.reflect.Manifest
[error]                      ^^^^^^^^
[error] /path/to/github.com/ara-ta3/scala-validate-manifest-sample/example/src/main/scala/Json4sExample.scala:8:44: error: [NoManifestRule.NoManifest] scala.reflect.Manifest の使用は禁止されています。
[error]   def decode[A](json: String)(implicit mf: Manifest[A]): A =
[error]                                            ^^^^^^^^
[error] (example / Compile / scalafix) scalafix.sbt.ScalafixFailed: LinterError
[error] Total time: 0 s, completed 2025/12/14 14:05:33
```

これで **ローカルで Manifest が混入した瞬間にコンパイルを落とす** 仕組みができました。
Manifest を消す（`import scala.reflect.Manifest` を削除し、`ClassTag` に書き換えるなど）と、そのまま `scalafix --check` が通るようになります。落ちる/通るの差分をすぐ確認できます。

:::message
semanticdb を使わない場合の余談

- `sbt example/scalafix --check` を semanticdb 無効のまま実行すると、`MissingSemanticDBError: SemanticDB not found; compile with -Yrangepos and semanticdb` と言われて止まります。
- 仮に semanticdb を使わず AST だけでマッチすると、`import scala.reflect.{ Manifest => M }` の alias や implicit parameter 経由の `Manifest` を検知できません。

「漏れなく検知してビルドを落とす」用途では semanticdb 前提の Semantic Rule が現実的です。
:::

---

## まとめ

semanticdb + scalafix の Semantic Rule で、import alias/implicit 経由でも `Manifest` を検知出来るようになりました。  
Scala3 移行のために機械的に検出したい際に使えると良いなと思います。  
また、scalafix のカスタムルールを作るのも容易だったので、何かしら禁止にしたいことや Scala3 移行で困ることがあれば使っていきたいなと思いました。
