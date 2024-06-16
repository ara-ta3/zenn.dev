---
title: "Scala3の新機能で個人的に使いそうなもののメモたち"
emoji: "🦔"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "Scala3"]
published: true
---

# 概要

Scala3が出てそれなりに経ちました。  
そろそろ向き合うかと思いドキュメントを眺めて差分をまとめてみるかと思ったのですが、結構多いしメタプログラミングはあまり触っていないので、向き合いきれないなと思い、個人的に使いそうだなと思った好きな機能を例と共に備忘録に残そうと思った次第です。  
主に https://docs.scala-lang.org/scala3/reference/index.html を見て、このページの目次の流れに沿いつつメモっています。  

## 参考URL

- https://docs.scala-lang.org/scala3/reference/index.html
- https://docs.scala-lang.org/ja/scala3/new-in-scala3.html
- https://speakerdeck.com/taisukeoe/why-things-are-changed-in-scala3

# New Types

## Intersection Types (Foo & Bar)

https://docs.scala-lang.org/scala3/reference/new-types/intersection-types.html  

TypeScriptとかにもあるIntersection型ですね。  

```scala
scala> trait Foo { def foo(): Unit = println("foo") }
// defined trait Foo

scala> trait Bar { def bar(): Unit = println("bar") }
// defined trait Bar

scala> def hoge(x: Foo & Bar): Unit = {
     | x.foo()
     | x.bar()
     | }
def hoge(x: Foo & Bar): Unit

scala> class Fuga extends Foo with Bar
// defined class Fuga

scala> hoge(new Fuga())
foo
bar
```

## Union Types (Foo | Bar)

https://docs.scala-lang.org/scala3/reference/new-types/union-types.html  

Intersectionに続いてUnion型ですね。  
こっちはパターンマッチで一部しかcaseに書かれていない際、Warningに落とせるのでsealed traitなどに落とし込まず使えるため便利そうな印象があります。  

```scala
scala> def hoge(x: Int|String): String = x match {
     | case i: Int => s"$i"
     | }
1 warning found
-- [E029] Pattern Match Exhaustivity Warning: ----------------------------------
1 |def hoge(x: Int|String): String = x match {
  |                                  ^
  |                                  match may not be exhaustive.
  |
  |                                  It would fail on pattern case: _: String
  |
  | longer explanation available when compiling with `-explain`
def hoge(x: Int | String): String

scala> def hoge(x: Int|String): String = x match {
     | case i: Int => s"$i"
     | case s: String => s
     | }
def hoge(x: Int | String): String
```

# Contextual Abstractions

## Given Instances / Using Clauses (implicit => given or using)

https://docs.scala-lang.org/scala3/reference/contextual/givens.html  
https://docs.scala-lang.org/scala3/reference/contextual/using-clauses.html  

Scala2ではimplicitがいろんな役割を持っていましたが、異なる名前付けがされてわかりやすくなりました。  
その1つとしてimplicit parameter周りがgivenとusingになっています。  

Scala2でmaxという関数に順序を定義するimplicit parameterを渡す例の例。  

```scala
implicit val intOrdering: Ordering[Int] = new Ordering[Int] {
  def compare(x: Int, y: Int): Int = x - y
}

def max[T](x: T, y: T)(implicit ord: Ordering[T]): T = {
  if (ord.compare(x, y) > 0) x else y
}
```

この順序を定義する側をgiven、使う側をusingにするとScala3の構文になるようです。  

```scala
scala> given Ordering[Int] with {
     |   def compare(x: Int, y: Int): Int = x - y
     | }

scala> def max[T](x: T, y: T)(using ord: Ordering[T]): T = {
     |   if ord.compare(x, y) > 0 then x else y
     | }
def max[T](x: T, y: T)(using ord: Ordering[T]): T

scala> max(10, 12)
val res1: Int = 12
```

意味がわかりやすくていいですね。  

## Extension Methods (implicit conversion => extension)

https://docs.scala-lang.org/scala3/reference/contextual/extension-methods.html

given、usingに続いてimplicit conversionで既存のクラスにメソッドを追加するような形で拡張していた機能も名前がつけられました。  
それがextension。  

```scala
extension (x: Int) {
    def isEven: Boolean = x % 2 == 0 
}

scala> extension (x: Int) {
     |     def isEven: Boolean = x % 2 == 0
     | }
def isEven(x: Int): Boolean

scala> 10.isEven
val res4: Boolean = true
```

自前の実装ではそうそうないと思いますが、ライブラリや標準機能を拡張したいとかなった場合に便利そうですね。  

# Other New Features

## Trait Parameters (trait Hoge(m: String))

https://docs.scala-lang.org/scala3/reference/other-new-features/trait-parameters.html  

Scala2ではTraitの初期化時にパラメータを持てませんでしたが、Scala3では持てるようになりました。  
それTraitなんだっけなって気持ちがほんのりよぎってはいるんですが、どうしても持たせたいときに便利そうです。  

```scala
scala> trait Hoge(m: String) {
     | def hoge(): Unit = println(m)
     | }
// defined trait Hoge

scala> (new Hoge("hello"){}).hoge()
hello
```

## Universal Apply Methods (class Hoge(n: Int) / Hoge(10))

https://docs.scala-lang.org/scala3/reference/other-new-features/creator-applications.html

case classではなくてもapplyが自動生成されるようになったようです。  
newを書く必要がなくなって地味に嬉しい機能ですね。  

```scala
scala> class Hoge(n: Int)
Hoge(10// defined class Hoge

scala> val h = Hoge(10)
val h: Hoge = Hoge@62108cd3

scala> h.n
-- [E173] Reference Error: -----------------------------------------------------
1 |h.n
  |^^^
  |value n cannot be accessed as a member of (h : Hoge) from object rs$line$4.
  |  private value n can only be accessed from class Hoge.
1 error found

scala> class Fuga(val n: Int)
// defined class Fuga

scala> val f = Fuga(10)
val f: Fuga = Fuga@4571cebe

scala> f.n
val res1: Int = 10
```

## Opaque Type Aliases (opaque type Foo = Int / def x(f: Foo) / x(10) to compile error)

https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html

**これ！！！最高！！！**  
Type Aliasでもコンパイルエラーになってくれます。  
めっちゃ欲しかった！  

```scala
scala> object Hoge {
     |   opaque type Foo = Int
     |   object Foo {
     |     def apply(x: Int): Foo = x
     |   }
     | }
// defined object Hoge

scala> def x(f: Hoge.Foo): Unit = println(f)
def x(f: Hoge.Foo): Unit

scala> x(Hoge.Foo(10))
10

scala> x(10)
-- [E007] Type Mismatch Error: -------------------------------------------------
1 |x(10)
  |  ^^
  |  Found:    (10 : Int)
  |  Required: Hoge.Foo
  |
  | longer explanation available when compiling with `-explain`
1 error found
```

## Open Classes (open class Hoge())

https://docs.scala-lang.org/scala3/reference/other-new-features/open-classes.html

デフォルトでclassは全てfinalになったようです。  
継承を許容するならopenを付ける必要があるとのこと。  
scala-cliで実行する場合、-source:futureをつけないとコンパイルエラーにはなりませんでした。  

```
scala-cli  -source:future -feature
Welcome to Scala 3.4.2 (22.0.1, Java OpenJDK 64-Bit Server VM).
Type in expressions for evaluation. Or try :help.

scala> class Hoge {}

// defined class Hoge

scala> class Foo extends Hoge
1 warning found
-- Feature Warning: ------------------------------------------------------------
1 |class Foo extends Hoge
  |                  ^^^^
  |Unless class Hoge is declared 'open', its extension in a separate file should be enabled
  |by adding the import clause 'import scala.language.adhocExtensions'
  |or by setting the compiler option -language:adhocExtensions.
  |See the Scala docs for value scala.language.adhocExtensions for a discussion
  |why the feature should be explicitly enabled.
// defined class Foo
```


### Parameter Untupling  (xs.map { case (x, y) ... } => xs.map { (x, y) ... })

https://docs.scala-lang.org/scala3/reference/other-new-features/parameter-untupling.html

Seq[(Int, String)]のようにTupleのListに対してmapを行う際にcaseを使って変数にbindしていましたが、caseを使わなくて良くなるそうです。  
便利ですね。  

```scala
scala> Seq[(Int, String)]((1, "a"), (2, "b")).map((x, y) => s"$x $y")
val res1: Seq[String] = List(1 a, 2 b)
```

# Other Changed Features

## Vararg Splices (seq: _* => seq*)

https://docs.scala-lang.org/scala3/reference/changed-features/vararg-splices.html

可変長引数にSeqの内容を渡す時、 `: _*` を使っていましたが、それが `*` になったようです。  
既存の構文は互換性のためWarningが出るようになっていて、将来的にはErrorになるようです。  

```scala
scala> def hoge(xs: Int*): Unit = xs.foreach(println)
def hoge(xs: Int*): Unit

scala> hoge(Seq(1, 2, 3)*)
1
2
3

scala> hoge(Seq(1, 2, 3): _*)
1
2
3
1 warning found
-- Warning: --------------------------------------------------------------------
1 |hoge(Seq(1, 2, 3): _*)
  |                   ^
  |The syntax `x: _*` is no longer supported for vararg splices; use `x*` instead

// ↓-source:futureの場合

scala> hoge(Seq(1, 2, 3): _*)
-- Error: ----------------------------------------------------------------------
1 |hoge(Seq(1, 2, 3): _*)
  |                   ^
  |The syntax `x: _*` is no longer supported for vararg splices; use `x*` instead
```


# Dropped Features

## Dropped: Package Objects

https://docs.scala-lang.org/scala3/reference/dropped-features/package-objects.html

package object内に変数などを置いていましたがそれがなくなるようです。  


## Dropped: Limit 22

https://docs.scala-lang.org/scala3/reference/dropped-features/limit22.html

:koresuki:  
Scalaの22問題がなくなったようですｗ  
引数100個持たせていきましょう。  

## Dropped: private[this] and protected[this]

https://docs.scala-lang.org/scala3/reference/dropped-features/this-qualifier.html

private[this]やprotected[this]がなくなったみたいですね。  

# その他気になった機能

個人的にプロダクションコードではあまり使わない気がするけど、少し気になった機能のメモ。  

## New Types -> Type Lambdas

https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html

ぶっちゃけわからなかったｗ  
なので、使い所が見え次第理解していきたい。  

## New Types -> Match Types

https://docs.scala-lang.org/scala3/reference/new-types/match-types.html#

Generics部分のパターンマッチが出来るようになったらしい。  
使い所がぱっと浮かんでいないので、上手く使える方法を理解していきたい。  

```scala
type Element[X] = X match {
  case String => Char
  case List[t] => t
  case Array[t] => t
}
```

## Metaprogramming -> Inline

https://docs.scala-lang.org/scala3/reference/metaprogramming/inline.html

コンパイル時に展開してくれるらしい。  
関数の呼び出し回数が気になるくらいにパフォーマンスを考慮する時に使えると良さそう。  

## Contextual Abstractions -> Multiversal Equality

https://docs.scala-lang.org/scala3/reference/contextual/multiversal-equality.html

Scala2のとき異なる型の比較が出来ていたが、それがエラーになるらしい。  
全然意識してなくて、知った時出来たのかと思った。  

Scala2の例。  

```scala
scala> val x: Int = 1
val x: Int = 1

scala> val y: String = "1"
val y: String = 1

scala> x == y
         ^
       warning: comparing values of types Int and String using `==` will always yield false
error: No warnings can be incurred under -Werror.
```

Scala3ではエラーになる。  

```scala
scala> val x: Int = 1
val x: Int = 1

scala> val y: String = "1"
val y: String = 1

scala> x == y
-- [E172] Type Error: ----------------------------------------------------------
1 |x == y
  |^^^^^^
  |Values of types Int and String cannot be compared with == or !=
1 error found
```


CanEqualを使って何か出来るらしいんだけど、使うことがなさそうであまり深掘れていない。  


## Other New Features -> Matchable Trait

https://docs.scala-lang.org/scala3/reference/other-new-features/matchable.html

MatchableというTraitが出来て、これに対してパターンマッチが使えるというようになったみたいですね。  
結果としてAny型に対してパターンマッチが使えなくなったようです。  

### Other New Features -> New Control Syntax

https://docs.scala-lang.org/scala3/reference/other-new-features/control-syntax.html

if thenで括弧を省略出来るようになったらしい。  

```
if x < 0 then
  "negative"
else if x == 0 then
  "zero"
else
  "positive"
```


# まとめというか感想

- 便利になる機能がたくさんあるので使っていきたいと思った
- 理解しきれていない部分が多々あるが、使いながら必要になるタイミングで理解していきたい
