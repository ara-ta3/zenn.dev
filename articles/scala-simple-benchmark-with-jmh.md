---
title: "ScalaでJMHを使ってシンプルにベンチマークを取る"
emoji: "⏱️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "JMH", "Benchmark"]
published: false
---

# はじめに

Scala で定番のマイクロベンチマークツール JMH を試したときのメモです。  
`sbt-jmh` を使うと sbt からベンチマークを測るコマンドが使えるので便利でした。

https://github.com/openjdk/jmh

https://github.com/sbt/sbt-jmh

今回利用したコードは以下の Repository に置いてあります。

https://github.com/ara-ta3/scala-jmh-getting-started

# 1. sbt-jmh の準備

`project/plugins.sbt` にプラグインを追加します。

```scala
// project/plugins.sbt
addSbtPlugin("pl.project13.scala" % "sbt-jmh" % "0.4.8")
```

`build.sbt` は以下のようにしました。`enablePlugins(JmhPlugin)` を付けるだけで JMH 用の設定が入ります。

```scala
// build.sbt
ThisBuild / scalaVersion := "3.3.7"

lazy val root = (project in file("."))
  .enablePlugins(JmhPlugin)
  .settings(
    name := "scala-jmh-sample",
    organization := "com.example",
    Test / fork := true,
    // ベンチマーク用のソースを src/bench/scala に置く
    Jmh / unmanagedSourceDirectories += baseDirectory.value / "src" / "bench" / "scala"
  )
```

`Test / fork := true` は、テスト（および test タスクにぶら下がるプラグイン動作）を sbt 本体とは別 JVM で実行する設定です。テスト実行時のクラスパス汚染や JVM オプションの影響が sbt セッションに漏れないので、特にベンチマークのように GC 設定やヒープサイズを変えたいときに便利という理解でいます。
今回はソースコードとは別に bench というディレクトリを作成し、そこにベンチマークのコードを書くことにしました。  
そのため、 `Jmh / unmanagedSourceDirectories += baseDirectory.value / "src" / "bench" / "scala"` という記述を追加しています。

# 2. 実装サンプルコードとベンチマーク計測用の記述を書く

プロダクション側はベンチマーク非依存にして、JMH のアノテーションはベンチマーク用クラスだけに閉じ込めます。  
フィボナッチを素直に再帰で計算する `SimpleFibonacci`（implementation1）、末尾再帰でスタックを使わない `TailrecFibonacci`（implementation2）、キャッシュで計算済みを再利用する `CachedFibonacci`（implementation3）の 3 パターンを用意しました。

```scala
// src/main/scala/example/Fibonacci.scala
package example

import scala.collection.mutable
import scala.annotation.tailrec

object SimpleFibonacci {
  def calculate(n: Int): Long = {
    if (n <= 1) n else calculate(n - 1) + calculate(n - 2)
  }
}

object TailrecFibonacci {
  def calculate(n: Int): Long = {
    @tailrec
    def loop(remaining: Int, a: Long, b: Long): Long = {
      if (remaining == 0) a else loop(remaining - 1, b, a + b)
    }
    loop(n, 0L, 1L)
  }
}

final class CachedFibonacci(cache: mutable.Map[Int, Long] = mutable.Map(0 -> 0L, 1 -> 1L)) {
  def calculate(n: Int): Long = {
    cache.getOrElseUpdate(n, calculate(n - 1) + calculate(n - 2))
  }
}
```

JMH 側のクラスでだけアノテーションを付け、プロダクションコードには一切 JMH 依存を入れません。`@Param` で入力サイズを変え、`@Setup(Level.Iteration)` で毎イテレーションごとに新しいキャッシュを作っています。

```scala
// src/bench/scala/example/FibonacciBenchmark.scala
package example

import java.util.concurrent.TimeUnit
import org.openjdk.jmh.annotations.*
import org.openjdk.jmh.infra.Blackhole

@State(Scope.Benchmark)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@BenchmarkMode(Array(Mode.AverageTime))
class FibonacciBenchmark {
  @Param(Array("20", "30", "35"))
  var n: Int = _

  private var cached: CachedFibonacci = _

  @Setup(Level.Iteration)
  def setup(): Unit = {
    cached = new CachedFibonacci()
  }

  @Benchmark
  def implementation1(blackhole: Blackhole): Unit = {
    blackhole.consume(SimpleFibonacci.calculate(n))
  }

  @Benchmark
  def implementation2(blackhole: Blackhole): Unit = {
    blackhole.consume(TailrecFibonacci.calculate(n))
  }

  @Benchmark
  def implementation3(blackhole: Blackhole): Unit = {
    blackhole.consume(cached.calculate(n))
  }
}
```

# 3. 実行してみる

`jmh:run` でベンチマークを実行できます。フィルタを付けると対象を絞れます。

```bash
sbt "jmh:run -i 3 -wi 1 -f1 -t1 .*FibonacciBenchmark.*"
```

- `-i 3`: 本計測のイテレーション数
- `-wi 1`: ウォームアップ回数
- `-f1`: fork の回数
- `-t1`: スレッド数

手元ではこんな結果になりました（数字は環境によります）。

```
Benchmark                              Mode  Cnt        Score        Error  Units
FibonacciBenchmark.implementation1     avgt    5  1200000.000 ±  15000.000  ns/op
FibonacciBenchmark.implementation2     avgt    5       50.000 ±      2.000  ns/op
FibonacciBenchmark.implementation3     avgt    5        8.000 ±      0.200  ns/op
```

`implementation1`（素朴再帰）は指数的に時間が伸び、`implementation2`（末尾再帰）は線形になって大幅に改善し、`implementation3`（キャッシュあり）はさらに速い、という差が見えます。

# 4. 小ネタ

- `jmh:compile` で事前に JMH のコード生成だけ行い、後で `jmh:runMain` で実行することも可能
- `Jmh / javaOptions += "-Xmx2g"` のように、計測用の JVM オプションを個別に付けられる
- Scala 3 でも sbt-jmh がそのまま使えるので、Kotlin/Java のコードと混ぜて比較するときに便利

# 5. まとめ

- sbt-jmh を入れると sbt からすぐベンチマークを回せる
- `Blackhole` で最適化を防ぐのが鉄則
- `-i` や `-wi` を調整して、手元の環境で安定する回数を見つけると良さそう
