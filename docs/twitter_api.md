# Twitter API

### 今日のツイートを取得する

#### HTTPリクエスト

`GET https://hacku-techlion.herokuapp.com/twitter/today/`

#### クエリパラメーター

| プロパティ | 必須 | 説明                                   |
| ---------- | ---- | -------------------------------------- |
| q          | No   | 指定した語句を含むツイートのみ取得する |

#### レスポンス

ツイートオブジェクトの配列を返します。



### 今日のツイートを構造化して取得する

#### HTTPリクエスト

`GET https://hacku-techlion.herokuapp.com/twitter/today/detail`

#### レスポンス

| プロパティ | タイプ | 説明                                         |
| ---------- | ------ | -------------------------------------------- |
| event      | Object | イベント中のツイートのツイートオブジェクト   |
| morning    | Object | 朝の挨拶を含むツイートのツイートオブジェクト |
| night      | Object | 夜の挨拶を含むツイートのツイートオブジェクト |
| breakfast  | Object | 朝ごはんを含むツイートのツイートオブジェクト |
| lunch      | Object | 昼ごはんを含むツイートのツイートオブジェクト |
| dinner     | Object | 晩ごはんを含むツイートのツイートオブジェクト |
| other      | Object | その他のツイートのツイートオブジェクト       |



### ツイートオブジェクト

| プロパティ | タイプ        | 説明                           |
| ---------- | ------------- | ------------------------------ |
| id         | Number        | ツイートID                     |
| text       | String        | ツイート内容                   |
| hashtags   | Array[String] | ハッシュタグの配列             |
| media      | Array[String] | メディアのURLの配列            |
| url        | Path          | 元ツイートのURL                |
| created_at | Object        | 投稿日時を表す日時オブジェクト |



### 日時オブジェクト

| プロパティ | タイプ | 説明 |
| ---------- | ------ | ---- |
| year       | Number | 年   |
| month      | Number | 月   |
| day        | Number | 日   |
| hour       | Number | 時   |
| minute     | Number | 分   |
| second     | Number | 秒   |

