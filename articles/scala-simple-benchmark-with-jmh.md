---
title: "Scala 3 + JMH を最短でセットアップする ~ sbt-jmh の最小構成 ~"
emoji: "⏱️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "JMH", "Benchmark"]
published: false
---

この記事は Scala Advent Calendar 2025 の 7 日目です。  
n 番煎じな記事ですが、せっかく空いているならと思い滑り込みました。

https://qiita.com/advent-calendar/2025/scala

# はじめに

Scala というか JVM 関連の言語で定番なのかなと思っているマイクロベンチマークツール JMH を試したときの備忘録です。  
`sbt-jmh` を使うと sbt からベンチマークを測るコマンドが使えるので便利でした。

https://github.com/openjdk/jmh

https://github.com/sbt/sbt-jmh

個人的には元々 Scala Meter というベンチマークツールを使っていたのですが、Scala 3 対応がまだ追いついていない印象があり、代替として別のツールを調べていたところ、JMH にたどり着き、sbt-jmh がシンプルで良かったため今回触ってみました。

https://zenn.dev/ara_ta3/articles/scala-meter-getting-started

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
なお、JMH はベンチマーク実行時に独自に fork（別 JVM 起動）を行うため、`Test / fork := true` は必須ではありません。
今回はテストタスクと sbt 本体の JVM を分離する目的で付けています。

今回はプロダクションコードと完全に分離するため、src/bench/scala に JMH 専用コードを配置する構成にしました。
sbt-jmh は src/jmh のようなデフォルトディレクトリを持たないため、unmanagedSourceDirectories で明示的に追加しています。

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
なお、JMH では計測対象の結果を Blackhole.consume に渡す必要があります。
そうしないと、JIT によって「結果が使われていない = 不要」と判断され、コードが削除されてしまいます。
その場合、意図しない高速化が起きるため、ベンチマークとして正しい値が出ません。

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

`Jmh/run` でベンチマークを実行できます。フィルタを付けると対象を絞れます。

```bash
sbt "Jmh/run -i 3 -wi 1 -f 1 -t 1 .*FibonacciBenchmark.*"
```

- `-i 3`: 本計測のイテレーション数
- `-wi 1`: ウォームアップ回数
- `-f 1`: fork の回数
- `-t 1`: スレッド数

ベンチマーク名やメソッドをリネームしたのに前のコードが走る場合、JMH の生成コードやコンパイル成果物が `target/` に残っている可能性があります。  
なので、`sbt Jmh/clean` → `sbt Jmh/compile`で再生成すると反映されます。全スコープを掃除したいときは `sbt clean` でも問題ありません。

手元ではこんな結果になりました。

```
[info] Benchmark                           (n)  Mode  Cnt         Score         Error  Units
[info] FibonacciBenchmark.implementation1   20  avgt    3     10940.873 ±     771.730  ns/op
[info] FibonacciBenchmark.implementation1   30  avgt    3   1291339.533 ±  138631.600  ns/op
[info] FibonacciBenchmark.implementation1   35  avgt    3  14861651.639 ± 6639040.520  ns/op
[info] FibonacciBenchmark.implementation2   20  avgt    3         2.204 ±       2.782  ns/op
[info] FibonacciBenchmark.implementation2   30  avgt    3         3.100 ±       1.506  ns/op
[info] FibonacciBenchmark.implementation2   35  avgt    3         2.763 ±       0.728  ns/op
[info] FibonacciBenchmark.implementation3   20  avgt    3         1.922 ±       0.283  ns/op
[info] FibonacciBenchmark.implementation3   30  avgt    3         2.009 ±       0.632  ns/op
[info] FibonacciBenchmark.implementation3   35  avgt    3         2.012 ±       0.505  ns/op
```

`implementation1`（素朴再帰）は指数的に時間が伸びて厳しく、`implementation2`（末尾再帰）は線形で数ナノ秒程度に収まり、`implementation3`（キャッシュあり）はほぼ同水準かわずかに速い、という差が見えます（今回は各イテレーションでキャッシュを作り直しているため、キャッシュの恩恵は小さめ）。

# 4. まとめ

- sbt-jmh は導入が軽く、Scala 3 でも問題なく動作する
- ベンチマーク専用ディレクトリを分ければプロダクションコードにも影響しない
- Scala Meter が使いにくい場合の選択肢として十分実用的
