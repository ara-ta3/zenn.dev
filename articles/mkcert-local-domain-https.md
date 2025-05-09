---
title: "HTTPS for .local Domains with mkcert"
emoji: "🔒"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: []
published: false
---
## はじめに

ローカルネットワーク内で、`.local`ドメインを使用してHTTPS通信を実現する方法について解説します。mkcertというツールを使用することで、簡単に自己署名証明書を作成し、安全な通信を確立できます。
## mkcertのインストール

mkcertは、自己署名証明書を簡単に作成できるツールです。以下のコマンドでインストールできます。

```bash
brew install mkcert
```

または、

```bash
apt-get install mkcert
```
## 証明書の生成

mkcertを使用して、`.local`ドメイン用の証明書を生成します。

```bash
mkcert -install
mkcert yourdomain.local
```

`yourdomain.local`の部分は、実際に使用するドメイン名に置き換えてください。
## Webサーバーの設定 (nginxの例)

nginxの設定ファイル (`/etc/nginx/conf.d/yourdomain.local.conf`など) を作成し、以下のように設定します。

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.local;

    ssl_certificate /path/to/yourdomain.local.pem;
    ssl_certificate_key /path/to/yourdomain.local-key.pem;

    root /path/to/your/web/root;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

`/path/to/yourdomain.local.pem`と`/path/to/yourdomain.local-key.pem`は、mkcertで生成した証明書と秘密鍵のパスに置き換えてください。
`/path/to/your/web/root`は、Webサイトのルートディレクトリのパスに置き換えてください。
## まとめ

mkcertを使用することで、ローカルネットワーク内でのHTTPS通信を簡単に実現できます。安全な開発環境を構築し、快適なWebサイト開発を行いましょう。
