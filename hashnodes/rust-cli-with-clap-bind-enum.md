---
title: "How to Use Enums with clap to Build Rust CLI Commands and Options"
emoji: "🦀"
type: "tech"
topics: ["rust", "clap", "cli"]
published: true
---

# Rust Advent Calendar 2024 - Day 19

This article was written as the 19th entry in the Rust Advent Calendar 2024:  
https://qiita.com/advent-calendar/2024/rust

The previous entry was by @sotanengel:  
["Making docs.rs less painful to write"](https://qiita.com/sotanengel/items/81a25106d039aec919a3)

# Overview

While getting more comfortable with Rust, I decided to try writing a simple CLI.  
I looked for a library that could elegantly handle commands and found **clap**.  
This post is a quick note on how to map CLI commands and options to enums using `clap`.

Base `Cargo.toml` configuration:

```toml
[package]
name = "cli-with-clap"
version = "0.1.0"
edition = "2021"

[dependencies]
clap = { version = "4.5.23", features = ["derive"] }
```

# Getting CLI Commands as Strings

Here’s a basic example where we receive a CLI command as a string:

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

```bash
cargo run hoge
Cli { command: "hoge" }
```

## Adding Options like --hoge

Using `#[arg()]`, you can add options to the command:

```rust
use clap::Parser;

#[derive(Parser, Debug)]
struct Cli {
    command: String,

    #[arg(short, long, default_value_t = String::from(""))]
    mojiretu: String,

    #[arg(long)]
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

# Mapping CLI Commands to Enums

To map commands to enums, use `Subcommand`:

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
        Commands::Add { task } => println!("Add task: {}", task),
        Commands::Remove { task } => println!("Remove task: {}", task),
        Commands::List => println!("List tasks"),
    }
}
```

```bash
cargo run list
List tasks

cargo run add hoge
Add task: hoge
```

## Explicit Subcommand Name Mapping with `command(name="")`

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

```bash
cargo run hogefuga
Cli { command: FooBar }
```

## Change Subcommand Case Mapping with `rename_all`

By default, subcommand names use kebab-case. You can change this with `rename_all`:

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

```bash
cargo run foo_bar
Cli { command: FooBar }
```

# Getting CLI Options as Enums

To map CLI options to enums, use `ValueEnum`:

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

```bash
cargo run -- --log-level info
Cli { log_level: Info }
```

# Conclusion

- Achieved everything without much hassle
- `clap` + `derive` is powerful
- Enum-based commands make Rust's pattern matching extremely ergonomic
