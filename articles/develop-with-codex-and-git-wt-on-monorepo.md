---
title: "docker-compose前提のモノレポで Codexアプリ × git-wt による並列開発を回す"
emoji: "😸"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["git", "gitworktree", "codex", "monorepo", "dockercompose"]
published: false
---

## はじめに

最近Codexアプリとgit-wtで色々なタスクを回し続けるという開発スタイルで過ごしています。  
しかし、バックエンドやフロントエンドや他のミドルウェアなどが混在しているdocker-compose内の開発環境において、ビルド結果の反映がしづらいという困りごとが発生しました。  
各作業の成果物は基本的にそれぞれのworktree内に閉じるため、確認するには「メインワークツリーへ成果物を持ってくる」か「そのworktree側でも検証環境を立ち上げる（`docker compose up`）」のどちらかが必要になります。  
ただ、後者を並列でやるとPCリソースをかなり使うのでつらく、前者も毎回手で寄せるのが面倒です。  
そこで今回は、メインのworktree内でreview用のブランチを作成し、ビルド成果物の確認などそこで行うためにどのような運用にしているかを備忘録として残します。

### 3行まとめ

- ワークツリーを切って、Codexアプリで並列開発しよう
- ローカル環境がワークツリー毎に作りづらい場合はメインワークツリーにレビュー用のブランチを作ろう
  - この記事ではgit clone直後の作業ディレクトリをメインワークツリーと呼ぶ
- ワークツリーはgit-wtか、Codexアプリのworktree機能を使おう

## git-wtコマンドについて

まず前提として `git worktree` は、  
**1つのリポジトリでブランチごとに作業場所（ディレクトリ）を分けられる機能**です。  
`git clone` を増やさなくても、並列で別ブランチを触りやすくなります。

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

## Codexアプリについて

もともとはターミナルで `codex` コマンドを打って使っていました。  
ターミナル運用だと、原因は特定しきれていないものの制御文字が混ざることもあり、  
VSCodeをラッパーにして使っていました。  
Codexアプリが出たときはどうせアプリケーションを起動するならこっちが良いじゃんと思って入れたのですが、  
実際わりと良かったです。

当然ながらターミナルでできることはだいたいできますし、  
左に Thread（作業中の一覧）が出るので、並列で回しているときに見通しが良いです。

https://openai.com/ja-JP/index/introducing-the-codex-app/

### Codexアプリのworktree機能について

Codexアプリのworktree機能は、雑に言うと「タスクごとに作業場所を分けてくれる」機能です。  
同じリポジトリでも作業が干渉しにくいので、並列で投げるときに気が楽です。

実際に作られたworktree側の `.git` を見ると、次のように `gitdir: ...` の形式になっていました。

```txt
gitdir: /path/to/repo/.git/worktrees/xxxxx
```

つまりこれは独自実装というより、`git worktree` の仕組みを使っていると理解しています。

### git-wtとCodexアプリのworktree機能の違いについて

正直、最初はCodexアプリのworktreeをあまり理解しないまま使っていませんでした。  
ただ、よく見ると `git worktree` の仕組みなので、`git wt` の一覧にも普通に出てきます。

そのうえで今のところ、自分の観測範囲では  
「Codexアプリ側でworktree作業を始めるときに、最初からブランチを切る導線」は見つけられていません。  
なのでブランチ起点で作業したいときは、先に `git-wt` で切っておくほうが楽だと感じています。

一方で、`git-wt` で作ったworktreeはCodexアプリの Threads に手動追加が必要なので、  
ここはちょっと面倒です。  
今は「ブランチを先に切りたいときは `git-wt`、Thread管理を優先したいときはCodexアプリ」くらいで使い分けています。

### ワークツリー間の移動の便利関数

普段は `ghq list -p` だけを `peco` で選んで移動していました。  
ただ、Codexアプリで作ったworktreeは `~/.codex/worktrees` 配下にできるので、  
ここも `find` で候補に混ぜるようにしています。  
これで「メインワークツリー」「ghq配下」「Codexアプリ配下」の移動を1つの関数で済ませられて便利です。

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

## レビュー用のブランチを作る

背景は「はじめに」で書いた通りですが、バックエンド / フロントエンド / その他 を `docker compose` で動かしていると、  
各ワークツリーごとに開発環境を立てるとリソース消費が重くてつらい、という事情があります。  
そのため、どこか1か所（メインワークツリー）で検証できる状態を作りたくなりました。

git worktree運用では、作業ブランチをリモートにpushしていなくてもローカルのGit管理下に既にあるので、  
メインワークツリー側からそのブランチを元にレビュー用ブランチを生やせます。

ただし、git worktreeで使用中のブランチ名はそのまま使えないので、  
`review/` プレフィックスを付けて別名で切るようにしています。  
毎回手で打つのが面倒なので、関数にしました。

```zsh
function gwreview () {
	local b=$1
	git switch -C review/$b $b
}
```

例えば `feature/add-login` をレビューしたいときは、  
`gwreview feature/add-login` で `review/feature/add-login` を作って切り替えるイメージです。

## まとめ

Codexアプリと git-wt を使った並列開発の一例を紹介しました。  
docker-compose 前提のモノレポ構成では、 各worktreeで同じ環境を立てるのは現実的ではないため、  
検証はメインワークツリーに寄せる、という運用にしています。  
同じような構成で似たような困り事がある方の参考になれば幸いです。
