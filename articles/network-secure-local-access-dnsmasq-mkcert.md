---
title: "スマホから家庭内ネットワークのOpenHandsにアクセス出来るようにしてスマホからAIエージェントに指示を出せるようにした"
emoji: "🌐"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["mkcert", "dnsmasq", "openhands", "network"]
published: true
---

## はじめに

家庭内にある `OpenHands` サーバへスマホからアクセスしたくなりました。
手が離せない状態でアクセスし、個人開発で簡単な作業をやってもらうのをどうにか出来ないかなと思ったのがきっかけでした。
PC なら /etc/hosts をいじれば済むのですが、スマホにはその機能がないので DNS を使う必要がありました。

:::message
OpenHands は元々 OpenDevin という名で、ブラウザ上でチャットにより指示を出すと作業をしてくれる AI エージェントのオープンソース版です
:::

https://github.com/All-Hands-AI/OpenHands

IP アドレスでのアクセスでは不便だったので、ドメイン名でのアクセスを出来るようにしました。
合わせて一応やるかというのテンションで HTTPS アクセスできるようにした備忘録となります。

## ネットワーク環境と目的

- サーバ：Ubuntu（IP 例：`192.168.0.20`）
- クライアント：iPhone
- ゴール：iPhone のブラウザから `https://openhands.yourdomain.local/` にアクセス可能な状態

:::message
.local ドメインは mDNS 用に予約されているため、他の仕組み（例：Avahi）が動いている場合は .home や .lan などを使うのが無難かもしれません。
:::

https://datatracker.ietf.org/doc/html/rfc6762

## 前提

- OpenHands サーバの起動
- mkcert + nginx で `https://openhands.yourdomain.local` にアクセス可能

主にこちらの記事でアクセス出来るような状態にしているので参考にしてください。

https://zenn.dev/ara_ta3/articles/openhands-nginx-settings

3 行でまとめると

- Docker で OpenHands のサーバを起動
- mkcert で証明書作成し nginx へと設定
- nginx に server name の設定をした上で起動

という感じです。  
mkcert の証明書は後々スマホへ渡して利用する予定があります。

## スマホから DNS 解決のための dnsmasq 設定

### dnsmasq のインストールと設定

```bash
sudo apt install dnsmasq
```

ドメイン名 `openhands.yourdomain.local` をローカル IP に解決させる設定を追加します。

:::message
IP アドレスはサーバにて `ip a` コマンド等で調べて入れてください。

```bash
$ip a
...
2: enp3s0f0: <...> ...
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
    inet 192.168.0.20/24 brd 192.168.0.255 scope global enp3s0f0 # ここの192.168.0.20 の部分
       valid_lft forever preferred_lft forever
```

:::

/etc/dnsmasq.d/local.conf のファイルを作成し、内容を以下のようにします。

```bash
address=/openhands.yourdomain.local/192.168.0.20
```

上流 DNS の明示（ルーターなど）をします。

:::message
現時点でどの値が使われているかは `resolvectl status` などのコマンドで確認してください

```bash
$resolvectl status
Global
         Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
  resolv.conf mode: stub

Link 2 (enp3s0f0)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 192.168.0.1
       DNS Servers: 192.168.0.1 # この部分
```

:::

/etc/dnsmasq.d/upstream.conf のファイルを作成し、内容を以下のようにします。

```bash
server=192.168.0.1
```

以下 2 ファイルを作成し中身を入れたのでこの設定を反映させます。

- /etc/dnsmasq.d/local.conf
- /etc/dnsmasq.d/upstream.conf

```bash
sudo systemctl restart dnsmasq
```

ここでおそらく 53 番ポートが使われているため起動しないかと思います。
systemd-resolved がローカルでスタブ DNS[^1] として 53 番ポートを使用していたためです。
なので、systemd-resolved のスタブ DNS の設定を止める必要があります。

[^1]: 自分自身で名前解決はせず、他の DNS サーバに問い合わせを「転送するだけ」の小さな DNS

### `systemd-resolved` のスタブを無効化

/etc/systemd/resolved.conf のファイルを以下のように変更します。

```
[Resolve]
DNSStubListener=no
```

そして設定を反映します。

```bash
sudo systemctl restart systemd-resolved
```

### resolv.conf の修正

/etc/resolv.conf は通常、systemd-resolved によって管理されており、DNS リクエストは 127.0.0.53 に転送されます。  
この状態では dnsmasq を経由しないため、dnsmasq に切り替えるにはリンクを削除して上書きする必要があります。  
127.0.0.1 を指定して dnsmasq を参照するようにします。

```bash
sudo rm /etc/resolv.conf
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
```

## スマホの DNS 設定

Wi-Fi 設定で、接続中のネットワークを開き「DNS を手動」に設定し、DNS サーバとして `192.168.0.20` を指定します。

## HTTPS のための mkcert 設定（iOS 対応）

mkcert の Ubuntu サーバでの設定は完了している前提で進めます。  
詳細な mkcert や nginx の設定は、以下の記事にまとめています。

https://zenn.dev/ara_ta3/articles/mkcert-local-domain-https
https://zenn.dev/ara_ta3/articles/openhands-nginx-settings

### iOS に証明書をインストール

`mkcert -CAROOT` でルート CA の場所を確認し、なんらかの方法で iOS に証明書を渡します。
以下の rootCA.pem が対象です。

```bash
ls "$(mkcert -CAROOT)"
rootCA-key.pem	rootCA.pem
```

- AirDrop やメールなどで iPhone に送信
- iPhone 側でプロファイルをインストール
- 「設定 > 一般 > 情報 > 証明書 信頼設定」からインストールした CA を「完全に信頼」

Android は未検証ですが、iPhone と同様に証明書をインストールする形になると思われます。(未確認で、すみません)

これで設定した URL とアクセスすれば無事表示できるはずです。

```
https://openhands.yourdomain.local
```

## おわりに

OpenHands をスマホから開いて指示を出す環境を整えてみました。  
dnsmasq + mkcert は構築も楽で良かったです。  
手が空かないんだけど、なんかあのコードの検証するスクリプト書いてくれないかな〜みたいな指示を OpenHands 経由で出して時間を有効活用していけると良いなと思いました。
