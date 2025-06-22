---
title: "The `entr` Command: Convenient Tool for Executing Custom Commands via Pipe on File Change"
emoji: "🔖"
type: "tech"
topics: ["command", "cli"]
published: false
---

# Introduction

During development, it's common to want to monitor file changes and automatically run a specific command when a change is detected.  
In this article, I’ll introduce a useful tool for that purpose: the `entr` command.

# What is the `entr` Command?

`entr` is a UNIX utility that monitors file changes and executes a specified command when a change is detected.  
It reads a list of files from standard input and executes the given command if any of those files are modified.

**Official Site**  
https://eradman.com/entrproject/

**GitHub**  
https://github.com/eradman/entr

## Installation

On macOS, you can use Homebrew, and on Debian-based systems, you can install it with apt.

```bash
# macOS (Homebrew)
brew install entr

# Ubuntu/Debian
apt install entr
```

## Basic Usage

`entr` reads a list of files from standard input and monitors them for changes.

```bash
# Basic usage
echo "filename" | entr command

# Example: monitor changes to hoge.txt and run echo
## Terminal A
$ ls
hoge.txt
$ echo abc > hoge.txt

## Terminal B
$ echo hoge.txt | entr echo fuga
fuga
# After running 'echo abc > hoge.txt' in Terminal A,
# 'echo fuga' is executed and printed again.
fuga
```

# Practical Use Cases

## Run Tests When Source or Test Files Change

```bash
# Monitor test files and run tests
find . -name "*.test.js" | entr npm test

# Monitor TypeScript files and build
find src -name "*.ts" | entr npm run build

# Monitor config file changes
echo "config.yml" | entr -r ./restart-service.sh
```

Using `find` is common here, especially when you want to build code while watching for changes.  
I found `entr` when I wanted to combine it with the `sbt-native-packager`'s `sbt stage` command.

# Useful Options

## -r: Restart the process

```bash
# Start the server and restart it on file change
find . -name "*.js" | entr -r node server.js
```

## -c: Clear the terminal before execution

```bash
# Clear terminal before running tests
find . -name "*.go" | entr -c go test ./...
```

## -d: Watch for directory changes as well

```bash
# Monitor directory changes
find . -type d | entr -d echo "Directory changed"
```

# Conclusion

The `entr` command is a simple yet powerful tool that automatically runs commands when files change.  
It's extremely helpful for automating tasks like test execution, builds, or server restarts during development.  
With its minimalistic design and ease of use, it’s an excellent choice when no other tool fits your watch-and-run use case.
