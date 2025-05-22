---
title: "Using Vike to SSG a Vite + TypeScript + React Page"
emoji: "🐈"
type: "tech"
topics: ["vike", "vite", "ssg", "react", "typescript"]
published: true
---

# Overview

I wanted to host it on GitHub Pages, so I thought, why not try SSG while I'm at it.  
While developing with Vite + TypeScript + React, I came across a library called Vike for SSG.  
Originally, it seems to have been a Vite plugin called `vite-plugin-ssr`.

https://vite-plugin-ssr.com/

> The vite-plugin-ssr project has been renamed Vike.

This time, I’ll use Vike to generate static files from a page built with TypeScript + React.

:::message
Although you can skip some parts by using the `vike-react` extension, I’m not using it here to better understand how Vike works.

https://github.com/vikejs/vike-react
:::

Here’s the repository with the code I used:

https://github.com/ara-ta3/vike-ssg-getting-started

The versions used for Vite, Vike, and React are:

```
"react": "19.0.0"
"react-dom": "19.0.0"
"vike": "0.4.210"
"vite": "6.0.5"
```

# Outputting to HTML

Let’s start with a basic Hello World.  
Add settings in `vite.config.ts`, place some files under `pages` and `renderer` directories, and run `vite dev` to see Hello World.

## Setup vite.config.ts

Add Vike to plugins and set `prerender` to true.

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import vike from "vike/plugin";

export default defineConfig({
  plugins: [react(), vike({ prerender: true })],
});
```

## Setup src/pages and src/renderer

### src/pages

Implement individual pages here.  
Let’s put an `h1` with Hello World for now.  
For more complex pages, you’ll call components here.  
Place `+Page.tsx` under `src/pages/` to match URL `/`.  
For `/hoge`, create `src/pages/hoge/+Page.tsx`.

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

### src/renderer

Refer to the following to create `+onRenderClient.tsx` and `+onRenderHtml.tsx`.

https://vike.dev/onRenderHtml  
https://vike.dev/onRenderClient  
https://github.com/vikejs/vike/tree/main/examples/react-minimal  
https://github.com/vikejs/vike/tree/main/examples/react-full

These files are unnecessary if using `vike-react`.

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

Directory and file structure:

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
```

# Add a New Page Under src/pages

Let’s add a page at `/hoge`.  
Just add `+Page.tsx` in `src/pages/hoge`.

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

Directory structure:

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
```

Nice and simple.

# Customize Title Tag per URL

If you're doing SSG, you’ll want meta tags like the title to vary by URL.  
In `src/renderer/+config.ts`, add config to support `title`, then set the title in `src/pages/+config.ts`.

Also, `src/renderer/+onRenderHtml.tsx` already fetches `pageContext.config.title` for the head tag.

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

Run `vite build` and check `dist/client/index.html`, you’ll see the title set.

```bash
cat dist/client/index.html|grep title
        <title>title from config</title>
```

# Simplify Renderer with vike-react

Although not shown in the original repo, using the `vike-react` extension eliminates the need for the `renderer` directory entirely.  
Just run `npm install vike-react` and add an `extends` field in `src/pages/+config.ts`.

src/pages/+config.ts

```ts
import vikeReact from "vike-react/config";

export default {
  extends: [vikeReact],
  title: "title from config",
  description: "description from config",
};
```

Directory structure:

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

# Summary

- Used Vike and Vite to statically generate a React app
- Easy configuration makes SSG very convenient

## (Side Note) Deploying to GitHub Pages

After running `vite build`, host the `dist/client` directory to deploy to GitHub Pages.

## References

Used in the following sites:

### Nekometry

https://nekometry.web.app/?utm_source=hashnode&utm_medium=referral&utm_campaign=article20250523

### Personal Site

https://github.com/ara-ta3/ara-ta3.github.io  
https://ara-ta3.github.io/
