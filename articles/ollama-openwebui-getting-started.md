---
title: "UbuntuにOllamaとOpen WebUIをインストールして、ChatGPT風のローカル対話環境を構築する"
emoji: "🦙"
type: "tech"
topics: ["Ollama", "Open WebUI", "Ubuntu"]
published: true
---

## はじめに

この記事では、Ubuntu 環境に Ollama と Open Web UI をインストールし、ChatGPT のようなローカル対話環境を構築する方法を備忘録がてら紹介します。  
Ollama は、様々な LLM をローカル実行できるツールで、Open Web UI は、Ollama を Web UI 経由で利用するためのインタフェースを提供します。

## 前提条件

以下の環境で動作確認を行っています。
Ubuntu とは言っていますが、Mac mini 2018 に Ubuntu を入れているので超貧弱です。

```bash
lsb_release -d
Description:	Ubuntu 24.04 LTS
```

```bash
ollama --version
ollama version is 0.6.8
```

## 手順

### 1. Ollama のインストール

まず、Ollama をインストールします。以下のコマンドを実行します。

```bash
curl -L https://ollama.ai/install.sh | bash
```

インストール後、Ollama が正常に動作することを確認します。

```bash
ollama --version
```

Ollama で利用するモデルは、[ollama.com](https://ollama.com/) から探して、`ollama pull <model_name>` または `ollama run <model_name>` で取得できます。

https://ollama.com/

例:

```bash
ollama pull phi4
ollama run phi4

ollama pull gemma3
ollama run gemma3
```

### 2. Open Web UI のインストール

Open Web UI を起動します。

```bash
docker run -d -p 3000:8080  --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

### 2.5. Docker 内部から Ollama に接続できない場合の対応

Docker 内の Open Web UI から Ollama に接続できなかったので、Docker 内から curl を叩くことで疎通しているのかを確認しました。  
結果として届いていないことがわかったので、それを許可する設定を追加しました。

1.  Docker 内から Ollama への接続確認

```bash
docker run --rm curlimages/curl http://172.17.0.1:11434
```

2.  Ollama 外部からの接続許可設定

上記で接続できない場合、Ollama が外部からの接続を許可するように設定が必要です。
`/etc/systemd/system/ollama.service` を編集し、`Environment="OLLAMA_HOST=0.0.0.0"` を追加します。
検証するだけでしたら `OLLAMA_HOST=0.0.0.0 ollama serve` でも良いでしょう。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

:::message
`OLLAMA_HOST=0.0.0.0` は接続元を全て許容するデバッグ用途なので、本番環境では適切な設定をしてください。
:::

### 3. Open Web UI の利用

Open Web UI が起動したら、Web ブラウザで`http://localhost:3000`にアクセスします。Open Web UI のインタフェースから、Ollama でダウンロード済みのモデルを選択し、チャットを開始できます。

## まとめと感想

Ubuntu 環境に Ollama と Open Web UI をインストールし、ChatGPT のようなローカル対話環境を構築する方法を解説しました。  
そんなに強くない貧弱な PC に入れたので、予想通りではありますが、Response はそこまで早くないしあまり賢くはなかったです。
Agent モードに使ったらどうかなーと思って色々試し始めましたが、今のところさすがに期待は出来ないかなぁという気持ちです。
とはいえなにか面白い使い方が出てきたら試していきたいなぁと思いました。
