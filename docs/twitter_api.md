# Twitter用API

### 今日のツイートを取得する

#### HTTPリクエスト

`GET https://hacku-techlion.herokuapp.com/twitter/today/{twitter_id}`

#### リクエストヘッダー

| プロパティ    | 値            |
| ------------- | ------------- |
| Authorization | Basic {token} |



#### パスパラメータ

| プロパティ | 必須 | 説明                                  | デフォルト |
| ---------- | ---- | ------------------------------------- | ---------- |
| twitter_id | Yes  | ツイッターのID（@以下のものではない） | なし       |

#### クエリパラメータ

なし

#### レスポンス

ツイートオブジェクトの配列を返します。



### ツイートオブジェクト

| プロパティ | タイプ        | 説明                |
| ---------- | ------------- | ------------------- |
| id         | Number        | ツイートID          |
| text       | String        | ツイート内容        |
| hashtags   | Array[String] | ハッシュタグの配列  |
| media      | Array[String] | メディアのURLの配列 |
| url        | Path          | 元ツイートのURL     |
| created_at | Object        | 日時オブジェクト    |



### 日時オブジェクト

| プロパティ | タイプ | 説明 |
| ---------- | ------ | ---- |
| year       | Number | 年   |
| month      | Number | 月   |
| day        | Number | 日   |
| hour       | Number | 時   |
| minute     | Number | 分   |
| second     | Number | 秒   |

