# -*- coding: utf-8 -*-
import MeCab
from pymongo import MongoClient
from collections import defaultdict


def morphological_analysis(sentence):
    '''
    MeCabを用いて形態素解析を行う
    ----------
    sentence (str): TwitterAPIから取得したツイートの本文
    '''
    mc = MeCab.Tagger('-Ochasen')
    sentence = sentence.replace('\n', ' ')
    node = mc.parseToNode(sentence)
    node = mc.parseToNode(sentence)
    result_dict = defaultdict(list)
    for i in range(140):  # ツイートなのでMAX140文字
        if node.surface != "":  # ヘッダとフッタを除外
            word_type = node.feature.split(",")[0]  # 0番目に品詞情報
            if word_type in ["形容詞", "動詞", "名詞", "副詞"]:
                plain_word = node.feature.split(",")[6]  # 6番目に単語
                if plain_word != "*":
                    result_dict[word_type].append(plain_word)
        node = node.next
        if node is None:
            break

    return result_dict


def get_list_from_dict(result, key):
    '''
    辞書型配列を入力してリストを返す
    ---
    result (dict): morphological_analysis()の出力で、各品詞をキーとした辞書
    key (str): 名詞、動詞などの品詞
    '''
    if key in result.keys():
        result_list = result[key]
    else:
        result_list = []
    return result_list


def get_setntiment(word_list):
    '''
    与えられた文章（単語リスト）に対する感情値を返す
    (-1:ネガティブ、1:ポジティブ)
    ---
    word_list (list): 各要素が単語から構成されたリスト
    '''
    val = 0
    score = 0
    word_count = 0
    val_list = []
    for word in word_list:
        val = pn_dict[word] if word in pn_dict else None
        val_list.append(val)
        if val is not None and val != 0:  # 見つかればスコアを足し合わせて単語カウントする
            score += val
            word_count += 1

    # 各単語のポジネガ値の総和を取り、文を構成する単語数で割ってその文章全体のポジネガを算出
    return score / float(word_count) if word_count != 0. else 0.


if __name__ == '__main__':
    connect = MongoClient('localhost', 27017)
    word_db = connect.word_info
    db = connect.mydb
    posi_nega_dict = word_db.posi_nega_dict
    bitcoin_tweet = db.bitcoin_ja.find()

    # 単語のポジ・ネガ辞書のmongoDBへのインポート

    # 日本語評価極性辞書（用言編）ver.1.0（2008年12月版）をmongodbへインポート
    # ポジの用語は 1 ,ネガの用語は -1 と数値化する
    with open("../japanese_sentiment_dictionary/wago.121808.pn",
              'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.split('\t')
            line[1] = line[1].replace(" ", "").replace('\n', '')
            value = 1 if line[0].split('（')[0] == "ポジ" else -1
            posi_nega_dict.insert({"word": line[1], "value": value})

    # 日本語評価極性辞書（名詞編）ver.1.0（2008年12月版）をmongodbへインポート
    # pの用語は 1 eの用語は 0 ,nの用語は -1 と数値化する
    with open("../japanese_sentiment_dictionary/pn.csv.m3.120408.trim",
              'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.split('\t')

            if line[1] == "p":
                value = 1
            elif line[1] == "e":
                value = 0
            elif line[1] == "n":
                value = -1

            posi_nega_dict.insert({"word": line[0], "value": value})

    # 感情度の設定
    pn_dict = {tweet['word']: tweet['value']
               for tweet in posi_nega_dict.find({}, {'word': 1, 'value': 1})}

    for tweet in bitcoin_tweet:
        result = morphological_analysis(tweet['text'])
        noun_list = get_list_from_dict(result, u'名詞')
        verb_list = get_list_from_dict(result, u'動詞')
        adjective_list = get_list_from_dict(result, u'形容詞')
        adverb_list = get_list_from_dict(result, u'副詞')

        # 元の情報に加えて、各品詞のリストを追加
        item = {'id': tweet['id'], 'user': tweet['user']['screen_name'],
                'text': tweet['text'], 'created_at': tweet['created_at'],
                'verb': verb_list, 'adjective': adjective_list,
                'noun': noun_list, 'adverb': adverb_list}

        # 感情スコアと感情の分類を追加
        word_list = [word for k in result.keys() for word in result[k]]
        item['sentiment_score'] = get_setntiment(word_list)
        if item['sentiment_score'] > 0:
            item['sentiment'] = 'positive'
        elif item['sentiment_score'] == 0:
            item['sentiment'] = 'even'
        elif item['sentiment_score'] < 0:
            item['sentiment'] = 'negative'

        db.bitcoin_sentiment.insert(tweet)
