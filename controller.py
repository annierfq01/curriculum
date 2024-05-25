import json, time, random, string
from cgitb import html
import smtplib
import urllib.parse
from email.message import EmailMessage as EM

from var import *

def generate_ramdon_id():
    characters = string.ascii_letters + string.digits
    cad = ''.join(random.choice(characters)for _ in range(8))
    return cad

def get_time():
    t = time.localtime(time.time())
    tt = str(t.tm_year) + '/' + str(t.tm_mon)  + '/' + str(t.tm_mday) + '/' + str(t.tm_hour) + ':' + str(t.tm_min)
    return tt

def get_points(area:str, tipo:str, level:str):
    with open(f'db/points.json') as f:
        data = json.load(f)
        return data[area][tipo][level]

def sendActivate(email:str, username:str, key:str):
    mess = EM()
    mess["From"] = e_sender

    escaped_token = urllib.parse.quote(key)
    params = {'token':key, 'user':username}

    url = URL_BASE + 'validate/?' + urllib.parse.urlencode(params)

    try:
        server = smtplib.SMTP(m_smtp, port=puerto)
        server.ehlo()
        server.starttls()
        server.login(e_sender, e_pass)
    except:
        return False

    mess["To"] = email
    mess["Subject"] = "Código de activación"

    htmlContent = f""""
<a href="{url}">Activate acount</a>
    """

    mess.set_content(htmlContent, subtype = "html")
    server.sendmail(e_sender, email, mess.as_string())
    server.quit()

    return True
    
def is_super(user:str):
    supers = []
    with open(f'db/supers.json') as f:
        supers = json.load(f)
        return user in supers