import requests
import time

# test that homepage loads
r = requests.get('http://localhost')
assert r.status_code == 200

# give time to retrieve some data
time.sleep(10)

# test basic search functionality
r = requests.get('http://localhost/search/coltrane')
print(f'search {r.status_code}')
assert r.status_code == 200

print('---TESTS PASSED---')