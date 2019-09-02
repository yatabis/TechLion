# Google Calendar API

### 今日のイベントの一覧を取得する

#### HTTPリクエスト

`GET http://hacku-techlion.herokuapp.com/google/events/today`

#### レスポンス

| プロパティ | タイプ | 説明                                   |
| ---------- | ------ | -------------------------------------- |
| title      | String | イベントタイトル                       |
| start      | Object | イベント開始時刻の日時オブジェクト     |
| end        | Object | イベント終了時刻の日時オブジェクト     |
| location   | Object | イベントが行われる場所オブジェクト     |
| link       | Path   | Googleカレンダーの当該イベントのリンク |



### 日時オブジェクト

| プロパティ | タイプ | 説明 |
| ---------- | ------ | ---- |
| year       | Number | 年   |
| month      | Number | 月   |
| day        | Number | 日   |
| hour       | Number | 時   |
| minute     | Number | 分   |
| second     | Number | 秒   |



### 場所オブジェクト

| プロパティ | タイプ | 説明                 |
| ---------- | ------ | -------------------- |
| name       | String | 場所の名前           |
| photo      | Path   | 代表的な写真のリンク |
| latitude   | Number | 緯度                 |
| longitude  | Number | 経度                 |

