# Weather API

### 今日のツイートを取得する

#### HTTPリクエスト

`GET http://hacku-techlion.herokuapp.com/weather`

#### クエリパラメーター

| プロパティ | 必須 | 説明                     |
| ---------- | ---- | ------------------------ |
| lat        | Yes  | 天気を取得する地点の緯度 |
| lng        | Yes  | 天気を取得する地点の経度 |

#### レスポンス

| プロパティ | タイプ | 説明                 |
| ---------- | ------ | -------------------- |
| weather    | String | 天気                 |
| icon_url   | Path   | 天気のアイコンの画像 |
| temp       | Number | 平均気温             |
| humid      | Number | 平均湿度             |