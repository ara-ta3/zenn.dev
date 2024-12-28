---
title: "Vikeを使ってvite+typescript+reactのページをSSGする"
emoji: "🐈"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["vike", "vite", "ssg", "react", "typescript"]
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

```
Uncaught (in promise) Error: [vike][Wrong Usage] pageContext.pageProps isn't defined on the client-side, see https://vike.dev/passToClient#error
    at createErrorWithCleanStackTrace (createErrorWithCleanStackTrace.js?v=11d75d3e:4:17)
    at assertUsage (assert.js?v=11d75d3e:65:24)
    at passToClientHint (getPageContextProxyForUser.js?v=11d75d3e:46:9)
    at Object.get (getPageContextProxyForUser.js?v=11d75d3e:18:13)
    at render (+onRenderClient.tsx:9:17)
```
