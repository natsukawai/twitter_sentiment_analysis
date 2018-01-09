from pymongo import MongoClient
from tweetCrawler import TweetCrawler


if __name__ == '__main__':
    # pythonからmongoDBにアクセス
    client = MongoClient('localhost', 27017)
    db = client.mydb

    crawler = TweetCrawler()
    tweets = crawler.fetch_tweets(u'ビットコイン', 100000)

    # ツイートから必要な情報だけを取り出してダウンロード
    # 今回は、id、本文、投稿日時、投稿者名を取得
    for tweet in tweets:
        tweet_info = {}
        tweet_info['id'] = tweet['id']
        tweet_info['text'] = tweet['text']
        tweet_info['created_at'] = tweet['created_at']
        tweet_info['user'] = {'screen_name': tweet['user']['screen_name']}

        db.bitcoin.insert(tweet_info)  # ツイート情報をMongoDBに保存
