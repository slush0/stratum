#!/usr/bin/env python
try:
    import ecdsa
    from ecdsa import curves
except ImportError:
    print "ecdsa package not installed. Signing of messages not available."
    ecdsa = None
    
import base64
import hashlib
import time

import jsonical
import json
import custom_exceptions

if ecdsa:
    # secp256k1, http://www.oid-info.com/get/1.3.132.0.10
    _p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
    _r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
    _b = 0x0000000000000000000000000000000000000000000000000000000000000007L
    _a = 0x0000000000000000000000000000000000000000000000000000000000000000L
    _Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
    _Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L
    curve_secp256k1 = ecdsa.ellipticcurve.CurveFp(_p, _a, _b)
    generator_secp256k1 = ecdsa.ellipticcurve.Point(curve_secp256k1, _Gx, _Gy, _r)
    oid_secp256k1 = (1,3,132,0,10)
    SECP256k1 = ecdsa.curves.Curve("SECP256k1", curve_secp256k1, generator_secp256k1, oid_secp256k1 )
    
    # Register SECP256k1 to ecdsa library
    curves.curves.append(SECP256k1)

def generate_keypair():
    if not ecdsa:
        raise custom_exceptions.SigningNotAvailableException("ecdsa not installed")
    
    private_key = ecdsa.SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    return (private_key, public_key)
    
def load_privkey_pem(filename):
    return ecdsa.SigningKey.from_pem(open(filename, 'r').read().strip())
        
def sign(privkey, data):
    if not ecdsa:
        raise custom_exceptions.SigningNotAvailableException("ecdsa not installed")

    hash = hashlib.sha256(data).digest()
    signature = privkey.sign_digest(hash, sigencode=ecdsa.util.sigencode_der)
    return base64.b64encode(signature)

def verify(pubkey, signature, data):
    if not ecdsa:
        raise custom_exceptions.SigningNotAvailableException("ecdsa not installed")

    hash = hashlib.sha256(data).digest()
    sign = base64.b64decode(signature)
    try:
        return pubkey.verify_digest(sign, hash, sigdecode=ecdsa.util.sigdecode_der)
    except:
        return False

def jsonrpc_dumps_sign(privkey, privkey_id, is_request, message_id, method='', params=[], result=None, error=None):
    '''Create the signature for given json-rpc data and returns signed json-rpc text stream'''
    
    # Build data object to sign
    sign_time = int(time.time())
    data = {'method': method, 'params': params, 'result': result, 'error': error, 'sign_time': sign_time}
       
    # Serialize data to sign and perform signing
    txt = jsonical.dumps(data)
    signature = sign(privkey, txt)
    
    # Reconstruct final data object and put signature
    if is_request:
        data = {'id': message_id, 'method': method, 'params': params,
                'sign': signature, 'sign_algo': 'ecdsa;SECP256k1', 'sign_id': privkey_id, 'sign_time': sign_time}
    else:
        data = {'id': message_id, 'result': result, 'error': error,
                'sign': signature, 'sign_algo': 'ecdsa;SECP256k1', 'sign_id': privkey_id, 'sign_time': sign_time}
        
    # Return original data extended with signature
    return jsonical.dumps(data)

def jsonrpc_loads_verify(pubkeys, txt):
    '''
        Pubkeys is mapping (dict) of sign_id -> ecdsa public key.
        This method deserialize provided json-encoded data, load signature ID, perform the lookup for public key
        and check stored signature of the message. If signature is OK, returns message data.
    '''
    data = json.loads(txt)
    signature_algo = data['sign_algo']
    signature_id = data['sign_id']
    signature_time = data['sign_time']
    
    if signature_algo != 'ecdsa;SECP256k1':
        raise custom_exceptions.UnknownSignatureAlgorithmException("%s is not supported" % signature_algo)
    
    try:
        pubkey = pubkeys[signature_id]
    except KeyError:
        raise custom_exceptions.UnknownSignatureIdException("Public key for '%s' not found" % signature_id)
    
    signature = data['sign']
    message_id = data['id']
    method = data.get('method', '')
    params = data.get('params', [])
    result = data.get('result', None)
    error = data.get('error', None)
    
    # Build data object to verify
    data = {'method': method, 'params': params, 'result': result, 'error': error, 'sign_time': signature_time}        
    txt = jsonical.dumps(data)
    
    if not verify(pubkey, signature, txt):
        raise custom_exceptions.SignatureVerificationFailedException("Signature doesn't match to given data")
    
    if method:
        # It's a request
        return {'id': message_id, 'method': method, 'params': params}
    
    else:
        # It's aresponse
        return {'id': message_id, 'result': result, 'error': error}    

if __name__ == '__main__':
    (private, public) = generate_keypair()
    print private.to_pem()
