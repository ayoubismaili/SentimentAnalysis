#!/usr/bin/env python3
# encoding: utf-8

"""A class that allows fetching tweets from Twitter"""

# MIT License
# 
# Copyright (c) 2020 Ayoub Ismaili <ayoubismaili1@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import urllib.parse
import urllib.request
import json
import os
import time

class TweetCollector:
    
    def __init__(self):
        self.renew_session()
    
    def renew_session(self):
        self.url_format = 'https://api.twitter.com/2/timeline/conversation/{}.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&count=20&ext=mediaStats%2ChighlightedLabel'
        
        self.headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
              'Accept' : '*/*',
              'Accept-Language' : 'en-US,en;q=0.5',
              'authorization' : 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
              'x-guest-token' : None,
              'x-twitter-client-language' : 'en',
              'x-twitter-active-user' : 'yes',
              'x-csrf-token' : None,
              'Origin' : 'https://twitter.com',
              'Connection' : 'keep-alive',
              'Cookie' : None,
              'TE' : 'Trailers'}
        
        csrf_token = self.get_csrf_token()
        cookies = self.get_cookies()
        cookies.update({'ct0': csrf_token})
        self.headers['x-guest-token'] = cookies['gt']
        self.headers['x-csrf-token'] = csrf_token
        self.headers['Cookie'] = '; '.join(['{}={}'.format(k, v) for k, v in cookies.items()])
    
    def get_csrf_token(self):
        prefix = b'CODEX'
        remainder = 32//2 - len(prefix)
        rem_bytes = os.urandom(remainder)
        return (prefix + rem_bytes).hex()
    
    """ We implemented hacky way to get the multiple Set-Cookie headers """
    def get_cookies(self):
        url = 'https://twitter.com'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            headers = response.info()
            headers = str(headers).split('\n')
            cookies = {}
            for h in headers:
                if h.startswith('set-cookie:'):
                    cookie = h.replace('set-cookie:', '').strip().split(';')[0]
                    eq_idx = cookie.index('=')
                    cookie_key = cookie[:eq_idx]
                    cookie_value = cookie[eq_idx+1:]
                    cookies.update({cookie_key: cookie_value})
        return cookies
    
    def get_tweet(self, id):
        req = urllib.request.Request(self.url_format.format(id), headers=self.headers)
        with urllib.request.urlopen(req) as response:
            data = response.read()
            data = json.loads(data)
            data = data['globalObjects']['tweets']
            key = None
            # A Tweet maybe a retweet, in that case the tweet may have multiple IDs related to it.
            # We get the first ID regardless of the tweet kind.
            for k in data:
                key = k
                break
            data = data[key]['full_text']
        return data
    
    def get_tweet_list(self, id_list):
        for id in id_list:
            while True:
                try:
                    tweet = self.get_tweet(id)
                    break
                except urllib.error.HTTPError as ex:
                    if ex.code == 429:
                        # If we get 429 (Too Many Requests) renew session
                        time.sleep(5)
                        self.renew_session()
                    else:
                        tweet = None
                        break
                except:
                    time.sleep(1)
                    tweet = None
                    break
            yield tweet
    
