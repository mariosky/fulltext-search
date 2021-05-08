from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from flaskr.title_search import get_title_content
from werkzeug.security import generate_password_hash, check_password_hash
from redisearch import Client, Query, TextField, IndexDefinition
import redis
import json
import time
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

password = None
if 'API_USER_PASSWORD' not in os.environ or  not os.environ['API_USER_PASSWORD']:
    password = 'masterkey'
else:
    password = os.environ['API_USER_PASSWORD']

users = {
    "user": generate_password_hash(password),
}

r = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=6380, db=0)

redis_ready = False
while not redis_ready:
    try:
        redis_ready = r.ping()
    except:
        print("waiting for redis")
        time.sleep(3)
print("redis alive")

client = Client("myIdx", conn=r)


def get_parameters():
    request_data = request.get_json()

    url = request_data['url']
    title = request_data['title']
    body = request_data['body']

    return url, title, body



@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route('/')
@auth.login_required
def index():
    definition = IndexDefinition(prefix=['url:'])
    client.create_index((TextField("title", weight=5.0), TextField("body")), definition=definition)

    return "Hello, {} Index Created".format(auth.current_user())


@app.route('/add-document', methods=['POST'])
@auth.login_required
def add_document():
    url, title, body = get_parameters()
    client.redis.hset(
        'url:'+url,
        mapping={
            'title': title,
            'body': body,
        })

    return '''
               The title  is: {}
               The body value is: {}'''.format(title, body)


@app.route('/add-md-document', methods=['POST'])
@auth.login_required
def add_documents():
    url, title, body = get_parameters()

    content = get_title_content(body)
    for key in content:
        client.redis.hset(
            'url:'+url+key,
            mapping={
                'title': title,
                'body': " ".join(content[key]),
            })

    return '''
               The title  is: {}
               The body value is: {}'''.format(title, body)


@app.route('/query', methods=['GET'])
@auth.login_required
def query_redis():
    request_data = request.get_json()

    query = request_data['query']

    q = Query(query).with_scores()
    res = client.search(q)

    # Process documents
    result = {'documents': [{'url': doc.id, 'body': doc.body[:128], 'title':doc.title} for doc in res.docs],
              'total': res.total,
              'duration': res.duration}

    return json.dumps(result)




if __name__ == '__main__':
    app.run(host='0.0.0.0')
