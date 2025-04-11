---
title: "ScalaTestのtaggedAsでmultiarg infix syntax ... deprecatedという警告が出る"
emoji: "👏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["scala", "scalatest", "scala3"]
published: true
---

タイトルの長さが70文字らしいので適度に省略してしまったのですが、ScalaTest実行時に警告が出て、調べたときの備忘録です。  
Scalaは2.13.13  
ScalaTestは3.2.18  
scalacOptionsに-Xlintを入れています。  

この状態で以下のようなコードのテストを実行すると `multiarg infix syntax looks like a tuple and will be deprecate` という警告が出ます。  

```scala
import org.scalatest.Tag
import org.scalatest.freespec.AnyFreeSpec

object CustomTag1 extends Tag("CustomTag1")
object CustomTag2 extends Tag("CustomTag2")

class TaggedAsSpec extends AnyFreeSpec {
  "taggedAs の書き方" - {
    "警告が出る書き方" taggedAs (CustomTag1, CustomTag2) in {
      assert(1+1 == 2)
    }
  }
}
```

build.sbtやコードの構成は以下の通りです。  

```zsh
tree -I project -I target
.
├── build.sbt
└── src
    └── test
        └── scala
            └── TaggedAsSpec.scala
```

build.sbt  

```sbt
ThisBuild / scalaVersion := "2.13.13"

lazy val root = (project in file("."))
.settings(
    name := "tagged-as-warning-sample",
    scalacOptions ++= Seq(
      "-Xlint",
      ),
    libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.18" % Test
    )
```

# 結論 .taggedAs(A, B)を使う

x op yのように空白を入れたメソッド呼び出し(infix operatorと言います)を使わず、.で呼び出す形(.taggedAs(A, B))にすると警告は起きません。  

```scala
import org.scalatest.Tag
import org.scalatest.freespec.AnyFreeSpec

object CustomTag1 extends Tag("CustomTag1")
object CustomTag2 extends Tag("CustomTag2")

class TaggedAsSpec extends AnyFreeSpec {
  "taggedAs の書き方" - {
    "警告が出る書き方" taggedAs (CustomTag1, CustomTag2) in {
      assert(1+1 == 2)
    }

    "警告が出ない書き方".taggedAs(CustomTag1, CustomTag2) in {
      assert(1+1 == 2)
    }
  }
}
```

# 実際の警告と補足

```
[warn] /path/to/tagged-as-warnings/src/test/scala/TaggedAsSpec.scala:9:16: multiarg infix syntax looks like a tuple and will be deprecate
[warn]     "警告が出る書き方" taggedAs (CustomTag1, CustomTag2) in {
[warn]                ^
[warn] one warning found
[info] TaggedAsSpec:
[info] taggedAs の書き方
[info] - 警告が出る書き方
[info] Run completed in 28 milliseconds.
[info] Total number of tests run: 1
[info] Suites: completed 1, aborted 0
[info] Tests: succeeded 1, failed 0, canceled 0, ignored 0, pending 0
[info] All tests passed.
```

ここで `"警告が出る書き方" taggedAs (CustomTag1, CustomTag2)` としているとinfix operatorによるメソッド呼び出しになっており、  
この引数が複数になる場合Scala3では禁止する方向性なため、Scala2.13では警告が出るようになったというのが理由でした。  
したがって、infix operatorではなく`"警告が出ない書き方".taggedAs(CustomTag1, CustomTag2)`のように.を用いて呼ぶようにすれば警告は出なくなるということになります。  


# 背景など

Scalaでは(2, 3関わらず)x op yのように.を使わずにメソッドを呼び出すのをinfix operatorと呼ばれる書き方が出来ますが、  
Scala3では複数引数の場合、つまりmultiarg infix記法は禁止する方針になったようです。  
autotuplingとmultiarg infixで書かれたものが曖昧でわかりづらいためautotuplingは廃止、multiarg infixは禁止（？）という方向性になったという理解を私はしています。  

https://contributors.scala-lang.org/t/multiarg-infix-application-considered-warty/4490

autotuplingも廃止の方向性がありそうでしたが、残す方向性になったようです。  
https://contributors.scala-lang.org/t/lets-drop-auto-tupling/1799/24

最終的にScala3でinfixで書きたい場合は明示的にinfixと書くようになったみたいです。  
https://docs.scala-lang.org/scala3/reference/changed-features/operators.html


