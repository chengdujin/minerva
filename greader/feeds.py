#!/usr/bin/python
# -*- coding: utf-8 -*-

##
# this script serves to fetch all of a provider's feeds (a limit 
# for the historical feeds would be 5000). and then the feeds are
# stored in mongodb
#
# @author Yuan JIN
# @contact chengudjin@gmail.com
# @since 2012.03.03
# @latest 2012.09.04

#relaod the script encoding
import sys
reload(sys)
sys.setdefaultencoding('UTF-8')

# CONSTANTS
DB = '107.22.242.25:27017'
SOURCE_URL = "http://www.google.com/trends/hottrends/atom/hourly"
SOURCE_NAME = 'hott rends'.strip().lower().replace(' ', '_')
GOOGLE_REQUEST_URL = 'http://www.google.com/reader/atom/feed/%s?n=%i%s'

# Google OAuth
SCOPE = "http://www.google.com/reader/api http://www.google.com/reader/atom"
REQUEST_OAUTH_TOKEN_URL = "https://www.google.com/accounts/OAuthGetRequestToken?scope=%s" % SCOPE
AUTHORIZE_URL = "https://www.google.com/accounts/OAuthAuthorizeToken"
ACCESS_TOKEN_URL = "https://www.google.com/accounts/OAuthGetAccessToken"

CLIENT_ID = "149442296180.apps.googleusercontent.com"
CLIENT_SECRET = "w9M59S7pdsRUoZLCrMuy1hG8"


def store_feeds(feeds, collection):
    'store the feeds in mongodb '
    from pymongo.errors import CollectionInvalid
    from pymongo.collection import Collection
    from pymongo.connection import Connection
    con = Connection(DB)
    from pymongo.database import Database
    db = Database(con, 'queries')

    col = None
    try:
        col = db.create_collection(collection)
    except CollectionInvalid as e:
        col = Collection(db, collection)

    for feed in feeds:
        existed = col.find_one({'query':feed}, {'$exists':'true'})
        if not existed:
            col.save({'query':feed})

def parse_feeds(data):
    'parse out necessary information'
    feeds = []

    import HTMLParser
    html_decoder = HTMLParser.HTMLParser()
    decoded_data = html_decoder.unescape(data)
    #f = open('/home/ec2-user/hottrends/test', 'w')
    #f.write(str(decoded_data))
    #f.close()
    
    import re
    from BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(decoded_data)

    page_code = '&c=%s' % soup.find('gr:continuation').text

    hot_query_links = soup.findAll(href=re.compile("http://www.google.com/trends/hottrends#a=*"))
    print 'total:', len(hot_query_links)
    for q in hot_query_links:
        feeds.append(q.text)

    return page_code, set(feeds)
    
def create_oauth_client():
    'authorize with google reader - get the access token'
    import oauth2
    consumer = oauth2.Consumer(CLIENT_ID, CLIENT_SECRET)

    import os.path
    if not (os.path.exists('access_token') and os.path.exists('access_token_secret')):
        client = oauth2.Client(consumer)
        
        # request oauth token
        response, content = client.request(REQUEST_OAUTH_TOKEN_URL, 'GET')
        import urlparse
        request_token = dict(urlparse.parse_qsl(content))
    
        # authorization
        print "Open this link in a browser..:"
        print "%s?oauth_token=%s" % (AUTHORIZE_URL, request_token['oauth_token'])
        print
        print "Press ENTER when ready.."
        raw_input()
        
        # get access token
        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        client = oauth2.Client(consumer, token)
        
        response, content = client.request(ACCESS_TOKEN_URL, 'GET')
        access_token = dict(urlparse.parse_qsl(content))
        
        # record the token
        f = open ('access_token', 'w')
        f.write (access_token['oauth_token'])
        f.close ()
        oauth_token = access_token['oauth_token']
            
        f = open ('access_token_secret', 'w')
        f.write (access_token['oauth_token_secret'])
        f.close ()
        oauth_token_secret = access_token['oauth_token_secret']
    else:
        # read in the token and secret from local disk
        f = open('access_token', 'r')
        oauth_token = f.read()
        f.close()
            
        f = open ('access_token_secret', 'r')
        oauth_token_secret = f.read()
        f.close()
    
    token = oauth2.Token(oauth_token, oauth_token_secret)
    client = oauth2.Client(consumer, token)
    return client
    
def retrieve_data(url, limit, page_code):
    'read from google reader service'
    # request access token or find it locally
    client = create_oauth_client()

    # unlimited access to a provider's historical feeds
    # courtesy of google
    url = GOOGLE_REQUEST_URL % (url, limit, page_code)
    print url

    response, feeds = client.request(url, 'GET')
    
    return feeds

def main():
    'entrance to feeds retrieval and storing'
    LIMIT = 3000
    PAGE_CODE = ''

    while LIMIT > 0:
        data = retrieve_data(SOURCE_URL, LIMIT, PAGE_CODE)
        LIMIT = LIMIT - 1000

        PAGE_CODE, feeds = parse_feeds(data)
        print PAGE_CODE
        store_feeds(feeds, SOURCE_NAME)

if __name__ == '__main__':
    main()
