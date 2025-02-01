---
title: "Prismaを使って既存のテーブルスキーマからコードを生成する"
emoji: "✨"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["prisma", "mysql"]
published: false
---

# 背景と概要

発端は既存のテーブル構成からORMっぽい役割のコードを生成できないかと思って探していました。  
その時はScala(scalikejdbc)のコードだったのでscalikejdbc-mapper-generatorというのを使おうとしていましたが、調べている間にPrismaの名前を見て、前知り合いが発表していたなと思い検証してみました。その時の備忘録です。  

検証したコードなどはこちらにあります。  

https://zenn.dev/ara_ta3/scraps/45124487a548ee

https://github.com/ara-ta3/prisma-scala-gettingstarted

# Prismaとは

PrismaはNode.js用のORMですが、schema.prismaという固有のスキーマファイルを生成し、それを元にDBマイグレーションやコード生成などを行えるという特徴があります。  
当然TypeScript / JavaScriptの生成もできるのですが、独自のジェネレータを書くことによって、TypeScript / JavaScript以外の言語のコード生成も可能というのも1つの利点です。  

https://www.prisma.io/

ちょっと前に見た知り合いの発表資料のslide 45のPrisma ORMの仕組みのページがわかりやすいのでおすすめです。  

https://speakerdeck.com/hoto17296/orm-toxiang-kihe-u?slide=45

# 目次

- 既存のテーブル定義からスキーマファイルを生成する
- スキーマファイルから「テーブルデータをマッピングするクラス」を生成するコードを書く
- 「テーブルデータをマッピングするクラス」を生成してみる


マッピングするクラスはScalaのコードにしたかったので、Scalaのコードを生成してみます。  
後に出てくるコードを見るとわかりますが、JavaScript(TypeScript)で生成するコードを書くので、任意のファイルを生成できるため、Scalaに限った話ではありません。  


# 既存のテーブル定義からスキーマファイルを生成する


# スキーマファイルから「テーブルデータをマッピングするクラス」を生成するコードを書く


# 「テーブルデータをマッピングするクラス」を生成してみる

 

