---
title: "ScalaTestのEitherValuesでvalueに誤ったアクセスをしたら不意にNotAllowedExceptionで怒られた話"
emoji: "👻"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Scala", "Test"]
published: true
---

# 初めに結論

下記のようにAnyFreeSpecで`in` ではなく `-` の中で.valueでLeftにアクセスしていて怒られました。  
単純に使い方のミスです。  
EitherValuesの.valueは-ではなくinの中で使いましょう。  

```scala
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.diagrams.Diagrams
import org.scalatest.EitherValues._

class TestEitherValueNotInInSpec extends AnyFreeSpec with Diagrams {
  "test" - {
    val v = TestEitherValueNotInIn.bar.value
    "bar" in {
      assert(v == "foo")
    }

  }
}

object TestEitherValueNotInIn {
  def bar: Either[Int, String] = Left(10)
}


```

怒られた様子。  

```zsh
[info] TestEitherValueNotInInSpec:
[info] TestEitherValueNotInInSpec *** ABORTED ***
[info]   Assertion should be put inside in clause, not - clause. (TestEitherValueNotInIn.scala:7)
```

# ScalaTestのEitherValuesとは

https://www.scalatest.org/user_guide/using_EitherValues

EitherValuesの.valueはLeftが返ってくる時に.valueでアクセスするとTestFailedExceptionを投げてくれて、  
Rightが返ってくるはずなのにLeftが返ってきたというときにテストを落としてくれる便利機能です。  

https://github.com/scalatest/scalatest/blob/8a2629ba2dcc66131c1b2cf799421772ca93f537/jvm/core/src/main/scala/org/scalatest/EitherValues.scala#L84

そして、TestFailedExceptionはAnyFreeSpecの場合、inの中で記述されることを期待されています。  
inの中でなければNotAllowedExceptionがthrowされます。  

https://github.com/scalatest/scalatest/blob/8a2629ba2dcc66131c1b2cf799421772ca93f537/jvm/freespec/src/main/scala/org/scalatest/freespec/AnyFreeSpecLike.scala#L271-L297

# エラーの理由

なぜ直面したかを一言でいうと、初めRightのままで.valueを使ってもはコケなかったが、  
リファクタリングしようとして破壊活動してしまったらとLeftになって急にコケてしまいました。  
非常に雑なサンプルですが、冒頭に書いていたようなテストを書いていました。  

```scala
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.diagrams.Diagrams
import org.scalatest.EitherValues._

class TestEitherValueNotInInSpec extends AnyFreeSpec with Diagrams {
  "test" - {
    val v = TestEitherValueNotInIn.bar.value
    "bar" in {
      assert(v == "foo")
    }

  }
}

object TestEitherValueNotInIn {
  def bar: Either[Int, String] = Right("foo")
}
```

この場合、valueでアクセスしていたのはinの中ではないですが、  
返ってくる値はRightなのでTestFailedExceptionにならず、NotAllowedExceptionにもなりません。  
このコードをリファクタリングしようとしたとき、特定のロジックの結果Leftが返るようになっていました。  

```scala
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.diagrams.Diagrams
import org.scalatest.EitherValues._

class TestEitherValueNotInInSpec extends AnyFreeSpec with Diagrams {
  "test" - {
    val v = TestEitherValueNotInIn.bar.value
    "bar" in {
      assert(v == "foo")
    }

  }
}

object TestEitherValueNotInIn {
  private val kibun: Boolean = false
  def bar: Either[Int, String] = if (kibun) Right("foo") else Left(10)
}
```

結果としてテストがコケたのでロジックかテストケースが誤っていたのですが、  
単純にテストがコケるのではなくNotAllowedExceptionが発生し、何が怒られたのか一瞬わからず困惑の時間が過ぎました。  

# 結論 - 用法用量を守って.valueを使おう

- EitherValuesのvalueでのアクセスはinの中でassertionと共に使おう
- 用法用量を守って意図した使い方で書いてテストがコケたときに備えよう
- リファクタリングはテストが通らなければ単なる破壊活動

