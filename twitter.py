import os, sys, re, yaml, json, argparse
import tweepy
import time
import socket
import http.client

from datetime import datetime
from hanziconv import HanziConv

from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener


# Number of seconds to wait after an exception before restarting the stream.
tcpip_delay = 0.25
MAX_TCPIP_TIMEOUT = 16


class QueueListener(StreamListener):

    def __init__(self, args):
        """Creates a new stream listener with an internal queue for tweets."""
        super(QueueListener, self).__init__()
        self.num_handled = 0
        self.queue = [] #Queue.Queue()
        self.batch_size = 100
        self.lang = args.lang

        # tweepy
        cfg = yaml.load(open('config.yml', 'rt'))['twitter']
        self.auth = OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
        self.auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
        self.api = tweepy.API(self.auth)

        # corpus file
        if not os.path.exists('corpus'): os.makedirs('corpus')
        self.dumpfile = "corpus/%s_%s.txt" % (self.lang, datetime.now().strftime("%Y%m%d_%H%M%S"))
        

    def on_data(self, data):
        """Routes the raw stream data to the appropriate method."""
        raw = json.loads(data)
        if 'in_reply_to_status_id' in raw:
            if self.on_status(raw) is False:
                return False
        elif 'limit' in raw:
            if self.on_limit(raw['limit']['track']) is False:
                return False
        return True

    def on_status(self, raw):
        if isinstance(raw.get('in_reply_to_status_id'), int):
            print("(%s)%s / %i" % (raw['in_reply_to_status_id'], raw['text'], len(self.queue)))
            line = (raw.get('in_reply_to_status_id'), raw.get("text"))
            self.queue.append(line)
            if len(self.queue) >= self.batch_size: self.dump()
        return True

    def on_error(self, status):
        print('ON ERROR:', status)

    def on_limit(self, track):
        print('ON LIMIT:', track)

    def dump(self):
        pcnt = 0
        with open(self.dumpfile, 'a') as fdump:
            (sids, texts), self.queue = zip(*self.queue), []
            while True:
                try:
                    lines_mapper = {s.id_str: s.text for s in self.api.statuses_lookup(sids)}
                    break
                except Exception as e:
                    print("[Error]", e)
                    time.sleep(10)
            lines_grps = [[lines_mapper.get(str(sid)), txt] for sid, txt in zip(sids, texts) if lines_mapper.get(str(sid))]
            lines_grps = [[self.preprocess(s) for s in lines] for lines in lines_grps]
            
            for lines in lines_grps:
                for i in range(len(lines)-1):
                    fdump.write("%s\n%s\n" % (lines[i], lines[i+1]))
                    pcnt += 1
        self.num_handled += pcnt


    is_zh = re.compile(r'([\p{IsHan}]+)', re.UNICODE)
    def preprocess(self, line, cond=None):
        line = HanziConv.toTraditional(line)
        # line = re.sub(r"\@[a-z0-9][a-z0-9]*", '', line)
        # line = re.sub(r"\#[a-z0-9][a-z0-9]*", '', line)
        # line = re.split(r"\([a-z][a-z]\)", line.lower())[0]
        if cond == 'only_zh':
            words = [w for w in jieba.cut(line) if is_zh.search(w)]
            line = ' '.join(words)
        line = re.sub("\s+", ' ', line).strip().lower()
        return line


def main():
    # parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', type=str, required=True, help='language: en/zh/ja')
    args = parser.parse_args()

    # open stream
    listener = QueueListener(args)
    stream = Stream(listener.auth, listener) #, language='zh')

    # [stream filter]
    if args.lang == 'en':
        stream.filter(locations=[-122.75,36.8,-121.75,37.8, -74,40,-73,41])  # San Francisco or New York City
    elif args.lang == 'zh':
        stream.filter(languages=["zh"], track=['I', 'you', 'http', 'www', 'co', '@', '#', '。', '，', '！', '.', '!', ',', ':', '：', '』', ')', '...', '我', '你', '他', '哈', '的', '是', '人', '-', '/'])
    elif args.lang == 'ja':
        stream.filter(languages=["ja"], track=['I', 'you', 'http', 'www', 'co', '@', '#', '。', '，', '！', '.', '!', ',', ':', '：', '』', ')', '...'])
    # stream.filter(locations=[-122.75,36.8,-121.75,37.8])  # San Francisco
    # stream.filter(locations=[-74,40,-73,41])  # New York City
    # stream.filter(languages=["en"], track=['python', 'obama', 'trump'])
    # 
    # stream.filter(languages=["zh"], locations=[-180,-90,180,90])
    # stream.filter(languages=["ja"], track=['バイト'])

    try:
        while True:
            try:
                stream.sample()  # blocking!
            except KeyboardInterrupt:
                print('KEYBOARD INTERRUPT')
                return
            except (socket.error, http.client.HTTPException):
                global tcpip_delay
                print('TCP/IP Error: Restarting after %.2f seconds.' % tcpip_delay)
                time.sleep(min(tcpip_delay, MAX_TCPIP_TIMEOUT))
                tcpip_delay += 0.25
    finally:
        stream.disconnect()
        print('Exit successful, corpus dumped in %s' % (listener.dumpfile))


if __name__ == '__main__':
    sys.exit(main())
