from datetime import timedelta, date, datetime
import os
import threading
from flask import Flask
from flask import render_template
from flask import request
import time
import copy
import requests
import json
from dotenv import load_dotenv
import typesense
import math

app = Flask(__name__)
load_dotenv()
TOKEN = os.environ.get('DISCOGS_API_KEY')
# Use the application default credentials.


client = typesense.Client({
   'api_key': 'xyz',
   'nodes': [{
      'host': 'localhost',
      'port': '8108',
      'protocol': 'http'
   }],
   'connectionTimeoutSeconds': 2
})
'''client.collections['collection'].delete()

client.collections.create({
   "name": "collection",
   "fields": [
      {"name": ".*", "type": "auto" },
      # {"name": "artists", "type": "auto", "index": False},
      # {"name": "labels", "type": "auto", "index": False},
      # {"name": "credits", "type": "auto", "index": False},
      # {"name": "tracklist", "type": "auto", "index": False},
      # {"name": "identifiers", "type": "auto", "index": False}
   ]
})'''



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

def updateCollection():
   print('starting')
   tomorrow = date.today() + timedelta(days=1)
   next_2am_eastern = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7)
   delta = (next_2am_eastern - datetime.now()).total_seconds()
   threading.Timer(delta, updateCollection).start()
   global client
   folders = requestWrapper(f'https://api.discogs.com/users/WKCR/collection/folders?token={TOKEN}&per_page=100')
   for folder in folders['folders']:
      if folder['id'] != 0:
         name = folder['name']
         print(f'at folder {name}')
         url = folder['resource_url']
         releases = requestWrapper(f'{url}/releases?token={TOKEN}')
         while True:
            for release in releases['releases']:
               try:
                  client.collections["collection"].documents[str(release["instance_id"])].update({
                     "folder": name,
                     "wkcr_location": release["notes"][0]["value"] if ("notes" in release) else None,
                  })
               except:
                  print(release['id'])
                  url = release['basic_information']['resource_url']
                  release_info = requestWrapper(f'{url}?token={TOKEN}')
                  
                  artists = []
                  for artist in release["basic_information"]["artists"]:
                     artists.append(json.dumps(artist))
                  labels = []
                  for label in release["basic_information"]["labels"]:
                     labels.append(json.dumps(label))
                  credits = []
                  for credit in release_info["extraartists"]:
                     credits.append(json.dumps(credit))
                  tracklist = []
                  for track in release_info["tracklist"]:
                     tracklist.append(json.dumps(track))
                  identifiers = []
                  for identifier in release_info["identifiers"]:
                     identifiers.append(json.dumps(identifier))

                  client.collections["collection"].documents.create({
                     "id": str(release["instance_id"]),
                     "title": release["basic_information"]["title"],
                     "folder": name,
                     "wkcr_location": release["notes"][0]["value"] if ("notes" in release) else None,
                     "image": release["basic_information"]["cover_image"],
                     "artists": artists,
                     "year": str(release["basic_information"]["year"]),
                     "labels": labels,
                     "genres": release["basic_information"]["genres"],
                     "styles": release["basic_information"]["styles"],
                     "credits": credits,
                     "tracklist": tracklist,
                     "country": release_info["country"] if "country" in release_info else "",
                     "notes": release_info["notes"] if "notes" in release_info else "",
                     "identifiers": identifiers,
                     "url": release_info["uri"],
                  })
               
               
            if 'next' not in releases['pagination']['urls']:
               print(f'here at {client.collections["collection"].retrieve()["num_documents"]}')
               break
            releases = requestWrapper(releases['pagination']['urls']['next'])            
   return

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


@app.route('/')
def home():
   global count
   return render_template('home.html', length=client.collections["collection"].retrieve()["num_documents"])

@app.route('/search/<query>')
def search(query):
   page = request.args.get("page", default=1, type=int)
   uc = request.args.get("uc", default="")
   global collection
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
         'query_by': ['artists', 'credits'],
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
         'query_by': ['title', 'artists', 'year', 'tracklist', 'country', 'labels', 'genres', 'styles', 'credits', 'notes'],
         'page': page
      })

   ret = unflatten(results)
   max_page = math.ceil(results["found"]/10)
   
   return render_template('search.html', uc=uc, query=query, len=results["found"], results=ret, version='search', term=term, page=page, max_page = max_page)

@app.route('/view/<id>')
def view(id):
   return render_template('view.html', item=for_view(id))

@app.route('/artist/<id>')
def artist(id):
   return 'will be implemented soon!'

@app.route('/label/<id>')
def label(id):
   return 'will be implemented soon!'

if __name__ == '__main__':
   tomorrow = date.today() + timedelta(days=1)
   next_2am_eastern = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7)
   delta = (next_2am_eastern - datetime.now()).total_seconds()
   threading.Timer(0, updateCollection).start()
   try:
      app.run(debug = False, use_reloader = False)
   except KeyboardInterrupt:
      os._exit(1)