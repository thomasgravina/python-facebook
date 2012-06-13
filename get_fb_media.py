#!/usr/bin/python2.6
from __future__ import division
from threading import Thread
import math
import os
import json
import urllib2
import urllib
import urlparse
import BaseHTTPServer
import webbrowser
import Queue
import time
import array

APP_ID = ''
APP_SECRET = ''
ENDPOINT = 'graph.facebook.com'
REDIRECT_URI = 'http://127.0.0.1:9999/'
ACCESS_TOKEN = None
LOCAL_FILE = '.fb_access_token'
URL_FB_FRIENDS_MEDIA = '/fql?q=SELECT uid, name, movies, music FROM user where uid IN (SELECT uid1 FROM friend WHERE uid2=me() LIMIT 5000) ORDER BY name LIMIT 5000'

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
print CURRENT_DIRECTORY
PHOTOS_DIRECTORY = os.path.join(CURRENT_DIRECTORY, 'pictures')
url_queue = Queue.Queue()
start = 0

def get_url(path, args=None):
    args = args or {}
    if ACCESS_TOKEN:
        args['access_token'] = ACCESS_TOKEN
    if 'access_token' in args or 'client_secret' in args:
        endpoint = "https://"+ENDPOINT
    else:
        endpoint = "http://"+ENDPOINT
    print endpoint+urllib.quote(path, '?/=()')+'&'+urllib.urlencode(args)
    return endpoint+urllib.quote(path, '?/=()')+'&'+urllib.urlencode(args)

def get(path, args=None):
    return urllib2.urlopen(get_url(path, args)).read()

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        global ACCESS_TOKEN
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        code = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('code')
        code = code[0] if code else None
        if code is None:
            self.wfile.write("Sorry, authentication failed.")
            sys.exit(1)
        response = get('/oauth/access_token', {'client_id':APP_ID,
                                               'redirect_uri':REDIRECT_URI,
                                               'client_secret':APP_SECRET,
                                               'code':code})
        ACCESS_TOKEN = urlparse.parse_qs(response)['access_token'][0]
        open(LOCAL_FILE,'w').write(ACCESS_TOKEN)
        self.wfile.write("You have successfully logged in to facebook. "
                         "You can close this window now.")

if __name__ == '__main__':
    if not os.path.exists(LOCAL_FILE):
        print "Logging you in to facebook..."
        webbrowser.open(get_url('/oauth/authorize',
                                {'client_id':APP_ID,
                                 'redirect_uri':REDIRECT_URI,
                                 'scope':'user_likes, friends_likes'}))

        httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', 9999), RequestHandler)
        while ACCESS_TOKEN is None:
            httpd.handle_request()
    else:
        ACCESS_TOKEN = open(LOCAL_FILE).read()

    musics = []
    movies = []
    media = json.loads(get(URL_FB_FRIENDS_MEDIA))['data']

    for med in media:

        for movie in med['movies'].split(', '):
            movies.append(movie.encode('utf-8'))
        
        for music in med['music'].split(', '):
            musics.append(music.encode('utf-8'))

    for music in musics:
        print music

    for movie in movies:
        print movie