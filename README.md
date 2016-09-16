# Twitter Scraper


Scraping twitter content from [twitter streaming API](https://dev.twitter.com/streaming/overview), in python3.


## How it works

### Setup

1. Copy the `config.yml.default` to `config.yml`, and fill your twitter application tokens you got from [twitter developers](https://apps.twitter.com/).


2. just type    `python3 twitter.py`, the listener will start to dump corpus in: `corpus/<YYYYMMDD_HHMMSS.txt>`
    
### Output

I build this corpus for training the neural network model [**ChatBot**](https://github.com/Marsan-Ma/tf_chatbot_seq2seq_antilm), thus the corpus is arranged as consecutive dialog where even sentences are the response of odd sentences, like:


Line number | Sentences
------------|---------
1 | happy birthday!
2 | thank you :)
3 | game of throne is the best drama i've seen.
4 | I'll say the walking dead is even better.

Where (1,2), (3,4) are two independent dialog pairs.


## Content Filters

Twitter streaming API supports [some filter](https://dev.twitter.com/streaming/overview/request-parameters), and the most useful  ones are:

### Location filter
simply place the logitude and altitude in [South,West,North,East] format, for example:

Place | filter
------|-------------
San Francisco | [-122.75,36.8,-121.75,37.8])  
New York City | [-74,40,-73,41]
San Francisco or New York City | [-122.75,36.8,-121.75,37.8, -74,40,-73,41]


### Language filter

there are threads questioning about `language` filter is not work, actually is does, it just need to accompanied with `track` filter, like:


This won't work.  
`stream.filter(languages=["en"])`   

This works.
`stream.filter(languages=["en"], track=['machine', 'learning'])` 


### If you want language other than English

Twitter can't tokenize some languages like Japanese or Chinese correctly, your `track` parameter won't work for these languages. For example, you might setup:

`stream.filter(languages=["ja"], track=['バイト'])`

While you expect you will get a lot of tweets about **バイト**, but you simply can't get it, because twitter can't tokenize Japenses and Chinese correctly.

If you just want some corpus, regardless of the topics, here are the **work around**: use some generic English keywords instead, like:

`stream.filter(languages=["zh"], track=['I', 'you', 'http', 'www', '@', '。', '，', '！', '』', ')', '...', '-', '/'])`

According to document, you could add up to 400 keywords on this list, even some emoji also works.


