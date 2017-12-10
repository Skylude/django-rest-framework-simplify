import base64
import hmac

from hashlib import sha1
from six import PY3


def generate(uri, params, token, utf=PY3):
    # compute the signature for a given request
    s = uri
    if len(params) > 0:
        for k, v in sorted(params.items()):
            s += k + str(v)

    # compute signature and compare signatures
    mac = hmac.new(token, s.encode('utf-8'), sha1)
    computed = base64.b64encode(mac.digest())
    if utf:
        computed = computed.decode('utf-8')

    return computed.strip()


def validate(signature_1, signature_2):
    # validate signatures
    if len(signature_1) != len(signature_2):
        return False

    result = True
    for c1, c2 in zip(signature_1, signature_2):
        result &= c1 == c2

    return result
