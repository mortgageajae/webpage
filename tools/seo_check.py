"""배포될 페이지 SEO·GEO 점검. 사용: python3 -I tools/seo_check.py (저장소 루트)

배포 제외(.assetsignore)·옛 주소 이동(_redirects)을 반영해, 실제로 공개될 HTML만 본다.
"""
import fnmatch, glob, html, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://mortgageajae.ca'


def ignored(rel):
    pats = [l.strip() for l in open(os.path.join(ROOT, '.assetsignore')) if l.strip() and not l.startswith('#')]
    return any(rel == p or rel.startswith(p.rstrip('/') + '/') or fnmatch.fnmatch(rel, p) for p in pats)


REDIRECTS = {}
for l in open(os.path.join(ROOT, '_redirects')):
    if l.strip() and not l.startswith('#'):
        a, b = l.split()[:2]
        REDIRECTS[a] = b


class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.t = ''; s.intitle = False; s.metas = {}; s.links = []; s.h1 = 0; s.imgs = []; s.a = []
        s.ld = []; s.inld = False; s.lang = None; s.alts = {}; s.canon = None; s.h1text = ''; s.inh1 = False

    def handle_starttag(s, tag, at):
        d = dict(at)
        if tag == 'html': s.lang = d.get('lang')
        if tag == 'title': s.intitle = True
        if tag == 'meta':
            k = d.get('name') or d.get('property')
            if k: s.metas[k] = d.get('content', '')
        if tag == 'link':
            if d.get('rel') == 'canonical': s.canon = d.get('href')
            if d.get('rel') == 'alternate' and d.get('hreflang'): s.alts[d['hreflang']] = d.get('href')
        if tag == 'h1': s.h1 += 1; s.inh1 = True
        if tag == 'img': s.imgs.append(d)
        if tag == 'a' and d.get('href'): s.a.append(d['href'])
        if tag == 'script' and d.get('type') == 'application/ld+json': s.inld = True; s.ld.append('')

    def handle_endtag(s, tag):
        if tag == 'title': s.intitle = False
        if tag == 'script': s.inld = False
        if tag == 'h1': s.inh1 = False

    def handle_data(s, data):
        if s.intitle: s.t += data
        if s.inld: s.ld[-1] += data
        if s.inh1: s.h1text += data


def path_of(rel):
    p = '/' + rel
    return p[:-len('index.html')] if p.endswith('index.html') else p


def exists(url_path):
    if url_path in REDIRECTS: return True
    p = url_path.split('#')[0].split('?')[0]
    cand = [p.lstrip('/'), p.lstrip('/') + 'index.html', p.lstrip('/').rstrip('/') + '.html', p.lstrip('/').rstrip('/') + '/index.html']
    return any(os.path.isfile(os.path.join(ROOT, c)) and not ignored(c) for c in cand if c)


issues, pages = [], {}
for f in sorted(glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)):
    rel = os.path.relpath(f, ROOT)
    if ignored(rel) or rel.startswith(('src/', 'tools/', '.claude/')):
        continue
    p = P(); p.feed(open(f, encoding='utf-8').read())
    path = path_of(rel); pages[path] = p
    noindex = 'noindex' in p.metas.get('robots', '')
    W = lambda m: issues.append(f'{path}: {m}')
    if 'tailwindcss.com' in open(f, encoding='utf-8').read(): W('Tailwind Play CDN 사용')
    if noindex: continue
    t = html.unescape(p.t.strip()); d = p.metas.get('description', '')
    if not t: W('title 없음')
    elif len(t) > (65 if p.lang == 'en' else 45) and not re.match(r'/(kr|en)/newsletter/2', path): W(f'title 김 ({len(t)}자)')  # 뉴스레터 제목은 원문 유지
    if not d: W('description 없음')
    elif not (50 if p.lang == 'en' else 35) <= len(d) <= (170 if p.lang == 'en' else 120): W(f'description 길이 {len(d)}자')
    if p.canon != SITE + path: W(f'canonical 불일치: {p.canon}')
    if p.h1 != 1: W(f'h1 {p.h1}개')
    if not p.lang: W('html lang 없음')
    for k in ('og:title', 'og:description', 'og:image', 'og:url'):
        if k not in p.metas: W(f'{k} 없음')
    for b in p.ld:
        try: json.loads(b)
        except Exception as e: W(f'JSON-LD 오류: {e}')
    for im in p.imgs:
        if 'alt' not in im: W(f'img alt 없음: {im.get("src")}')
        if im.get('src', '').startswith('/') and not exists(im['src']): W(f'이미지 없음: {im["src"]}')
    for h in p.a:
        if h.startswith('/') and not exists(h): W(f'깨진 내부 링크: {h}')
    for lang, href in p.alts.items():
        if href.startswith(SITE):
            tp = href[len(SITE):]
            if not exists(tp): W(f'hreflang {lang} 대상 없음: {tp}')

# hreflang 상호 연결
for path, p in pages.items():
    for lang, href in p.alts.items():
        tp = href[len(SITE):] if href.startswith(SITE) else None
        if tp and tp != path and tp in pages and lang != 'x-default':
            back = pages[tp].alts
            if path not in [v[len(SITE):] for v in back.values()]:
                issues.append(f'{path}: hreflang 상대 페이지({tp})가 되돌려 연결하지 않음')

# 중복 title/description
for key in ('title', 'description'):
    seen = {}
    for path, p in pages.items():
        v = p.t.strip() if key == 'title' else p.metas.get('description', '')
        if v and 'noindex' not in p.metas.get('robots', ''): seen.setdefault(v, []).append(path)
    for v, ps in seen.items():
        if len(ps) > 1: issues.append(f'중복 {key}: {ps[:4]}')

# sitemap
sm = re.findall(r'<loc>https://mortgageajae.ca([^<]+)</loc>', open(os.path.join(ROOT, 'sitemap.xml')).read())
for u in sm:
    if u not in pages: issues.append(f'sitemap 주소가 페이지 없음: {u}')
indexable = [p for p, v in pages.items() if 'noindex' not in v.metas.get('robots', '')]
for p in indexable:
    if p not in sm: issues.append(f'sitemap 누락: {p}')

# llms.txt 링크
for u in re.findall(r'https://mortgageajae.ca(/[^)\s]*)', open(os.path.join(ROOT, 'llms.txt')).read()):
    if not exists(u): issues.append(f'llms.txt 깨진 링크: {u}')

print(f'공개 페이지 {len(pages)}개, 색인 대상 {len(indexable)}개, sitemap {len(sm)}개')
print('\n'.join(issues) if issues else '문제 없음')
