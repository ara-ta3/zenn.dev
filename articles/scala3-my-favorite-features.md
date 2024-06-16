---
title: "Scala3の新機能で個人的に使いそうなもののメモたち"
emoji: "🦔"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "Scala3"]
published: false
---

# 概要

Scala3が出てそれなりに経ちました。  
そろそろ向き合うかと思いドキュメントを眺めて差分をまとめてみるかと思ったのですが、結構多いしメタプログラミングはあまり触っていないので、向き合いきれないなと思い、個人的に使いそうだなと思った好きな機能を例と共に備忘録に残そうと思った次第です。  
主に https://docs.scala-lang.org/scala3/reference/index.html を見て、このページの目次の流れに沿いつつメモっています。  

## 参考URL

- https://docs.scala-lang.org/scala3/reference/index.html
- https://docs.scala-lang.org/ja/scala3/new-in-scala3.html

# New Types

## Intersection Types (Foo & Bar)

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

## Extension Methods (implicit conversion => extension)

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

# Other New Features

## Trait Parameters (trait Hoge(m: String))

```scala
scala> trait Hoge(m: String) {
     | def hoge(): Unit = println(m)
     | }
// defined trait Hoge

scala> (new Hoge("hello"){}).hoge()
hello
```

## Universal Apply Methods (class Hoge(n: Int) / Hoge(10))

- https://docs.scala-lang.org/scala3/reference/other-new-features/creator-applications.html
- case classじゃなくてもapplyが自動生成されるようになった
- ↓が可能になった
    - class Hoge(n: Int)
    - Hoge(10)

## Opaque Type Aliases (opaque type Foo = Int / def x(f: Foo) / x(10) to compile error)

- https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html
- Typeでもコンパイルエラーになってくれる！！！
- めっちゃ欲しかったやつ！！！

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

- https://docs.scala-lang.org/scala3/reference/other-new-features/open-classes.html
- デフォルトでfinalになったらしい
- 継承を許容するならopenをつけよう

### Parameter Untupling  (xs.map { case (x, y) ... } => xs.map { (x, y) ... })
- https://docs.scala-lang.org/scala3/reference/other-new-features/parameter-untupling.html
- Tupleを関数の引数に自動で適用できるって！！！！
    - 便利じゃん！！！！

### New Control Syntax

- カッコの省略形
    - if thenが使いやすいかも

# Other Changed Features

## Vararg Splices (seq: _* => seq*)

- https://docs.scala-lang.org/scala3/reference/changed-features/vararg-splices.html
- `: _*` から `*` になった


# Dropped Features

## Dropped: Package Objects

- https://docs.scala-lang.org/scala3/reference/dropped-features/package-objects.html


## Dropped: Limit 22

https://docs.scala-lang.org/scala3/reference/dropped-features/limit22.html

:koresuki:

## Dropped: private[this] and protected[this]

https://docs.scala-lang.org/scala3/reference/dropped-features/this-qualifier.html


# その他気になった機能

個人的にプロダクションコードではあまり使わない気がするけど、少し気になった機能のメモ。  

## New Types -> Type Lambdas

- https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html

## New Types -> Match Types
- https://docs.scala-lang.org/scala3/reference/new-types/match-types.html#

- マッチタイプのパターンマッチが出来るようになったらしい
- 使い所がぱっと浮かばなくてむずい

```scala
type Element[X] = X match {
  case String => Char
  case List[t] => t
  case Array[t] => t
}
```

## Metaprogramming -> Inline
- https://docs.scala-lang.org/scala3/reference/metaprogramming/inline.html


## Contextual Abstractions -> Multiversal Equality

- https://docs.scala-lang.org/scala3/reference/contextual/multiversal-equality.html


## Other New Features -> Matchable Trait
- https://docs.scala-lang.org/scala3/reference/other-new-features/matchable.html
- Anyでmatchできなくなった
- Matchable Traitなら出来る


