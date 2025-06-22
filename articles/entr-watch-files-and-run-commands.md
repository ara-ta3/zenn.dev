---
title: "ファイルの変更を検知して任意のコマンドをパイプで渡して実行できるentrコマンドが便利"
emoji: "🔖"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["command", "cli"]
published: false
---

# はじめに

ファイルの変更を監視して、変更があった際に任意のコマンドを実行したいという場面は開発中によくあります。  
今回は、そのような用途に便利な`entr`コマンドについて紹介します。

# entr コマンドとは

`entr`は、ファイルの変更を監視して、変更があった際に指定したコマンドを実行する Unix ツールです。  
標準入力からファイルリストを受け取り、それらのファイルの変更があった際にコマンドを実行します。

**公式サイト**
https://eradman.com/entrproject/

**GitHub**
https://github.com/eradman/entr

## インストール

Mac の場合は HomeBrew、Debian などであれば apt でも入るようです。

```bash
# macOS (Homebrew)
brew install entr

# Ubuntu/Debian
apt install entr
```

## 基本的な使い方

`entr`は標準入力からファイルリストを受け取り、それらのファイルの変更を監視します。

```bash
# 基本的な形
echo "ファイル名" | entr コマンド

# 例: hoge.txt の変更を監視してecho実行
## ターミナルA
$ls
hoge.txt
$echo abc > hoge.txt

## ターミナルB
$echo hoge.txt | entr echo fuga
fuga
# ここでターミナルAがecho abc > hoge.txtを行う
# するとecho fugaが実行され標準出力に出てきました
fuga
```

# 実際の使用例

## ソースコードやテストファイルの変更を監視してテストを実行

```bash
# テストファイルの変更を監視
find . -name "*.test.js" | entr npm test

# TypeScriptファイルの変更を監視してビルド
find src -name "*.ts" | entr npm run build

# 設定ファイルの変更を監視
echo "config.yml" | entr -r ./restart-service.sh
```

find コマンドを例に上げていますが、watch しながらソースコードをビルドするものはよくあると思うので、  
そのコマンドと併用しながら回すのが良いでしょう。  
私は sbt-native-packager の`sbt stage` コマンドと併用する形で使いたくなり、このコマンドを知りました。

# 便利なオプション

## -r: プロセスを再起動

```bash
# サーバーを起動し、ファイル変更時に再起動
find . -name "*.js" | entr -r node server.js
```

## -c: 実行前にターミナルをクリア

```bash
# テスト実行前にターミナルをクリア
find . -name "*.go" | entr -c go test ./...
```

## -d: ディレクトリの変更も監視

```bash
# ディレクトリの変更も含めて監視
find . -type d | entr -d echo "ディレクトリが変更されました"
```

# まとめ

`entr`コマンドは、ファイルの変更を監視して自動的にコマンドを実行するシンプルで強力なツールです。  
開発中のテスト実行、ビルド、サーバー再起動などの自動化に非常に便利です。  
シンプルな設計で使いやすいので、watch しながら何かコマンドを走らせたいが、それに合う機能が周辺にない場合活用すると良いでしょう。
