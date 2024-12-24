---
title: "Vikeを使ってSSGした話 (TODO)"
emoji: "🐈"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["vike", "vite", "ssg"]
published: false
---

- vikeとは

# シンプルにhtmlを出力する

- pagesにディレクトリを掘って+Page.tsxを置く
- これでhtmlは生成される

# ベースとなるHTMLの変更

- src/renderer/+onRenderHtml.tsxで記述する
- Layoutもここでやると良い

## vike-reactを使った場合

- vike-reactを使ったときどうやるといいのかがわかっていない

# metaタグ(title)の変更

- meta tagのtitleの変更
  - src/pages/+config.tsxで出来るっぽい
    - が、できていない
    - 自前でやっているのがうまくいっていないかも？
    - vike-reactだとうまくいくのかがわかっていない

## vike-reactを使った場合

# フロントに出てくるエラーについて

- pageContext.pageProps isn't defined on the client-side, see https://vike.dev/passToClient#error
    - client sideでrenderingするときプロパティアクセス可能なものが絞られているのでアクセスの仕方を変える必要がある

