from dotenv import load_dotenv
import os
import time
import typesense
import requests
import json
import threading
from datetime import timedelta, date, datetime

load_dotenv()
TOKEN = os.environ.get('DISCOGS_API_KEY')
# Use the application default credentials.

# give Typesense time to boot
time.sleep(10)
client = typesense.Client({
   'api_key': 'xyz',
   'nodes': [{
      'host': 'typesense',
      'port': '8100',
      'protocol': 'http'
   }],
   'connectionTimeoutSeconds': 2
})

'''client.collections['collection'].delete()'''

try:
   client.collections['collection'].retrieve()
except:
   try:
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
      })
   except:
      # in case initial try catch failed because of 503 but collection already exists
      client.collections['collection'].retrieve()

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

updateCollection()