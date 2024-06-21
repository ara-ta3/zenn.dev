---
title: "ScalaのsortedやsortByで降順にする"
emoji: "✨"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "sort"]
published: true
---


ScalaでsortedやsortByを使ったとき昇順に並びますが、降順にするにはどうすれば良いのかと思いググったらstackoverflowに神アンサーがあったのでそれを踏まえた降順にするコードのメモです。  

https://stackoverflow.com/questions/7802851/whats-the-best-way-to-inverse-sort-in-scala


# sortedの結果に.reverseをつける

これはstackoverflowに載っているわけではないのですが、ぱっと浮かぶ方法でしょう。  

```scala
scala> Seq(3, 1, 2).sorted
val res1: Seq[Int] = List(1, 2, 3)

scala> Seq(3, 1, 2).sorted.reverse
val res2: Seq[Int] = List(3, 2, 1)
```

# sortByの数字にマイナスをつける

これは確かに〜〜〜〜〜ってなりましたｗ  

```scala
scala> case class Hoge(n: Int)
// defined case class Hoge

scala> Seq(Hoge(1), Hoge(0), Hoge(10)).sortBy(- _.n)
val res5: Seq[Hoge] = List(Hoge(10), Hoge(1), Hoge(0))
```

# sortedのimplicit parameterのOrderingにreverseをつける

これが載っていた方法なのですが、なるほどとなりました。  
sortedやsortByの引数には順番を決めるOrderingを渡せるようになっていますが、そこに逆順であることを明示して渡せば良いということでした。  
考えてみればそうだなと思ったんですが、気づけていなかったので目からウロコでした。  

```scala
scala> Seq(3, 1, 2).sorted(Ordering[Int].reverse)
val res3: Seq[Int] = List(3, 2, 1)

scala> case class Hoge(n: Int)
// defined case class Hoge

scala> Seq(Hoge(1), Hoge(0), Hoge(10)).sortBy(_.n)(Ordering[Int].reverse)
val res4: Seq[Hoge] = List(Hoge(10), Hoge(1), Hoge(0))
```

### Ordering.byを使う

sortByに近いような形でやるOrdering.byを使っても書けるようです。  

```scala
scala> Seq(Hoge(1), Hoge(0), Hoge(10)).sorted(Ordering.by((_: Hoge).n).reverse)
val res7: Seq[Hoge] = List(Hoge(10), Hoge(1), Hoge(0))
```

# まとめ

- マイナスをつけて目がすべるよりは型でやれると良さそうｗ
- Orderingを引数に渡すでもいいし、Ordering.byを作って渡す形も良さそう

