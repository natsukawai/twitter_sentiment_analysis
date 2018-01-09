# Twitter_Sentiment_Analysis

# Requirement
Japanese Sentiment Dictionary (Volume of Verbs and Adjectives) ver. 1.0  
Japanese Sentiment Dictionary (Volume of Nouns) ver. 1.0  
(http://www.cl.ecei.tohoku.ac.jp/index.php?Open%20Resources%2FJapanese%20Sentiment%20Polarity%20Dictionary)

# Usage
1. Make a directory `Japanese Sentiment Dictionary` that containing two japansese on the same directory as the scripts.

2. Open `download_tweets.py` and rewrite `query` (line 11) and database name (line 23).  
You can use any name XXX in db.XXX.insert(tweet_info).

3. Run `download_tweet.py` like `python3 download_tweet.py`
