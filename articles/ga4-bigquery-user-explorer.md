---
title: "BigQueryのクエリを使ってGA4のユーザエクスプローラに近い探索を行う"
emoji: "📌"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: []
published: false
---


```sql
WITH user_ids AS (
  SELECT
    (
      SELECT
        value.string_value
      FROM
        UNNEST(user_properties)
      WHERE
        KEY = 'user_id'
    ) AS user_id,
    user_pseudo_id
  FROM
    `project.analytics_xxxxxxxx.*`
  WHERE
    _TABLE_SUFFIX BETWEEN 'events_20250101'
    AND 'events_20250131'
    AND (
      SELECT
        value.string_value
      FROM
        UNNEST(user_properties)
      WHERE
        KEY = 'user_id'
    ) is not null
  group by
    user_id,
    user_pseudo_id
)
SELECT
  user_ids.user_id,
  t.event_date,
  FORMAT_TIMESTAMP(
    '%Y-%m-%d %H:%M:%S',
    TIMESTAMP_TRUNC(timestamp_micros(event_timestamp), SECOND),
    "Asia/Tokyo"
  ) as event_timestamp_to_datetime,
  t.event_name,
  (
    SELECT
      value.string_value
    FROM
      UNNEST(t.event_params)
    WHERE
      KEY = 'page_location'
  ) as page_location,
  t.user_pseudo_id,
  device.category,
  device.operating_system_version,
  device.web_info.browser,
  device.is_limited_ad_tracking,
  traffic_source.source,
  traffic_source.medium,
  traffic_source.name,
  session_traffic_source_last_click.manual_campaign.source,
  session_traffic_source_last_click.manual_campaign.medium,
  session_traffic_source_last_click.manual_campaign.campaign_name
FROM
  `project.analytics_xxxxxxxx.*` AS t
  JOIN user_ids on t.user_pseudo_id = user_ids.user_pseudo_id
WHERE
  _TABLE_SUFFIX BETWEEN 'events_20250101'
  AND 'events_20250131'
ORDER BY
  event_timestamp desc, event_name desc
```
