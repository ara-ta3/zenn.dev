---
title: "ScalaでJMHを使ってシンプルにベンチマークを取る"
emoji: "⏱️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "JMH", "Benchmark"]
published: false
---

Scala で定番のマイクロベンチマークツール JMH を試したときのメモです。  
`sbt-jmh` を使うと sbt からそのまま実行でき、Java/Scala どちらのコードも計測できます。

# 1. sbt-jmh の準備

`project/plugins.sbt` にプラグインを追加します。

```scala
// project/plugins.sbt
addSbtPlugin("pl.project13.scala" % "sbt-jmh" % "0.4.6")
```

`build.sbt` はこんな感じにしました。`enablePlugins(JmhPlugin)` を付けるだけで JMH 用の設定が入ります。  
計測時に JVM を分けたい場合は `Jmh / fork := true` を入れておくと安心です。

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

`Test / fork := true` は、テスト（および test タスクにぶら下がるプラグイン動作）を sbt 本体とは別 JVM で実行する設定です。テスト実行時のクラスパス汚染や JVM オプションの影響が sbt セッションに漏れないので、特にベンチマークのように GC 設定やヒープサイズを変えたいときに安全です。

手元で有効になっているか確かめる簡単な方法:

- `sbt "show Test / fork"` で true/false を見る
- `sbt -debug "Test / test"` を流すと、`Forking tests - java ...` のログが出る（false の場合はそのログが出ない）
- さらに PID を確認したい場合は、一時的に `Test / javaOptions += "-Dshow.pid=true"` を入れ、テストコード側で `println(java.lang.management.ManagementFactory.getRuntimeMXBean.getName)` を出力すると、sbt 本体とは別 PID で動いているのが分かる

# 2. ベンチマークを書く

プロダクション側はベンチマーク非依存にして、JMH のアノテーションはベンチマーク用クラスだけに閉じ込めます。  
フィボナッチを素直に再帰で計算する `SimpleFibonacci`（before）と、キャッシュで計算済みを再利用する `CachedFibonacci`（after）を用意しました。

```scala
// src/main/scala/example/Fibonacci.scala
package example

import scala.collection.mutable

object SimpleFibonacci {
  def calculate(n: Int): Long = {
    if (n <= 1) n else calculate(n - 1) + calculate(n - 2)
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
  def before(blackhole: Blackhole): Unit = {
    blackhole.consume(SimpleFibonacci.calculate(n))
  }

  @Benchmark
  def after(blackhole: Blackhole): Unit = {
    blackhole.consume(cached.calculate(n))
  }
}
```

# 3. 実行してみる

`jmh:run` でベンチマークを実行できます。フィルタを付けると対象を絞れます。

```bash
sbt "jmh:run -i 5 -wi 3 -f1 -t1 .*FibonacciBenchmark.*"
```

- `-i 5`: 本計測のイテレーション数  
- `-wi 3`: ウォームアップ回数  
- `-f1`: fork の回数  
- `-t1`: スレッド数  

手元ではこんな結果になりました（数字は環境によります）。

```
Benchmark                     Mode  Cnt        Score        Error  Units
FibonacciBenchmark.before     avgt    5  1200000.000 ±  15000.000  ns/op
FibonacciBenchmark.after      avgt    5     8000.000 ±    200.000  ns/op
```

`before`（キャッシュなし）は指数的に時間が伸び、`after`（キャッシュあり）は線形時間になり、大きな差が出ているのがわかります。

# 4. 小ネタ

- `jmh:compile` で事前に JMH のコード生成だけ行い、後で `jmh:runMain` で実行することも可能
- `Jmh / javaOptions += "-Xmx2g"` のように、計測用の JVM オプションを個別に付けられる
- Scala 3 でも sbt-jmh がそのまま使えるので、Kotlin/Java のコードと混ぜて比較するときに便利

# 5. まとめ

- sbt-jmh を入れると sbt からすぐベンチマークを回せる
- `Blackhole` で最適化を防ぐのが鉄則
- `-i` や `-wi` を調整して、手元の環境で安定する回数を見つけると良さそう
