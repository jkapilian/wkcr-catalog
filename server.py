from os import sync
from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
import copy
import requests
import discogs_client
import json
app = Flask(__name__)
d = discogs_client.Client('ExampleApplication/0.1', user_token="lzXNWHvkWFJNbyDRonbOoQwhttIRsyGxDTWbpxmX")
syncCount = d.identity().num_collection
collection = json.loads(open("static/base.json").read())
# collection = {}

def updateCollection():
   global d
   global syncCount
   global collection
   syncCount = d.identity().num_collection
   for i in range(1,len(d.identity().collection_folders)):
      name = d.identity().collection_folders[i].name
      for item in d.identity().collection_folders[i].releases:
         print(len(collection))
         release = item.release
         releaseObject = {
            "id": item.instance_id,
            "discogs_id": release.id,
            "title": release.title,
            "year": release.year,
            "genres": release.genres,
            "image": None,
            "country": release.country,
            "notes": release.notes,
            "styles": release.styles,
            "url": release.url,
            "tracklist": tracklist(release.tracklist),
            "artists": object_list(release.artists),
            "credits": object_list(release.credits),
            "labels": object_list(release.labels),
            "companies": object_list(release.companies),
            "folder": name,
            "wkcr_location": item.notes,
            "wkcr_scanned": str(item.date_added),
         }
         if release.images and release.images[0] and release.images[0]['uri']:
            releaseObject['image'] = release.images[0]['uri']
         collection[item.instance_id] = releaseObject
   print(json.dumps(collection))
   return

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
      if query in str(collection[key][param]).lower():
         results.append(collection[key])
         continue
   return results

def listSearch(query, param):
   global collection
   results = []
   for key in collection:
      for item in collection[key][param]:
         if query in item.lower():
            results.append(collection[key])
            break
   return results

def objectSearch(query, param1, param2):
   global collection
   results = []
   for key in collection:
      flag = False
      for item in collection[key][param1]:
         if query in item["name"].lower():
            flag = True
            results.append(collection[key])
            break
      if flag:
         continue

      for item in collection[key][param2]:
         if query in item["name"].lower():
            results.append(collection[key])
            break
   return results

# ROUTES


@app.route('/')
def home():
   return render_template('home.html')

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
      results = paramSearch(term, "country")
   elif queryLower[0:6] == "notes:":
      term = queryLower[6:].strip()
      results = paramSearch(term, "notes")
   elif queryLower[0:6] == "genre:":
      term = queryLower[6:].strip()
      results = listSearch(term, "genres")
   elif queryLower[0:6] == "style:":
      term = queryLower[6:].strip()
      results = listSearch(term, "styles")
   elif queryLower[0:5] == "song:":
      term = queryLower[5:].strip()
      results = listSearch(term, "tracklist")
   elif queryLower[0:7] == "artist:":
      term = queryLower[7:].strip()
      results = objectSearch(term, "artists", "credits")
   elif queryLower[0:6] == "label:":
      term = queryLower[6:]
      results = objectSearch(term, "labels", "companies")
   else:
      results = []
      for key in collection:
         flag = False
         if queryLower in collection[key]["title"].lower():
            loc = int(0.5*len(results)*(1-len(queryLower)/len(collection[key]["title"])))
            results.insert(loc, collection[key])
            continue

         for track in collection[key]["tracklist"]:
            if queryLower in track.lower():
               loc = int(0.5*len(results)*(1-len(queryLower)/len(track)))
               results.insert(loc, collection[key])
               flag = True
               break
         if flag:
            continue

         for artist in collection[key]["artists"]:
            if queryLower in artist["name"].lower():
               loc = int(0.5*len(results)*(1-len(queryLower)/len(artist["name"])))
               results.insert(loc, collection[key])
               flag = True
               break
         if flag:
            continue

         for artist in collection[key]["credits"]:
            if queryLower in artist["name"].lower():
               loc = int(0.5*len(results)*(1-len(queryLower)/len(artist["name"])))
               results.insert(loc, collection[key])
               flag = True
               break
         if flag:
            continue
 
         if queryLower in str(collection[key]["year"]).lower():
            loc = int(0.5*len(results)*(2-len(queryLower)/len(collection[key]["title"])))
            results.insert(loc, collection[key])
            continue

         if queryLower in str(collection[key]["country"]).lower():
            loc = int(0.5*len(results)*(2-len(queryLower)/len(collection[key]["country"])))
            results.insert(loc, collection[key])
            continue
         
         if queryLower in str(collection[key]["notes"]).lower():
            loc = int(0.5*len(results)*(2-len(queryLower)/len(collection[key]["notes"])))
            results.insert(loc, collection[key])
            continue

         for genre in collection[key]["genres"]:
            if queryLower in genre.lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(genre)))
               results.insert(loc, collection[key])
               flag = True
               break
         if flag:
            continue

         for style in collection[key]["styles"]:
            if queryLower in style.lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(style)))
               results.insert(loc, collection[key])
               break
         if flag:
            continue

         for label in collection[key]["labels"]:
            if queryLower in label["name"].lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(label["name"])))
               results.insert(loc, collection[key])
               flag = True
               break
         if flag:
            continue

         for label in collection[key]["companies"]:
            if queryLower in label["name"].lower():
               loc = int(0.5*len(results)*(2-len(queryLower)/len(label["name"])))
               results.insert(loc, collection[key])
               flag = True
               break
         if flag:
            continue

   
   return render_template('search.html', query=query, results=results, version='search', term=term)

@app.route('/view/<id>')
def view(id):
   return render_template('view.html', item=collection[id])

@app.route('/artist/<id>')
def artist(id):
   global collection
   results = []
   for key in collection:
      flag = False
      for artist in collection[key]["artists"]:
         if str(artist["id"]) == id:
            flag = True
            name = artist["name"]
            break
      if flag:
         results.append(collection[key])
         continue
      for artist in collection[key]["credits"]:
         if str(artist["id"]) == id:
            flag = True
            name = artist["name"]
            break
      if flag:
         results.append(collection[key])
         continue
   return render_template('search.html', results=results, query=name, version='artist')

@app.route('/label/<id>')
def label(id):
   global collection
   results = []
   for key in collection:
      flag = False
      for label in collection[key]["labels"]:
         if str(label["id"]) == id:
            flag = True
            name = label["name"]
            break
      if flag:
         results.append(collection[key])
         continue
      for company in collection[key]["companies"]:
         if str(company["id"]) == id:
            flag = True
            name = company["name"]
            break
      if flag:
         results.append(collection[key])
         continue
   return render_template('search.html', results=results, query=name, version='label')

if __name__ == '__main__':
   # updateCollection()
   app.run(debug = True)
