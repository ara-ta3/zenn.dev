---
title: "Testing Shell Scripts with Bats"
emoji: "📌"
type: "tech"
topics: ["shell", "bash", "bats"]
published: true
---

# Introduction

This article was written as the 12th entry in the Shell Script & PowerShell Advent Calendar 2024:

https://qiita.com/advent-calendar/2024/shell

# Overview

https://github.com/bats-core/bats-core

Bats is a testing framework for Bash.  
I discovered it when I wanted to add tests to a simple script that didn’t need to be written in a full programming language.  
Here, I introduce some basic examples of Bats test code.

The code examples shown in this article are available here:  
https://gist.github.com/ara-ta3/df3bbd45b916bc137fb6196ce2e213d9

I installed Bats via Homebrew and used version 1.11.0:  
https://formulae.brew.sh/formula/bats-core

```bash
> bats --version
Bats 1.11.0
```

# Simple Test Code

Bats test code is written in separate files from shell scripts. You run the tests by executing the test file with the `bats` command.  
Test cases are defined like this:

```bash
#!/usr/bin/env bats

@test "echo hoge" {
    result=$(echo hoge)
    [ "$result" = "hoge" ]
}

@test "echo hoge expected to fuga" {
    result=$(echo hoge)
    [ "$result" = "fuga" ]
}
```

Running it gives:

```zsh
> bats test_simple.bats
test_simple.bats
 ✓ echo hoge
 ✗ echo hoge expected to fuga
   (in test file test_simple.bats, line 10)
     `[ "$result" = "fuga" ]' failed

2 tests, 1 failure
```

## The `run` Helper and Special Global Variables

Bats provides a `run` helper command that captures the output and status of a command into special global variables:

- `$status`: The exit code
- `$output`: Combined stdout and stderr (can be separated with `--separate-stderr`)
- `$lines`: Array of lines split from `$output`

https://github.com/bats-core/bats-core/blob/b640ec3cf2c7c9cfc9e6351479261186f76eeec8/man/bats.7.ronn?plain=1#L94

Example:

```bash
#!/usr/bin/env bats

@test "exit with 0 with status variable" {
    run test 1 -eq 1 
    [ "$status" -eq 0 ]
}

@test "1 + 1 = 2 with output variable" {
    run echo $((1+1))
    [ "$output" -eq 2 ]
}
```

Result:

```bash
> bats test_simple_global_vars.bats
test_simple_global_vars.bats
 ✓ exit with 0 with status variable
 ✓ 1 + 1 = 2 with output variable

2 tests, 0 failures
```

## Options for the `run` Helper

The `run` command supports options for asserting exit codes directly.

https://github.com/bats-core/bats-core/blob/b640ec3cf2c7c9cfc9e6351479261186f76eeec8/docs/source/writing-tests.md?plain=1#L150-L165

```bash
#!/usr/bin/env bats

setup() {
    # Ensure minimum version to use run options
    bats_require_minimum_version 1.5.0
}

@test "(expected to fail) exit with non 0 with ! option" {
    run ! -- test 1 -eq 1 
}

@test "(expected to fail) exit with non 0 with -N option" {
    run -1 -- test 1 -eq 1 
}
```

Result:

```bash
> bats test_simple_run_helper.bats
test_simple_run_helper.bats
 ✗ (expected to fail) exit with non 0 with ! option
   `run ! -- test 1 -eq 1 ' failed, expected nonzero exit code!
 ✗ (expected to fail) exit with non 0 with -N option
   `run -1 -- test 1 -eq 1 ' failed, expected exit code 1, got 0

2 tests, 2 failures
```

## Tagging and Filtering Tests

You can assign tags to tests with comments, and use `--filter-tags` to run only tests with specific tags:

```bash
#!/usr/bin/env bats

# bats test_tags=1digits
@test "1 + 1 = 2" {
    run echo $((1+1))
    [ "$output" -eq 2 ]
}

# bats test_tags=2digits
@test "10 + 15 = 25" {
    run echo $((10+15))
    [ "$output" -eq 25 ]
}
```

```bash
> bats --filter-tags 1digits ./test_tags.bats
 ✓ 1 + 1 = 2

> bats --filter-tags 2digits ./test_tags.bats
 ✓ 10 + 15 = 25
```

### Using the `bats:focus` Tag to Run a Single Test

```bash
#!/usr/bin/env bats

# bats test_tags=bats:focus
@test "focus echo" {
    run echo hoge
    [ "$output" = "hoge" ]
}

@test "not focus echo fuga" {
    run echo fuga
    [ "$output" = "fuga" ]
}
```

```bash
> bats ./test_tags_focus.bats
WARNING: This test run only contains tests tagged `bats:focus`!
ok 1 focus echo
Marking test run as failed due to `bats:focus` tag. (Set `BATS_NO_FAIL_FOCUS_RUN=1` to disable.)
```

## Testing with External Functions

You can split functions into a separate file and test them by sourcing them in the `setup` function:

**functions.sh**
```bash
get_day_of_week() {
    echo "${TEST_DAY:-$(gdate +%u)}"
}

should_run_main() {
    local day_of_week=$(get_day_of_week)
    if [[ "$day_of_week" -eq 6 || "$day_of_week" -eq 7 ]]; then
        return 1
    fi
    return 0
}

main() {
    if ! should_run_main; then
        return
    fi
    echo "main is running"
}
```

**test_functions.bats**
```bash
#!/usr/bin/env bats

setup () {
    source "./functions.sh"
}

@test "on Monday should_run_main returns 0" {
    TEST_DAY=1
    run should_run_main
    [ "$status" -eq 0 ]
}

@test "on Sunday should_run_main returns 1" {
    TEST_DAY=7
    run should_run_main
    [ "$status" -eq 1 ]
}
```

```bash
> bats test_functions.bats
 ✓ on Monday should_run_main returns 0
 ✓ on Sunday should_run_main returns 1

2 tests, 0 failures
```

## Notes (e.g. assert_output)

Although not used in this article, helper functions like `assert_output` are available:  
https://github.com/bats-core/bats-assert  
https://bats-core.readthedocs.io/en/stable/tutorial.html#quick-installation

# Conclusion

- Bats is useful for testing shell scripts.
- ~~For larger projects, using a language like Go might be more appropriate.~~
- It’s easy to use and ideal for lightweight, quickly written scripts.
