import os, smtplib, ssl
from requests import get
from requests.exceptions import RequestException

def safeget(url, *args, **kwargs):
    try: resp = get(url, *args, **kwargs)
    except RequestException as ex: return
    if resp.ok and resp.status_code == 200:
        return resp

def sendgmail(content, fr, to, pas):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(fr, pas)
        server.sendmail(fr, to, content)

def log(data, filename='log.txt'):
    if not os.path.isfile(filename): open(filename, 'a').close()
    with open(filename, 'w') as logf: print(data, file=logf)
