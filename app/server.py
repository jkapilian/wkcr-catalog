import os
from dotenv import load_dotenv
from flask import Flask
from flask import render_template
from flask import request
import time
import copy
import requests
import json
import typesense
import math

application = Flask(__name__)

load_dotenv()
TOKEN = os.environ.get('DISCOGS_API_KEY')


# give Typesense time to boot
time.sleep(3)
client = typesense.Client({
   'api_key': 'xyz',
   'nodes': [{
      'host': 'typesense',
      'port': '8100',
      'protocol': 'http'
   }],
   'connectionTimeoutSeconds': 2
})

last_rate = 0

def requestWrapper(url):
   global last_rate
   cur_time = time.time()
   if (cur_time - last_rate) > 60:
      resp = requests.get(url)
      if resp.headers['X-Discogs-Ratelimit-Remaining'] == '0':
         last_rate = cur_time
         print(f'Sleeping for {last_rate + 60 - cur_time}')
         print(f'Indexed {client.collections["collection"].retrieve()["num_documents"]} releases')
         time.sleep(last_rate + 60 - cur_time)
         return requestWrapper(url)
      elif resp.headers['X-Discogs-Ratelimit-Remaining'] == '1':
         last_rate = cur_time
      return resp.json()
   else:
      print(f'Sleeping for {last_rate + 60 - cur_time}')
      print(f'Indexed {client.collections["collection"].retrieve()["num_documents"]} releases')
      time.sleep(last_rate + 60 - cur_time)
      return requestWrapper(url)

def for_view(id):
   global db
   global client
   item = client.collections["collection"].documents[id].retrieve()
   artists = []
   for artist in item["artists"]:
      artists.append(json.loads(artist))
   item["artists"] = artists
   labels = []
   for label in item["labels"]:
      labels.append(json.loads(label))
   item["labels"] = labels
   credits = []
   for credit in item["credits"]:
      credits.append(json.loads(credit))
   item["credits"] = credits
   tracklist = []
   for track in item["tracklist"]:
      tracklist.append(json.loads(track))
   item["tracklist"] = tracklist
   identifiers = []
   for identifier in item["identifiers"]:
      identifiers.append(json.loads(identifier))
   item["identifiers"] = identifiers
   return item

def unflatten(results):
   ret = []
   for result in results["hits"]:
      item = copy.deepcopy(result["document"])
      artists = []
      for artist in item["artists"]:
         artists.append(json.loads(artist))
      item["artists"] = artists
      labels = []
      for label in item["labels"]:
         labels.append(json.loads(label))
      item["labels"] = labels
      credits = []
      for credit in item["credits"]:
         credits.append(json.loads(credit))
      item["credits"] = credits
      tracklist = []
      for track in item["tracklist"]:
         tracklist.append(json.loads(track))
      item["tracklist"] = tracklist
      identifiers = []
      for identifier in item["identifiers"]:
         identifiers.append(json.loads(identifier))
      item["identifiers"] = identifiers
      ret.append(item)
   return ret

# ROUTES


@application.route('/')
def home():
   global count
   return render_template('home.html', length=client.collections["collection"].retrieve()["num_documents"])

@application.route('/search/<query>')
def search(query):
   page = request.args.get("page", default=1, type=int)
   uc = request.args.get("uc", default="")
   global client
   queryLower = query.lower()
   term = queryLower
   if queryLower[0:6] == "title:":
      term = queryLower[6:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'title',
         'page': page
      })
   elif queryLower[0:5] == "year:":
      term = queryLower[5:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'year',
         'page': page
      })
   elif queryLower[0:8] == "country:":
      term = queryLower[8:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'country',
         'page': page
      })
   elif queryLower[0:6] == "notes:":
      term = queryLower[6:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'notes',
         'page': page
      })
   elif queryLower[0:6] == "genre:":
      term = queryLower[6:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'genres',
         'page': page
      })
   elif queryLower[0:6] == "style:":
      term = queryLower[6:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'styles',
         'page': page
      })
   elif queryLower[0:5] == "song:":
      term = queryLower[5:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'tracklist',
         'page': page
      })
   elif queryLower[0:7] == "artist:":
      term = queryLower[7:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'artists,credits',
         'page': page
      })
   elif queryLower[0:6] == "label:":
      term = queryLower[6:].strip()
      results = client.collections['collection'].documents.search({
         'q': term,
         'query_by': 'labels',
         'page': page
      })
   else:
      results = client.collections['collection'].documents.search({
         'q': queryLower,
         'query_by': 'title,artists,year,tracklist,country,labels,genres,styles,credits,notes',
         'page': page
      })

   ret = unflatten(results)
   max_page = math.ceil(results["found"]/10)
   
   return render_template('search.html', uc=uc, query=query, len=results["found"], results=ret, version='search', term=term, page=page, max_page = max_page)

@application.route('/view/<id>')
def view(id):
   return render_template('view.html', item=for_view(id))

@application.route('/artist/<id>')
def artist(id):
   page = request.args.get("page", default=1, type=int)
   uc = request.args.get("uc", default="")
   global client
   global TOKEN
   term = id
   results = client.collections['collection'].documents.search({
      'q': term,
      'query_by': ['artists', 'credits'],
      'page': page
   })
   ret = unflatten(results)
   max_page = math.ceil(results["found"]/10)

   artist = requestWrapper(f'https://api.discogs.com/artists/{id}?token={TOKEN}')

   return render_template('search.html', uc=uc, query=artist["name"], len=results["found"], results=ret, version='artist', term=term, page=page, max_page = max_page)

@application.route('/label/<id>')
def label(id):
   page = request.args.get("page", default=1, type=int)
   uc = request.args.get("uc", default="")
   global client
   global TOKEN
   term = id
   results = client.collections['collection'].documents.search({
      'q': term,
      'query_by': 'labels',
      'page': page
   })
   ret = unflatten(results)
   max_page = math.ceil(results["found"]/10)

   label = requestWrapper(f'https://api.discogs.com/labels/{id}?token={TOKEN}')

   return render_template('search.html', uc=uc, query=label["name"], len=results["found"], results=ret, version='label', term=term, page=page, max_page = max_page)

if __name__ == '__main__':
   try:
      application.run(debug = False, use_reloader = False, host='0.0.0.0', port=80)
   except KeyboardInterrupt:
      os._exit(1)