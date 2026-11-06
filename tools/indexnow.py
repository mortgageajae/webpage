"""sitemap.xml 의 주소를 IndexNow 로 알림 (Bing·Naver 등이 받음).

사용: python3 -I tools/indexnow.py            # sitemap 전체
      python3 -I tools/indexnow.py /kr/ /en/  # 일부만
키 파일은 저장소 최상위의 <키>.txt (내용 = 키). 공개 파일이라 비밀이 아님.
"""
import glob, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = 'mortgageajae.ca'
ENDPOINTS = ['https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow']

key = next(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, '*.txt'))
           if re.fullmatch(r'[0-9a-f]{32}\.txt', os.path.basename(p)))
if sys.argv[1:]:
    urls = [f'https://{HOST}{p}' for p in sys.argv[1:]]
else:
    urls = re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read())

body = json.dumps({'host': HOST, 'key': key, 'keyLocation': f'https://{HOST}/{key}.txt', 'urlList': urls}).encode()
for ep in ENDPOINTS:
    req = urllib.request.Request(ep, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(ep, r.status, len(urls), 'urls')
    except urllib.error.HTTPError as e:
        print(ep, e.code, e.read()[:200])
