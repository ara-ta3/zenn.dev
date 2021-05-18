---
title: "Scala Meterを使ってScalaコードのベンチマークを測る"
emoji: "⛳"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "Benchmark"]
published: false
---

Scala のベンチマークツールの ScalaMeter を使ってみたので、メモがてらの紹介です。

ScalaMeter はこちら
https://scalameter.github.io/

今回使用したコードはここにあります。
https://github.com/ara-ta3/scalameter-getting-started

# 1. build.sbt の準備

まずは準備に build.sbt を用意します。  
sbt のバージョンは 1.5.2。Scala は 2.13.6 を使いました。  
commonSettings はよく使ってるやつを持ってきただけなので、特段意図はありません。  
設定は root の変数のほうがメインです。

TODO:

- resolver の追加について
  - https://scalameter.github.io/home/gettingstarted/0.7/sbt/index.html
- parallelExecution in Test := false について
  - 分けるために Bench っての作った
  - 参考 https://github.com/scalameter/scalameter-examples/blob/master/basic-with-separate-config/build.sbt
- testFrameworks += new TestFramework("org.scalameter.ScalaMeterFramework")
- logBuffered
  - https://www.scala-sbt.org/1.x/docs/Testing.html これらしいな

```scala
val commonSettings = Seq(
  version := "0.1-SNAPSHOT",
  scalaVersion := "2.13.6",
  scalacOptions ++= Seq(
    "-deprecation",
    "-feature",
    "-unchecked",
    "-language:implicitConversions",
    "-Xlint",
    "-Xfatal-warnings",
    "-Ywarn-numeric-widen",
    "-Ywarn-unused",
    "-Ywarn-unused:imports",
    "-Ywarn-value-discard",
  )
)

lazy val Benchmark = config("bench") extend Test
lazy val root = (project in file("."))
  .settings(commonSettings)
  .settings(
      name := "scalameter-getting-started",
      libraryDependencies ++= Seq(
          "com.storm-enroute" %% "scalameter" % "0.19" % "bench",
          "org.scalatest" %% "scalatest"   % "3.1.1" % "test",
          ),
      resolvers ++= Seq(
          "Sonatype OSS Snapshots" at "https://oss.sonatype.org/content/repositories/snapshots",
          "Sonatype OSS Releases" at "https://oss.sonatype.org/content/repositories/releases"
      ),
      testFrameworks += new TestFramework("org.scalameter.ScalaMeterFramework")

  ).configs(Benchmark).settings(inConfig(Benchmark)(Defaults.testSettings): _*)
```

# 2. Hello Scala Meter

# 3. フィボナッチ数列の ScalaMeter

こんなコードを書いてみました。  
末尾再帰のコードと素直に書いた一般的なフィボナッチ数列のコードです。

src/main/scala/com/ru/waka/App.scala

```scala
package com.ru.waka

object App {
  def fibonacciTailrec(n: Int): Int = {

    @scala.annotation.tailrec
    def loop(n: Int, a1: Int = 0, a2: Int = 1): Int =
      if (n <= 0) a1
      else loop(n-1, a2, a1 + a2)
    loop(n)
  }

  def fibonacci(n: Int): Int =
    if (n <= 0) 0
    else if (n == 1 || n == 2) 1
    else fibonacci(n - 1) + fibonacci(n - 2)
}
```

これに対し、ベンチマークを書いたコードがこちらになります。

src/bench/scala/com/ru/waka/AppBenchmark.scala

```scala
package com.ru.waka

import org.scalameter.api._

object AppBenchmark extends Bench.LocalTime {
  val sizes: Gen[Int] = Gen.range("sizes")(10, 40, 10)

  performance of "N" in  {
    measure method "fibonacci" in {
      using(sizes) in { x => App.fibonacciTailrec(x) }
    }
    measure method "fibonacciSlow" in {
      using(sizes) in { x => App.fibonacci(x) }
    }
  }
}
```

# 4. 感想&まとめ
