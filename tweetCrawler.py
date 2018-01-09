# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime
import time
import sys

# set API key, token
KEYS = {'consumer_key': '**********',
        'consumer_secret': '**********',
        'access_token': '**********',
        'access_secret': '**********'}


class TweetCrawler:
    def __init__(self):
        self.session = OAuth1Session(KEYS['consumer_key'], KEYS['consumer_secret'],
                                     KEYS['access_token'], KEYS['access_secret'])

    def fetch_tweets(self, query, number_of_tweets):
        '''
        TwitterAPIを通じてツイートを取得
        ---
        query (str): 検索クエリ
        number_of_tweets (int): 取得するツイート数の上限
        '''
        # アクセス可能かチェック
        self.checkLimit()

        url = 'https://api.twitter.com/1.1/search/tweets.json'
        params = {'q': query, 'count': 100}

        cnt = 0
        unavailableCnt = 0
        while True:
            res = self.session.get(url, params=params)
            # 503エラーが出た場合はエラー内容を表示してループを続ける
            if res.status_code == 503:
                # 503 : Service Unavailable
                if unavailableCnt > 10:
                    raise Exception(
                        'Twitter API error {}'.format(res.status_code))

                unavailableCnt += 1
                print('Service Unavailable 503')
                self.waitUntilReset(time.mktime(
                    datetime.datetime.now().timetuple()) + 30)
                continue

            unavailableCnt = 0

            # APIがうまく動いているときはステータスコードが200になる
            if res.status_code != 200:
                raise Exception('Twitter API error {}'.format(res.status_code))

            # tweetの情報をリスト化
            tweets = []
            res_text = json.loads(res.text)
            for tweet in res_text['statuses']:
                tweets.append(tweet)

            # 取得するツイートがない場合はループを抜ける
            if len(tweets) == 0:
                print('length of tweet becomes zero.')
                break

            # リスト化したtweetを返すジェネレータを作成
            for tweet in tweets:
                yield tweet

                cnt += 1
                if cnt % 500 == 0:
                    print('{}tweets'.format(cnt))

                if number_of_tweets > 0 and cnt >= number_of_tweets:
                    return

            # 今回取得したツイートの最大IDを保存、次のループでこの続きから再開
            params['max_id'] = tweet['id'] - 1

            # ヘッダ確認 （回数制限）
            # X-Rate-Limit-Remaining が入ってないことが稀にあるのでチェック
            if ('X-Rate-Limit-Remaining' in res.headers and 'X-Rate-Limit-Reset' in res.headers):
                if (int(res.headers['X-Rate-Limit-Remaining']) == 0):
                    self.waitUntilReset(int(res.headers['X-Rate-Limit-Reset']))
                    self.checkLimit()
            else:
                print('not found  -  X-Rate-Limit-Remaining or X-Rate-Limit-Reset')
                self.checkLimit()

    def checkLimit(self):
        unavailableCnt = 0
        while True:
            url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
            res = self.session.get(url)

            if res.status_code == 503:
                # 503 : Service Unavailable
                if unavailableCnt > 10:
                    raise Exception('Twitter API error %d' % res.status_code)

                unavailableCnt += 1
                print('Service Unavailable 503')
                self.waitUntilReset(time.mktime(
                    datetime.datetime.now().timetuple()) + 30)
                continue

            unavailableCnt = 0

            if res.status_code != 200:
                raise Exception('Twitter API error %d' % res.status_code)

            # 待つ必要があればwaitUntilReset()を呼び出す
            remaining, reset = self.getLimitContext(json.loads(res.text))
            if (remaining == 0):
                self.waitUntilReset(reset)
            else:
                break

    def waitUntilReset(self, reset):
        seconds = reset - time.mktime(datetime.datetime.now().timetuple())
        seconds = max(seconds, 0)
        print('== waiting {} sec =='.format(seconds))
        sys.stdout.flush()
        time.sleep(seconds + 10)  # 念のため + 10 秒

    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['search']['/search/tweets']['remaining']
        reset = res_text['resources']['search']['/search/tweets']['reset']

        return int(remaining), int(reset)
