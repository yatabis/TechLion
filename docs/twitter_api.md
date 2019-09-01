# Twitter用API

### 今日のツイートを取得する

#### HTTPリクエスト

`GET https://hacku-techlion.herokuapp.com/twitter/today/`

#### リクエストヘッダー

| プロパティ   | 値               |
| ------------ | ---------------- |
| Content-Type | application/json |



#### リクエストボディ

| プロパティ | 必須 | 説明                               | デフォルト |
| ---------- | ---- | ---------------------------------- | ---------- |
| user       | Yes  | ユーザーID（Gmailアドレスの@以前） | なし       |

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

