---
title: "Ubuntu に Ollama と Open WebUI をインストールして、ChatGPT 風のローカル対話環境を構築する"
emoji: "💻"
type: "tech"
topics: ["Ollama", "Open WebUI", "Ubuntu", "ChatGPT"]
published: false
---

## はじめに

本記事では、Ubuntu 環境に Ollama と Open WebUI をインストールし、ChatGPT のようなローカル対話環境を構築する方法を解説します。Ollama は、様々な LLM（Large Language Model）をローカルで実行できるツールです。Open WebUI は、Ollama を Web UI 経由で利用するためのインターフェースを提供します。

## 前提条件

- Ubuntu 20.04 以降がインストールされていること
- インターネット接続があること
- sudo 権限があること

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

### 2. Open WebUI のインストール

次に、Open WebUI をインストールします。Open WebUI は Docker コンテナとして提供されているため、Docker がインストールされている必要があります。Docker がインストールされていない場合は、以下のコマンドでインストールします。

```bash
sudo apt update
sudo apt install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

Docker がインストールされたら、Open WebUI を起動します。

```bash
docker run -d -p 3000:3000 --add-host=host.docker.internal:host-gateway --name openwebui --restart always ghcr.io/openwebui/openwebui:latest
```

### 3. Open WebUI へのアクセス

Open WebUI が起動したら、Web ブラウザで`http://localhost:3000`にアクセスします。

### 4. モデルのダウンロード

Open WebUI にアクセス後、Ollama で利用可能なモデルをダウンロードします。Open WebUI のインターフェースからモデルを選択し、ダウンロードできます。例えば、`llama2`などのモデルをダウンロードできます。

### 5. チャットの開始

モデルのダウンロードが完了したら、Open WebUI のインターフェースからチャットを開始できます。

## トラブルシューティング

- **Open WebUI にアクセスできない場合:**
  - Docker コンテナが正常に起動しているか確認してください。`docker ps`コマンドで確認できます。
  - ファイアウォール設定を確認し、ポート 3000 へのアクセスが許可されているか確認してください。
- **モデルのダウンロードに失敗する場合:**
  - インターネット接続を確認してください。
  - Ollama が正常に動作しているか確認してください。
  - Open WebUI のログを確認し、エラーがないか確認してください。

## まとめ

本記事では、Ubuntu 環境に Ollama と Open WebUI をインストールし、ChatGPT のようなローカル対話環境を構築する方法を解説しました。この環境を利用することで、プライバシーを保護しながら、様々な LLM を試すことができます。
