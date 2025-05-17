---
title: "スマホから家庭内ネットワークの openhands にアクセスするために dnsmasq と証明書を整えたときの備忘録"
emoji: "👏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["mkcert", "dnsmasq"]
published: false
---
## はじめに

家庭内にある `openhands` サーバへ、iOS 端末から HTTPS でアクセスしたくなった。  
IPアドレスでのアクセスでは不便な上、HTTPS化していないとブラウザに警告が出てしまう。  
そこで以下の2点を整えることにした。

- ドメイン名でアクセスできるようにする（DNS解決）
- HTTPSで信頼される証明書を使う

## ネットワーク環境と目的

- サーバ：Ubuntu（IP例：`192.168.11.20`）
- クライアント：iPhone
- 目的：iPhoneの Safari から `https://openhands/` にアクセスできるようにする

## DNS解決のための dnsmasq 設定

### `systemd-resolved` を無効化

```bash
sudo nano /etc/systemd/resolved.conf
```

以下のように変更：

```
[Resolve]
DNSStubListener=no
MulticastDNS=yes
```

設定を反映：

```bash
sudo systemctl restart systemd-resolved
```

### resolv.conf の修正

```bash
sudo rm /etc/resolv.conf
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
```

### dnsmasq のインストールと設定

```bash
sudo apt install dnsmasq
```

ドメイン名 `openhands` をローカルIPに解決させる設定を追加：

```bash
sudo nano /etc/dnsmasq.d/local.conf
```

```
address=/openhands/192.168.11.20
```

上流DNSの明示（ルーターなど）：

```bash
sudo nano /etc/dnsmasq.d/upstream.conf
```

```
server=192.168.11.1
```

設定を反映：

```bash
sudo systemctl restart dnsmasq
```

### スマホの DNS 設定

iOS の Wi-Fi 設定で、接続中のネットワークを開き「DNS を手動」に設定し、DNSサーバとして `192.168.11.20` を指定する。

## HTTPS のための mkcert 設定（iOS対応）

### mkcert のインストール（Ubuntu）

```bash
sudo apt install libnss3-tools
brew install mkcert    # Linuxbrew を使用している場合
mkcert -install
```

### 証明書の作成

```bash
mkcert openhands
```

→ `openhands.pem`（証明書）と `openhands-key.pem`（秘密鍵）が生成される。

### Webサーバに設定（例：Node.jsやnginxなど）

（例を省略、ここは環境に応じて）

### iOS に証明書をインストール

1. `mkcert -CAROOT` でルートCAの場所を確認
2. `.pem` を `.cer` に変換：

```bash
cp "$(mkcert -CAROOT)/rootCA.pem" rootCA.cer
```

3. AirDrop やメールなどで iPhone に送信
4. iPhone 側でプロファイルをインストール
5. 「設定 > 一般 > 情報 > 証明書信頼設定」からインストールした CA を「完全に信頼」

## 動作確認

iPhone の Safari から：

```
https://openhands
```

にアクセスし、警告なしに接続できれば成功。

## おわりに

ローカル開発環境や家庭内サービスでも、HTTPS と名前解決があるだけで体験は大きく変わる。  
dnsmasq + mkcert は構築も軽く、継続的に使える組み合わせだった。

