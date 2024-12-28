---
title: "Vikeを使ってVite+TypeScript+ReactのページをSSGする"
emoji: "🐈"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["vike", "vite", "ssg", "react", "typescript"]
published: true
---

# 概要

GitHub Pages にホスティングしようと思って、せっかくなら SSG やってみるかと思って試した備忘録です。  
Vite + TypeScript + React で開発している状態で SSG を行おうと思ったら Vike というライブラリを知りました。  
元々は `vite-plugin-ssr` という Vite の plugin だったようですね。

https://vite-plugin-ssr.com/

> The vite-plugin-ssr project has been renamed Vike.

今回は TypeScript + React ベースのページを Vike を使って静的ファイルにして生成してみます。

:::message
`vike-react` という拡張を使えば不要な部分がありますが、vike の理解を深めるために一旦使わずに書いています。

https://github.com/vikejs/vike-react
:::

利用したコードが置いてあるリポジトリはこちらです。

https://github.com/ara-ta3/vike-ssg-getting-started

使用した Vite、Vike、React のバージョンは以下のとおりです。

```
"react": "19.0.0"
"react-dom": "19.0.0"
"vike": "0.4.210"
"vite": "6.0.5"
```

# 最低限 HTML に出力する

まず Hello World します。  
vite.config.ts に設定を追加し、pages と renderer ディレクトリにいくつかファイルを置くことで準備が完了します。  
そして vite dev などで起動すると Hello World が確認できます。

## vite.config.ts の準備

plugins に vike の設定を追加し、prerender を true とします。

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import vike from "vike/plugin";

export default defineConfig({
  plugins: [react(), vike({ prerender: true })],
});
```

## src/pages と src/renderer の準備

### src/pages の準備

src/pages には各々のページとなる実装を追加します。  
ここではとりあえず h1 タグに Hello World でも書いておきましょう。  
もう少し複雑にする場合、ここで component などを呼び出して使うことになります。  
今回は `src/pages/` に `+Page.tsx` を置いて URL が`/`にあたるものを記述しています。  
また、後述するように `src/pages/hoge/+Page.tsx` のようにすると URL は `/hoge` になります。

```tsx
import React from "react";

export { Page };

function Page() {
  return (
    <div>
      <h1>Hello World</h1>
    </div>
  );
}
```

### src/renderer の準備

以下を参考に `+onRenderClient.tsx`と `+onRenderHtml.tsx`を作成します。

https://vike.dev/onRenderHtml
https://vike.dev/onRenderClient
https://github.com/vikejs/vike/tree/main/examples/react-minimal
https://github.com/vikejs/vike/tree/main/examples/react-full

ここは vike-react を使えば必要ない部分になるはずです。

https://vike.dev/react

src/renderer/+onRenderClient.tsx

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import type { PageContextBuiltInClient } from "vike";

export { render as onRenderClient };

async function render(pageContext: PageContextBuiltInClient) {
  const { Page } = pageContext;
  const root = document.getElementById("root")!;
  const pageProps = "pageProps" in pageContext && pageContext.pageProps;
  // [vike][Wrong Usage] pageContext.pageProps isn't defined on the client-side, see https://vike.dev/passToClient#error
  // ↓だと↑のようなエラーが起きる
  //  const { Page, pageProps } = pageContext;

  ReactDOM.hydrateRoot(
    root,
    <React.StrictMode>
      <Page {...pageProps} />
    </React.StrictMode>
  );
}
```

src/renderer/+onRenderHtml.tsx

```tsx
import React from "react";
import { renderToString } from "react-dom/server";
import { dangerouslySkipEscape, escapeInject } from "vike/server";

async function onRenderHtml(pageContext) {
  const { Page } = pageContext;
  //  const viewHtml = dangerouslySkipEscape(
  //    renderToString(
  //      <>
  //        <div>hoge</div>
  //        <Page />
  //      </>,
  //    ),
  //  );
  // ↑のようにPage以外に追加で書いたりしていると↓のようなエラーが出る
  /*
   * Uncaught Error: Hydration failed because the server rendered HTML didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:
   * - A server/client branch `if (typeof window !== 'undefined')`.
   * - Variable input such as `Date.now()` or `Math.random()` which changes each time it's called.
   * - Date formatting in a user's locale which doesn't match the server.
   * - External changing data without sending a snapshot of it along with the HTML.
   * - Invalid HTML tag nesting.
   *
   * It can also happen if the client has a browser extension installed which messes with the HTML before React loaded.
   */
  const viewHtml = dangerouslySkipEscape(renderToString(<Page />));
  const title = pageContext.config.title || "default title";
  const description = pageContext.config.description || "default description";

  return escapeInject`<!DOCTYPE html>
    <html>
        <title>${title}</title>
        <meta name="description" content="${description}">
        <body>
            <div id="root">${viewHtml}</div>
        </body>
    </html>`;
}
export default onRenderHtml;
```

最終的にディレクトリやコードの構成はこうなりました。

```bash
tree -I node_modules -I dist
.
├── package-lock.json
├── package.json
├── src
│   ├── pages
│   │   └── +Page.tsx
│   └── renderer
│       ├── +onRenderClient.tsx
│       └── +onRenderHtml.tsx
├── tsconfig.json
└── vite.config.ts

4 directories, 7 files
```

# src/pages にディレクトリを追加し別のページを追加する

次に/hoge というページを作成してみます。  
やることとしては `src/pages/hoge` に`+Page.tsx`を追加するだけです。

```tsx
import React from "react";

export { Page };

function Page() {
  return (
    <div>
      <h1>This is hoge page</h1>
      <a href="/">to root</a>
    </div>
  );
}
```

ディレクトリ構成はこんな感じ

```bash
tree -I node_modules -I dist
.
├── package-lock.json
├── package.json
├── src
│   ├── pages
│   │   ├── +Page.tsx
│   │   └── hoge
│   │       └── +Page.tsx
│   └── renderer
│       ├── +onRenderClient.tsx
│       └── +onRenderHtml.tsx
├── tsconfig.json
└── vite.config.ts

5 directories, 8 files
```

簡単ですね

# title タグを URL 毎に変更する

SSG やるなら当然 meta タグなどを URL 毎に変更したくなるのでそれをやります。  
`src/renderer/+config.ts` に対して、config に title を持たせられるように設定し、`src/pages/+config.ts` で 具体的な title を設定します。
`src/renderer/+onRenderHtml.tsx` にすでに記述してしまっていましたが、title を `pageContext.config.title` から取得して head タグに埋め込むようにしているという前提も含んでいます。

src/renderer/+config.ts

```ts
import type { Config } from "vike/types";

export const config = {
  meta: {
    title: {
      env: { server: true, client: true },
    },
    description: {
      env: { server: true, client: true },
    },
  },
} satisfies Config;
```

src/pages/+config.ts

```ts
export default {
  title: "title from config",
  description: "description from config",
};
```

この状態で vite build を行い `dist/client/index.html` を見ると title が `title from config` になっているかと思います。

```bash
cat dist/client/index.html|grep title
        <title>title from config</title>
```

# vike-react の拡張を使って src/renderer の実装周りを任せる

これは初めの方に記載したリポジトリには記載していないのですが、`vike-react` の extension を使うと renderer ディレクトリはそもそも必要なくなります。  
使い方としても、`npm install vike-react` と `src/pages/+config.ts` への extends の記載で完了するので非常に便利です。

src/pages/+config.ts

```ts
import vikeReact from "vike-react/config";

export default {
  extends: [vikeReact],
  title: "title from config",
  description: "description from config",
};
```

最終的にディレクトリはこうなりました。

```bash
tree -I node_modules -I dist
.
├── package-lock.json
├── package.json
├── src
│   └── pages
│       ├── +Page.tsx
│       ├── +config.ts
│       └── hoge
│           └── +Page.tsx
├── tsconfig.json
└── vite.config.ts
```

# まとめ

- vike と vite を使って react のアプリケーションを SSG しました
- 設定が簡単なので軽い気持ちで SSG できて便利

## (余談) GitHub Pages へのデプロイ

GitHub Pages へは vite build 後に dist/client というディレクトリが生成されるので、その dist/client ディレクトリをホスティングするとうまく表示できます。
