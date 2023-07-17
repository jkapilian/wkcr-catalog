import requests

# test that homepage loads
r = requests.get('http://localhost:8000')
assert r.status_code == 200

# test basic search functionality
r = requests.get('http://localhost/search/coltrane:8000')
assert r.status_code == 200

print('---TESTS PASSED---')