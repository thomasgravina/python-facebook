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

APP_ID = ''
APP_SECRET = ''
ENDPOINT = 'graph.facebook.com'
REDIRECT_URI = 'http://127.0.0.1:8080/'
ACCESS_TOKEN = None
LOCAL_FILE = '.fb_access_token'
URL_MY_PICTURES = '/fql?q=SELECT src_big FROM photo WHERE aid IN (SELECT aid FROM album WHERE owner = me()) LIMIT 5000'
URL_FRIENDS_PICTURES = '/fql?q=SELECT src_big FROM photo WHERE aid IN (SELECT aid FROM album WHERE owner IN (SELECT uid2 FROM friend WHERE uid1 = me())) LIMIT 5000'
URL_MY_FRIENDS = '/fql?q=SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) ORDER BY name LIMIT 5000'

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

# Download pictures from queue until this last one is empty.
def download_pictures():
    while (url_queue.empty() == False):
        user = url_queue.get().split('~')[0]
        source = url_queue.get().split('~')[1]
        filename = source.split('/')[len(source.split('/')) - 1]
        dest = os.path.join(PHOTOS_DIRECTORY, user, filename)
        urllib.urlretrieve(source, dest)
        print "# remaining pictures:", url_queue.qsize()

if __name__ == '__main__':
    if not os.path.exists(LOCAL_FILE):
        print "Logging you in to facebook..."
        webbrowser.open(get_url('/oauth/authorize',
                                {'client_id':APP_ID,
                                 'redirect_uri':REDIRECT_URI,
                                 'scope':'user_photos, friends_photos'}))

        httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', 8080), RequestHandler)
        while ACCESS_TOKEN is None:
            httpd.handle_request()
    else:
        ACCESS_TOKEN = open(LOCAL_FILE).read()

    # Check if the pictures directory exists, otherwise we create it
    if not os.path.exists(PHOTOS_DIRECTORY): os.mkdir(PHOTOS_DIRECTORY)

    # Get my pictures URL
    '''
    pictures = json.loads(get(URL_MY_PICTURES))['data']
    print "You have", len(pictures), "pictures."
    i = 0
    # Put them in a queue
    for picture in pictures:
        source = picture['src_big']
        url_queue.put(source)
        i = i + 1
        print math.floor(i * 100 / len(pictures)), '%'

    # Download pictures from URL in queue with 3 threads.
    start = time.time()
    print url_queue.empty()
    t1 = Thread(target=download_pictures)
    t2 = Thread(target=download_pictures)
    t3 = Thread(target=download_pictures)
    t1.start()
    t2.start()
    t3.start()'''

    # Get friends ID
    friends = json.loads(get(URL_MY_FRIENDS))['data']
    print len(friends), "friends."

    # For each friend, get all of their pictures
    for friend in friends:
        if not os.path.exists(os.path.join(PHOTOS_DIRECTORY, friend['name'])) : os.mkdir(os.path.join(PHOTOS_DIRECTORY, friend['name']))
        pictures = json.loads(get('/fql?q=SELECT src_big FROM photo WHERE aid IN (SELECT aid FROM album WHERE owner = '+str(friend['uid'])+')'))['data']
        for picture in pictures:
            url_queue.put(friend['name'] + '~' + picture['src_big'])
    print url_queue.qsize(), "pictures."
    
    # Launch 50 threads to download the pictures
    i = 0
    while i < 50:
        Thread(target=download_pictures).start()
        i = i + 1