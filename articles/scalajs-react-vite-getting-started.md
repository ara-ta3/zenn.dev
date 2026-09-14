---
title: "Scala.js + React + ViteでTODOアプリを動かすまで"
emoji: "📝"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["scala", "scalajs", "react", "vite", "tailwindcss"]
published: false
---

## はじめに

今フロントエンドを書くとなったらTypeScriptほぼ一択ですが、昔はAltJSというのが流行っていました。そんな中、Vue.jsをScala.jsで触れたのがScala.jsとの思い出です。

https://arata.hatenadiary.com/entry/2015/08/07/215021

失礼なことにもうScala.jsの開発は流石に止まってるかなぁとか思ったんですが、依然として続いていることに驚きました。  

https://github.com/scala-js/scala-js

なんならscalajs-reactやscalawindなるものもあると知り笑顔になりました。  

https://github.com/japgolly/scalajs-react
https://github.com/nguyenyou/scalawind

なので今回はScala.js + React + TailwindでTODOアプリを作ってみました。  
TODO アプリの作り方そのものよりも、Scala のコードがどこで JavaScript になり、npm の React とどうつながってブラウザに表示されるのかを見ています。  
今回作ったものは、TODO の追加・完了・削除だけができるものです。

![TODO を追加・完了・削除できる画面](/images/scalajs-react/todo-app.png)

今回の登場人物は以下です。

- Scala.js: Scala を JavaScript に変換してブラウザで動かす仕組み
- scalajs-react: React の API を Scala から型安全に使うためのライブラリ
- Vite: 開発サーバーと、ブラウザ向けアセットの配信・ビルド
- Tailwind CSS: utility class から CSS を生成する仕組み
- ScalaWind: Tailwind の class を Scala の型付き API として書くためのコード生成ツール
- sbt: Scala のコードを JavaScript にビルドする
- npm: React、Vite、Tailwind などの JavaScript 側の依存関係を取得する

最終的なディレクトリ構成は次のようになります。

```text
scalajs-react-vite-todo/
├── build.sbt
├── package.json
├── index.html
├── main.js
├── style.css
├── vite.config.js
├── postcss.config.js
├── tailwind.config.cjs
├── project/
│   ├── build.properties
│   └── plugins.sbt
└── src/main/scala/todo/
    ├── Main.scala
    ├── components/
    │   ├── TodoForm.scala
    │   └── TodoList.scala
    ├── domain/
    │   └── Todo.scala
    └── pages/
        └── TodoPage.scala
```

:::message
ScalaWind が生成する `src/main/scala/todo/scalawind.scala` は `.gitignore` に入れます。`npm install` 時に再生成できるため、生成物をコミットする必要はありません。
:::

## 1. ブラウザが最初に読むファイルを用意する

まず、ブラウザが読む HTML と JavaScript の入口を作ります。ブラウザは `index.html` を開き、そこから `main.js` を読みます。

```html:index.html
<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Scala.js TODO</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/main.js"></script>
  </body>
</html>
```

`#app` は React が画面を描画する場所です。まだ TODO アプリのコードはありませんが、React の描画先だけ先に用意します。

```js:main.js
import "./style.css";
import "scalajs:main.js";
```

`style.css` は後で Tailwind CSS に処理してもらう CSS の入口です。`scalajs:main.js` は、後で設定する Vite plugin が Scala.js の出力先に解決します。

## 2. ScalaをJavaScriptに変換し、Viteにつなぐ

次に sbt と Scala.js の設定を置きます。`project/plugins.sbt` は sbt が使う plugin、`build.sbt` はアプリの Scala 設定です。

```scala:project/plugins.sbt
addSbtPlugin("org.scala-js" % "sbt-scalajs" % "1.22.0")
```

```text:project/build.properties
sbt.version=1.13.0
```

```scala:build.sbt
import org.scalajs.linker.interface.{ModuleKind, ModuleSplitStyle}

lazy val todoApp = project
  .in(file("."))
  .enablePlugins(ScalaJSPlugin)
  .settings(
    scalaVersion := "3.9.0",
    scalaJSUseMainModuleInitializer := true,
    scalaJSLinkerConfig ~= {
      _.withModuleKind(ModuleKind.ESModule)
        .withModuleSplitStyle(ModuleSplitStyle.SmallModulesFor(List("todo")))
    },
    libraryDependencies ++= Seq(
      "org.scala-js" %%% "scalajs-dom" % "2.8.1",
      "com.github.japgolly.scalajs-react" %%% "core" % "4.0.0"
    )
  )
```

`scalaJSUseMainModuleInitializer := true` は、生成された JavaScript を読み込んだときに Scala の `main` を実行する設定です。ESM で出力する設定は、Vite が JavaScript module として扱えるようにするためです。

Vite plugin は `scalajs:main.js` を sbt が生成する JavaScript へつなぎます。

```js:vite.config.js
import { defineConfig } from "vite";
import scalaJSPlugin from "@scala-js/vite-plugin-scalajs";

export default defineConfig({
  plugins: [scalaJSPlugin()],
});
```

npm 側の依存関係とコマンドは `package.json` に書きます。Scala の依存関係は sbt、React や Vite の依存関係は npm が管理する形です。

```json:package.json
{
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "postinstall": "scalawind generate --check-duplication --check-optimization -f scalajs-react -o ./src/main/scala/todo/scalawind.scala -p todo"
  },
  "dependencies": {
    "react": "19.3.0",
    "react-dom": "19.3.0"
  },
  "devDependencies": {
    "@scala-js/vite-plugin-scalajs": "1.1.0",
    "autoprefixer": "10.6.0",
    "postcss": "8.5.28",
    "scalawind": "1.0.3",
    "tailwindcss": "3.4.17",
    "vite": "8.3.0"
  }
}
```

## 3. ScalaからTailwindのclassを型安全に書けるようにする

Tailwind の class は文字列で書けますが、今回は ScalaWind を使います。ScalaWind は Tailwind の設定から `tw` という Scala の API を生成します。

例えば、次の Scala コードです。

```scala
tw.rounded_lg.bg_blue_600.px_3.py_2.text_white
```

ScalaWind によって、次の Tailwind class へ展開されます。

```text
rounded-lg bg-blue-600 px-3 py-2 text-white
```

`package.json` の `postinstall` には、すでに生成コマンドを書いてあります。ただし ScalaWind は `tailwind.config.cjs` を読むため、先に Tailwind の設定を置きます。

## 4. Tailwind CSSを生成してブラウザで読み込めるようにする

`style.css` は Tailwind の directive だけを書きます。Vite がこのファイルを PostCSS に渡し、Tailwind が使われている class の CSS を生成します。

```css:style.css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

PostCSS に Tailwind と Autoprefixer を登録します。

```js:postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

Tailwind は class が書かれているファイルを走査します。Scala のソースを読めるように ScalaWind の transform を指定します。

```js:tailwind.config.cjs
const { scalaSourceTransform } = require("scalawind/dist/transform");

module.exports = {
  content: {
    files: [
      "./index.html",
      "./src/main/scala/todo/Main.scala",
      "./src/main/scala/todo/components/**/*.scala",
      "./src/main/scala/todo/domain/**/*.scala",
      "./src/main/scala/todo/pages/**/*.scala",
    ],
    transform: scalaSourceTransform,
  },
};
```

この設定が揃ってから依存関係を取得します。

```bash
npm install
```

`npm install` の最後に `postinstall` が実行され、`scalawind.scala` が生成されます。生成ファイルまで走査対象に含めると、使っていない Tailwind class も大量に CSS へ出てしまうため、`tailwind.config.cjs` の対象から外しています。

## 5. Scalaで画面を書く

ここで初めて画面を実装します。`Main` は `#app` を React の root にします。

```scala:src/main/scala/todo/Main.scala
package todo

import japgolly.scalajs.react.ReactDOMClient
import org.scalajs.dom
import todo.pages.TodoPage

object Main {
  def main(args: Array[String]): Unit = {
    ReactDOMClient.createRoot(dom.document.getElementById("app")).render(TodoPage())
  }
}
```

TODO の値は `domain` に置きます。ID を `Todo.Id` にして、ただの `Int` と区別します。

```scala:src/main/scala/todo/domain/Todo.scala
package todo.domain

final case class Todo(id: Todo.Id, title: String, isDone: Boolean)

object Todo {
  final case class Id(value: Int)
}
```

`TodoPage` が state と追加・完了・削除の操作を持ち、`TodoForm` と `TodoList` は props を受け取って描画します。

```scala:src/main/scala/todo/pages/TodoPage.scala
package todo.pages

import japgolly.scalajs.react.*
import japgolly.scalajs.react.vdom.html_<^.*
import todo.*
import todo.components.{TodoForm, TodoList}
import todo.domain.Todo

object TodoPage {
  private val initialTodos = Vector(
    Todo(Todo.Id(1), "Scala.js を触ってみる", false),
    Todo(Todo.Id(2), "記事を書く", false),
    Todo(Todo.Id(3), "React の仕組みを読む", true)
  )

  private val Component = ScalaFnComponent.withHooks[Unit]
    .useState("")
    .useState(initialTodos)
    .render((_, title, todos) => {
      def addTodo: Callback = {
        val trimmedTitle = title.value.trim

        if (trimmedTitle.isEmpty) {
          Callback.empty
        } else {
          todos.modState { items =>
            val nextId = items.map(_.id.value).maxOption.getOrElse(0) + 1
            items :+ Todo(Todo.Id(nextId), trimmedTitle, false)
          } >> title.setState("")
        }
      }

      def toggleTodo(todoId: Todo.Id): Callback = {
        todos.modState(_.map { todo =>
          if (todo.id == todoId) todo.copy(isDone = !todo.isDone)
          else todo
        })
      }

      def deleteTodo(todoId: Todo.Id): Callback = {
        todos.modState(_.filterNot(_.id == todoId))
      }

      <.main(^.className := tw.min_h_screen.bg_slate_50.py_20.css,
        <.div(^.className := tw.mx_auto.max_w_xl.rounded_2xl.border.border_slate_200.bg_white.p_8.shadow_sm.css,
          <.h1(^.className := tw.text_3xl.font_bold.tracking_tight.text_slate_800.css, "TODO"),
          TodoForm(TodoForm.Props(title.value, title.setState, addTodo)),
          TodoList(TodoList.Props(todos.value, toggleTodo, deleteTodo))
        )
      )
    })

  def apply() = Component()
}
```

`tw` は ScalaWind が生成した API です。scalajs-react は React の代わりではなく、Scala 側の VDOM や `useState`、`Callback` を npm の React API へつなぐ層です。実際の描画と state 更新は React / react-dom が担当します。

## 6. Viteでビルドして動かす

開発サーバーは Vite だけで起動できます。

```bash
npm run dev
```

Vite plugin が Scala.js の出力を必要なタイミングで扱うため、まずはこのコマンドだけで `http://localhost:5173` で開けるサーバが起動します。  

本番ビルドも Vite だけで実行します。

```bash
npm run build
```

このとき Vite plugin が `fullLinkJS` を実行し、Scala.js の JavaScript と Tailwind の CSS を production 用のアセットへまとめます。

:::message
Scala の変更だけを追いながら JavaScript を更新したいときは、別ターミナルで次を実行できます。

```bash
sbt '~fastLinkJS'
```

これは Scala ファイルを保存するたびに、Scala.js の JavaScript 出力を更新します。通常の起動には必須ではなく、Scala.js の差分更新を確認したいときの補助コマンドです。
:::


## Scala.js + Reactがブラウザで動くまで

全体の流れは以下です。

```text
Scala のソースコード
  ↓ sbt の `fastLinkJS` / `fullLinkJS`
JavaScript
  ↓ Vite
ブラウザ
  ↓ React が DOM を描画
画面
```

`sbt` が Scala のコードをブラウザで実行できる JavaScript にビルドします。開発中は素早く出力する `fastLinkJS`、本番ビルドでは時間をかけて最適化する `fullLinkJS` が使われます。

Vite は Scala を直接コンパイルするものではありません。Vite plugin を通じて sbt の生成した JavaScript を読み込み、HTML や Tailwind CSS と一緒にブラウザへ配信します。最後に React が DOM を描画します。

## まとめ

- Scala.js、現代でも普通に動きました。
- React + Tailwind cssという環境で動く状況に非常に驚きました
  - ~~もの好きがいるのは時が経っても同じですね~~
- まずないかなと思いますがScala.jsをフロントエンドに使いたくなったときに参考になったら幸いです。

### 余談

KurashiLabという「お金と時間の余白をつくって、人生を楽しむ。」というコンセプトのサービス個人開発で作っていますが、ここは上記の構成でやっています。  
AIなかったら無理かなという気持ちが結構強いですが、Scala.jsやcatsを混ぜて試すという観点では非常に楽しいです。  
https://kurashilab.app/

専用にしたXアカウントもあるので気になる方はフォローお願いします。  
https://x.com/KurashiLabApp
