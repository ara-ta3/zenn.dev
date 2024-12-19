---
title: "Rustのclapでcliのコマンドやオプションをenumで取得する"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["rust", "clap", "cli"]
published: false
---

# Rust Advent Calendar 2024 19 日目

この記事は Rust Advent Calendar 2024 の 19 日目として書いています。
今日見たら偶然 19 日が空いていたので 9 日目同様にせっかくなら入れるかと思って入れています。
https://qiita.com/advent-calendar/2024/rust

昨日は @sotanengel さんによる `「docs.rs 書くのめんどくさくない？」をできるだけ楽にした話` でした。

https://qiita.com/sotanengel/items/81a25106d039aec919a3

# 概要

Rust に慣れるがてら簡単な cli を書いてみようと思い、コマンドをいい感じに出来るライブラリを簡単にググって見つけたので、備忘録としてコマンドを struct にマッピングする周りを書き残そうと思いました。
いくつかコードが出てきますが、ベースの Cargo.toml はこちらです。

```toml
[package]
name = "cli-with-clap"
version = "0.1.0"
edition = "2021"

[dependencies]
clap = { version = "4.5.23", features = ["derive"] }
```

# cli のコマンドを文字列で取得する

まず簡単な使い方としてコマンドを文字列で受け取るコードです。
struct に Parser の derive をつけ、parse を呼べばマッピングできます。

```rust
use clap::Parser;

#[derive(Parser, Debug)]
struct Cli {
    command: String,
}

fn main() {
    let cli = Cli::parse();
    println!("{:?}", cli);
}
```

実行してみたのがこんな感じです。

```bash
cargo run hoge
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.06s
     Running `target/debug/cli-with-clap hoge`
Cli { command: "hoge" }
```

## --hoge などのオプションをつける

`#[arg()]` の derive を追加することでオプションを渡せるようになります。

```rust
use clap::Parser;

#[derive(Parser, Debug)]
struct Cli {
    command: String,

    #[arg(short, long, default_value_t = String::from(""))]
    mojiretu: String,

    #[arg(long)] // shortは-mでかぶるので外しています
    maybe_mojiretu: Option<String>,

    #[arg(short, long, default_value_t = 0)]
    suuji: u32,

    #[arg(short, long)]
    flag: bool,
}

fn main() {
    let cli = Cli::parse();
    println!("{:?}", cli);
}
```

実行するとこうです。

```bash
cargo run hoge
   Compiling cli-with-clap v0.1.0 (/Users/arata/Documents/Workspace/rust/cli-with-clap)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.50s
     Running `target/debug/cli-with-clap hoge`
Cli { command: "hoge", mojiretu: "", maybe_mojiretu: None, suuji: 0, flag: false }

cargo run hoge -m hoge -s 100 -f
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.05s
     Running `target/debug/cli-with-clap hoge -m hoge -s 100 -f`
Cli { command: "hoge", mojiretu: "hoge", maybe_mojiretu: None, suuji: 100, flag: true }
```

# cli のコマンドを enum で取得する

次に、文字列でコマンドを受け取りつつ、enum にマッピングしていきます。
Subcommand 用の enum を作成し、そこに Subcommand の derive を追加することでマッピングできます。

```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Add { task: String },
    Remove { task: String },
    List,
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Add { task } => {
            println!("タスクを追加 {}", task);
        }
        Commands::Remove { task } => {
            println!("タスクを削除: {}", task);
        }
        Commands::List => {
            println!("タスク一覧");
        }
    }
}
```

簡単でいいですね。
Rust の pattern match も強力なので enum に出来るとその後の処理が書きやすくてとても良いです。

これを実行するとこうなります。

```bash
cargo run hoge
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.06s
     Running `target/debug/cli-with-clap hoge`
error: unrecognized subcommand 'hoge'

Usage: cli-with-clap <COMMAND>

For more information, try '--help'.
zsh: exit 2     cargo run hoge

cargo run list
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.06s
     Running `target/debug/cli-with-clap list`
タスク一覧

cargo run add hoge
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.05s
     Running `target/debug/cli-with-clap add hoge`
タスクを追加 hoge
```

## cli 上のサブコマンド名と enum のマッピングを command(name="")で明示する

上記のコマンドでは add という文字列を渡した際、自動的に Add へとマッピングしてくれていますが、これを明示的にできます。
以下は foo-bar というコマンドを用意しつつ、名前は hogefuga という名前にした例です。

```rust
use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    #[command(name = "hogefuga")]
    FooBar,
}

fn main() {
    let cli = Cli::parse();
    println!("{:?}", cli);
}
```

hogefuga で実行するとこうなります。

```bash
cargo run hogefuga
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.05s
     Running `target/debug/cli-with-clap hogefuga`
Cli { command: FooBar }
```

## cli 上のサブコマンドの自動変換のルールを rename_all で kebab-case 以外にする

`#[command]`derive には rename_all というオプションがあり、ここに snake_case などを渡すことで、kebab-case 以外も引数に渡すことができます。  
初期値は kebab-case です。

参考:
https://docs.rs/clap/latest/clap/_derive/index.html#command-attributes

```rust
use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
#[command(rename_all = "snake_case")]
enum Commands {
    FooBar,
}

fn main() {
    let cli = Cli::parse();
    println!("{:?}", cli);
}

```

`-` と `_` なので少し目が滑りますが、以下のように変わっていることがわかります。

```bash
# kebab-case
cargo run foo-bar
   Compiling cli-with-clap v0.1.0 (/Users/arata/Documents/Workspace/rust/cli-with-clap)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.56s
     Running `target/debug/cli-with-clap foo-bar`
error: unrecognized subcommand 'foo-bar'

  tip: a similar subcommand exists: 'foo_bar'

Usage: cli-with-clap <COMMAND>

For more information, try '--help'.

# snake case
cargo run foo_bar
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.04s
     Running `target/debug/cli-with-clap foo_bar`
Cli { command: FooBar }
```

# cli のオプションを enum で取得する

オプションを enum として取得するには ValueEnum を使うと良いみたいです。

```rust
use clap::{Parser, ValueEnum};

#[derive(Parser, Debug)]
struct Cli {
    #[arg(short, long)]
    log_level: Level,
}

#[derive(Debug, Clone, ValueEnum)]
enum Level {
    Debug,
    Info,
    Error,
}

fn main() {
    let cli = Cli::parse();
    println!("{:?}", cli);
}
```

以下のように実行すると level が取得できました。

```bash
cargo run -- --log-level info
   Compiling cli-with-clap v0.1.0 (/Users/arata/Documents/Workspace/rust/cli-with-clap)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.72s
     Running `target/debug/cli-with-clap --log-level info`
Cli { log_level: Info }
```

# まとめ

- だいたいやりたいことを頑張らずにできました
- clap + derive feature 便利
- enum にマッピング出来ると強力なパターンマッチで扱えるのでとても楽
