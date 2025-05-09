---
title: "家のネットワーク内で.localドメインをhttpsで通信できるようにmkcertで証明書の設定をする"
emoji: "🔒"
type: "tech"
topics: ["mkcert", "https"]
published: false
---

## はじめに

自宅などのローカルネットワーク内で、`.local`ドメインを使用しているのですが、https で通信をしたくなりました。  
探してみたら mkcert を使うと楽に出来そうだったのでやってみたときの備忘録です。  
今回のケースでは、Ubuntu 上にポート 3000 で起動したウェブサービスがあり、それを Mac からアクセスする状況を想定します。

### 概要

1.  Ubuntu の設定
    - `mkcert` を使用して証明書を生成
    - ウェブサービス (例: Node.js アプリ、Python Flask アプリ) をポート 3000 で実行
    - nginx にウェブサービスと証明書の設定
2.  Mac の設定
    - `/etc/hosts` ファイルに、`.local` ドメインの設定
    - 証明書を信頼するための設定
    - ブラウザでウェブサービスにアクセス (例: `https://yourdomain.local`)

## 証明書の生成

### mkcert のインストール

`mkcert` は、自己署名の証明書の作成を簡素化するツールです。
以下を使用してインストールします。

```bash
sudo apt install mkcert
```

`mkcert` コマンドを用いて `.local` ドメインの証明書を生成します。

```bash
mkcert -install
mkcert yourdomain.local
```

これにより、必要な証明書が作成されます。

## nginx の設定例

この設定は、`localhost:3000` で実行されているバックエンドサービスにリクエストをプロキシするという例です。

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

certs ファイルはどこでもいいですが、私は `/etc/nginx/certs` ディレクトリを作成して置くことにしました。

## ブラウザの信頼

証明書は自己署名なので、ブラウザが警告を出してくるはずです。  
正しい挙動なのですが、家のネットワーク内の想定しているリクエストでは出ないようにしたいというのが今回やりたかったことなので、これを Mac のキーチェインに登録し警告を回避する設定をします。

1.  Ubuntu 側で、mkcert のルート証明書を取得

場所は `mkcert -CAROOT` コマンドで確認できます。

```bash
mkcert -CAROOT
/home/myuser/.local/share/mkcert
```

2.  Ubuntu から Mac に、この`rootCA.pem`ファイルを安全な方法（例：scp、sftp）でコピー

Mac 側からの実行の想定です。

```bash
scp yourdomain.local:/home/myuser/.local/share/mkcert/rootCA.pem ./
```

3.  キーチェインに証明書を追加

Mac のターミナルで、以下のコマンドを実行して、キーチェインに証明書を追加します。

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/rootCA.pem
```

`/path/to/rootCA.pem`は、実際にコピーした`rootCA.pem`ファイルのパスに置き換えてください。

4.  `https://yourdomain.local`にアクセス

Chrome などのブラウザで、`https://yourdomain.local`にアクセスします。 警告が表示されなくなるはずです。

:::message
起動済みのブラウザの場合、一度再起動しないと反映されません。  
反映されない場合は、完全に終了してから再度開いてみてください。
:::

## まとめ

`mkcert` を使用して、`.local` ドメインを使用したローカル開発の HTTPS 設定を簡単にできました。  
用法用量を守って良い感じに使いましょう。
