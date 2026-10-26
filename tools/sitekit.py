"""공용 페이지 틀 (머리말·꼬리말·상담 띠). 모든 생성 스크립트가 이 함수를 쓴다."""
import hashlib, html, json, os, re

SITE = 'https://mortgageajae.ca'
GA = 'G-LPHD8XR0XD'
FONTS = 'https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Gowun+Dodum&display=swap'

NAV = {
    'kr': [('계산기', '/kr/#tools'), ('뉴스레터', '/kr/newsletter/'), ('카드뉴스', '/kr/#insights')],
    'en': [('Calculators', '/en/#tools'), ('Newsletter', '/en/newsletter/')],
}
TXT = {
    'kr': dict(book='상담 예약', book_url='/kr/consultation/', home='/kr/',
               cta_h='계산 결과가 복잡하다면?', cta_p='고객님 상황을 꼼꼼히 분석해, 놓치기 쉬운 혜택까지 챙긴 맞춤 전략을 세워드립니다.',
               cta_btn='1:1 화상상담 신청하기 →', note='일반 정보 제공 목적이며 개인 상담을 대체하지 않습니다.',
               privacy=('개인정보 처리방침', '/kr/privacy/'), menu='주요 메뉴'),
    'en': dict(book='Book a call', book_url='/en/consultation/', home='/en/',
               cta_h='Need help reading the numbers?', cta_p='Get a strategy built around your situation, including the benefits that are easy to miss.',
               cta_btn='Book a 1:1 video call →', note='For general information only; not a substitute for personal advice.',
               privacy=('Privacy policy', '/en/privacy/'), menu='Main menu'),
}


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bust(page):
    """/assets/css/*.css 링크에 내용 해시를 붙여 캐시된 옛 CSS가 쓰이지 않게 한다."""
    def rep(m):
        f = os.path.join(ROOT, m.group(1).lstrip('/'))
        if not os.path.exists(f):
            return m.group(0)
        h = hashlib.md5(open(f, 'rb').read()).hexdigest()[:8]
        return f'href="{m.group(1)}?v={h}"'
    return re.sub(r'href="(/assets/css/[^"?]+\.css)"', rep, page)


def esc(s):
    return html.escape(s or '', quote=True)


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>\n'


PERSON = {'@type': 'Person', '@id': SITE + '/#justin', 'name': 'Justin Bae', 'honorificSuffix': 'M.Sc., P.Eng.',
          'jobTitle': 'Mortgage Broker', 'url': SITE + '/kr/', 'image': SITE + '/images/profile-1000.jpg',
          'knowsLanguage': ['ko', 'en'], 'areaServed': {'@type': 'AdministrativeArea', 'name': 'British Columbia, Canada'},
          'hasCredential': {'@type': 'EducationalOccupationalCredential', 'credentialCategory': 'license',
                            'name': 'Mortgage Broker registration (BCFSA) MB610304',
                            'recognizedBy': {'@type': 'Organization', 'name': 'BC Financial Services Authority', 'url': 'https://www.bcfsa.ca'}},
          'worksFor': {'@type': 'Organization', 'name': 'Huntington Cross Mortgage'}}


def shell(*, lang, title, description, path, body, alternates=None, extra_head='', og_type='website',
          active=None, cta=True, robots=None, og_image=None):
    t = TXT[lang]
    url = SITE + path
    if not og_image:
        og_image = '/images/og/og-kr.png' if lang == 'kr' else '/images/og/og-en.png'
    alt = ''
    if alternates:  # {'ko': '/kr/..', 'en': '/en/..'}
        alt = ''.join(f'<link rel="alternate" hreflang="{k}" href="{SITE}{v}">\n' for k, v in alternates.items())
        alt += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alternates.get("en", path)}">\n'
    nav = '\n      '.join(f'<a href="{u}"' + (' aria-current="page"' if active == u else '') + f'>{esc(n)}</a>' for n, u in NAV[lang])
    other = (alternates or {}).get('en' if lang == 'kr' else 'ko', '/en/' if lang == 'kr' else '/kr/')
    kor, eng = (('class="on" href="' + path + '"', 'href="' + other + '"') if lang == 'kr'
                else ('href="' + other + '"', 'class="on" href="' + path + '"'))
    cta_html = f'''<section class="cta">
  <div class="wrap">
    <div>
      <h2 class="disp">{esc(t["cta_h"])}</h2>
      <p>{esc(t["cta_p"])}</p>
    </div>
    <a class="pill yellow" href="{t["book_url"]}">{esc(t["cta_btn"])}</a>
  </div>
</section>
''' if cta else ''
    return bust(f'''<!DOCTYPE html>
<html lang="{'ko' if lang == 'kr' else 'en'}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{f'<meta name="robots" content="{robots}">' + chr(10) if robots else ''}<link rel="canonical" href="{url}">
{alt}<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{SITE}{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)}">
<meta property="og:locale" content="{'ko_KR' if lang == 'kr' else 'en_CA'}">
<meta name="twitter:card" content="summary_large_image">
<meta property="og:site_name" content="{'모기지아재' if lang == 'kr' else 'Mortgageajae'}">
<link rel="icon" href="/images/logo-face-160.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
{extra_head}</head>
<body>
<header class="site-header">
  <div class="wrap nav">
    <a class="brand" href="{t["home"]}"><img src="/images/logo-face-160.png" alt="" width="31" height="44"><span>{'모기지아재' if lang == 'kr' else 'Mortgageajae'}</span></a>
    <nav class="nav-links" aria-label="{t["menu"]}">
      {nav}
    </nav>
    <div class="lang"><a {kor}>KOR</a><a {eng}>ENG</a></div>
    <a class="pill" href="{t["book_url"]}">{esc(t["book"])}</a>
  </div>
</header>
<main>
{body}
</main>
{cta_html}<footer class="site-footer">
  <div class="wrap">
    <div class="rule">
      <div><strong>Justin Bae, M.Sc., P.Eng.</strong><br>Mortgage Broker (BCFSA MB610304)<br>Huntington Cross Mortgage</div>
      <div>Email: mortgageajae@gmail.com · Phone: 250-581-6862<br>KakaoTalk: mortgageajae · @mortgageajae<br><a href="{t["privacy"][1]}">{esc(t["privacy"][0])}</a></div>
    </div>
    <p class="note">{esc(t["note"])} © 2026 Mortgageajae</p>
  </div>
</footer>
</body>
</html>
''')
