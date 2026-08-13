import json
import time
import random
import threading
import requests
import warnings

import arjun.core.config as mem

from ratelimit import limits, sleep_and_retry
from arjun.core.utils import dict_to_xml

warnings.filterwarnings('ignore')

_thread_local = threading.local()


def _get_session():
    if not hasattr(_thread_local, 'session'):
        s = requests.Session()
        s.verify = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        _thread_local.session = s
    return _thread_local.session


@sleep_and_retry
@limits(calls=mem.var['rate_limit'], period=1)
def requester(request, payload={}):
    """
    central function for making http requests
    returns str on error otherwise response object of requests library
    """
    payload = dict(payload)
    if request.get('include') and len(request.get('include', '')) != 0:
        payload.update(request['include'])

    cache_bust = {}
    if not mem.var.get('no_cache_bust'):
        cache_bust['_arjcb'] = random.randint(100000, 9999999)

    if mem.var['stable']:
        mem.var['delay'] = random.choice(range(3, 10))
    time.sleep(mem.var['delay'])
    url = request['url']
    if mem.var['kill']:
        return 'killed'

    session = _get_session()

    try:
        if request['method'] == 'GET':
            payload.update(cache_bust)
            response = session.get(url,
                params=payload,
                headers=request['headers'],
                allow_redirects=False,
                timeout=mem.var['timeout'],
            )
        elif request['method'] == 'JSON':
            headers = dict(request['headers'])
            headers['Content-Type'] = 'application/json'
            if mem.var['include'] and '$arjun$' in mem.var['include']:
                json_payload = mem.var['include'].replace('$arjun$',
                    json.dumps(payload).rstrip('}').lstrip('{'))
                response = session.post(url,
                    data=json_payload,
                    params=cache_bust,
                    headers=headers,
                    allow_redirects=False,
                    timeout=mem.var['timeout'],
                )
            else:
                response = session.post(url,
                    json=payload,
                    params=cache_bust,
                    headers=headers,
                    allow_redirects=False,
                    timeout=mem.var['timeout'],
                )
        elif request['method'] == 'XML':
            headers = dict(request['headers'])
            headers['Content-Type'] = 'application/xml'
            xml_payload = mem.var['include'].replace('$arjun$',
                dict_to_xml(payload))
            response = session.post(url,
                data=xml_payload,
                params=cache_bust,
                headers=headers,
                allow_redirects=False,
                timeout=mem.var['timeout'],
            )
        else:
            response = session.post(url,
                data=payload,
                params=cache_bust,
                headers=request['headers'],
                allow_redirects=False,
                timeout=mem.var['timeout'],
            )
        return response
    except Exception as e:
        return str(e)
