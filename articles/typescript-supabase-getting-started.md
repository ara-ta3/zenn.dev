---
title: "Supabaseをローカルで動かしてタスク一覧をvite+reactで表示する"
emoji: "🗂"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["supabase", "typescript", "react", "vite", "pnpm"]
published: false
---

TypeScript + Vite + React で Supabase を使った簡単な TODO アプリを作ってみた時の備忘録です。  
ローカル環境での Supabase 起動からアプリケーション実装まで一通り試してみました。

今回作成したコードは以下のリポジトリに置いてあります。

https://github.com/ara-ta3/supabase-local-getting-started

使用したツールとバージョン(package.json)は以下のとおりです。

```json
{
  "name": "supabase-local-getting-started",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "keywords": [],
  "author": "",
  "license": "ISC",
  "packageManager": "pnpm@10.12.1",
  "dependencies": {
    "@supabase/supabase-js": "^2.50.2",
    "@types/react": "^19.1.8",
    "@types/react-dom": "^19.1.6",
    "@vitejs/plugin-react": "^4.6.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "supabase": "^2.26.9",
    "typescript": "^5.8.3",
    "vite": "^7.0.0"
  }
}
```

# Supabase のローカル環境セットアップ

## Supabase CLI のインストールと初期化

まず Supabase CLI をインストールして、プロジェクトを初期化します。
初期化すると `supabase/` ディレクトリが作成され、設定ファイルが生成されます。

```bash
> pnpm add supabase
> pnpm approve-builds
```

:::message
今回 pnpm を利用しましたが、pnpm の場合、postinstall 等のスクリプトは自動で実行されないようになっています。
そして、supabase のスクリプトは postinstall によって生成されるため approbe-builds を実行する必要があります。  
:::

**参考**

https://zenn.dev/ara_ta3/scraps/aee0c57bec5e0b

## ローカル環境の起動

Docker を使ってローカル環境を起動します。  
PostgreSQL や Supabase Studio が含まれた環境が立ち上がります。

```bash
> pnpm exec supabase start
```

:::message

colima などを使っている場合に、 `container is not ready: unhealthy` と言われ起動しないことがあります。  
これは Docker 上からログを取得して死活監視する vector と logflare がうまく行っていないためです。  
今回軽く検証したのですが、どうにも動かせなかったため-x オプションにより除外し動かすことにしています。

```bash
> pnpm exec supabase start -x vector -x logflare
```

:::

**参考**
https://zenn.dev/ara_ta3/scraps/7a3e9c5dfacf81

起動が完了すると、以下のような出力が表示されます。

```bash
Started supabase local development setup.

         API URL: http://127.0.0.1:54321
     GraphQL URL: http://127.0.0.1:54321/graphql/v1
  S3 Storage URL: http://127.0.0.1:54321/storage/v1/s3
          DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
      Studio URL: http://127.0.0.1:54323
    Inbucket URL: http://127.0.0.1:54324
      JWT secret: your-jwt-secret
        anon key: your-anon-key
service_role key: your-service-role-key
   S3 Access Key: your-s3-access-key
   S3 Secret Key: your-s3-secret-key
       S3 Region: local
```

Studio URL にアクセスすると、ブラウザ上でデータベースを管理できます。

## マイグレーションファイルの作成

TODO テーブルを作成するためのマイグレーションファイルを生成します。

```bash
> pnpm exec supabase migration new init
Created new migration at supabase/migrations/20250628000000_init.sql
```

`supabase/migrations/` ディレクトリに新しい SQL ファイルが作成されるので、以下の内容を記述します。

```sql
create table public.tasks (
  id           bigserial primary key,
  title        text        not null,
  done         boolean     default false,
  inserted_at  timestamptz default now()
);

alter table public.tasks enable row level security;

create policy "anyone can read" on public.tasks
  for select using ( true );
```

### マイグレーションの適用方法

ローカルだけを考えたときにマイグレーションを適用する方法はいくつかあります。

- reset --local
  - ローカルのデータベースを全て初期化した上でマイグレーション+シードデータ(後述)を適用
- db push --local
  - push はローカルではなくリモートの supabase に適用するコマンド
  - --local オプションによってローカルへと適用が可能
- migration up
  - 適用していない migration をローカルに適用するコマンド

```bash
pnpm exec supabase db reset --local
pnpm exec supabase db push --local
pnpm exec supabase migration up
```

## シードデータの追加

初期データを投入するためのシードファイルを作成します。  
`supabase/seed.sql` ファイルを作成し、以下の内容を記述します。
`supabase/seed.sql` というファイル名にしておくことにより db reset 時にローカルには適用してくれるようです。

```sql
insert into public.tasks (title, done)
values ('買い物をする', false),
       ('記事を書く',  true),
       ('テストを実装する', false);

```

シードデータを適用するには、データベースをリセットします。

```bash
> pnpm exec supabase db reset --local
Resetting local database...
Recreating database...
Initialising schema...
Seeding globals from roles.sql...
Applying migration 20250628000000_init.sql...
NOTICE (42P06): schema "supabase_migrations" already exists, skipping
Seeding data from supabase/seed.sql...
Restarting containers...
Finished supabase db reset on branch main.
```

# TypeScript + Vite + React アプリケーションの作成

Vite + React 製の supabase 上にある task を表示するだけのアプリケーションを作成します。
必要なものは以下の package.json のとおりです。

```json
{
  "name": "supabase-local-getting-started",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "keywords": [],
  "author": "",
  "license": "ISC",
  "packageManager": "pnpm@10.12.1",
  "dependencies": {
    "@supabase/supabase-js": "^2.50.2",
    "@types/react": "^19.1.8",
    "@types/react-dom": "^19.1.6",
    "@vitejs/plugin-react": "^4.6.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "supabase": "^2.26.9",
    "typescript": "^5.8.3",
    "vite": "^7.0.0"
  }
}
```

## Supabase クライアントの設定

`src/lib/supabase.ts` ファイルを作成し、Supabase クライアントを設定します。
supabase に関する設定は環境変数から取得できるようにしています。

```typescript
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabaseの環境変数が設定されていません");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

## 型定義の生成

Supabase から型定義を生成します。

```bash
> pnpm exec supabase gen types typescript --local src/types/database.types.ts
```

## タスク一覧表示の実装

`src/App.tsx` を作成し、タスクの一覧表示を行います。

```typescript
import { useEffect, useState } from "react";
import { supabase } from "./lib/supabase";
import type { Database } from "./types/database.types";

type Task = Database["public"]["Tables"]["tasks"]["Row"];

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase.from("tasks").select("*");

      if (error) {
        setError(error.message);
      } else {
        setTasks(data || []);
      }
    } catch (err) {
      setError("予期しないエラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>読み込み中...</div>;
  if (error) return <div>エラー: {error}</div>;

  return (
    <div>
      <h1>タスク一覧</h1>
      {tasks.length === 0 ? (
        <p>タスクがありません</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
              {task.title} - {task.done ? "完了" : "未完了"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
```

**src/main.tsx**

```ts
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

**/index.html**

```html
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Supabase React App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

# アプリケーションの実行

開発サーバーを起動してアプリケーションを確認します。

```bash
pnpm exec vite
```

ブラウザで http://localhost:5173 にアクセスすると、supabase 上に保存されたタスク一覧を表示するアプリがみれます。

# まとめ

- Supabase CLI を使ってローカル環境を簡単に構築できました
- マイグレーションとシードデータで開発環境を整備できました
- TypeScript + React で型安全な Supabase クライアントアプリを実装
- CRUD オペレーションとリアルタイム機能も簡単に組み込めて便利

Supabase の開発体験は非常に良く、バックエンドの複雑な設定なしにフルスタックアプリケーションを開発できるのが魅力的でした。
