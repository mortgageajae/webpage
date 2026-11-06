"""sitemap.xml 의 주소를 IndexNow 로 알림 (Bing·Naver 등이 받음).

사용: python3 -I tools/indexnow.py                     # sitemap 전체
      python3 -I tools/indexnow.py /kr/ /en/           # 일부만
      python3 -I tools/indexnow.py --changed <이전> <이후>  # 두 커밋 사이에 바뀐 페이지만 (GitHub Actions 용)
키 파일은 저장소 최상위의 <키>.txt (내용 = 키). 공개 파일이라 비밀이 아님.
"""
import glob, json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = 'mortgageajae.ca'
ENDPOINTS = ['https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow']

key = next(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, '*.txt'))
           if re.fullmatch(r'[0-9a-f]{32}\.txt', os.path.basename(p)))
sitemap = re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read())

if sys.argv[1:2] == ['--changed']:
    before, after = sys.argv[2], sys.argv[3]
    files = subprocess.run(['git', '-C', ROOT, 'diff', '--name-only', before, after],
                           capture_output=True, text=True, check=True).stdout.split()
    changed = {f'https://{HOST}/' + f[:-len('index.html')] for f in files if f.endswith('index.html') and not f.startswith('src/')}
    urls = [u for u in sitemap if u in changed]
elif sys.argv[1:]:
    urls = [f'https://{HOST}{p}' for p in sys.argv[1:]]
else:
    urls = sitemap

if not urls:
    print('바뀐 공개 페이지 없음, 보내지 않음')
    sys.exit(0)
print('\n'.join(urls))
body = json.dumps({'host': HOST, 'key': key, 'keyLocation': f'https://{HOST}/{key}.txt', 'urlList': urls}).encode()
for ep in ENDPOINTS:
    req = urllib.request.Request(ep, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(ep, r.status, len(urls), 'urls')
    except urllib.error.HTTPError as e:
        print(ep, e.code, e.read()[:200])
