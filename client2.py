'''The simplest non-twisted client using HTTP polling'''
import urllib2
import time

n = 1
data = '{"id": 1, "method": "example.pubsub.subscribe", "params": [1]}'+"\n"
data += '{"id": 2, "method": "example.ping", "params": ["cus"]}'+"\n"
#data += '{"id": 3, "method": "example.synchronous", "params": [5]}'+"\n"
#data += '{"id": 4, "method": "example.synchronous", "params": [5]}'+"\n"
#data += '{"id": 5, "method": "example.synchronous", "params": [5]}'+"\n"
 
''' 
data = '{"id": 1, "method": "blockchain.block.ping", "params": ["test"]}'+"\n"
data += '{"id": 2, "method": "firstbits.resolve", "params": ["1marek"]}'+"\n"
data += '{"id": 3, "method": "blockchain.block.ping", "params": ["test2"]}'+"\n"
data += '{"id": 4, "method": "txradar.lookup", "params": ["202e0d0ef7b1299a2193a7aa7bc58161789d72b62948b6005f2a4f190302740c"]}'+"\n"
'''

try:
    headers = {'cookie': open('cookie.txt', 'r').read().strip(),}
except:
    headers = {}
    
headers['content-type'] = 'application/stratum'
#headers['x-callback-url'] = 'http://localhost:20000'

s = time.time()

for x in range(n):
    r = urllib2.Request('http://california.stratum.bitcoin.cz:8000', data, headers)
#    r = urllib2.Request('http://localhost:8000', data, headers)
    resp = urllib2.urlopen(r)

    for h in resp.headers:
        print h, resp.headers[h]
        if h == 'set-cookie':
            open('cookie.txt', 'w').write(resp.headers[h])
        
    print resp.read()
print float(n) / (time.time() - s)
