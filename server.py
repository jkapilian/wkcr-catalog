from datetime import timedelta, date, datetime
import os
import threading
from turtle import update
from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
import time
import copy
import requests
import json
app = Flask(__name__)
TOKEN = 'lzXNWHvkWFJNbyDRonbOoQwhttIRsyGxDTWbpxmX'
collection = json.loads(open("static/new_base.json").read())
d_releases = json.loads(open("static/releases.json").read())

last_rate = 0

def requestWrapper(url):
   global last_rate
   if (time.time() - last_rate) > 60:
      resp = requests.get(url)
      if resp.headers['X-Discogs-Ratelimit-Remaining'] == '1':
         last_rate = time.time()
      return resp.json()
   else:
      print(f'Sleeping for {last_rate + 60 - time.time()}')
      print(f'Indexed {len(d_releases)} releases')
      time.sleep(last_rate + 60 - time.time())
      return requestWrapper(url)

def updateCollection():
   tomorrow = date.today() + timedelta(days=1)
   next_2am_eastern = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7)
   delta = (next_2am_eastern - datetime.now()).total_seconds()
   threading.Timer(delta, updateCollection).start()
   global collection
   global d_releases
   folders = requests.get(f'https://api.discogs.com/users/WKCR/collection/folders?token={TOKEN}&per_page=100').json()
   for folder in folders['folders']:
      if folder['id'] != 0:
         name = folder['name']
         print(f'at folder {name}')
         url = folder['resource_url']
         releases = requestWrapper(f'{url}/releases?token={TOKEN}')
         while True:
            for release in releases['releases']:
               collection[release['instance_id']] = release
               collection[release['instance_id']]["folder"] = name
               if str(release['id']) not in d_releases:
                  print(release['id'])
                  pull_release(release['id'], release['basic_information']['resource_url'])
            if 'next' not in releases['pagination']['urls']:
               print(f'here at {len(d_releases)}')
               break
            releases = requestWrapper(releases['pagination']['urls']['next'])            
   return

def pull_release(release_id, url):
   global d_releases
   release_info = requestWrapper(f'{url}?token={TOKEN}')
   d_releases[release_id] = release_info

def for_search(id):
   global collection
   global d_releases
   item = collection[id]
   d_release = d_releases[str(item["id"])]
   return {
      "id": item["instance_id"],
      "title": item["basic_information"]["title"],
      "folder": item["folder"],
      "wkcr_location": item["notes"] if ("notes" in item) else None,
      "image": item["basic_information"]["cover_image"],
      "artists": item["basic_information"]["artists"],
      "credits": d_release["extraartists"],
      "tracklist": d_release["tracklist"],
   }

def for_view(id):
   global collection
   global d_releases
   item = collection[id]
   d_release = d_releases[str(item["id"])]
   return {
      "id": item["instance_id"],
      "title": item["basic_information"]["title"],
      "folder": item["folder"],
      "wkcr_location": item["notes"] if ("notes" in item) else None,
      "image": item["basic_information"]["cover_image"],
      "artists": item["basic_information"]["artists"],
      "credits": d_release["extraartists"],
      "tracklist": d_release["tracklist"],
      "year": item["basic_information"]["year"],
      "country": d_release["country"] if "country" in d_release else "",
      "labels": item["basic_information"]["labels"],
      "genres": item["basic_information"]["genres"],
      "styles": item["basic_information"]["styles"],
      "notes": d_release["notes"] if "notes" in d_release else "",
      "identifiers": d_release["identifiers"]
   }

def tracklist(tracks):
   arr = []
   for track in tracks:
      arr.append(track.title)
   return arr

def object_list(list):
   arr = []
   for item in list:
      arr.append({"id": item.id, "name": item.name})
   return arr

def paramSearch(query, param):
   global collection
   results = []
   for key in collection:
      if query in str(collection[key]['basic_information'][param]).lower():
         results.append(for_search(key))
         continue
   return results

def releaseSearch(query, param):
   global collection
   global d_releases
   results = []
   for key in collection:
      d_id = str(collection[key]["id"])
      d_release = d_releases[d_id]
      if param in d_release and query in str(d_release[param]).lower():
         results.append(for_search(key))
         continue
   return results

def listSearch(query, param):
   global collection
   results = []
   for key in collection:
      for item in collection[key]['basic_information'][param]:
         if query in item.lower():
            results.append(for_search(key))
            break
   return results

def objectSearch(query, param_within, param1, param2=None):
   global collection
   global d_releases
   results = []
   for key in collection:
      d_id = str(collection[key]["id"])
      d_release = d_releases[d_id]
      flag = False
      for item in d_release[param1]:
         if query in item[param_within].lower():
            flag = True
            results.append(for_search(key))
            break
      if flag or not param2:
         continue

      for item in d_release[param2]:
         if query in item[param_within].lower():
            results.append(for_search(key))
            break
   return results

# ROUTES


@app.route('/')
def home():
   global collection
   return render_template('home.html', length=len(collection))

@app.route('/search/<query>')
def search(query):
   global collection
   queryLower = query.lower()
   term = queryLower
   if queryLower[0:6] == "title:":
      term = queryLower[6:].strip()
      results = paramSearch(term, "title")
   elif queryLower[0:5] == "year:":
      term = queryLower[5:].strip()
      results = paramSearch(term, "year")
   elif queryLower[0:8] == "country:":
      term = queryLower[8:].strip()
      results = releaseSearch(term, "country")
   elif queryLower[0:6] == "notes:":
      term = queryLower[6:].strip()
      results = releaseSearch(term, "notes")
   elif queryLower[0:6] == "genre:":
      term = queryLower[6:].strip()
      results = listSearch(term, "genres")
   elif queryLower[0:6] == "style:":
      term = queryLower[6:].strip()
      results = listSearch(term, "styles")
   elif queryLower[0:5] == "song:":
      term = queryLower[5:].strip()
      results = objectSearch(term, "title", "tracklist")
   elif queryLower[0:7] == "artist:":
      term = queryLower[7:].strip()
      results = objectSearch(term, "name", "artists", "extraartists")
   elif queryLower[0:6] == "label:":
      term = queryLower[6:]
      results = objectSearch(term, "name", "labels", "companies")
   else:
      results = []
      for key in collection:
         flag = False
         d_id = str(collection[key]["id"])
         d_release = d_releases[d_id]
         if queryLower in collection[key]["basic_information"]["title"].lower():
            loc = int(0.5*len(results)*(1-len(queryLower)/len(collection[key]["basic_information"]["title"])))
            results.insert(loc, for_search(key))
            continue

         for track in d_release["tracklist"]:
            if queryLower in track["title"].lower():
               loc = int(0.5*len(results)*(1-len(queryLower)/len(track)))
               results.insert(loc, for_search(key))
               flag = True
               break
         if flag:
            continue

         for artist in collection[key]["basic_information"]["artists"]:
            if queryLower in artist["name"].lower():
               loc = int(0.5*len(results)*(1-len(queryLower)/len(artist["name"])))
               results.insert(loc, for_search(key))
               flag = True
               break
         if flag:
            continue

         for artist in d_release["extraartists"]:
            if queryLower in artist["name"].lower():
               loc = int(0.5*len(results)*(1-len(queryLower)/len(artist["name"])))
               results.insert(loc, for_search(key))
               flag = True
               break
         if flag:
            continue
 
         if "year" in collection[key]["basic_information"] and queryLower in str(collection[key]["basic_information"]["year"]).lower():
            loc = int(0.5*len(results)*(2-len(queryLower)/len(collection[key]["basic_information"]["title"])))
            results.insert(loc, for_search(key))
            continue

         if "country" in d_release and queryLower in str(d_release["country"]).lower():
            loc = int(0.5*len(results)*(2-len(queryLower)/len(d_release["country"])))
            results.insert(loc, for_search(key))
            continue
         
         if "notes" in d_release and queryLower in str(d_release["notes"]).lower():
            loc = int(0.5*len(results)*(2-len(queryLower)/len(d_release["notes"])))
            results.insert(loc, for_search(key))
            continue

         for genre in collection[key]["basic_information"]["genres"]:
            if queryLower in genre.lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(genre)))
               results.insert(loc, for_search(key))
               flag = True
               break
         if flag:
            continue

         for style in collection[key]["basic_information"]["styles"]:
            if queryLower in style.lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(style)))
               results.insert(loc, for_search(key))
               break
         if flag:
            continue

         for label in collection[key]["basic_information"]["labels"]:
            if queryLower in label["name"].lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(label["name"])))
               results.insert(loc, for_search(key))
               flag = True
               break
         if flag:
            continue

         for label in d_release["companies"]:
            if queryLower in label["name"].lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(label["name"])))
               results.insert(loc, for_search(key))
               flag = True
               break
         if flag:
            continue

   
   return render_template('search.html', query=query, results=results, version='search', term=term)

@app.route('/view/<id>')
def view(id):
   return render_template('view.html', item=for_view(id))

@app.route('/artist/<id>')
def artist(id):
   global collection
   global d_releases
   results = []
   for key in collection:
      d_id = str(collection[key]["id"])
      d_release = d_releases[d_id]
      flag = False
      for artist in collection[key]["basic_information"]["artists"]:
         if str(artist["id"]) == id:
            flag = True
            name = artist["name"]
            break
      if flag:
         results.append(for_search(key))
         continue
      for artist in d_release["extraartists"]:
         if str(artist["id"]) == id:
            flag = True
            name = artist["name"]
            break
      if flag:
         results.append(for_search(key))
         continue
   return render_template('search.html', results=results, query=name, version='artist')

@app.route('/label/<id>')
def label(id):
   global collection
   global d_releases
   results = []
   for key in collection:
      d_id = str(collection[key]["id"])
      d_release = d_releases[d_id]
      flag = False
      for label in collection[key]["basic_information"]["labels"]:
         if str(label["id"]) == id:
            flag = True
            name = label["name"]
            break
      if flag:
         results.append(for_search(key))
         continue
      for company in d_release["companies"]:
         if str(company["id"]) == id:
            flag = True
            name = company["name"]
            break
      if flag:
         results.append(for_search(key))
         continue
   return render_template('search.html', results=results, query=name, version='label')

if __name__ == '__main__':
   tomorrow = date.today() + timedelta(days=1)
   next_2am_eastern = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7)
   delta = (next_2am_eastern - datetime.now()).total_seconds()
   threading.Timer(delta, updateCollection).start()
   try:
      app.run(debug = True)
   except KeyboardInterrupt:
      os._exit(1)
   # updateCollection()
   # open("static/new_base.json", "a").write(json.dumps(collection))