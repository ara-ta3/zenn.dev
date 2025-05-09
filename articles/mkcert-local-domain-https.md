---
title: "家のネットワーク内で.localドメインをhttpsでアクセスできるように証明書の設定をする"
emoji: "🔒"
type: "tech"
topics: ["mkcert", "https"]
published: false
---

## はじめに

ローカルネットワーク内で、`.local`ドメインを使用して HTTPS 通信を実現する方法について解説します。mkcert というツールを使用することで、簡単に自己署名証明書を作成し、安全な通信を確立できます。

今回のケースでは、Ubuntu 上にポート 3000 で起動した Web サービスがあり、それを Mac から HTTPS 経由でアクセスする状況を想定します。

### 概要

1.  **Ubuntu の設定:**
    - `mkcert` を使用して証明書を生成します。
    - Web サービス (例: Node.js アプリ、Python Flask アプリ) をポート 3000 で実行します。
    - nginx などの Web サーバーを設定して、HTTPS リクエストを処理し、ポート 3000 のサービスにプロキシします。
2.  **Mac の設定:**
    - Mac の `/etc/hosts` ファイルに、`.local` ドメインを Ubuntu の IP アドレスにマッピングするエントリを追加します。
    - ブラウザで HTTPS 経由で Web サービスにアクセスします (例: `https://yourdomain.local`)。

## 証明書の生成

### mkcert のインストール

`mkcert` は、自己署名証明書の作成を簡素化するツールです。以下を使用してインストールします。

```bash
# macOS (Homebrew を使用)
brew install mkcert

# Debian/Ubuntu
sudo apt install mkcert
```

`.local` ドメインの証明書を生成するには、`mkcert` を使用します。`yourdomain.local` を実際のドメイン名に置き換えてください。

```bash
mkcert -install
mkcert yourdomain.local
```

これにより、必要な証明書が作成され、CA 証明書がシステムのトラストストアにインストールされます。

## nginx の設定例

### バックエンドサービスへのプロキシ (Node.js、Python など)

この設定は、`localhost:3000` で実行されているバックエンドサービスにリクエストをプロキシします。

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.local;

    ssl_certificate /path/to/yourdomain.local.pem;
    ssl_certificate_key /path/to/yourdomain.local-key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

バックエンドサービスがポート 3000 で実行されていることを前提としています。必要に応じて、`proxy_pass` ディレクティブを調整してください。

## ブラウザの信頼

証明書は自己署名されているため、ブラウザは接続がプライベートではないことを警告する可能性があります。Ubuntu 側で生成した mkcert のルート証明書を Mac のキーチェーンに登録することで、この警告を回避できます。

1.  Ubuntu 側で、mkcert のルート証明書を取得します。mkcert は、ルート証明書の場所を`CAROOT`環境変数で定義しています。通常は、`/usr/local/share/mkcert/rootCA.pem`にあります。
2.  Ubuntu から Mac に、この`rootCA.pem`ファイルを安全な方法（例：scp、sftp）でコピーします。
3.  Mac のターミナルで、以下のコマンドを実行して、キーチェーンに証明書を追加します。

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/rootCA.pem
```

`/path/to/rootCA.pem`は、実際にコピーした`rootCA.pem`ファイルのパスに置き換えてください。

4.  Chrome などのブラウザで、`https://yourdomain.local`にアクセスします。警告が表示されなくなるはずです。

## まとめ

`mkcert` を使用すると、`.local` ドメインを使用したローカル開発の HTTPS 設定が簡素化されます。  
これにより、安全な開発環境を作成し、Web アプリケーションをより快適に開発できます。
