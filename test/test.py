import requests

# test that homepage loads
r = requests.get('http://localhost')
print(f'homepage {r.status_code}')
assert r.status_code == 200

# test basic search functionality
r = requests.get('http://localhost/search/coltrane')
assert r.status_code == 200
print(f'search {r.status_code}')

print('---TESTS PASSED---')