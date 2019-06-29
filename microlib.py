from requests import get
from requests.exceptions import RequestException

def safeget(url, *args, **kwargs):
    try: resp = get(url, *args, **kwargs)
    except RequestException as ex: return
    if resp.ok and resp.status_code == 200:
        return resp
