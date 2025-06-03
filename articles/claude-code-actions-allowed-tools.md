---
title: "Claude Code Actionで allowed_toolsにBash(npm:*) を追加してコマンドを実行できるようにする"
emoji: "🐕"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["claude", "claudecode", "vibecodeing"]
published: false
---

## はじめに

Claude Code Action は、AI アシスタントによるコード生成や編集を支援する機能ですが、デフォルトではセキュリティ上の理由からコマンド実行が制限されています。  
この記事は、`allowed_tools` の設定を追加して、npm コマンドを実行できるようにしたときの備忘録です。

https://github.com/anthropics/claude-code-action

## 環境

まずはサンプルコードです。  
uvu によるシンプルなテストコードを用意し、それを実行するためのコマンドを package.json の scripts に用意しました。

https://github.com/ara-ta3/claude-code-action-getting-started

```bash
tree
.
├── node_modules
├── package-lock.json
├── package.json
└── sample.test.js

2 directories, 3 files

cat package.json
{
  "name": "claude-code-action-getting-started",
  "version": "1.0.0",
  "type": "module",
  "repository": {
    "type": "git",
    "url": "git+ssh://git@github.com/ara-ta3/claude-code-action-getting-started.git"
  },
  "license": "ISC",
  "scripts": {
    "test": "node sample.test.js"
  },
  "devDependencies": {
    "uvu": "^0.5.6"
  }
}
```

これを検証用の issue を立てて以下のようなプロンプトで claude に試してもらっています。

```
@claude このRepositoryでコマンドを打てるかどうかの確認をしたいです

以下のコマンドを実行できるか確認してください
結果は表にして表示してください

- npm run test
- node sample.test.js
```

https://github.com/ara-ta3/claude-code-action-getting-started/issues/2

## allowed_tools の動作検証

### 初めにまとめ

- Bash の全てを許容する場合は `Bash` と記述する
- 特定のコマンドのみにしたい場合は `Bash(npm:*),Bash(node:*)` のように記述する
- サブコマンドまで指定したい場合は `Bash(npm install),Bash(npm run test)` のように記述する

| Configuration                          | npm commands | node commands | Status             |
| -------------------------------------- | ------------ | ------------- | ------------------ |
| No allowed_tools                       | ❌           | ❌            | Permission Denied  |
| `Bash(npm*)`                           | ❌           | ❌            | シンタックスエラー |
| `Bash(npm:*)`                          | ✅           | ❌            | npm のみ           |
| `Bash(npm:*),Bash(node:*)`             | ✅           | ✅            | npm + node         |
| `Bash`                                 | ✅           | ✅            | フルアクセス       |
| `Bash(npm:install),Bash(npm:run)`      | ❌           | ❌            | シンタックスエラー |
| `Bash(npm install),Bash(npm run test)` | ✅           | ✅            | **Not working**    |

### デフォルト状態

Claude Code Action では、初期設定ではセキュリティ上の理由からすべてのコマンド実行が禁止されています。  
なので npm など package 管理ツールのコマンドを実行できるようにするためには `allowed_tools` という欄でコマンドを許可する設定が必要になります。

### 全てを許可するパターン

コマンド全てを許容する場合は `Bash` と記述するだけです。  
全てが許されるのでプライベートリポジトリなどで行うのが無難かもしれません。

```yaml
- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Bash"
```

### サブコマンド全てを許容するパターン

サブコマンド以下全てを許容した上で特定のコマンドのみを許容する場合は `Bash(npm:*),Bash(node:*)` のように記述します。

```yaml
- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Bash(npm:*),Bash(node:*)"
```

`Bash(コマンド:*)` というような記述ですね。  
このとき、package.json の scripts 以下にコマンドが定義されている場合は許可されていなくても実行できます。

つまり、 `Bash(npm:*)` しかなかったとして、package.json の scripts 以下に `"test": "node sample.test.js"` の記述がある場合、 node の権限なしで npm の権限のみであっても`npm run test`経由で実行できます。

### サブコマンドも指定して許容するパターン

完全にコマンドを指定して許容する場合は `Bash(npm install)` のように記述します。

```yaml
- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Bash(npm install),Bash(npm run test)"
```

全てをこれで記述するとかなり大変だと思うので、一部のコマンドはサブコマンド全てを許容し、特定のコマンドのみサブコマンド含めて許容する記述にするのが良さそうですね。

## まとめと感想

- allowed_tools を指定して安全に楽しく @claude と開発をしましょう
- Claude Code Action で遊ぶのは楽しいですが、無制限にお金が溶けていくのが困りどころさん
