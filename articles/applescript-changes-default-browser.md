---
title: "AppleScriptでデフォルトブラウザを変更する"
emoji: "🗂"
type: "tech"
topics: ["AppleScript", "macOS"]
published: true
publiched_at: 2021-05-17
---

デフォルトブラウザを仕事とプライベートで切り替えるタイミングが発生したので、Script で出来ないかなと思い、Apple Script にたどり着いたのでデフォルトブラウザを切り替えてみました。
最初は vim を使ってい書いていましたが、日本語が上手く扱えずおそらくデフォルトで入っているスクリプトエディタ.app を利用しました。

# 1. システム設定を開く

`tell application "hoge"`で開けるようですが、この `hoge` 部分はスクリプトエディタを開き、`ファイル`から`用語説明を開く` を選択し システム環境設定.app をダブルクリックすると `System Preferences.sdef` というタイトルのウィンドウが出てきます。
この.sdef の名前を入れるといいみたいです。  
試しに Music.app の方も同じようにやったら表示できました。  
もし正確でなかったら教えて欲しいです…

```applescript
tell application "System Preferences"
	activate
end tell
```

activate まで入れることでアプリケーションを開いて表示できるみたいですね。  
前後の処理を追加することで終わったら消すみたいなこともできるみたいです。

```applescript
set didRunSystemPreferences to get running of application "System Preferences"

tell application "System Preferences"
	activate
end tell

if not didRunSystemPreferences then
	quit application "System Preferences"
end if
```

# 2. 一般のページ(?)に移動する

ここのページ(?)に移動するには `set current pane to pane "pane id"` という構文を使うようなのですが、ここで `pane id` がなにか確認する必要があります。
ここでやはり最速の print debug を使います。

```applescript
set didRunSystemPreferences to get running of application "System Preferences"

tell application "System Preferences"
	log id of every pane as list
end tell

if not didRunSystemPreferences then
	quit application "System Preferences"
end if

-- 結果(長い)
-- (*com.apple.preferences.AppleIDPrefPane, com.apple.preferences.Bluetooth, com.apple.preference.dock, com.apple.preference.expose, com.apple.preference.sidecar, com.apple.preference.speech, com.apple.preference.spotlight, com.apple.prefs.backup, com.apple.preference.universalaccess, com.apple.preferences.internetaccounts, com.apple.preference.keyboard, com.apple.preference.sound, com.apple.preference.screentime, com.apple.preference.security, com.apple.preferences.softwareupdate, com.apple.preference.displays, com.apple.preference.desktopscreeneffect, com.apple.preference.trackpad, com.apple.preference.network, com.apple.preferences.FamilySharingPrefPane, com.apple.preference.printfax, com.apple.preferences.configurationprofiles, com.apple.preference.mouse, com.apple.preferences.users, com.apple.preference.general, com.apple.preferences.extensions, com.apple.preference.startupdisk, com.apple.preferences.sharing, com.apple.Localization, com.apple.preference.energysaver, com.apple.preference.notifications, com.apple.preference.datetime*)
```

なんか一覧に載ってる奴らが対応している雰囲気があるので 1 つずつ見ていくと、 `com.apple.preference.general` とそれっぽいものがあるのでこれに移動してみることにします。
終了されると確認しづらいので、起動する部分だけを一旦使います。
これで一般のページにいけました。

```applescript
tell application "System Preferences"
	set current pane to pane "com.apple.preference.general"
end tell
```

# 3. デフォルトの Web ブラウザを変更する

ここまで来たらデフォルト Web ブラウザの部分をクリックして選択して終われば `ﾖｼｯ` ですね。
デフォルトの Web ブラウザの部分のメニューをクリックしてあげればよさそうですが、何を指定してあげればいいか調べる必要があります。  
やはりここも print debug。  
まずこのメニューがどこにあるのかを探します。  
window を指定できるといいみたいなのですが、その window 名を取得してみます。

```applescript
tell application "System Preferences"
	set current pane to pane "com.apple.preference.general"
	tell application "System Events" to tell application process "System Preferences"
		log every UI element as list
	end tell
end tell

-- 結果
-- (*window 一般 of application process System Preferences, menu bar 1 of application process System Preferences*)
```

結果を見ると `window "一般" of application process "System Preferences"` というものの中にあるようです。  
さらにこのメニューも print debug で出してみます。

```applescript
tell application "System Preferences"
	set current pane to pane "com.apple.preference.general"
	tell application "System Events" to tell window "一般" of application process "System Preferences"
		log every UI element as list
	end tell
end tell

-- 結果
-- 上から順番に載っているようなので関係ありそうなところを抜粋するとこうなりました。
-- static text デフォルトのWebブラウザ: of window 一般 of application process System Preferences, pop up button 3 of window 一般 of application process System Preferences, static text スクロールバーの表示: of window 一般 of application process System Preferences
--
```

結果からみると `pop up button 3 of window 一般 of application process System Preferences` が対象のようです。
これをクリックすればいいのですが、それでは選択されないのでさらにメニューの項目をクリックする必要があります。  
その対象もやはり print(ry

```applescript
tell application "System Preferences"
	set current pane to pane "com.apple.preference.general"
	tell application "System Events" to tell window "一般" of application process "System Preferences"
		click pop up button 3
		tell pop up button 3
			log every UI element as list
			-- ここで `menu 1` という要素が存在するのがわかる
			log every UI element of menu 1 as list
			-- ここでGoogle Chrome.appやSafari.appがあることがわかる
		end tell
	end tell
end tell
```

コメントに書いたように debug の結果 Google Chrome.app やらを click してあげれば良いみたいです。  
なのでこれをもとに Google Chrome.app を選択するには下のような Script になりました。

```applescript
tell application "System Preferences"
	set current pane to pane "com.apple.preference.general"
	tell application "System Events" to tell window "一般" of application process "System Preferences"
		click pop up button 3
		tell pop up button 3
			click menu item "Google Chrome.app" of menu 1
		end tell
	end tell
end tell
```

# 4. 完成

これを元に起動していないときは終了してもらうのも追加すると最終形はこうなりました。  
script に chmod +x しつつ、Google Chrome.app の部分を適当な値に変更すれば別のブラウザに変更もできるでしょう。

```applescript
#!/usr/bin/env osascript

set didRunSystemPreferences to get running of application "System Preferences"

tell application "System Preferences"
	set current pane to pane "com.apple.preference.general"
	tell application "System Events" to tell window "一般" of application process "System Preferences"
		click pop up button 3
		tell pop up button 3
			click menu item "Google Chrome.app" of menu 1
		end tell
	end tell
end tell

if not didRunSystemPreferences then
	quit application "System Preferences"
end if
```

# 感想

- Apple Script 完全に理解した()
- ブラウザ別に固定すればええやん()
- なんか Apple Script ちょっとわかったのでまあいいか

# 参考

- https://qiita.com/satosystems/items/8fff5b2313ecd6f81af3
- https://www.tantan-biyori.info/blog/2019/05/applescript-popup.html
