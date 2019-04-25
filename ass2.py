from functools import partial
from sys import maxsize as maxint
import twitter
import sys
import sys
import time
from urllib.error import URLError
from http.client import BadStatusLine
import json
import twitter
import networkx
import matplotlib.pyplot as plt

def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): 
    
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
    
        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e
    
        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes
    
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429: 
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'                  .format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
def oauth_login():
    # XXX: Go to http://twitter.com/apps/new to create an app and get values
    # for these credentials that you'll need to provide in place of these
    # empty string values that are defined as placeholders.
    # See https://developer.twitter.com/en/docs/basics/authentication/overview/oauth
    # for more information on Twitter's OAuth implementation.
    
    CONSUMER_KEY = 'mjrRU9LNLWn9JMlOHE33ONJvM'
    CONSUMER_SECRET = 'faErdgu8zIPa6VqG0JEml2ma2LTz26kxJShq5kNE4XtMLzhIyU'
    OAUTH_TOKEN = '1099296248580968448-70PY44k9pDe26DTwa6HhqI3ohRB6Hz'
    OAUTH_TOKEN_SECRET = 'I0uXDEBuehIyiBOigRRpU1ThGU3ISedu32vy9LkcODsfT'
    
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                               CONSUMER_KEY, CONSUMER_SECRET)
    
    twitter_api = twitter.Twitter(auth=auth)
    return twitter_api

def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None),     "Must have screen_name or user_id, but not both"
    
    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters
    
    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, 
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids, 
                                count=5000)

    friends_ids, followers_ids = [], []
    
    for twitter_api_func, limit, ids, label in [
                    [get_friends_ids, friends_limit, friends_ids, "friends"], 
                    [get_followers_ids, followers_limit, followers_ids, "followers"]
                ]:
        
        if limit == 0: continue
        
        cursor = -1
        while cursor != 0:
        
            # Use make_twitter_request via the partially bound callable...
            if screen_name: 
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else: # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']
        
            print('Fetched {0} total {1} ids for {2}'.format(len(ids),label, (user_id or screen_name)),file=sys.stderr)
        
            # XXX: You may want to store data during each iteration to provide an 
            # an additional layer of protection from exceptional circumstances
        
            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]
def get_user_profile(twitter_api, screen_names=None, user_ids=None):
   
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None),     "Must have screen_names or user_ids, but not both"
    
    items_to_info = {}

    items = screen_names or user_ids
    
    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See http://bit.ly/2Gcjfzr for details.
        
        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup, 
                                            screen_name=items_str)
        else: # user_ids
            response = make_twitter_request(twitter_api.users.lookup, 
                                            user_id=items_str)
    
        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else: # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info

def get_top5_popular_reciprocal_friends(twitter_api, user_name=None,user_id=None):
    
    assert (user_name != None) != (user_id != None),"Must have user_name or user_id, but not both"
    if user_name:
        friends_ids, followers_ids = get_friends_followers_ids(twitter_api,
                                                           screen_name = user_name,
                                                           friends_limit=200,
                                                           followers_limit=200)
    else:
        friends_ids, followers_ids = get_friends_followers_ids(twitter_api,
                                                           user_id=user_id,
                                                           friends_limit=200,
                                                           followers_limit=200)
    reciprocal_friends_dict = {}
    reciprocal_friends_list = list(set(friends_ids) & set(followers_ids))
    print("find %d reciprocal friends\n"%len(reciprocal_friends_list))
   
    for x in reciprocal_friends_list:
        res = get_user_profile(twitter_api, user_ids=[x])
        reciprocal_friends_dict[str(x)] = res[x]['followers_count']
        #print(str(x)+" followers_count: "+str(res[x]['followers_count']))

    # if number of reciprocal_friends < 5 return number of reciprocal_friends
    length = 0
    if len(reciprocal_friends_dict) < 5:
        length = len(reciprocal_friends_dict)
    else:
        length = 5

    # sort by followers_count
    sorted_dict = list(map(lambda x:x[0],sorted(reciprocal_friends_dict.items(),key=lambda x:x[1],reverse=True)))
    if user_id:
        print("id: ", user_id)
    if screen_name:
        print("screen_name: ", screen_name)
    print("most popular reciprocal friends:",sorted_dict[:length])
    return sorted_dict[:length]



#Crawling
twitter_api = oauth_login()
# start point
# id and screen_name
screen_name = "auntieYoudan"
user_id =   "1099296248580968448"

# friend 's id and screen_name
#user_id="3556898536"
#screen_name ="freediabeauty"

#network list
bfs_list = []
bfs_dict = {}
top5 = get_top5_popular_reciprocal_friends(twitter_api, screen_name)
bfs_dict[user_id] = top5
bfs_list.insert(0, bfs_dict)
next_queue = top5

level = 1
while level < 3:
    level += 1
    (queue, next_queue) = (next_queue, [])
    for id in queue:
        bfs_dict2 = {}
        top5 = get_top5_popular_reciprocal_friends(twitter_api, user_id = id)
        next_queue += top5
        bfs_dict2[id] = top5
        bfs_list.append(bfs_dict2)



#create graph
G =networkx.MultiGraph()
for i in bfs_list:
    for parent, child_list in i.items():
        G.add_node(parent)
        for child in child_list:
            if (G.has_edge(parent,child) == False):
                G.add_edge(parent,child)


#Printing the proper output
print ("size of the graph: ", G.size())
print ("number of nodes in the graph: ", G.number_of_nodes())
print ("number of edges in the graph: ", G.number_of_edges())
print ("diameter of the graph: ", networkx.diameter(G))
print( "average distance of the graph: ", networkx.average_shortest_path_length(G))
f = open("output","w+")
print ("size of the graph: ", G.size(),file=f)
print ("number of nodes in the graph: ", G.number_of_nodes(),file=f)
print ("number of edges in the graph: ", G.number_of_edges(),file=f)
print ("diameter of the graph: ", networkx.diameter(G),file=f)
print( "average distance of the graph: ", networkx.average_shortest_path_length(G),file=f)
f.close()
networkx.draw(G, with_labels = True)
plt.savefig("Social_network.png") # save as png
plt.show() # display
