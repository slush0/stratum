'''The simplest non-twisted client using HTTP polling'''
import urllib2
 
data = '{"id": 1, "method": "blockchain.block.ping", "params": ["test"]}'+"\n"
data += '{"id": 2, "method": "firstbits.resolve", "params": ["1marek"]}'+"\n"
data += '{"id": 3, "method": "blockchain.block.ping", "params": ["test2"]}'+"\n"
data += '{"id": 4, "method": "txradar.lookup", "params": ["202e0d0ef7b1299a2193a7aa7bc58161789d72b62948b6005f2a4f190302740c"]}'+"\n"

try:
    headers = {'cookie': open('cookie.txt', 'r').read().strip(),}
except:
    headers = None

r = urllib2.Request('http://localhost:8000', data, headers)
resp = urllib2.urlopen(r)

for h in resp.headers:
    if h == 'set-cookie':
        open('cookie.txt', 'w').write(resp.headers[h])
        
print resp.read()