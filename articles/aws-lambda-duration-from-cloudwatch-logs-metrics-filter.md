---
title: "CloudWatch LogsのメトリクスフィルタでLambdaの実行時間をカスタムメトリクスに飛ばす"
emoji: "📚"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["AWS", "Lambda", "CloudWatch", "CloudWatchLogs"]
published: false
---

https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/logs/MonitoringPolicyExamples.html

# メトリクスフィルタフィルタを作成する

- LambdaのDurationが書かれているLogのフォーマット
- テスト方法


```
[report_label="REPORT", ,request_id, duration_label="Duration:", duration_value, ]
```
