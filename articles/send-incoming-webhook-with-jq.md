---
title: "jq -nと--argでJSONを生成し、SlackにWebhook経由でメッセージを送信する"
emoji: "📚"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["jq", "Slack", "JSON"]
published: true
---

なんらかのJSONをパースして情報を取得するというときにjqコマンドを良く使っていたのですが、今回はJSONを生成するというときにも使えるじゃんということに気づいたのでその時の備忘録です。  
curlで取得した文字列をゴニョゴニョして、最終的にSlackに通知するというのを雑に作っていたときにjqの-n(--null-input)と--argを使ったらJSONを生成し、そのままSlack Incoming Webhookに投げれて便利だなとなりました。  

このとき使ったjqのバージョンは以下のとおりです。  

```bash
jq --version
jq-1.7.1
```

- jqコマンドについて
    - https://jqlang.github.io/jq/

# jq --null-inputと--argでJSONを生成する

jqの-n(--null-input)オプションは、入力データを必要とせずに新しいJSONデータを生成する時に便利なオプションです。  
--argオプションを使うことで、以下のように変数に名前をつけてJSONオブジェクトのフィールドに挿入することができます。  

```bash
jq -n --arg name "Foo" --arg age "30" '{name: $name, age: $age}'
{
  "name": "Foo",
  "age": "30"
}
```

## --argjson

argjsonはargと似ていますが、valueにJSONを入れることが出来ます。  

```bash
jq -n --argjson data '{"foo": "bar"}' '{user: $data}'
{
  "user": {
    "foo": "bar"
  }
}
```

当然jqで生成したものを入れることも出来ますね。  

```bash
jq -n --argjson data "$(jq -n --arg name Foo --arg age 30 '{name: $name, age: $age}' )" '{user: $data}'
{
  "user": {
    "name": "Foo",
    "age": "30"
  }
}
```

## --args

argsは複数の値を入れて$ARGS.positionalでアクセスし、array出来るようです。  

```bash
jq -n --args '$ARGS.positional' hoge fuga piyo
[
  "hoge",
  "fuga",
  "piyo"
]
```

これは--argsが渡った場合、$ARGSにpositionalというkeyで値が渡されてるぽいですね。  
同時に--argではとnamedというkeyに値が入ってるようです。  

```bash
jq -n --args '$ARGS' hoge fuga piyo
{
  "positional": [
    "hoge",
    "fuga",
    "piyo"
  ],
  "named": {}
}

jq -n --args '$ARGS' hoge fuga piyo --arg hoge fuga
{
  "positional": [
    "hoge",
    "fuga",
    "piyo"
  ],
  "named": {
    "hoge": "fuga"
  }
}
```


## --jsonargs

--argと--argjsonの関係と同じように--argsのvalueとしてJSONを入れたい場合はこの引数を使うと良いようです。  
```bash
jq -n --jsonargs '$ARGS.positional' '{"name": "foo"}' '{"name": "bar"}'
[
  {
    "name": "foo"
  },
  {
    "name": "bar"
  }
]
```


# 生成したJSONをワンライナーでWebhookに送信する

以下のようにcurlコマンドでSlackのIncoming Webhookに対してRequestを投げれば後はSlack通知が可能です。  

```bash
jq -n --arg text "Foo" '{text: $text}' | curl -X POST -H 'Content-type: application/json' --data @- https://hooks.slack.com/services/your/webhook/url
```

## curlの--dataオプションの引数として@-を使って標準入力を渡す

--dataの引数として@-を使うと標準入力を渡せるということをここで知りました。  
data以外でもところどころ使えるんですね。  

https://curl.se/docs/manpage.html

> If you start the data with the letter @, the rest should be a filename to read the data from, or - if you want curl to read the data from stdin.

# まとめ

今回は、jqの--null-inputと--argを使ってJSONを生成しSlackに送信する話でした。  
簡単な通知をしたい時に便利に使えると思うので使っていきたいと思いました。  

# 参考資料

- https://jqlang.github.io/jq/
- https://api.slack.com/messaging/webhooks
