---
title: "Build a Todo App with Scala.js, React, and Vite"
emoji: "📝"
type: "tech"
topics: ["scala", "scalajs", "react", "vite", "tailwindcss"]
published: false
---

## Introduction

I first tried Scala.js with Vue.js years ago. Recently, I revisited it and found that the ecosystem also has React bindings and ScalaWind for writing Tailwind classes through a typed Scala API.

This article follows how a small Todo application reaches the browser: Scala becomes JavaScript, Vite serves it, and React renders the page. The application supports adding, completing, and deleting tasks.

It is an English adaptation of my [Japanese article on Zenn](https://zenn.dev/ara_ta3/articles/scalajs-react-vite-getting-started).

The [public sample](https://github.com/ara-ta3/zlab-scalajs-react-getting-started/tree/174a50dc24023f1cdda8024fddd8e68429760393) uses plain CSS. I'll use that reproducible baseline first, then add the Tailwind/ScalaWind integration from the Japanese article. The versions below reflect this checked configuration rather than every version listed in the original article.

## What each tool does

| Tool | Role |
| --- | --- |
| Scala.js | Compiles and links Scala into JavaScript |
| scalajs-react | Exposes React APIs to Scala code |
| sbt | Manages Scala dependencies and the Scala.js build |
| npm | Manages React, Vite, and the CSS tooling |
| Vite | Serves and bundles the browser assets |
| Tailwind CSS | Generates CSS for utility classes, in the optional extension |
| ScalaWind | Generates a typed Scala API for Tailwind classes |

```text
Scala source -> sbt / Scala.js -> JavaScript -> Vite -> browser
                                                        |
                                         React renders the DOM
```

Vite does not compile Scala directly. Its Scala.js plugin connects it to sbt's output. The React implementation itself comes from npm; scalajs-react is the Scala-facing layer.

## Run the complete baseline

Install a JDK, sbt, and Node.js. This example uses Scala 3.3.3, sbt 1.10.11, Scala.js 1.22.0, scalajs-react 4.0.0, React 19.1.1, and Vite 7.3.6. The build was checked with Node.js 24.

```bash
git clone https://github.com/ara-ta3/zlab-scalajs-react-getting-started.git
cd zlab-scalajs-react-getting-started
git checkout 174a50dc24023f1cdda8024fddd8e68429760393
npm ci
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`. The checked-out sample has Japanese task labels; the snippets below translate them into English.

The important files are:

```text
build.sbt
project/plugins.sbt
project/build.properties
package.json
index.html
main.js
style.css
vite.config.js
src/main/scala/todo/
  Main.scala
  domain/Todo.scala
  pages/TodoPage.scala
  components/TodoForm.scala
  components/TodoList.scala
```

## Connect the HTML entry point to Scala.js

The browser starts with `index.html`:
```html
<!doctype html>
<html lang="en">
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

React will render into `#app`. The module entry point, `main.js`, imports the stylesheet and Scala.js module:
```javascript
import "./style.css";
import "scalajs:main.js";
```

`scalajs:main.js` is resolved by the Vite plugin configured in `vite.config.js`:
```javascript
import { defineConfig } from "vite";
import scalaJSPlugin from "@scala-js/vite-plugin-scalajs";

export default defineConfig({
  plugins: [scalaJSPlugin()],
});
```

## Configure sbt and Scala.js

In `project/plugins.sbt`, enable the Scala.js plugin:
```scala
addSbtPlugin("org.scala-js" % "sbt-scalajs" % "1.22.0")
```

In `project/build.properties`, select sbt:
```text
sbt.version=1.10.11
```

The application's `build.sbt` configures Scala, the JavaScript module format, and its Scala dependencies:
```scala
import org.scalajs.linker.interface.{ModuleKind, ModuleSplitStyle}

lazy val todoApp = project
  .in(file("."))
  .enablePlugins(ScalaJSPlugin)
  .settings(
    scalaVersion := "3.3.3",
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

`scalaJSUseMainModuleInitializer := true` runs the Scala `main` method when the generated module loads. ES modules let Vite handle the linked JavaScript as modules.

The `%%%` dependency notation selects Scala.js artifacts. It does not install npm's React package; that dependency is managed separately in `package.json`.

## Render the Todo application

`Main.scala` connects the Scala component to the React root:
```scala
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

The domain value, in `domain/Todo.scala`, uses `Todo.Id` to distinguish a task ID from an arbitrary integer:
```scala
package todo.domain

final case class Todo(id: Todo.Id, title: String, isDone: Boolean)

object Todo {
  final case class Id(value: Int)
}
```

`pages/TodoPage.scala` owns the input text, the list, and the operations:
```scala
package todo.pages

import japgolly.scalajs.react.*
import japgolly.scalajs.react.vdom.html_<^.*
import todo.components.{TodoForm, TodoList}
import todo.domain.Todo

object TodoPage {
  private val initialTodos = Vector(
    Todo(Todo.Id(1), "Try Scala.js", false),
    Todo(Todo.Id(2), "Write an article", false),
    Todo(Todo.Id(3), "Read about React", true)
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

      <.main(^.className := "todo-app",
        <.h1("TODO"),
        TodoForm(TodoForm.Props(title.value, title.setState, addTodo)),
        TodoList(TodoList.Props(todos.value, toggleTodo, deleteTodo))
      )
    })

  def apply() = Component()
}
```

`useState` keeps the input and list state. `Callback` represents the effects passed into React's event handlers. `modState` updates the list from its previous value.

`components/TodoForm.scala` receives its value and callbacks as props:
```scala
package todo.components

import japgolly.scalajs.react.*
import japgolly.scalajs.react.vdom.html_<^.*
import org.scalajs.dom

object TodoForm {
  final case class Props(value: String, onChange: String => Callback, onSubmit: Callback)

  private val Component = ScalaFnComponent[Props] { props =>
    <.form(
      ^.className := "todo-form",
      ^.onSubmit ==> (_.preventDefaultCB >> props.onSubmit),
      <.input(
        ^.value := props.value,
        ^.onChange ==> { event =>
          props.onChange(event.target.asInstanceOf[dom.HTMLInputElement].value)
        },
        ^.placeholder := "Enter a task"
      ),
      <.button(^.`type` := "submit", "Add")
    )
  }

  def apply(props: Props) = Component(props)
}
```

The form prevents the browser's default submit behavior and runs the callback supplied by the page.

`components/TodoList.scala` renders the list and passes task IDs back to the page:
```scala
package todo.components

import japgolly.scalajs.react.*
import japgolly.scalajs.react.vdom.html_<^.*
import todo.domain.Todo

object TodoList {
  final case class Props(
    todos: Vector[Todo],
    onToggle: Todo.Id => Callback,
    onDelete: Todo.Id => Callback
  )

  private val Component = ScalaFnComponent[Props] { props =>
    <.ul(^.className := "todo-list",
      props.todos.map { todo =>
        <.li(^.key := todo.id.value.toString, ^.className := "todo-item",
          <.label(^.className := "todo-label",
            <.input.checkbox(
              ^.checked := todo.isDone,
              ^.onChange --> props.onToggle(todo.id)
            ),
            <.span(^.classSet("is-done" -> todo.isDone), todo.title)
          ),
          <.button(
            ^.className := "delete-button",
            ^.onClick --> props.onDelete(todo.id),
            "Delete"
          )
        )
      }.toVdomArray
    )
  }

  def apply(props: Props) = Component(props)
}
```

The application keeps its state in memory. Refreshing the page resets the tasks; there is no backend or persistent storage in this example. The complete baseline stylesheet is in the linked sample's `style.css`.

## Add Tailwind CSS and ScalaWind

The Japanese article also explores typed Tailwind classes. This extension keeps the baseline app and its existing CSS, adding a typed class expression to the heading.

The configuration below uses Tailwind CSS 3's PostCSS integration. It is not a Tailwind CSS 4 setup. ScalaWind 1.0.4 is used here because the version listed in the original article could not be retrieved during verification.

Install the extension's packages:

```bash
npm install --save-dev --save-exact scalawind@1.0.4 tailwindcss@3.4.17 postcss@8.5.30 autoprefixer@10.6.1
```

Create `postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

Create `tailwind.config.cjs`:

```javascript
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

The generated ScalaWind source is deliberately excluded from the scanned paths. Scanning its full generated API would include utility classes the application does not use.

Prepend these directives to the existing `style.css`, keeping the baseline rules below them:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Register the generator and run it:

```bash
npm pkg set 'scripts.postinstall=scalawind generate --check-duplication --check-optimization -f scalajs-react -o ./src/main/scala/todo/scalawind.scala -p todo'
npm run postinstall
```

Add `src/main/scala/todo/scalawind.scala` to `.gitignore`. Subsequent installs can regenerate the file through `postinstall` after the Tailwind configuration exists.

In `TodoPage.scala`, add this import:

```scala
import todo.*
```

Then replace `<.h1("TODO")` with:

```scala
<.h1(^.className := tw.text_3xl.font_bold.text_slate_800.css, "TODO")
```

ScalaWind generates the typed `tw` API. The expression produces `text-3xl font-bold text-slate-800`; Tailwind generates the corresponding CSS. ScalaWind generates Scala code, while Tailwind generates CSS, so both parts are needed.

## Build for production

```bash
npm run build
npm run preview
```

The Vite plugin connects the production build to Scala.js's `fullLinkJS`. The output combines the linked JavaScript and CSS under `dist/`.

For a separate Scala watch process during development, run this in another terminal:

```bash
sbt '~fastLinkJS'
```

`fastLinkJS` favors a short development cycle; `fullLinkJS` performs production optimizations. A successful build checks compilation and bundling, while browser interaction still needs its own check.

## Summary

The flow became easier for me to follow once I separated the roles: sbt and Scala.js produce JavaScript, scalajs-react connects Scala components to React, and Vite serves or bundles the assets. ScalaWind and Tailwind add typed utility classes and the corresponding CSS on top.

I also use this combination in [KurashiLab](https://kurashilab.app/), a personal project about making room for more time and financial flexibility. Revisiting Scala.js has been a fun way to experiment with Scala on the frontend again.

## References

- [Scala.js: Getting Started with Scala.js and Vite](https://www.scala-js.org/doc/tutorial/scalajs-vite.html)
- [Scala.js Vite plugin](https://github.com/scala-js/vite-plugin-scalajs)
- [scalajs-react](https://github.com/japgolly/scalajs-react)
- [ScalaWind](https://github.com/nguyenyou/scalawind)
