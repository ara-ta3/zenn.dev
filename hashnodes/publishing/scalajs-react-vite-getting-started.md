# Build a Todo App with Scala.js, React, and Vite

## 投稿情報

- 日本語原文: https://zenn.dev/ara_ta3/articles/scalajs-react-vite-getting-started
- 本文: hashnodes/scalajs-react-vite-getting-started.md（投稿時はfrontmatterを除く）
- 推奨slug: scalajs-react-vite-getting-started
- タグ候補: scala, scalajs, react, vite, tailwindcss（投稿時にHashnodeの候補から選択）
- SEO title: Scala.js + React + Vite: Build a Todo App
- SEO description: Build a Todo app with Scala.js, React, and Vite. Follow the Scala-to-JavaScript build flow and add typed Tailwind CSS classes with ScalaWind.
- カバー: images/hashnode/scalajs-react-vite-getting-started.png
- カバーalt: Software modules connected to a browser window containing a Todo list.
- 画像サイズ: 1672 × 941 px

英語本文は独立した記事として扱い、日本語原文へのリンクを本文に記載しています。canonicalを日本語原文へ自動設定する処理はありません。

## 検証

公開サンプル174a50dc24023f1cdda8024fddd8e68429760393を取得し、npm ci / npm run build成功。英語版のTailwind設定とScalaWind生成・見出し変更を一時サンプルに適用し、生成と本番ビルド成功。ブラウザ操作は未確認。

Hashnodeの下書き画面・公開画面での表示確認は未実施です。

## 原文からの調整

公開サンプルは通常のCSS、原文はTailwind併用という差を明記。sbt 1.10.11 / Scala 3.3.3 / React 19.1.1 / Vite 7.3.6の実在サンプルを基準に説明。原文のScalaWind 1.0.3は取得できず1.0.4へ変更。Tailwind 3.4.17 / PostCSS 8.5.30 / Autoprefixer 10.6.1で確認。生成したScalaファイルを除いた走査設定を維持。

サンプル依存の監査では、通常CSSの構成で1件、ScalaWind追加後に8件の指摘がありました。ビルド成功は依存監査の成功を意味しません。依存の修正はこのPRの対象外です。

## 画像生成プロンプト

生成方法: built-in image_gen。生成後に文字・構図を目視確認し、リポジトリへコピー。

```text
Use case: stylized-concept. Asset type: technical blog cover, landscape 16:9 matching an editorial series. Off-white paper background, dark navy large serif typography, teal and muted orange accents, gentle dimensional shapes and fine paper texture. Left half exact text: 'Scala.js' then 'React + Vite'. Right half: An elegant row of abstract software modules linked to a minimal browser window containing three task rows with checkboxes, suggesting Scala source transformed into an interactive browser application. Spacious balanced composition, comfortable margins, title completely readable at thumbnail size. No logos, watermarks, extra text, pseudo-code, invented syntax or tiny unreadable labels. This is conceptual cover artwork rather than a technical diagram.
```
