---
title: "Batsを使ってシェルスクリプトをテストする"
emoji: "📌"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["shell", "bash", "bats"]
published: true
---

# はじめに

この記事はシェルスクリプト＆PowerShell Advent Calendar 2024の14日目として書かれています。  

https://qiita.com/advent-calendar/2024/shell

# 概要

https://github.com/bats-core/bats-core

BatsはBash用のテストフレームワークです。  
何らかのプログラミング言語で書くまででもない簡単なスクリプトを書こうと思った際に、とはいえテストが欲しいと思って見つけたのがBatsでした。  
今回は簡単なBatsのテストコードの紹介をします。  

# シンプルなテストコード

Batsのテストコードはシェルスクリプトとは別のファイルに書き、batsコマンドでそのファイルを実行することでテストを実行できます。  
テストケースは`@test "test case name"` のように書けます。  

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

実行するとこのようになります。  

```zsh
> bats test_simple.bats
test_simple.bats
 ✓ echo hoge
 ✗ echo hoge expected to fuga
   (in test file test_simple.bats, line 10)
     `[ "$result" = "fuga" ]' failed

2 tests, 1 failure
```

## run helperと特殊なグローバル変数

Batsにはrunというヘルパーコマンドが用意されており、これを使って関数を実行すると、いくつかのグローバル変数に結果が書き込まれます。  

- $status
  - 関数実行時のexit code
- $output
  - 標準出力と標準エラー出力
  - --separate-stderrをつけることで分けることができるようです
- $lines
  - 配列でoutputを行ごとに分けたものが入ります

https://github.com/bats-core/bats-core/blob/b640ec3cf2c7c9cfc9e6351479261186f76eeec8/man/bats.7.ronn?plain=1#L94

それらを使ってテストを書いてみるとこのようになります。  

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

実行するとこのようになります。  

```bash
> bats test_simple_global_vars.bats
test_simple_global_vars.bats
 ✓ exit with 0 with status variable
 ✓ 1 + 1 = 2 with output variable

2 tests, 0 failures
```

## run helperのオプション

runコマンドにはオプションがあり、それらを使うとexit codeのassertionなどをオプションで済ませることができます。  

https://github.com/bats-core/bats-core/blob/b640ec3cf2c7c9cfc9e6351479261186f76eeec8/docs/source/writing-tests.md?plain=1#L150-L165

```bash
#!/usr/bin/env bats

setup() {
    # 1.5以上でrunにoptionを使えるようなのでそれを指定してWarningを回避しています
    # BATS_VERSIONの環境変数に入れるでも問題ないようです
    # @see https://github.com/bats-core/bats-core/blob/b640ec3cf2c7c9cfc9e6351479261186f76eeec8/lib/bats-core/common.bash#L55
    bats_require_minimum_version 1.5.0
}

@test "(expected to fail) exit with non 0 with ! option" {
    run ! -- test 1 -eq 1 
}

@test "(expected to fail) exit with non 0 with -N option" {
    run -1 -- test 1 -eq 1 
}
```

実行するとこのようになります。  
結果がわかりやすいように失敗させています。  

```bash
> bats test_simple_run_helper.bats
test_simple_run_helper.bats
 ✗ (expected to fail) exit with non 0 with ! option
   (in test file test_simple_run_helper.bats, line 11)
     `run ! -- test 1 -eq 1 ' failed, expected nonzero exit code!
 ✗ (expected to fail) exit with non 0 with -N option
   (in test file test_simple_run_helper.bats, line 15)
     `run -1 -- test 1 -eq 1 ' failed, expected exit code 1, got 0

2 tests, 2 failures
```

## タグを付けての実行

コメントでタグをつけることができます。  
そのタグのみを指定して実行できるようです。  

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

実行するとこのようになります。  

```bash
bats --filter-tags 1digits ./test_tags.bats
test_tags.bats
 ✓ 1 + 1 = 2
1 test, 0 failures
> bats --filter-tags 2digits ./test_tags.bats
test_tags.bats
 ✓ 10 + 15 = 25
```

### bats:focusタグを使って一つだけテストを実行する

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

実行するとこのようになります。  
全体のテストを行わず一部機能のリファクタリングなどに使う用途を意図してか、意図的に成功とするようにしないと正常終了しないようになっています。  
CIなどで全体のテストが回らずに通ってしまうことは起きないようですね。  

```bash
> bats ./test_tags_focus.bats
WARNING: This test run only contains tests tagged `bats:focus`!
1..1
suite /path/totest-with-bats/test_tags_focus.bats
begin 1 focus echo
ok 1 focus echo
Marking test run as failed due to `bats:focus` tag. (Set `BATS_NO_FAIL_FOCUS_RUN=1` to disable.)
```


## 関数を読み込んだ上でのテスト

関数をまとめて別ファイルに切り出しておき、それのテストを行ってみます。  
setupで読み込み、今まで通りテストするだけです。  


functions.sh
```bash
get_day_of_week() {
    echo "${TEST_DAY:-$(gdate +%u)}"
}

should_run_main() {
    local day_of_week=$(get_day_of_week)

    # 月曜1 ~ 日曜7
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

test_functions.bats

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

実行するとこのようになります。  

```bash
> bats test_functions.bats
test_functions.bats
 ✓ on Monday should_run_main returns 0
 ✓ on Sunday should_run_main returns 1

2 tests, 0 failures
```

## 備考(assert_outputなど)

今回は使いませんでしたが、assertionなどのヘルパーもあるようです。  
https://github.com/bats-core/bats-assert

https://bats-core.readthedocs.io/en/stable/tutorial.html#quick-installation

# まとめ

- シェルスクリプトを書いたときにテストするならBatsが便利
- ~~規模が大きくなるならGoとかのほうがいいのでは~~

