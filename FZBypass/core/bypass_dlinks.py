from base64 import b64decode
from traceback import format_exc
from asyncio import create_task, gather
from http.cookiejar import MozillaCookieJar
from json import loads
from os import path
from re import findall, match, search, sub
from time import sleep
from urllib.parse import parse_qs, quote, unquote, urlparse
from uuid import uuid4
 
from bs4 import BeautifulSoup
from cloudscraper import create_scraper
from lxml import etree
from requests import Session
from aiohttp import ClientSession 
 
from FZBypass import LOGGER, Config
from FZBypass.core.exceptions import DDLException
 
 
async def filepress(url: str):
    cget = create_scraper().request
    try:
        url = cget('GET', url).url
        raw = urlparse(url)
        async with ClientSession() as sess:
            json_data = {
                'id': raw.path.split('/')[-1],
                'method': 'publicDownlaod',
            }
            async with await sess.post(f'{raw.scheme}://{raw.hostname}/api/file/downlaod/', headers={'Referer': f'{raw.scheme}://{raw.hostname}'}, json=json_data) as resp:
                d_id = await resp.json()
            if d_id.get('data', False):
                dl_link = f"https://drive.google.com/uc?id={d_id['data']}&export=download"
                parsed = BeautifulSoup(cget('GET', dl_link).content, 'html.parser').find('span')
                combined = str(parsed).rsplit('(', maxsplit=1)
                name, size = combined[0], combined[1].replace(')', '') + 'B'
            else:
                dl_link = "Link Not Found" if d_id["statusText"] == "Bad Request" else d_id["statusText"]
                name, size = "N/A", "N/A"
            del json_data['method']
            async with await sess.post(f'{raw.scheme}://{raw.hostname}/api/file/telegram/downlaod/', headers={'Referer': f'{raw.scheme}://{raw.hostname}'}, json=json_data) as resp:
                tg_id = await resp.json()
            if tg_id.get('data', False):
                t_url = f"https://tghub.xyz/?start={tg_id['data']}"
                bot_name = findall("filepress_[a-zA-Z0-9]+_bot", cget('GET', t_url).text)[0]
                tg_link = f"https://t.me/{bot_name}/?start={tg_id['data']}"
            else:
                tg_link = 'Telegram Not Uploaded / Unavailable' if tg_id["statusText"] == "Ok" else tg_id["statusText"]
    except Exception as e:
        raise DDLException(f'<b>ERROR:</b> {e.__class__.__name__}')
    return f'''<b>📁 NAME:</b> <code>{name}</code>\n\n
<b>💽 SIZE :</b> <code>{size}</code>\n
<b>🔗 FILEPRESS LINK:</b> <code>{url}</code>\n
<b>📩 <a href="{dl_link}">DOWNLOAD LINK</a></b>: <code>{dl_link}</code>\n
<b>📺 TG FILE LINK :</b> {tg_link}'''
 
 
async def gdtot(url):
    cget = create_scraper().request
    try:
        url = cget('GET', url).url
        p_url = urlparse(url)
        res = cget("POST", f"{p_url.scheme}://{p_url.hostname}/ddl", data={'dl': str(url.split('/')[-1])})
    except Exception as e:
        raise DDLException(f'{e.__class__.__name__}')
    if (drive_link := findall(r"myDl\('(.*?)'\)", res.text)) and "drive.google.com" in drive_link[0]:
        d_link = drive_link[0]
    elif Config.GDTOT_CRYPT:
        cget('GET', url, cookies={'crypt': Config.GDTOT_CRYPT})
        p_url = urlparse(url)
        js_script = cget('POST', f"{p_url.scheme}://{p_url.hostname}/dld", data={'dwnld': url.split('/')[-1]})
        g_id = findall('gd=(.*?)&', js_script.text)
        try:
            decoded_id = b64decode(str(g_id[0])).decode('utf-8')
        except:
            raise DDLException("Try in your browser, mostly file not found or user limit exceeded!")
        d_link = f'https://drive.google.com/open?id={decoded_id}'
    else:
        raise DDLException('Drive Link not found, Try in your broswer! GDTOT_CRYPT not Provided!')
    soup = BeautifulSoup(cget('GET', url).content, "html.parser")
    parse_data = (soup.select('meta[property^="og:description"]')[0]['content']).replace('Download ' , '').rsplit('-', maxsplit=1)
    return f'''<b>📁 File Name :</b> <code>{parse_data[0]}</code>\n\n
<b>💽 SIZE :</b> <code>{parse_data[-1]}</code>\n
<b>🔗 <a href="{url}">GDTOT LINK </a></b>: <code>{url}</code>\n
<b>📩 BYPASS LINK :</b> {d_link}'''
 
 
async def drivescript(url, crypt, dtype):
    rs = Session()
    resp = rs.get(url)
    title = findall(r'>(.*?)<\/h4>', resp.text)[0]
    size = findall(r'>(.*?)<\/td>', resp.text)[1]
    p_url = urlparse(url)
    dlink = ''
    if dtype != "DriveFire":
        try:
            js_query = rs.post(f"{p_url.scheme}://{p_url.hostname}/ajax.php?ajax=direct-download", data={'id': str(url.split('/')[-1])}, headers={'x-requested-with': 'XMLHttpRequest'}).json()
            if str(js_query['code']) == '200':
                dlink = f"{p_url.scheme}://{p_url.hostname}{js_query['file']}"
        except Exception as e:
            LOGGER.error(e)
        
    if not dlink and crypt:
        rs.cookies.update({'crypt': crypt})
        try:
            js_query = rs.post(f"{p_url.scheme}://{p_url.hostname}/ajax.php?ajax=download", data={'id': str(url.split('/')[-1])}, headers={'x-requested-with': 'XMLHttpRequest'}).json()
        except Exception as e:
            raise DDLException(f'{e.__class__.__name__}')
        if str(js_query['code']) == '200':
            dlink = f"{p_url.scheme}://{p_url.hostname}{js_query['file']}"
    
    if dlink:    
        res = rs.get(dlink)
        soup = BeautifulSoup(res.text, 'html.parser')
        gd_data = soup.select('a[class="btn btn-primary btn-user"]')
        parse_txt = f'''<b>📁 NAME:</b> <code>{title}</code>\n\n
<b>💽 SIZE :</b> <code>{size}</code>\n
<b>📜 {dtype} Link :</b> <code>{url}</code>\n
'''
        if dtype == "HubDrive":
            parse_txt += f'''<b>📩 BYPASS LINK:</b> {gd_data[0]['href']}
<b>🔗 INSTANT LINK:</b> <a href="{gd_data[1]['href']}">CLICK HERE</a>'''
        else:
            parse_txt += f"<b>📩 BYPASS LINK:</b> {gd_data[0]['href']}"
        return parse_txt
    elif not dlink and not crypt:
        raise DDLException(f'{dtype} Crypt Not Provided & {js_query["file"]}')
    else:
        raise DDLException(f'{js_query["file"]}')
 
 
async def appflix(url):
    async def appflix_single(url):
        d_link = await sharer_scraper(url)
        cget = create_scraper().request
        url = cget("GET", url).url
        soup = BeautifulSoup(cget('GET', url).content, "html.parser")
        ss = soup.select("li[class^='list-group-item']")
        return f'''<b>📁 NAME:</b> <code>{ss[0].string.split(":")[1]}</code>\n\n
<b>💽 SIZE:</b> <i>{ss[2].string.split(":")[1]}</i>
<b>🔗 <a href="{url}">SOURCE LINK</a></b>: <code>{url}</code>\n
<b>📩 BYPASS LINK :</b> {d_link}'''
    if "/pack/" in url:
        cget = create_scraper().request
        url = cget("GET", url).url
        soup = BeautifulSoup(cget("GET", url).content, "html.parser")
        p_url = urlparse(url)
        body = ""
        atasks = [create_task(appflix_single(f"{p_url.scheme}://{p_url.hostname}" + ss['href'])) for ss in soup.select("a[href^='/file/']")]
        completed_tasks = await gather(*atasks, return_exceptions=True)
        for bp_link in completed_tasks:
            if isinstance(bp_link, Exception):
                body += "\n\n" + f"<b>Bypass Error:</b> {bp_link}"
            else:
                body += "\n\n" + bp_link
        return f'''<b>📁 NAME:</b> <code>{soup.title.string}</code>
<b>♦️ SOURCE PACK:</b> <code>{url}{body}</code>'''
    return await appflix_single(url)
 
 
async def sharer_scraper(url):
    cget = create_scraper().request
    try:
        url = cget('GET', url).url
        raw = urlparse(url)
        header = {"useragent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10"}
        res = cget('GET', url, headers=header)
    except Exception as e:
        raise DDLException(f'{e.__class__.__name__}')
    key = findall('"key",\s+"(.*?)"', res.text)
    if not key:
        raise DDLException("Download Link Key not found!")
    key = key[0]
    if not etree.HTML(res.content).xpath("//button[@id='drc']"):
        raise DDLException("Link don't have direct download button")
    boundary = uuid4()
    headers = {
        'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary{boundary}',
        'x-token': raw.hostname,
        'useragent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10'
    }
 
    data = f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action"\r\n\r\ndirect\r\n' \
           f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="key"\r\n\r\n{key}\r\n' \
           f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action_token"\r\n\r\n\r\n' \
           f'------WebKitFormBoundary{boundary}--\r\n'
    try:
        res = cget("POST", url, cookies=res.cookies, headers=headers, data=data).json()
    except Exception as e:
        raise DDLException(f'ERROR: {e.__class__.__name__}')
    if "url" not in res:
        raise DDLException('Drive Link not found, Try in your browser')
    if "drive.google.com" in res["url"]:
        return res["url"]
    try:
        res = cget('GET', res["url"])
    except Exception as e:
        raise DDLException(f'ERROR: {e.__class__.__name__}')
    if (drive_link := etree.HTML(res.content).xpath("//a[contains(@class,'btn')]/@href")) and "drive.google.com" in drive_link[0]:
        return drive_link[0]
    else:
        raise DDLException('Drive Link not found, Try in your browser')
 
 
 
