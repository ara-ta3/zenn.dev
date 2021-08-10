---
title: "Sentry JavaScript SDKでUser Feedbackウィジェットを使ってみる"
emoji: "🐕"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Sentry", "JavaScript"]
published: false
---

アプリケーションのモニタリングツールに Sentry というものがあるのですが、  
その JavaScript SDK にユーザフィードバック用のウィジェットがあるみたいで、それを試したのでそのメモです。

Sentry  
https://sentry.io/welcome/

Sentry User Feedback  
https://docs.sentry.io/platforms/javascript/enriching-events/user-feedback/

今回試したコードはここに置きました。  
https://github.com/ara-ta3/sentry-report-dialog-sample

# 1. とりあえず表示してみる

簡単に表示してみましょう。  
ドキュメントには React やら Angular などのフレームワークを利用していない場合の例が載っていました。  
beforeSend 時に Dialog を表示するように設定しつつ init して、Sentry にイベントを送ったら表示されるみたいです。

最小限のコードはこんな感じになります。  
beforeSend で行う場合簡単に表示できますが、なんらかのエラーが起こるたびに表示されてしまい不便でした。  
なので、後述する自前でハンドリングしながら時折表示させる方が良さそうに思いました。

```js
// DSNはsentryのドキュメントから取ってきました
const sentryDSN = "https://examplePublicKey@o0.ingest.sentry.io/0";
Sentry.init({
  dsn: sentryDSN,
  beforeSend(event) {
    if (event.exception) {
      Sentry.showReportDialog({ eventId: event.event_id });
    }
    return event;
  },
});

const hub = getCurrentHub();
hub.captureException(new Error("hoge"));
```

実際にボタンがクリックされたタイミングで行ったコードはこんな感じなりました。
リポジトリにあるコードを並べただけです。

src/Sentry.ts

```js
import * as Sentry from "@sentry/browser";
import { getCurrentHub } from "@sentry/browser";
import { sentryDSN } from "./env";

export function init(): void {
  Sentry.init({
    dsn: sentryDSN,
    beforeSend(event) {
      if (event.exception) {
        Sentry.showReportDialog({
          eventId: event.event_id,
          onLoad: () => {
            console.log("hi");
          },
        });
      }
      return event;
    },
  });
}

export function reportSentry(e: Error): void {
  const hub = getCurrentHub();
  hub.captureException(e);
}
```

src/components/SentryReport.tsx

```js
import * as React from "react";

export const SentryReport: React.FC<{
  onClick: () => void,
}> = (props) => {
  return (
    <div>
      <button onClick={props.onClick}>Click</button>
    </div>
  );
};
```

src/main.ts

```js
import * as React from "react";
import * as ReactDOM from "react-dom";
import { init as SentryInit, reportSentry } from "./Sentry";
import { SentryReport } from "./components/SentryReport";

SentryInit();

ReactDOM.render(
  <SentryReport
    onClick={() => {
      reportSentry(new Error("hoge"));
    }}
  />,
  document.getElementById("root")
);
```

この状態で `make build` = `webpack` を行い、dist/index.html を開き、表示されているボタンを押して Dialog を表示した結果

![](/images/sentry/sentry1.png)

# 2. beforeSend に任せず自前のエラーハンドリングで表示させる

もしエラーハンドリングを行う箇所があるならば beforeSend を使わずに showReportDialog を呼ぶことも可能です。  
この場合、直前に送られたエラーに対してのフィードバックになるようです。

例えば、下記のように main.ts を変えた場合、Sentry には hoge というメッセージを持ったエラーと fuga というメッセージを持ったエラーが通知されます。  
その後、showReportDialog が呼ばれますが、これは fuga というメッセージを持ったエラーの方に内容が渡されます。

また、下記コードでは captureException を showReportDialog 前に呼んでいますが、 captureException が無い場合 Dialog は表示されなかったので、事前にイベントを飛ばしておく必要があるようです。

src/main.ts

```js
ReactDOM.render(
  <SentryReport
    onClick={() => {
      const hub = getCurrentHub();
      hub.captureException(new Error("hoge"));
      hub.captureException(new Error("fuga"));
      Sentry.showReportDialog();
    }}
  />,
  document.getElementById("root")
);
```

fuga のメッセージに Feedback が来ている様子

![](/images/sentry/sentry2.png)

# まとめ

- ユーザから何か Feedback をもらいたい場合の Dialog を簡単に表示できた
  - Sentry 上のエラーに絡めてその Feedback が表示されるので便利
- 自前で通知する場合は `getCurrentHub().captureException(new Error("hoge"))` 後に `Sentry.showReportDialog()` を呼ぶと良さそう

ユーザから状態のフィードバックを得られるなら得られるに越したことはないと思うし便利機能だと思うので（送ってくれないとかそういうのはあると思うけど）Sentry を使ってる人はぜひ使ってみましょう。
