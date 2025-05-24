---
title: "SSG a Vite+TypeScript+React Dynamic Routing Page with Meta Info Using Vike"
emoji: "🐕"
type: "tech"
topics: ["React", "SSG", "Vite", "Vike", "contest2025ts"]
published: true
---

## Introduction

Previously, I wrote an article titled ["SSG Vite+TypeScript+React pages using Vike"](https://zenn.dev/ara_ta3/articles/typescript-vike-ssg-getting-started) where I explored SSG with Vite and Vike.  
In this article, I share my experience embedding meta information like title and description into dynamic pages (e.g., `/hoge/:id`) and performing SSG.

The versions of the tools used are as follows:

```
"@vitejs/plugin-react": "^4.4.1",
"typescript": "^5.8.3",
"vike": "^0.4.229",
"vike-react": "^0.6.1",
"vite": "^6.3.5"
```

GitHub Repository:  
https://github.com/ara-ta3/vike-ssg-dynamic-pages-getting-started

## Preparation

We'll be using the `vike-react` plugin.  
In my previous article, I tried an approach without `vike-react`, but it seems rare not to use it, so this article assumes its use.

Vike settings are now defined in `src/pages/+config.ts`.  
While they were previously in `vike.config.js`, doing so now triggers a warning:

```
23:00:00 [vike][Warning] Define Vike settings in +config.js instead of vite.config.js https://vike.dev/migration/settings
```

Here’s how the configuration file looks:  
`src/pages/+config.ts`

```ts
import vikeReact from "vike-react/config";

export default {
  extends: [vikeReact],
  prerender: true,
};
```

## Overview

Here’s what we’ll be doing:

- Define dynamic route path in `+route.ts`
- Create page content in `+Page.tsx`
- Fetch title in `+onBeforeRender.ts` and pass to `pageContext`
- Output meta info in `+Head.tsx`
- List static paths in `+onBeforePrerenderStart.ts`

Final directory structure under `src/pages/hoge`:

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

## Defining the Dynamic Route (`+route.ts`)

Enable handling of dynamic route `/hoge/@id`:

```ts
export default "/hoge/@id";
```

https://vike.dev/route

## Creating Page Content (`+Page.tsx`)

Props aren't passed directly, so use `usePageContext()`.  
The `PageContext` generic is defined as `PageContext<Data = unknown>`, so we use `as` to specify the data shape:

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

## Fetching Data and Passing Meta Info to `PageContext` (`+onBeforeRender.ts`)

Retrieve data and return it as `pageContext`:

```ts
import { PageContext } from "vike/types";

export async function onBeforeRender(pageContext: PageContext) {
  const id = parseInt(pageContext.routeParams.id);
  let title = "Hoge null";
  if (isNaN(id)) {
    return {
      pageContext: {
        data: { id, title, description: "Hoge null" },
      },
    };
  }
  title = `Hoge ${id}`;
  return {
    pageContext: {
      data: { id, title: `Hoge ${id}`, description: `Hoge ${id}` },
    },
  };
}
```

https://vike.dev/onBeforeRender

## Outputting Meta Info (`+Head.tsx`)

Responsible for outputting meta info:

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

## Listing Static Paths (`+onBeforePrerenderStart.ts`)

Enumerate the paths for prerendering:

```ts
export { onBeforePrerenderStart };

async function onBeforePrerenderStart() {
  const ids = ["1", "2"];
  return ids.map((id) => `/hoge/${id}`);
}
```

https://vike.dev/onBeforePrerenderStart

## Build

Run `vike build` to generate the HTML files:

```
./node_modules/.bin/vike build
...
✓ 3 HTML documents pre-rendered.
✓ built in 633ms
```

## Conclusion

Using Vite, Vike, and Vike-react, we were able to perform SSG for pages with dynamic IDs.  
It was surprisingly straightforward, reaffirming how convenient this stack is.  
However, Vike is still under active development, and small updates can cause warnings or break old setups.  
We need to stay flexible and test things ourselves while adapting to changes.

I hope this article helps you get started with SSG for dynamic routes!

## Reference

You can see this implementation live here:  
https://nekometry.web.app/?utm_source=zenn.dev&utm_medium=referral&utm_campaign=article20250513
