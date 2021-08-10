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

TODO: いろいろ

マッチングイベントってやつを全部キャンペーンにかえる
エンドポイント帰る
タイトルも変えたい感

特にエラーハンドリングを行う責務の部分がないならこれで良さそう

```js
export function init(): void {
  Sentry.init({
    dsn: sentryDSN,
    beforeSend(event) {
      if (event.exception) {
        Sentry.showReportDialog({ eventId: event.event_id });
      }
      return event;
    },
  });
}
```

もしエラーハンドリングを行う箇所があるならこんな感じにすると良さそう
直前に送られたエラーに対してのフィードバックになる

```js
ReactDOM.render(
  <SentryReport
    onClick={() => {
      reportSentry(new Error("hoge"));
      reportSentry(new Error("fuga"));
      Sentry.showReportDialog();
    }}
  />,
  document.getElementById("root")
);
```

この場合 fuga というエラーに対してフィードバックが行われる
