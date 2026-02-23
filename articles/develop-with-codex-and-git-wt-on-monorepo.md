---
title: "docker-compose前提のモノレポでCodex Appとgit-wtやCodex Appのworktree機能で並列開発を回す"
emoji: "😸"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["git", "gitworktree", "codex", "monorepo"]
published: false
---

## はじめに

最近Codex appとgit-wtで色々なタスクを回し続けるという開発スタイルで過ごしています。  
しかし、バックエンドやフロントエンドや他のミドルウェアなどが混在しているdocker-compose内の開発環境において、ビルド結果の反映がしづらいという困りごとが発生しました。  
複数のworktree内でdocker compose upできれば良いのですが、それなりにリソースを利用する環境の場合にはPCのリソースが足りません。  
そこで今回は、メインのworktree内でreview用のブランチを作成し、ビルド成果物の確認などそこで行うために環境を整備したときのコマンドなどを備忘録として残します。

### 3行まとめ

- ワークツリーを切ってCodex Appで並列で開発しよう
- ローカル環境がワークツリー毎に作りづらい場合はメインワークツリーにレビュー用のブランチを作ろう
- ワークツリーはgit-wtか、Codex Appのworktree機能を使おう

## git-wtコマンドについて

- git-wtを利用

https://github.com/k1LoW/git-wt

## Codex Appについて

- Codex App

https://openai.com/ja-JP/index/introducing-the-codex-app/

### Codex Appのworktree機能について

### git-wtとCodex Appの違いについて

## レビュー用のブランチを作る

```zsh
alias gw='git wt'

function gww () {
	git wt $(git wt | tail -n +2 | peco | awk '{print $(NF-1)}')
}

function gwreview () {
	local b=$1
	git switch -C review/$b $b
}
```

## ワークツリー間の移動

- ghq

```zsh
function gg () {
    local selected_dir=$(
        {
            printf "%s\n" "$HOME/dotfiles"
            ghq list -p
            find "$HOME/.codex/worktrees" -mindepth 2 -maxdepth 2 -type d
        } | peco --query "$LBUFFER"
    )
    if [ -n "$selected_dir" ]; then
        cd ${selected_dir}
    fi
}
```
