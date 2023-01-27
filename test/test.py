import requests
import time

# test that homepage loads
r = requests.get('http://localhost')
assert r.status_code == 200

# test basic search functionality
r = requests.get('http://localhost/search/coltrane')
assert r.status_code == 200

print('---TESTS PASSED---')