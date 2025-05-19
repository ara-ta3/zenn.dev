---
title: "Vikeを使ってVite+TypeScript+Reactの動的ルーティングのページにメタ情報を含めてSSGする"
emoji: "🐕"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["React", "SSG", "Vite", "Vike", "contest2025ts"]
published: true
---

## はじめに

以前、「Vike を使って Vite+TypeScript+React のページを SSG する」という記事を書き、Vite+Vike で SSG を行いました。  
今回は動的なページ (/hoge/:id のようなページ) に title や description などのメタ情報を埋め込み、SSG を行いたいと思って試した備忘録です。

https://zenn.dev/ara_ta3/articles/typescript-vike-ssg-getting-started

利用したツールのバージョンは以下の通りです。

```
"@vitejs/plugin-react": "^4.4.1",
"typescript": "^5.8.3",
"vike": "^0.4.229",
"vike-react": "^0.6.1",
"vite": "^6.3.5"
```

GitHubRepository はこちら

https://github.com/ara-ta3/vike-ssg-dynamic-pages-getting-started

## 事前準備

前提として vike-react の plugin を利用します。  
以前書いた記事では vike-react を利用せずに試したパターンを記述しましたが、vike-react を利用せずに全部書くことは少ないと思い始めたため、vike-react に乗っかる前提の話になります。  
https://zenn.dev/ara_ta3/articles/typescript-vike-ssg-getting-started

設定としては src/pages/+config.ts に設定を記述します。  
以前は vike.config.js に記述していましたが、現在は以下の様な警告が出るようになりました。

```
23:00:00 [vike][Warning] Define Vike settings in +config.js instead of vite.config.js https://vike.dev/migration/settings
```

設定は以下のような形です。  
src/pages/+config.ts

```ts
import vikeReact from "vike-react/config";

export default {
  extends: [vikeReact],
  prerender: true,
};
```

## 概要

概ねやることは以下の通りです。

- +route.ts に動的ルートのパスを定義
- +Page.tsx にページ内容を記述
- +onBeforeRender.ts で title 情報取得し pageContext に追加
- +Head でメタ情報を出力
- +onBeforePrerenderStart.ts で静的ページを列挙

最終的に src ディレクトリの構成はこのようになります。  
src/pages/hoge 以下が今回の話に関連するものです。

```tree
src
└── pages
    ├── +config.ts
    ├── +Head.tsx
    ├── +Page.tsx
    └── hoge
        ├── +Head.tsx
        ├── +onBeforePrerenderStart.ts
        ├── +onBeforeRender.ts
        ├── +Page.tsx
        └── +route.ts
```

## 動的ルートを定義する（+route.ts）

まず、動的ルート `/hoge/@id` を扱えるようにします。

```ts
export default "/hoge/@id";
```

https://vike.dev/route

## ページ内容を記述する（+Page.tsx）

props は渡ってこないので、`usePageContext()` を使って取得します。
PageContext の型パラメータは、PageContext<Data = unknown>となっており、data というキーの型を指定するように見えたため、as を利用し指定しています。

```tsx
import { usePageContext } from "vike-react/usePageContext";
import { PageContext } from "vike/types";

export { Page };

function Page() {
  const c = usePageContext() as PageContext<{
    id: number;
    title: string;
    description: string;
  }>;
  const title = c.data.title;
  const description = c.data.description;

  return (
    <div>
      <p>hello {c.data.id}</p>
    </div>
  );
}
```

https://vike.dev/Page

## メタ情報を生成するためのデータ取得とメタ情報を PageContext へ渡す設定（+onBeforeRender.ts）

ここのクラスではデータを取得し、id などのパラメータに対応するメタ情報を取得し、それを pageContext として返します。

```ts
import { PageContext } from "vike/types";

export async function onBeforeRender(pageContext: PageContext) {
  const id = parseInt(pageContext.routeParams.id);
  let title = "ほげ null";
  if (isNaN(id)) {
    return {
      pageContext: {
        data: { id, title, description: "ほげ null" },
      },
    };
  }
  title = `ほげ ${id}`;
  return {
    pageContext: {
      data: { id, title: `ほげ ${id}`, description: `ほげ ${id}` },
    },
  };
}
```

https://vike.dev/onBeforeRender

## メタ情報を出力する（+Head.tsx）

+Head.tsx はメタ情報を実際に出力する場所です。  
onBeforeRender で行っている処理も結局できてしまうのですが、責務的にデータを取得する部分は onBeforeRender へと任せる形としています。

```tsx
import React from "react";
import { usePageContext } from "vike-react/usePageContext";
import { PageContext } from "vike/types";

const Head: React.FC = () => {
  const c = usePageContext() as PageContext<{
    id: number;
    title: string;
    description: string;
  }>;

  const title = c.data.title;
  const description = c.data.description;

  return (
    <>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
      <meta charSet="UTF-8" />
    </>
  );
};

export default Head;
```

https://vike.dev/head-tags#head-setting

## 静的ページのパスを列挙する（+onBeforePrerenderStart.ts）

最後にパスを列挙します。  
これで列挙されたものが html として出力されるといった形になります。

```ts
export { onBeforePrerenderStart };

async function onBeforePrerenderStart() {
  const ids = ["1", "2"];
  return ids.map((id) => `/hoge/${id}`);
}
```

https://vike.dev/onBeforePrerenderStart

## ビルドする

vike build を実行し、実際に html ファイルを出力します。  
以下がログですが、dist/client/hoge 以下に 1、2 のディレクトリが作成され、その下に index.html が生成されました。

```
./node_modules/.bin/vike build
vite v6.3.5 building for production...
✓ 195 modules transformed.
computing gzip size (6)...vite v6.3.5 building SSR bundle for production...
dist/client/_temp_manifest.json                                1.83 kB │ gzip:  0.41 kB
dist/client/assets/static/vike-react-b64a028b.BcWtY8Ol.css     0.06 kB │ gzip:  0.08 kB
dist/client/assets/entries/src_pages_hoge.DvfzTQ7c.js          1.48 kB │ gzip:  0.56 kB
dist/client/assets/entries/src_pages.Ba18_hJI.js               1.71 kB │ gzip:  0.63 kB
dist/client/assets/chunks/chunk-2C7rdSYH.js                    4.74 kB │ gzip:  2.16 kB
dist/client/assets/entries/entry-client-routing.TzfcpEbg.js   73.25 kB │ gzip: 23.60 kB
dist/client/assets/chunks/chunk-DFYpO8u8.js                  189.37 kB │ gzip: 60.05 kB
✓ 10 modules transformed.
dist/server/package.json                0.02 kB
dist/server/_temp_manifest.json         1.06 kB
dist/server/chunks/chunk-CCwFZrSa.js    0.90 kB
dist/server/entries/src_pages.mjs       2.65 kB
dist/server/entry.mjs                   4.54 kB
dist/server/entries/src_pages_hoge.mjs  4.85 kB
✓ built in 30ms
vike v0.4.229 pre-rendering HTML...
dist/client/index.pageContext.json
dist/client/index.html
dist/client/hoge/2/index.pageContext.json
dist/client/hoge/1/index.html
dist/client/hoge/1/index.pageContext.json
dist/client/hoge/2/index.html
✓ 3 HTML documents pre-rendered.
✓ built in 633ms
```

## おわりに

vite+vike+vike-react を利用して、動的な ID を持つページの SSG が出来ました。
割とサクッと出来たので vite+vike はやはり便利だなと感じます。
一方で、vike はまだ発展途上の段階ということもあり、ちょっとしたアップデートで警告が出たり、古い情報が使えなくなる場面もあります。  
そうした変化の激しさも含めて受け入れつつ、自分の手で動かして確かめながら、強い気持ちで向き合っていく必要があるなと思いました。

この記事が、動的なページの SSG の足がかりになれば幸いです！

## 参考

参考までに以下サイトで利用しています。  

https://nekometry.web.app/?utm_source=zenn.dev&utm_medium=referral&utm_campaign=article20250513
