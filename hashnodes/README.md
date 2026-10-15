# 英語記事とHashnodeへの投稿

英語本文は `hashnodes/<slug>.md`、カバーは `images/hashnode/<slug>.png`、投稿情報と画像プロンプトは `hashnodes/publishing/<slug>.md` に保存します。

公開状況はHashnode側で確認します。英語原稿と投稿情報には公開ステータスを持たせず、投稿後の管理情報更新も不要とします。

## 今回の原稿

| 記事 | 本文 | 投稿情報 |
| --- | --- | --- |
| MySQL latest row per group | [本文](mysql-group-latest-row.md) | [投稿情報](publishing/mysql-group-latest-row.md) |
| Python Protocol + DI | [本文](python-protocol-getting-started.md) | [投稿情報](publishing/python-protocol-getting-started.md) |
| Go Viper + .env | [本文](golang-viper-reading-env.md) | [投稿情報](publishing/golang-viper-reading-env.md) |
| Scala.js + React + Vite | [本文](scalajs-react-vite-getting-started.md) | [投稿情報](publishing/scalajs-react-vite-getting-started.md) |
| MySQL median | [本文](mysql-median-sql.md) | [投稿情報](publishing/mysql-median-sql.md) |

## 生成スキル

[hashnode-english-article](../.agents/skills/hashnode-english-article/SKILL.md) に、候補選定から英語化・コード検証・画像生成・投稿情報作成までの手順をまとめています。このリポジトリ内の `.agents/skills/` に置いたスキルです。

依頼例:

```text
$hashnode-english-article を使って articles/<slug>.md を英語化し、カバーも作成してください。
```

画像生成にはbuilt-in image_genを使います。本文のコード、カバーの文字と構図、投稿情報の整合を確認し、実行できていない範囲も残します。

## 投稿するとき

1. 投稿情報のタイトル・slug・タグ候補・SEO説明文・カバーを確認する。
2. Hashnodeへfrontmatterを除いた本文を渡し、画像と投稿情報を設定する。
3. 下書き画面でコード・表・リンク・カバーの表示を確認する。

スキルの追加だけではHashnodeへの投稿は行いません。次の段階として下書き作成を連携する場合は、現行の連携手段・認証・画像アップロードを確認し、作成済みのIDを記録して重複作成を避ける設計にします。

## 検証と原文からの調整

- MySQL最新行: 8.0.36でCTE、派生テーブル、同時刻の選択、MAX/JOINの結果を確認。日本語記事でも、タイブレーク規則と最新日時に一致する全行の取得を説明。
- MySQL中央値: 日本語・英語のSQLをONLY_FULL_GROUP_BY有効の8.0.36で実行。両手法で奇数・偶数・1件・0件を確認。日本語原文のLIMIT/OFFSET構文、非集約列と集約関数の混在、説明の不一致を訂正。
- Python: 3.13.16、dependency-injector 4.49.1、pytest 9.1.1。本文から抽出したコードが動作し、6テストとmypyの `--check-untyped-defs` が成功。型注釈、Protocol、コンテナの役割を補足し、fixtureの採番値も調整。
- Go: 1.27.2、Viper 1.21.0。本文から抽出したコードで期待値を確認し、`go vet ./...` 成功。`.env` の明示指定とローカルViperインスタンスを使用。
- Scala.js: 公開サンプルの通常CSS構成と、英語記事で追加するTailwind/ScalaWind構成の生成・本番ビルドが成功。原文と公開サンプルの構成差、バージョンの調整、依存監査の結果は投稿情報に記載。ブラウザ操作は未確認。
- カバー: 5枚とも1672 × 941 px。生成後に目視確認。
- Hashnodeの下書き・公開画面での表示確認は未実施。
