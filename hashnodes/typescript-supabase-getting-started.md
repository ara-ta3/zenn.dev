---
title: "Running Supabase Locally and Displaying a Task List with Vite + React"
emoji: "🗂"
type: "tech"           # tech: Technical article / idea: Concept piece
topics: ["supabase", "typescript", "react", "vite", "pnpm"]
published: true
---

This is a brief memorandum of building a simple **TODO** application with **TypeScript + Vite + React** powered by **Supabase**.  
I walked through everything from spinning up Supabase locally to implementing the application UI.

All source code is available at:

<https://github.com/ara-ta3/supabase-local-getting-started>

Below is the toolchain (excerpt from `package.json`):

```json
{
  "name": "supabase-local-getting-started",
  "version": "1.0.0",
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
````

# Setting Up Supabase Locally

## Installing and Initialising Supabase CLI

First, install Supabase CLI and initialise your project.
Initialisation creates a `supabase/` directory with the necessary config files:

```bash
pnpm add supabase
pnpm approve-builds
```

> **Note**
> Because **pnpm** does *not* run `postinstall` scripts automatically, you must execute
> `pnpm approve-builds` so that Supabase’s post-install script is authorised and executed.

Reference: [https://zenn.dev/ara\_ta3/scraps/aee0c57bec5e0b](https://zenn.dev/ara_ta3/scraps/aee0c57bec5e0b)

## Starting the Local Stack

Launch the local stack with Docker.
This spins up PostgreSQL, Supabase Studio, and the other required services.

```bash
pnpm exec supabase start
```

> **Note – Colima users**
> If you see `container is not ready: unhealthy`, it is often due to **vector** and **logflare** health-checks failing inside Colima.
> In that case, exclude them with `-x`:
>
> ```bash
> pnpm exec supabase start -x vector -x logflare
> ```
>
> Reference: [https://zenn.dev/ara\_ta3/scraps/7a3e9c5dfacf81](https://zenn.dev/ara_ta3/scraps/7a3e9c5dfacf81)

Upon success, you will see output similar to:

```
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

Open **Studio URL** in your browser to manage the database visually.

## Creating a Migration

Generate a migration file for the `tasks` table:

```bash
pnpm exec supabase migration new init
# => supabase/migrations/20250628000000_init.sql
```

Edit the generated SQL as follows:

```sql
create table public.tasks (
  id           bigserial primary key,
  title        text        not null,
  done         boolean     default false,
  inserted_at  timestamptz default now()
);

alter table public.tasks enable row level security;

create policy "anyone can read" on public.tasks
  for select using (true);
```

### Applying Migrations

For local development you have several options:

| Command                     | Behaviour                                                                |
| --------------------------- | ------------------------------------------------------------------------ |
| `supabase db reset --local` | **Resets** the local DB, then runs *all* migrations and seeds.           |
| `supabase db push --local`  | Pushes the current schema to the **local** DB (normally targets remote). |
| `supabase migration up`     | Applies any migrations that have not yet been run locally.               |

```bash
pnpm exec supabase db reset --local
pnpm exec supabase db push --local
pnpm exec supabase migration up
```

## Adding Seed Data

Create `supabase/seed.sql`:

```sql
insert into public.tasks (title, done)
values ('Buy groceries',            false),
       ('Write article',            true),
       ('Implement tests',          false);
```

Because the file is named **`supabase/seed.sql`**, it is executed automatically during `db reset`:

```bash
pnpm exec supabase db reset --local
```

# Creating the TypeScript + Vite + React App

Our front-end only needs the packages already shown in `package.json`.

## Configuring the Supabase Client

`src/lib/supabase.ts`:

```ts
import { createClient } from "@supabase/supabase-js";

const supabaseUrl     = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase environment variables are not set.");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

## Generating Type Definitions

```bash
pnpm exec supabase gen types typescript --local src/types/database.types.ts
```

## Implementing the Task List

`src/App.tsx`:

```tsx
import { useEffect, useState } from "react";
import { supabase } from "./lib/supabase";
import type { Database } from "./types/database.types";

type Task = Database["public"]["Tables"]["tasks"]["Row"];

export default function App() {
  const [tasks,   setTasks]   = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
  }, []);

  async function fetchTasks() {
    try {
      setLoading(true);
      const { data, error } = await supabase.from("tasks").select("*");
      if (error) setError(error.message);
      else       setTasks(data ?? []);
    } catch {
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading…</div>;
  if (error)   return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Tasks</h1>
      {tasks.length === 0 ? (
        <p>No tasks found.</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
              {task.title} – {task.done ? "Done" : "Pending"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

`src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

`index.html`:

```html
<!DOCTYPE html>
<html lang="en">
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

# Running the Application

```bash
pnpm exec vite
```

Open [http://localhost:5173](http://localhost:5173) and you should see the list of tasks fetched from Supabase.

# Summary

* Supabase CLI lets you stand up a complete local environment with a single command.
* Migrations and seed data keep your development database predictable and disposable.

Supabase proved very convenient for rapid prototyping.
Unlike Firebase, it offers a full **PostgreSQL** backend, which I consider a significant advantage. I look forward to using it in future projects.

