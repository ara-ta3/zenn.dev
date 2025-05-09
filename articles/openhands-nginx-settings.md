---
title: "openhandsのUIにnginx+mkcertでhttpsでアクセス出来るようにする"
emoji: "🐙"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [openhands, nginx, mkcert, https]
published: false
---

## はじめに

openhands の UI を HTTPS で安全に利用できるように、nginx と mkcert を使って設定する方法を紹介します。

## 目次

- [mkcert のインストールと設定](#mkcertのインストールと設定)
- [nginx の設定](#nginxの設定)
- [openhands の UI へのアクセス確認](#openhandsのUIへのアクセス確認)

## mkcert のインストールと設定

mkcert を使ってローカルで HTTPS の証明書を作成します。

```bash
# mkcertのインストール (例: macOS)
brew install mkcert

# ローカルCA証明書のインストール
mkcert -install

# ドメインの証明書作成
mkcert openhands.yourdomain.local
```

mkcert コマンドを実行すると、`openhands.yourdomain.local.pem` と `openhands.yourdomain.local-key.pem` というファイルが生成されます。これらのファイルは、nginx の設定で使用します。

## nginx の設定

nginx の設定ファイルを作成し、HTTPS でアクセスできるように設定します。

````nginx
server {
    listen 443 ssl;
    listen 80;
    server_name openhands.yourdomain.local;
    ssl_certificate     /etc/nginx/certs/openhands.yourdomain.local.pem;
    ssl_certificate_key /etc/nginx/certs/openhands.yourdomain.local-key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }

    location /socket.io/ {
        proxy_pass http://localhost:3000;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

nginx の設定ファイルは、`/etc/nginx/conf.d/` などの場所に配置します。設定ファイルを配置したら、nginx を再起動して設定を反映させます。

```bash
sudo nginx -s reload
````

## openhands の UI へのアクセス確認

ブラウザで `https://openhands.yourdomain.local` にアクセスして、openhands の UI が表示されることを確認します。

もし表示されない場合は、以下の点を確認してください。

- nginx の設定ファイルに誤りがないか
- mkcert で生成された証明書のパスが正しいか
- nginx が正しく起動しているか
- ブラウザのキャッシュが残っていないか
