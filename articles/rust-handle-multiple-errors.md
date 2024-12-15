---
title: "プログラミングRust 7章を参考に複数種類エラー対応の理解を深める"
emoji: "🕌"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Rust", "error", "anyhow"]
published: false
---

プログラミング Rust の 7 章における複数種類のエラー対応の話を読んでいて、複数種類のエラーをハンドリングする際に昔躓いた気がするのを思い出したので、自分なりの備忘録として残そうと思いました。
Rust では、エラーが起こり得る処理を続けて書く際、 `?` を利用して書くことでエラーが起きた時点で即時リターンしてくれる機能が非常に便利です。  
その際、複数種類のエラーを混ざるとコンパイルが通らなくなりつまづきました。  
それをどう処理をすべきかを備忘録として書いておくというのが主な趣旨です。

# サンプルコード

今回は以下のような 100 と書かれたファイルを読み込んで数字に変換し、println で表示するというコードを例として使います。
ファイルの読み込み時に io::Error、文字列の変換時に std::num::ParseIntError が返りえます。

```rust
use std::fs::File;
use std::io::{self, BufRead};

fn read_number_from_file(file_path: &str) -> Result<i32, io::Error> {
    let file = File::open(file_path)?;
    let mut lines = io::BufReader::new(file).lines();
    let first_line = lines
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "File is empty"))??;

    let i = first_line
        .trim()
        .parse::<i32>()?;
    Ok(i)
}

fn main() {
    let x = read_number_from_file("./one_hundred.txt");
    match x {
        Ok(i) => println!("{}", i),
        Err(e) => println!("{:?}", e),
    }
}
```

これをビルドしてみるとこうなります。

```bash
error[E0277]: `?` couldn't convert the error to `std::io::Error`
  --> src/main.rs:44:24
   |
35 | fn read_number_from_file(file_path: &str) -> Result<i32, io::Error> {
   |                                              ---------------------- expected `std::io::Error` because of this
...
44 |         .parse::<i32>()?;
   |          --------------^ the trait `From<ParseIntError>` is not implemented for `std::io::Error`, which is required by `Result<i32, std::io::Error>: FromResidual<Result<Infallible, ParseIntError>>`
   |          |
   |          this can't be annotated with `?` because it has type `Result<_, ParseIntError>`
   |
   = note: the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait
   = help: the following other types implement trait `From<T>`:
             `std::io::Error` implements `From<ErrorKind>`
             `std::io::Error` implements `From<IntoInnerError<W>>`
             `std::io::Error` implements `From<NulError>`
             `std::io::Error` implements `From<TryReserveError>`
   = note: required for `Result<i32, std::io::Error>` to implement `FromResidual<Result<Infallible, ParseIntError>>`
```

io:Error を期待しているはずですが、std::num::ParseIntError を返そうとしており、From トレイトが存在しないため返り値として期待される型にできず、コンパイルが通りません。

:::message
?を使用した際に From トレイトが実装されていると自動的に必要な型へと変換してくれます。
参考: https://doc.rust-lang.org/std/convert/trait.From.html#examples
:::

# 対応策

対応策として主に以下の 3 つの方法があります。

1. map_err で型変換する
1. カスタムエラーを From トレイトと共に実装する
   1. 自前で実装する
   1. thiserror を使う
1. 全てのエラーに対応できる型を使う
   1. `Box<dyn std::error::Error + Send + Sync + 'static>` を使う
      - 他の言語で言うところの基底の Exception を使うというイメージ
   2. anyhow を使う

## map_err で型変換する

数字の変換の失敗が io::Error が妥当かどうかは置いといて、型パズルします。
それはそうという感じですが、型がとりあえず合うのでコンパイルを通したいという思いは通ります。

```rust
    first_line
        .trim()
        .parse::<i32>()
        .map_err(|x| io::Error::new(io::ErrorKind::InvalidData, x.to_string()))
```

## カスタムエラーを From トレイトと共に実装する

自前のカスタムエラーを定義し、io::Error と std:num::ParseIntError をそのカスタムエラーへと変換する From トレイトを用意し、返り値の型をカスタムエラーにすればコンパイルを通すことができます。

```rust
use std::fs::File;
use std::io::{self, BufRead};
use std::num::ParseIntError;
use std::fmt;

#[derive(Debug)]
enum MyError {
    IoError(io::Error),
    ParseError(ParseIntError),
}

impl fmt::Display for MyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MyError::IoError(e) => write!(f, "IO error: {}", e),
            MyError::ParseError(e) => write!(f, "Parse error: {}", e),
        }
    }
}

impl std::error::Error for MyError {}

impl From<io::Error> for MyError {
    fn from(err: io::Error) -> MyError {
        MyError::IoError(err)
    }
}

impl From<ParseIntError> for MyError {
    fn from(err: ParseIntError) -> MyError {
        MyError::ParseError(err)
    }
}

fn read_number_from_file(file_path: &str) -> Result<i32, MyError> {
    let file = File::open(file_path)?;
    let mut lines = io::BufReader::new(file).lines();
    let first_line = lines
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "File is empty"))??;

    let i = first_line
        .trim()
        .parse::<i32>()?;
    Ok(i)
}

fn main() {
    let x = read_number_from_file("./one_hundred.txt");
    match x {
        Ok(i) => println!("{}", i),
        Err(e) => println!("{:?}", e),
    }
}
```

### thiserror を使う

https://docs.rs/thiserror

thiserror は上記で行ったカスタムエラーの定義周りを簡潔にできるようにしてくれるライブラリです。  
自前で実装したものを thiserror に移行したものがこちらです。

```rust
use thiserror::Error;
use std::fs::File;
use std::io::{self, BufRead};
use std::num::ParseIntError;

#[derive(Error, Debug)]
enum MyError {
    #[error("IO error: {0}")]
    IoError(#[from] io::Error),

    #[error("Parse error: {0}")]
    ParseError(#[from] ParseIntError),
}

fn read_number_from_file(file_path: &str) -> Result<i32, MyError> {
    let file = File::open(file_path)?;
    let mut lines = io::BufReader::new(file).lines();
    let first_line = lines
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "File is empty"))??;

    let i = first_line
        .trim()
        .parse::<i32>()?;
    Ok(i)
}

fn main() {
    let x = read_number_from_file("./one_hundred.txt");
    match x {
        Ok(i) => println!("{}", i),
        Err(e) => println!("{:?}", e),
    }
}
```

とても便利。

## `Box<dyn std::error::Error + Send + Sync + 'static>` を使う

任意のエラー型のようなものを返すようにすればそりゃ通るよなとできます。  
さすがに長いのでプログラミング Rust の本から引用し`GenericError`という名にしています。
dyn は異なる型を`Box<dyn std::error::Error>`に入れるため必要なもの。  
Send と Sync はスレッドセーフにするべく入れといたほうが良いもの。  
`'static` はライフタイムの話だが、マルチスレッドなどで使用する場合はライフタイムが必要になるので入れておいた方がいいもの。  
という理解でいます(正直言葉のように覚えてしまっており、人に説明できるほど理解して使えてはいないです。)
今回のパターンで言えば `Box<dyn std::error::Error>`でも十分ですね。

```rust
use std::fs::File;
use std::io::{self, BufRead};

type GenericError = Box<dyn std::error::Error + Send + Sync + 'static>;

fn read_number_from_file(file_path: &str) -> Result<i32, GenericError> {
    let file = File::open(file_path)?;
    let mut lines = io::BufReader::new(file).lines();
    let first_line = lines
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "File is empty"))??;

    let i = first_line
        .trim()
        .parse::<i32>()?;
    Ok(i)
}

fn main() {
    let x = read_number_from_file("./one_hundred.txt");
    match x {
        Ok(i) => println!("{}", i),
        Err(e) => println!("{:?}", e),
    }
}
```

## anyhow を使う

anyhow は異なるエラー型を扱いながら、詳細なエラー情報を簡単に付加できるとても便利なライブラリです。
io::Error など標準で提供されているエラー型の変換などもやってくれるので、anyhow::Result 型を返すように定義すると楽に書けそうでした。

https://docs.rs/anyhow

```rust
use std::fs::File;
use std::io::{self, BufRead};
use anyhow::{Context, Result};

fn read_number_from_file(file_path: &str) -> Result<i32> {
    let file = File::open(file_path)?;
    let mut lines = io::BufReader::new(file).lines();
    let first_line = lines
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "File is empty"))??;

    let i = first_line
        .trim()
        .parse::<i32>()?;
    Ok(i)
}

fn main() {
    let x = read_number_from_file("./one_hundred.txt");
    match x {
        Ok(i) => println!("{}", i),
        Err(e) => println!("{:?}", e),
    }
}
```

また、Context トレイトの with_context を使ってエラー時の情報を追加できます。
backtrace も表示できるので非常に便利ですね。

```rust
use std::fs::File;
use std::io::{self, BufRead};
use anyhow::{Context, Result};

fn read_number_from_file(file_path: &str) -> Result<i32> {
    let file = File::open(file_path).with_context(|| format!("Failed to open file: {}", file_path))?;

    let mut lines = io::BufReader::new(file).lines();
    let first_line = lines
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "File is empty"))??;

    let i = first_line
        .trim()
        .parse::<i32>()
        .with_context(|| format!("Failed to parse number from: '{}'", first_line))?;
    Ok(i)
}

fn main() {
    let x = read_number_from_file("./one_hundred.txt");
    match x {
        Ok(i) => println!("{}", i),
        Err(e) => println!("{:?}", e),
    }
}
```

txt ファイルに hoge という文字列がある場合に下記のようにメッセージを出してくれるので便利です。

```bash
Failed to parse number from: 'hoge'

Caused by:
    invalid digit found in string
```

# まとめ

- とりあえず anyhow を使うのが楽そう
- カスタムエラーを定義したくなったら thiserror を使うと良さそう
- Rust のエラーハンドリング完全に理解した(俺達の戦い始まったばかりだ)
