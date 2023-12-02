---
title: "Goの設定系ライブラリのviperで.envファイルから設定を取得する"
emoji: "📚"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Go", "viper", "env"]
published: false
---

Go を久しぶりに触ったんですけど、設定を取得するライブラリってどんなのが良いのかなって思ってググったらこんな記事があって、star が多いのが viper というライブラリだったので、そこ少し触ってみた備忘録です。  
ref: https://qiita.com/tashxii/items/ae6382b89049ffbb8ba5

- 最小限の構成

```tree
.
├── go.mod
├── go.sum
└── main.go

1 directory, 3 files
```

- コード

```
go get github.com/spf13/viper
```

```env
XXX=a
YYY=b
ZZZ=c
```

```go
package main

import (
	"github.com/spf13/viper"
)

func main() {
	c, err := Load()
	if err != nil {
		panic(err)
	}
}

func Load() (config *EnvConfigs, err error) {
	viper.AddConfigPath(".")
	viper.SetConfigName(".env")
	viper.SetConfigType("env")

	if err := viper.ReadInConfig(); err != nil {
		return nil, err
	}

	if err := viper.Unmarshal(&config); err != nil {
		return nil, err
	}
	return
}

type EnvConfigs struct {
	X string `mapstructure:"XXX"`
	Y string `mapstructure:"YYY"`
}
```

- まとめ
