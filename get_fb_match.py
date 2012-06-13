#!/usr/bin/python2.6
from __future__ import division
from threading import Thread
from user import User
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
URL_FB_FRIENDS_MEDIA = '/fql?q=SELECT uid, name, movies, music, meeting_sex, sex FROM user WHERE uid IN (SELECT uid1 FROM friend WHERE uid2=me() LIMIT 5000) ORDER BY name LIMIT 5000'
URL_FB_ME_MEDIA = '/fql?q=SELECT uid, name, movies, music, sex, meeting_sex FROM user WHERE uid = me()'

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

if __name__ == '__main__':
    if not os.path.exists(LOCAL_FILE):
        print "Logging you in to facebook..."
        webbrowser.open(get_url('/oauth/authorize',
                                {'client_id':APP_ID,
                                 'redirect_uri':REDIRECT_URI,
                                 'scope':'user_likes, friends_likes, user_relationship_details, friends_relationship_details'}))

        httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', 9999), RequestHandler)
        while ACCESS_TOKEN is None:
            httpd.handle_request()
    else:
        ACCESS_TOKEN = open(LOCAL_FILE).read()

    # get my facebook info
    media = json.loads(get(URL_FB_ME_MEDIA))['data'][0]
    print "You're a", media['sex'], "looking for", media['meeting_sex']
    me = User(media['uid'], media['name'], media['sex'], media['meeting_sex'])
    for movie in media['movies'].split(', '):
        me.add_movie(movie.encode('utf-8'))
    for music in media['music'].split(', '):
        me.add_music(music.encode('utf-8'))

    # get my friends facebook info
    media = json.loads(get(URL_FB_FRIENDS_MEDIA))['data']
    for med in media:
        user = User(med['uid'], med['name'].encode("utf-8"), med['sex'], med['meeting_sex'])
        user.set_movies(med['movies'].encode("utf-8").split(', '))
        user.set_musics(med['music'].encode("utf-8").split(', '))
        User.users.append(user)

    #computes score
    acceptable_sex = [me.get_sex(), None, []]
    for user in User.users:
        if (acceptable_sex.count(user.get_meeting_sex()) > 0) and \
            me.get_meeting_sex().count(user.get_sex()) > 0:
                for movie in me.get_movies():
                    if user.get_movies().count(movie) > 0:
                        user.increment_score()
                for music in me.get_musics():
                    if user.get_musics().count(music) > 0:
                        user.increment_score()
    
    # displays result
    for user in User.users:
        if user.get_score() > 0:
            print user.get_uid(), user.get_name(), user.get_score()
