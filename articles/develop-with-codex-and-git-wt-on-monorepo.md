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
  - この記事ではgit clone直後にある作業ディレクトリをメインワークツリーと呼んでいます
- ワークツリーはgit-wtか、Codex Appのworktree機能を使おう

## git-wtコマンドについて

今のところ自分は `git worktree` の生コマンドではなく `git-wt` を使っています。  
`git worktree` は自分には少し難しそうで使いこなせる気がしなかったのですが、  
`git-wt` ならなんとなく回せそうだと思った、くらいの理由です。

https://github.com/k1LoW/git-wt

### 導入

```zsh
brew install k1LoW/tap/git-wt
```

以下は公式ドキュメントに書いてあるおまじないとして、そのまま入れています。

```zsh
eval "$(git wt --init zsh)"
```

### よく使う操作

```zsh
git wt                    # 一覧
git wt feature/foo        # worktreeへ移動（なければ作成）
git wt -d feature/foo     # 削除（worktree + branch）
git wt -D feature/foo     # 強制削除
```

`git wt <name>` だけで「既存worktreeへ移動」か「新規作成」を吸収してくれます。  
現状だと `git-wt` のデフォルト設定をそのまま使っています。  
削除時だけ `-d` と `-D` を使い分ける運用にしておくと、意図しない消し方を減らしやすいです。

#### エイリアスなど

git系のコマンドはだいたいエイリアスを入れていて、ここでは `gw` を切っています。  
あと `gww` を作って、`git wt` の一覧を `peco` で選んで移動する運用にしています。

```zsh
alias gw='git wt'

function gww () {
	git wt $(git wt | tail -n +2 | peco | awk '{print $(NF-1)}')
}
```

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
