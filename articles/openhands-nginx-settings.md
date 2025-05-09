---
title: "OpenHandsのUIにnginx+mkcertでhttpsでアクセス出来るようにする"
emoji: "🐙"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [openhands, nginx, mkcert, https]
published: true
---

## はじめに

OpenHands を家庭内ネットワークの Ubuntu にホスティングし、nginx と mkcert を使って https 経由でアクセス出来るようにしたので、その時の備忘録がてら設定内容をメモします。
前提として openhands.yourdomain.local というドメインに OpenHands と nginx をホスティングしています。
この際に mkcert で証明書を発行し nginx に設定しつつ、アクセス元側ではその証明書を許容する設定をします。

利用した OpenHands のバージョンは 0.36.0 です。

```bash
# 確認に利用したコマンド
docker exec {container id} cat pyproject.toml|grep -m 1 -B 1 version
name = "openhands-ai"
version = "0.36.0"
```

### OpenHands の実行

前提として、Ubuntu 上では、以下のようなコマンドを実行し OpenHands を起動してあります。

```bash
docker run -it --rm -d --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.36-nikolaik  \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway
    --name openhands-app
    docker.all-hands.dev/all-hands-ai/openhands:0.36

# 1行コピペ用
docker run -it --rm -d --pull=always -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.36-nikolaik -e LOG_ALL_EVENTS=true -v /var/run/docker.sock:/var/run/docker.sock -v ~/.openhands-state:/.openhands-state -p 3000:3000 --add-host host.docker.internal:host-gateway --name openhands-app docker.all-hands.dev/all-hands-ai/openhands:0.36
```

## mkcert のインストールと設定

まずは https でアクセスするための証明書の発行を行います。  
mkcert を利用し、ローカルで https の証明書を作成した後、アクセス元の Mac のキーチェインに証明書を追加します。  
mkcert については別記事でも紹介しているのでそちらを参考にしてください。

https://zenn.dev/ara_ta3/articles/mkcert-local-domain-https

ざっとここでやることしては以下の通りです。

```bash
# mkcertのインストール
brew install mkcert
sudo apt install mkcert

# ローカルCA証明書のインストール
mkcert -install

# ドメインの証明書作成
mkcert openhands.yourdomain.local
```

mkcert コマンドを実行すると、`openhands.yourdomain.local.pem` と `openhands.yourdomain.local-key.pem` というファイルが生成されます。これらのファイルは、nginx の設定で使用します。
このあとの nginx の設定では、 `/etc/nginx/certs/` ディレクトリにこのファイルを置くという前提で進めます。

### Mac のキーチェインに証明書を追加

ブラウザが警告を出さないようにするため、以下のコマンドで証明書をキーチェインに追加します。

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/rootCA.pem
```

:::message
家庭用ネットワーク内で利用するなどの個人利用の前提でやっています。
:::

## nginx の設定

openhands.yourdomain.local へアクセスした際にリバースプロキシする設定と、websocket のための設定を nginx に記述します。  
OpenHands はタスク指示の画面で WebSocket を利用するようなので、`/socket.io/` の設定が WebSocket 通信を可能にするため必要です。

```nginx
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
```

上記の設定ファイルを配置したら、nginx を再起動して設定を反映させます。

```bash
sudo systemctl reload nginx
```

## OpenHands の UI へのアクセス確認

:::message
アクセス元の `/etc/hosts` に Ubuntu の IP と openhands.yourdomain.local のマッピングがある前提です。
:::

ブラウザで `https://openhands.yourdomain.local` にアクセスして、OpenHands の UI が表示されることを確認します。

### WebSocket の疎通について

LLM や Git の API キーや Token の設定をした後に会話のページにて、下の方に　`クライアントの準備を待機中` などのメッセージが出てくると思います。  
ここが最終的に `エージェントがユーザ入力を待機中...` までいけば準備は完了です。

上記のメッセージが出ないが、nginx を経由せずにポート指定したアプリケーションでは動くなどの場合、WebSocket 周りの設定が上手く行っていないかもしれません。
また、バージョンが変わり、 WebSocket のパス変更がもし起きている場合は、Developers Console などでリクエストを見たりするのが良いかもしれません。
今回使っているバージョンの 0.36.0 では `wss://openhands.yourdomain.local/socket.io/` を Develops Console の Network 内で見つけたため、WebSocket の設定を nginx へと 追加しています。

## まとめ

仕事で使った Devin が便利だったので家で旧 OpenDevin という名の OpenHands を動かしてみました。
OpenHands を nginx+https 経由で動く状態が作れました。
まだ 0.36 というバージョンなこともあり過渡期だとは思いますが、Devin で感じた体験とはやはりまだ差があるなぁというのが感想です。
今後もアップデートあると思うので楽しみながら触れて、機会があれば OSS への貢献も出来たらなという気持ちでいます。
