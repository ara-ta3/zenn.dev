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
resolver はこちらのサンプルのものをそのまま持ってきました。  
https://github.com/scalameter/scalameter-examples/blob/master/basic-with-separate-config/build.sbt

parallelExecution の設定はおそらく同時に実行するとちゃんと計測できないためか false にすべきという感じでした。  
https://scalameter.github.io/home/gettingstarted/0.5/sbt/

ドキュメントの場合、 `parallelExecution in Test := false` となっているのですが、サンプルと同様の形にしていて、Test とは別に Benchmark というものを作ったので `parallelExecution in Benchmark := false` にしています。  
また、これは sbt のバージョンが上がったため、in ではなく/を使えという風に sbt のログが出てしまうので、 `Benchmark / parallelExecution := false` と書くと良さそうです。  
Test として認識させるために設定が必要なみたいなので、 `testFrameworks += new TestFramework("org.scalameter.ScalaMeterFramework")` も追記しています。  
最後に logBuffered ですが、 https://www.scala-sbt.org/1.x/docs/Testing.html ここに説明がありました。  
これが true の場合バッファを持って最後まで持ち続けるらしいのですが、特段メリットもないので false で良さそうです。

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
    "-Ywarn-value-discard"
  )
)

lazy val Benchmark = config("bench") extend Test
lazy val root = (project in file("."))
  .settings(commonSettings)
  .settings(
    name := "scalameter-getting-started",
    libraryDependencies ++= Seq(
      "com.storm-enroute" %% "scalameter" % "0.19" % "bench",
      "org.scalatest" %% "scalatest" % "3.1.1" % "test"
    ),
    resolvers ++= Seq(
      "Sonatype OSS Snapshots" at "https://oss.sonatype.org/content/repositories/snapshots",
      "Sonatype OSS Releases" at "https://oss.sonatype.org/content/repositories/releases"
    ),
    testFrameworks += new TestFramework("org.scalameter.ScalaMeterFramework"),
    Benchmark / parallelExecution := false,
    logBuffered := false
  )
  .configs(Benchmark)
  .settings(inConfig(Benchmark)(Defaults.testSettings): _*)
```

# 2. Hello Scala Meter

Scala Meter にあるサンプルをそのまま持ってきました。
サンプルがこれですね。  
https://scalameter.github.io/home/gettingstarted/0.7/simplemicrobenchmark/index.html

Gen.range というメソッドが用意されていて、そのメソッドを使って 1 から 5 まで 2 ずつ上げて対象のデータを作っています。  
便利ですね。  
それを元に List の map メソッドにかかる時間を計測している感じでした。

src/bench/scala/com/ru/waka/HelloBenchmark.scala

```scala
package com.ru.waka

import org.scalameter.api._

class HelloBenchmark extends Bench.LocalTime {
  val sizes: Gen[Int] = Gen.range("size")(from = 1, upto = 5, hop = 2)

  val ranges: Gen[Range] = for {
    size <- sizes
  } yield 0 until size

  performance of "Range" in {
    measure method "map" in {
      using(ranges) in { r =>
        r.map(_ + 1)
      }
    }
  }
}
```

これを sbt 'Bench/testOnly com.ru.waka.HelloBenchmark' で実行してみるとこんな感じの結果になります。

```bash
sbt 'Bench/testOnly com.ru.waka.HelloBenchmark'
[info] welcome to sbt 1.5.2 (Oracle Corporation Java 15)
[info] loading settings for project global-plugins from plugins.sbt ...
[info] loading global plugins from ...
[info] loading project definition from ...
[info] loading settings for project root from build.sbt ...
[info] set current project to scalameter-getting-started (in build ...)
[info] ::Benchmark Range.map::
[info] cores: 6
[info] hostname: ...
[info] name: Java HotSpot(TM) 64-Bit Server VM
[info] osArch: x86_64
[info] osName: Mac OS X
[info] vendor: Oracle Corporation
[info] version: 15+36-1562
[info] Parameters(size -> 1): 0.001506 ms
[info] Parameters(size -> 3): 0.001847 ms
[info] Parameters(size -> 5): 0.001738 ms
[info] Passed: Total 0, Failed 0, Errors 0, Passed 0
```

size が 1, 3, 5 のときの結果が出ていますね。

# 3. フィボナッチ数列の ScalaMeter

フィボナッチ数列を計算する関数を書いてみました。  
末尾再帰のコードと素直に書いた一般的なフィボナッチ数列のコードです。  
これらをベンチマークにかけてみようかなと思います。

src/main/scala/com/ru/waka/App.scala

```scala
package com.ru.waka

object App {
  def fibonacciTailrec(n: Int): Int = {

    @scala.annotation.tailrec
    def loop(n: Int, a1: Int = 0, a2: Int = 1): Int =
      if (n <= 0) a1
      else loop(n - 1, a2, a1 + a2)
    loop(n)
  }

  def fibonacci(n: Int): Int =
    if (n <= 0) 0
    else if (n == 1 || n == 2) 1
    else fibonacci(n - 1) + fibonacci(n - 2)
}
```

これに対し、ベンチマークを書いたコードがこちらになります。  
今回 Range を作る必要はなく size をそのまま使えば良いのでそれを利用しました。

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

これをコマンドを実行するとこんな感じになります。  
やはり末尾再帰が早いですね。

```bash
sbt 'Bench/testOnly com.ru.waka.AppBenchmark'
[info] welcome to sbt 1.5.2 (Oracle Corporation Java 15)
[info] loading settings for project global-plugins from plugins.sbt ...
[info] loading global plugins from ...
[info] loading project definition from ...
[info] loading settings for project root from build.sbt ...
[info] set current project to scalameter-getting-started (in build ...)
[info] ::Benchmark N.fibonacci::
[info] cores: 6
[info] hostname: ...
[info] name: Java HotSpot(TM) 64-Bit Server VM
[info] osArch: x86_64
[info] osName: Mac OS X
[info] vendor: Oracle Corporation
[info] version: 15+36-1562
[info] Parameters(sizes -> 10): 6.17E-4 ms
[info] Parameters(sizes -> 20): 7.39E-4 ms
[info] Parameters(sizes -> 30): 9.03E-4 ms
[info] Parameters(sizes -> 40): 5.34E-4 ms
[info] ::Benchmark N.fibonacciSlow::
[info] cores: 6
[info] hostname: ...
[info] name: Java HotSpot(TM) 64-Bit Server VM
[info] osArch: x86_64
[info] osName: Mac OS X
[info] vendor: Oracle Corporation
[info] version: 15+36-1562
[info] Parameters(sizes -> 10): 4.48E-4 ms
[info] Parameters(sizes -> 20): 0.020062 ms
[info] Parameters(sizes -> 30): 2.395007 ms
[info] Parameters(sizes -> 40): 298.800213 ms
[info] Passed: Total 0, Failed 0, Errors 0, Passed 0
```

これで同じコードがどれくらいパフォーマンス下がっているかがわかって便利ですね。

# 4. 感想&まとめ

- Scala Meter 雰囲気理解した
- Scala いいぞ〜
- sbt コマンドで実行できるのは便利ですね
