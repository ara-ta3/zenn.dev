---
title: "Goの設定ライブラリのviperで.envファイルから設定を取得する"
emoji: "📚"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Go", "viper", "env"]
published: false
---

Go を久しぶりに触ったんですけど、設定を取得するライブラリってどんなのが良いのかなって思って、awesome-go を見に行って見ました。
Ref: https://github.com/avelino/awesome-go
2023/12/3 現在、1k 以上スターがついてるライブラリをまとめてみると下記のような感じで、viper ってやつが強いんだなってなりました。

| repository                                   | star  |
| -------------------------------------------- | ----- |
| https://github.com/ilyakaznacheev/cleanenv   | 1.3k  |
| https://github.com/caarlos0/env              | 4k    |
| https://github.com/kelseyhightower/envconfig | 4.7k  |
| https://github.com/joho/godotenv             | 6.9k  |
| https://github.com/go-ini/ini                | 3.4k  |
| https://github.com/knadh/koanf               | 2.1k  |
| https://github.com/alecthomas/kong           | 1.6k  |
| https://github.com/spf13/viper               | 24.7k |

env を読み込むだけなら別のライブラリでもええやろと思いつつ、メモがてら viper で env から設定を取ってきた備忘録です。

# 構成

`go mod init ...` は行った上でとりあえず viper のインストールです。

```
go get github.com/spf13/viper
```

Go のバージョンやらディレクトリやらはこんな感じです。  
Ref: https://gist.github.com/ara-ta3/c07dabcdbad79bd542091a9f037af34c

```bash
$go version
go version go1.21.4 darwin/amd64

$tree
.
├── dot_env_file
├── go.mod
├── go.sum
└── main.go

1 directory, 4 files

$cat dot_env_file
XXX=a
YYY=b
ZZZ=c
```

# main.go

素朴に viper で設定を取ってきて struct に bind する関数を main で呼び出しているだけです。
Go 言語久々でしたが、最強のデバッグは`fmt.Printf("%+v")`であることだけは覚えていました。

```go
package main

import (
	"fmt"

	"github.com/spf13/viper"
)

func main() {
	c, err := Load()
	if err != nil {
		panic(err)
	}
	fmt.Printf("%+v\n", c)
}

func Load() (config *EnvConfigs, err error) {
	viper.AddConfigPath(".")
	viper.SetConfigName("dot_env_file")
	viper.SetConfigType("env")

	if err = viper.ReadInConfig(); err != nil {
		return
	}

	if err = viper.Unmarshal(&config); err != nil {
		return
	}
	return
}

type EnvConfigs struct {
	X string `mapstructure:"XXX"`
	Y string `mapstructure:"YYY"`
}

```

# 実行

```bash
go run main.go
&{X:a Y:b}
```

# まとめ

viper は json やら yaml やらでも設定が出来るらしいので、なんか別途やりたくなったらまたやってみたいなって思いましたとさ。
