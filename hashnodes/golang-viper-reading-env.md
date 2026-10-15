---
title: "How to Load a .env File into a Go Struct with Viper"
emoji: "📚"
type: "tech"
topics: ["go", "viper", "configuration"]
published: false
---

## Introduction

When I came back to Go, I wanted to load a small configuration file into a struct. I found [Viper](https://github.com/spf13/viper) while browsing awesome-go and tried it with an env-format file.

This example reads a `.env` file, maps its keys to struct fields, and prints the result. It is an English adaptation of my [Japanese article on Zenn](https://zenn.dev/ara_ta3/articles/golang-viper-reading-env).

## Set up the project

```bash
mkdir viper-env-example
cd viper-env-example
go mod init example.com/viper-env-example
go get github.com/spf13/viper
```

The project will contain:

```text
viper-env-example/
├── .env
├── go.mod
├── go.sum
└── main.go
```

Create `.env` with a few sample values:

```dotenv
XXX=a
YYY=b
ZZZ=c
```

These are sample values. Keep real credentials out of version control.

## Read the file and unmarshal it into a struct

Create `main.go`:

```go
package main

import (
    "fmt"

    "github.com/spf13/viper"
)

type EnvConfigs struct {
    X string `mapstructure:"XXX"`
    Y string `mapstructure:"YYY"`
}

func Load() (EnvConfigs, error) {
    config := viper.New()
    config.SetConfigFile(".env")
    config.SetConfigType("env")

    if err := config.ReadInConfig(); err != nil {
        return EnvConfigs{}, err
    }

    var result EnvConfigs
    if err := config.Unmarshal(&result); err != nil {
        return EnvConfigs{}, err
    }
    return result, nil
}

func main() {
    config, err := Load()
    if err != nil {
        panic(err)
    }
    fmt.Printf("%+v\n", config)
}
```

`SetConfigFile(".env")` selects the file explicitly, relative to the process's working directory. `SetConfigType("env")` specifies the parser. `ReadInConfig()` reads the file, and `Unmarshal()` decodes the values into `EnvConfigs`.

The `mapstructure` tags map `XXX` to `X` and `YYY` to `Y`. There is no field for `ZZZ`, so that value does not appear in the result.

I used `viper.New()` here to keep the configuration local to this loader, rather than using the package-level instance from the original experiment.

## Run the example

From the directory containing `.env`:

```bash
go run .
```

Expected output:

```text
{X:a Y:b}
```

If the file is missing, `Load()` returns an error. The example does not silently replace a missing file with an empty configuration.

## A .env file is different from process environment variables

This example reads a file as configuration. It does not export those values into the process environment, and it does not call `AutomaticEnv()` to read environment variables.

If you also want process environment variables to override file values, configure that separately. When decoding into a struct, explicitly binding the relevant keys with `BindEnv()` helps make the keys available to Viper; do not assume that calling `AutomaticEnv()` alone discovers every environment variable for `Unmarshal()`.

For this small example, reading the file alone is enough.

## Summary

Viper can read an env-format file and decode it into a Go struct using `mapstructure` tags. The key steps are selecting the file, setting its format, calling `ReadInConfig()`, and then calling `Unmarshal()`.

The original experiment used a file named `dot_env_file`; selecting `.env` explicitly makes this version easier to reuse in a typical project.

## References

- [Viper: Reading Config Files](https://github.com/spf13/viper#reading-config-files)
- [Viper: Working with Environment Variables](https://github.com/spf13/viper#working-with-environment-variables)
- [Viper: Unmarshaling](https://github.com/spf13/viper#unmarshaling)
