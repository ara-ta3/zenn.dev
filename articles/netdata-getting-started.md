---
title: "Netdataのstream機能でネットワーク内の親機にメトリクスを送る"
emoji: "📌"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["netdata", "監視", "SRE", "macOS"]
published: true
---

家のデータとかをモニタリングできないかなと思って探していたら netdata というものを知って、それを raspberry pi といつも作業している PC に入れて、メトリクスを raspberry pi の方に集約させてみたのでその時の備忘録です。

netdata についてはこちら

- https://www.netdata.cloud/

使用した raspberry pi はこんな感じでした。

```bash
$uname -a
Linux raspberrypi 5.10.103-v7+ #1529 SMP Tue Mar 8 12:21:37 GMT 2022 armv7l GNU/Linux
pi@raspberrypi(Up 95 days) ~

$lsb_release -a
No LSB modules are available.
Distributor ID:	Raspbian
Description:	Raspbian GNU/Linux 10 (buster)
Release:	10
Codename:	buster
```

途中にも記述がありますが、利用した netdata のバージョンはいずれも v1.44.1 です。

# 親機(raspberry pi)への netdata インストール

docs にコマンドが用意されており、それをやるだけでめちゃくちゃ簡単にインストール出来ました。

- https://learn.netdata.cloud/docs/installing/

いくつかオプションを外したものが下記になります。

```
wget -O /tmp/netdata-kickstart.sh https://my-netdata.io/kickstart.sh && sh /tmp/netdata-kickstart.sh --stable-channel --disable-telemetry
```

yes と打つだけで全てがインストールされて簡単の極みでした。
ちなみにインストールされたバージョンは v1.44.1 です。

```bash
$/opt/netdata/bin/netdata -v
netdata v1.44.1
```

# 親機(raspberry pi) への設定追加

## 1. API キーの生成

uuidgen コマンドを利用して UUID を生成して使います。  
つまりなんでも良いという感じです。

```bash
$uuidgen
17DD0B30-853A-404E-94D2-09F069A05F37
```

:::message
秘匿すべき API キーになるので本来記述すべきではないですが、今生成したもので実際には使っていないので、この記事ではこの値を利用します。
:::

## 2. stream.conf に API キーの設定追加

netdata がインストールされた先は /opt/netdata で、そのさらに etc/netdata にある部分が主に設定ファイルがある場所になります。  
つまり `/opt/netdata/etc/netdata` です。  
stream.conf という設定ファイルを編集したいのですが、確かデフォルトだとなかったと思います。(忘れちゃった・・・)  
その際、 `./edit-config stream.conf` のようにコマンドを叩くと、デフォルトの設定ファイルを持ってきて編集が始まるのでそのようにしましょう。  
ちなみに nano というエディタで編集が始まりますが、終了方法は ctrl+x です。
やりたいこととしては、stream.conf を作り、そこに設定を書くだけではあるので、単純にファイルを生成してもいいでしょうし、cp で自分で取ってきてもいいと思います。  
私はデフォルトのものを引き継いだ上でやりたいと思ったので、./edit-config か cp でデフォルトのものを持ってくるのをおすすめします。

```bash
$pwd
/opt/netdata/etc/netdata

$sudo ./edit-config stream.conf
Copying '/opt/netdata/usr/lib/netdata/conf.d//stream.conf' to '/opt/netdata/etc/netdata//stream.conf' ...
Editing '/opt/netdata/etc/netdata/stream.conf' ...
```

下の方に行くと、 `[API_KEY]` とあるのでそこに先程生成した uuid を API キーとして設定します。  
このあたり。

```
# [API_KEY] is [YOUR-API-KEY], i.e [11111111-2222-3333-4444-555555555555]
[API_KEY]
    # Default settings for this API key
```

いくつか設定して下記のような感じになりました。  
具体的には `enabled = yes` と `default memory mode = dbengine` だけ設定しています。  
dbengine は長めにデータを保持してもらおうかなと思ったので ram などではなくこれにしとくかくらいの軽い気持ちで設定しています。
allow from には本来であれば IP アドレス範囲を設定したほうが良いと思いますが、ネットワーク周りの設定は動いてから狭めたほうがハマりにくいと思っているので、とりあえずゆるゆるにしています。

```
[17DD0B30-853A-404E-94D2-09F069A05F37]
    # Default settings for this API key

    # This GUID is to be used as an API key from remote agents connecting
    # to this machine. Failure to match such a key, denies access.
    # YOU MUST SET THIS FIELD ON ALL API KEYS.
    type = api

    # You can disable the API key, by setting this to: no
    # The default (for unknown API keys) is: no
    enabled = yes

    # A list of simple patterns matching the IPs of the servers that
    # will be pushing metrics using this API key.
    # The metrics are received via the API port, so the same IPs
    # should also be matched at netdata.conf [web].allow connections from
    allow from = *

    # The default history in entries, for all hosts using this API key.
    # You can also set it per host below.
    # For the default db mode (dbengine), this is ignored.
    #default history = 3600

    # The default memory mode to be used for all hosts using this API key.
    # You can also set it per host below.
    # If you don't set it here, the memory mode of netdata.conf will be used.
    # Valid modes:
    #    save     save on exit, load on start
    #    map      like swap (continuously syncing to disks - you need SSD)
    #    ram      keep it in RAM, don't touch the disk
    #    none     no database at all (use this on headless proxies)
    #    dbengine like a traditional database
    default memory mode = dbengine
```

最後に反映させるためにリスタートさせます。

```bash
$sudo systemctl restart netdata
```

# 子機(Mac)への netdata インストール

brew install で入るので便利です。  
Intell Mac であれば、インストール先は `/usr/local/etc/netdata/` になるようです。
ちなみにインストールされたバージョンは親機同様 v1.44.1 でした。

```bash
$brew install netdata

$/usr/local/Cellar/netdata/1.44.1/sbin/netdata -v
netdata v1.44.1
```

# 子機(Mac)への 設定追加

親機同様に stream.conf へと設定を追加します。
変更箇所は、 `enabled = yes`、 `destination = 192.168.xx.xxx`、 `api key = 17DD0B30-853A-404E-94D2-09F069A05F37` です。
destination は親機の IP アドレスにします。

```
[stream]
    # Enable this on child nodes, to have them send metrics.
    enabled = yes

    # Where is the receiving netdata?
    # A space separated list of:
    #
    #      [PROTOCOL:]HOST[%INTERFACE][:PORT][:SSL]
    #
    # If many are given, the first available will get the metrics.
    #
    # PROTOCOL  = tcp, udp, or unix (only tcp and unix are supported by parent nodes)
    # HOST      = an IPv4, IPv6 IP, or a hostname, or a unix domain socket path.
    #             IPv6 IPs should be given with brackets [ip:address]
    # INTERFACE = the network interface to use (only for IPv6)
    # PORT      = the port number or service name (/etc/services)
    # SSL       = when this word appear at the end of the destination string
    #             the Netdata will encrypt the connection with the parent.
    #
    # This communication is not HTTP (it cannot be proxied by web proxies).
    destination = 192.168.xx.xxx

    # Skip Certificate verification?
    # The netdata child is configurated to avoid invalid SSL/TLS certificate,
    # so certificates that are self-signed or expired will stop the streaming.
    # Case the server certificate is not valid, you can enable the use of
    # 'bad' certificates setting the next option as 'yes'.
    #ssl skip certificate verification = yes

    # Certificate Authority Path
    # OpenSSL has a default directory where the known certificates are stored.
    # In case it is necessary, it is possible to change this rule using the variable
    # "CApath", e.g. CApath = /etc/ssl/certs/
    #
    #CApath =

    # Certificate Authority file
    # When the Netdata parent has a certificate that is not recognized as valid,
    # we can add it to the list of known certificates in "CApath" and give it to
    # Netdata as an argument, e.g. CAfile = /etc/ssl/certs/cert.pem
    #
    #CAfile =

    # The API_KEY to use (as the sender)
    api key = 17DD0B30-853A-404E-94D2-09F069A05F37
```

これもまた反映させるためにリスタートさせます。

```bash
$brew services restart netdata
```

# 反映の様子

ちゃんと設定ができていれば、例えば Nodes のところに追加したものが現れているはずです。

![](/images/netdata/result.png)

なんとなくやったら成功してしまったので、デバッグ等の方法を書けないのが心苦しいのですが、成功していない場合、ログは下記あたりに出ているので、そこから拾い上げられると良いのかな・・・と思います。

- 親機(raspberry pi)
  - /opt/netdata/var/log/netdata
- 子機(Mac)
  - /usr/local/var/log/netdata

# まとめ

- netdata、さらっとメトリクスを取れて便利だった
- カスタムメトリクスも送れるらしいので送りたい
  - 本当はこれを雑にやりたくて探していました
- アラート設定を行い、Slack 通知も出来るので便利です
  - https://learn.netdata.cloud/docs/alerting/notifications/agent-dispatched-notifications/slack
