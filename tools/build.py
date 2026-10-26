"""src/ 의 페이지 조각 → 공용 틀을 씌워 실제 경로에 생성.

사용: python3 -I tools/build.py   (저장소 루트에서)
각 src 파일 맨 위:  <!--meta {"out": "kr/index.html", "lang": "kr", "title": "...", "description": "...",
                           "path": "/kr/", "alternates": {"ko": "/kr/", "en": "/en/"}, "head": "...", "cta": true} -->
본문 안의 {{latest_newsletters}} 는 최근 뉴스레터 3개 목록으로 바뀐다 (tools/data/newsletters.json).
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sitekit import esc, shell  # noqa: E402
from build_newsletter import short_date  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def latest_newsletters(n=3, lang='kr'):
    p = os.path.join(ROOT, 'tools', 'data', 'newsletters.json' if lang == 'kr' else 'newsletters-en.json')
    if not os.path.exists(p):
        return ''
    items = json.load(open(p, encoding='utf-8'))[:n]
    return '<ul class="home-nl">\n' + '\n'.join(
        f'<li><a href="/{lang}/newsletter/{m["date"]}/"><span class="d">{short_date(m["date"], lang)}</span>'
        f'<span class="t">{esc(m["title"])}</span></a></li>' for m in items) + '\n</ul>'


REVIEWED = '2026-10-25'  # 계산기 규정·수치를 마지막으로 공식 자료와 대조한 날


def calculator_extras(meta, body):
    """계산기 페이지: 확인 기준일 표시 + 검색엔진·AI용 구조화 정보(WebApplication)."""
    ko = meta['lang'] == 'kr'
    y, mo, d = REVIEWED.split('-')
    note = (f'<p class="reviewed">계산 기준: {y}년 {int(mo)}월 {int(d)}일 공식 자료(CRA·CMHC·BC 정부 등)와 대조해 확인했습니다. '
            '결과는 참고용 추정치이며 실제 승인 조건은 금융기관마다 다릅니다.</p>' if ko else
            f'<p class="reviewed">Rules and figures last checked against official sources (CRA, CMHC, BC government) on '
            f'{REVIEWED}. Results are estimates for reference only; actual approval terms vary by lender.</p>')
    ld = {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': meta['title'].split(' | ')[0],
          'description': meta['description'], 'url': 'https://mortgageajae.ca' + meta['path'],
          'applicationCategory': 'FinanceApplication', 'operatingSystem': 'Any', 'browserRequirements': 'Requires JavaScript',
          'inLanguage': 'ko' if ko else 'en', 'isAccessibleForFree': True, 'dateModified': REVIEWED,
          'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'CAD'},
          'areaServed': {'@type': 'AdministrativeArea', 'name': 'British Columbia, Canada'},
          'author': {'@id': 'https://mortgageajae.ca/#justin', '@type': 'Person', 'name': 'Justin Bae'}}
    tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>\n'
    return tag + body.rstrip() + '\n<div class="wrap">' + note + '</div>\n'


def build():
    made, pages = [], []
    for src in sorted(glob.glob(os.path.join(ROOT, 'src', '**', '*.html'), recursive=True)):
        text = open(src, encoding='utf-8').read()
        m = re.match(r'\s*<!--meta\s*(\{.*?\})\s*-->\n?(.*)', text, re.S)
        if not m:
            print('meta 없음, 건너뜀:', src)
            continue
        meta, body = json.loads(m.group(1)), m.group(2)
        body = body.replace('{{latest_newsletters}}', latest_newsletters(lang=meta['lang']))
        if '/calculators/' in meta['path']:
            body = calculator_extras(meta, body)
        out = os.path.join(ROOT, meta['out'])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(shell(lang=meta['lang'], title=meta['title'], description=meta['description'], path=meta['path'],
                          body=body.strip(), alternates=meta.get('alternates'), extra_head=meta.get('head', ''),
                          active=meta.get('active'), cta=meta.get('cta', True), robots=meta.get('robots'),
                          og_image=meta.get('og_image')))
        made.append(meta['out'])
        if not meta.get('robots'):
            pages.append(meta['path'])
    print(len(made), 'pages:', ', '.join(made))
    write_sitemap(pages)


def write_sitemap(pages):
    import datetime
    today = datetime.date.today().isoformat()
    urls = [(p, today) for p in pages] + [('/kr/newsletter/', today)]
    for lang, fn in (('kr', 'newsletters.json'), ('en', 'newsletters-en.json')):
        p = os.path.join(ROOT, 'tools', 'data', fn)
        if os.path.exists(p):
            urls += [(f'/{lang}/newsletter/', today)] if lang == 'en' else []
            urls += [(f'/{lang}/newsletter/{m["date"]}/', m['date']) for m in json.load(open(p, encoding='utf-8'))]
    body = '\n'.join(f'  <url><loc>https://mortgageajae.ca{u}</loc><lastmod>{d}</lastmod></url>' for u, d in urls)
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '\n</urlset>\n')
    print('sitemap:', len(urls), 'urls')


if __name__ == '__main__':
    build()
