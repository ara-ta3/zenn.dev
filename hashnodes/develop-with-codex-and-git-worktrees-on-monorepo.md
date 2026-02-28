---
title: "Parallel Development in a Docker Compose Monorepo with the Codex App and git-wt"
emoji: "😸"
type: "tech"
topics: ["git", "gitworktree", "codex", "monorepo", "dockercompose"]
published: true
---

## Introduction

Lately, I've been working in a style where I keep multiple tasks running in parallel using the Codex app and `git-wt`.  
However, in a `docker compose`-based development environment where backend, frontend, and other middleware coexist, I ran into a problem: it was hard to verify build outputs.

Because each task's artifacts stay inside its own worktree, verification usually requires one of these:

- bring artifacts back into the main worktree
- start the verification environment in that worktree too (`docker compose up`)

Running the latter in parallel consumes a lot of machine resources, and doing the former manually every time is tedious.  
So in this article, I’m leaving a memo on how I operate by creating a review branch in the main worktree, so I can validate build results on the main worktree side.

### TL;DR (3 lines)

- Split work with multiple worktrees and run parallel development with the Codex app
- If it’s hard to create a local environment per worktree, create a review branch in the main worktree
  - In this article, the working directory right after `git clone` is called the main worktree
- Use either `git-wt` or the Codex app’s worktree feature

## About the `git-wt` command

As a prerequisite, `git worktree` is a feature that lets you split working directories by branch within one repository.  
You can work on multiple branches in parallel without increasing the number of `git clone`s.

For now, I use `git-wt` instead of raw `git worktree` commands.  
`git worktree` felt a little hard for me to master directly, while `git-wt` felt easy enough to run with.

https://github.com/k1LoW/git-wt

### Install

```zsh
brew install k1LoW/tap/git-wt
```

I also add the following as-is from the official documentation:

```zsh
eval "$(git wt --init zsh)"
```

### Commands I use often

```zsh
git wt                    # list
git wt feature/foo        # move to worktree (or create if missing)
git wt -d feature/foo     # delete (worktree + branch)
git wt -D feature/foo     # force delete
```

With `git wt <name>`, it handles both "move to existing worktree" and "create a new one."  
I currently use the default `git-wt` settings.  
Using `-d` and `-D` differently for deletion helps reduce accidental destructive operations.

#### Alias example

I use aliases for many `git` commands; here I alias `gw`.  
I also defined `gww`, which lets me pick from the `git wt` list via `peco` and jump there.

```zsh
alias gw='git wt'

function gww () {
	git wt $(git wt | tail -n +2 | peco | awk '{print $(NF-1)}')
}
```

## About the Codex app

I originally used the `codex` command in the terminal.  
With terminal-only usage, control characters occasionally mixed in (I couldn't fully pinpoint why), so I used VSCode as a wrapper.  
When the Codex app was released, I thought, if I’m launching an app anyway, this is better, so I installed it.  
In practice, it has been pretty good.

Naturally, it can do most things you can do in a terminal, and it shows Threads (ongoing tasks) on the left, which improves visibility when working in parallel.

https://openai.com/ja-JP/index/introducing-the-codex-app/

### About the Codex app’s worktree feature

Roughly speaking, the Codex app’s worktree feature separates workspaces per task.  
Even in the same repository, tasks interfere less, so parallel work feels easier.

Looking at `.git` inside a worktree created by the app, I saw this format:

```txt
gitdir: /path/to/repo/.git/worktrees/xxxxx
```

So my understanding is that this uses `git worktree` under the hood rather than a fully separate implementation.

### Difference between `git-wt` and the Codex app worktree feature

To be honest, at first I wasn’t using the Codex app worktree feature much because I didn’t fully understand it.  
But once I looked closely, it relies on `git worktree`, so worktrees created there also appear in `git wt` lists.

That said, as far as I can tell right now, I haven’t found a flow in the Codex app that creates a branch first when starting worktree-based tasks.  
So when I want branch-first workflows, creating them beforehand with `git-wt` feels easier.

On the other hand, worktrees created with `git-wt` need to be added manually to Codex app Threads, which is a bit inconvenient.  
For now I split usage like this: "use `git-wt` when I want to create a branch first," and "use the Codex app when I prioritize Thread management."

### Convenient function for moving across worktrees

I used to move by selecting only from `ghq list -p` with `peco`.  
But worktrees created by the Codex app are placed under `~/.codex/worktrees`, so I also include them via `find`.

This makes it convenient to move among "main worktree", "under ghq", and "under the Codex app" with a single function.

```zsh
function gg () {
    local selected_dir=$(
        {
            printf "%s\n" "$HOME/dotfiles"
            ghq list -p
            find "$HOME/.codex/worktrees" -mindepth 2 -maxdepth 2 -type d
        } | peco --query "$LBUFFER"
    )
    if [ -n "$selected_dir" ]; then
        cd ${selected_dir}
    fi
}
```

## Create a branch for review

As noted in the introduction, when backend / frontend / others are run with `docker compose`, spinning up full environments per worktree can be too resource-heavy.  
So I wanted a setup where verification can happen in one place (the main worktree).

With `git worktree`, even if your work branch hasn’t been pushed to remote, it already exists in local Git.  
That means you can create a review branch from it in the main worktree.

However, branch names currently in use by `git worktree` can’t be reused directly, so I create one with a `review/` prefix instead.  
Typing this every time is tedious, so I made a helper function.

```zsh
function gwreview () {
	local b=$1
	git switch -c review/$b $b
}
```

For example, if I want to review `feature/add-login`, I run `gwreview feature/add-login` to create and switch to `review/feature/add-login`.

## Conclusion

I introduced one example workflow for parallel development using the Codex app and `git-wt`.  
In a `docker compose`-based monorepo, creating the same environment in every worktree is often unrealistic, so I centralize verification in the main worktree.  
I hope this helps anyone facing similar issues in a similar setup.
