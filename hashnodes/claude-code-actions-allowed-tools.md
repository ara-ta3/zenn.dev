---
title: "Example Configuration for allowed_tools to Run Commands with Claude Code Action"
emoji: "🐕"
type: "tech"
topics: ["claude", "claudecode", "vibecodeing"]
published: true
---

## Introduction

Claude Code Action is a feature that assists with code generation and editing via an AI assistant. By default, command execution is restricted for security reasons.  
This article serves as a memo on how to configure `allowed_tools` to enable commands like npm to be executed.

https://github.com/anthropics/claude-code-action

## Environment

### Sample Code

Here's a sample setup.  
A simple test script using `uvu` is provided, and the command to run it is defined in the `scripts` section of `package.json`.

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

cat sample.test.js
import { test } from 'uvu';
import * as assert from 'uvu/assert';

test("What's 1000 minus 7?", () => {
  assert.is(1000 - 7, 993);
});

test.run();
```

### Verification Issue

A test issue was created to try this out with Claude using the following prompt:

```
@claude I want to test whether commands can be run in this repository.

Please try running the following commands and display the results in a table:

- npm run test
- node sample.test.js
```

https://github.com/ara-ta3/claude-code-action-getting-started/issues/2

## Testing allowed_tools

### Summary First

- Use `Bash` to allow all bash commands
- Use `Bash(npm:*),Bash(node:*)` to allow specific command categories
- Use `Bash(npm install),Bash(npm run test)` to allow specific subcommands

| Configuration                          | npm commands | node commands | Status                     |
| -------------------------------------- | ------------ | ------------- | -------------------------- |
| No allowed_tools                       | ❌           | ❌            | Permission Denied          |
| `Bash(npm*)`                           | ❌           | ❌            | Syntax Error               |
| `Bash(npm:*)`                          | ✅           | ❌            | npm only                   |
| `Bash(npm:*),Bash(node:*)`             | ✅           | ✅            | npm + node                 |
| `Bash`                                 | ✅           | ✅            | Full access                |
| `Bash(npm:install),Bash(npm:run)`      | ❌           | ❌            | Syntax Error               |
| `Bash(npm install),Bash(npm run test)` | ✅           | ✅            | npm install + npm run test |

### Default State

By default, Claude Code Action restricts all command execution for security.  
To allow commands like npm, you must explicitly specify them using the `allowed_tools` configuration.

### Allowing All Commands

To allow all commands, simply use `Bash`.  
This grants full permission, so it's best suited for private repositories.

```yaml
- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Bash"
```

### Allowing All Subcommands for Specific Tools

To allow all subcommands for specific tools, use syntax like `Bash(npm:*),Bash(node:*)`.

```yaml
- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Bash(npm:*),Bash(node:*)"
```

This allows `npm` and `node` command families.  
If the command is defined under `scripts` in `package.json`, it may still be executable even if only npm is allowed.

### Allowing Specific Subcommands

To allow specific commands only, use `Bash(npm install),Bash(npm run test)`.

```yaml
- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Bash(npm install),Bash(npm run test)"
```

Writing out everything this way can be tedious, so a mix of general and specific permissions may work best.

## Summary and Thoughts

With `Bash(npm:*)` and similar configurations, Claude can now execute commands like npm, which makes testing and automation easier.  
By properly configuring `allowed_tools`, you can enjoy developing safely and efficiently with @claude. (Claude Code Action is fun to play with, but be mindful of usage costs if you're on a usage-based API plan!)
