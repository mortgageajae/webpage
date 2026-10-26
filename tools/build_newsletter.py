"""뉴스레터 md 폴더 → kr/newsletter/ 정적 페이지 생성.

사용: python3 -I build_newsletter.py <뉴스레터 md 폴더> <웹사이트 저장소 루트>
- `web: yes` 인 호만 만든다.
- 각 호: kr/newsletter/YYYY-MM-DD/index.html, 목록: kr/newsletter/index.html
- 이 스크립트와 md 원본은 공개 저장소에 올리지 않는다 (.claude/ 는 git 제외).
"""
import glob, html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sitekit import SITE, PERSON, shell, jsonld  # noqa: E402

WEEKDAY = '월화수목금토일'


def parse_front(text):
    m = re.match(r'---\n(.*?)\n---\n?(.*)', text, re.S)
    if not m:
        raise ValueError('front matter 없음')
    meta, body, cur = {}, m.group(2), None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if line.startswith((' ', '\t')):                    # sources 아래 들여쓴 줄
            item = re.match(r'^\s+-\s+(.*)$', line)
            if item:
                cur = {}
                meta.setdefault('sources', []).append(cur)
                line = item.group(1)
            k, _, v = line.strip().partition(':')
            if cur is not None:
                cur[k.strip()] = unq(v.strip())
            continue
        k, _, v = line.partition(':')
        k, v = k.strip(), v.strip()
        cur = None
        if not v.startswith('"'):
            v = re.sub(r'\s+#.*$', '', v)
        if v.startswith('[') and v.endswith(']'):
            meta[k] = [x.strip() for x in v[1:-1].split(',') if x.strip()]
        elif v == '':
            meta[k] = []
        else:
            meta[k] = unq(v)
    return meta, body


def unq(v):
    if not v.startswith('"'):
        v = re.sub(r'\s+#.*$', '', v)
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    return v


def esc(s):
    return html.escape(s, quote=True)


HEAD_RE = re.compile(r'^(주요\s*내용\s*요약|핵심\s*요약|의미\s*및\s*시사점|시사점|전망|결론|Key Points|Key Takeaways|Summary|What It Means|What This Means|Implications|Outlook|Conclusion)\s*\??\s*:?$', re.I)
LABEL_RE = re.compile(r'^([^:：]{2,40})[:：]\s+(.+)$')


def inline(s):
    m = LABEL_RE.match(s)
    if m and not re.search(r'https?$', m.group(1)):
        return f'<strong>{esc(m.group(1))}:</strong> {esc(m.group(2))}'
    return esc(s)


def body_html(body):
    lines = [l.rstrip() for l in body.strip().splitlines()]
    # 첫 줄(제목)과 바이라인 제거
    if lines:
        lines = lines[1:]
    lines = [l for i, l in enumerate(lines) if not (i < 3 and 'Mortgage Broker' in l)]
    out, ul, first_p = [], False, True
    for l in lines:
        s = l.strip()
        if not s:
            if ul:
                out.append('</ul>'); ul = False
            continue
        if s in ('-', '•', '·', '*'):  # 내용 없는 글머리표 줄은 건너뜀
            continue
        if HEAD_RE.match(s):
            if ul:
                out.append('</ul>'); ul = False
            out.append(f'<h2>{esc(s.rstrip(":"))}</h2>')
            continue
        bm = re.match(r'^[-•·▪︎]\s*(.+)$', s)
        if bm:
            if not ul:
                out.append('<ul>'); ul = True
            out.append(f'<li>{inline(bm.group(1))}</li>')
            continue
        if ul:
            out.append('</ul>'); ul = False
        cls = ' class="lede"' if first_p else ''
        first_p = False
        out.append(f'<p{cls}>{inline(s)}</p>')
    if ul:
        out.append('</ul>')
    return '\n'.join(out)


def kdate(d, lang='kr'):
    import datetime
    dt = datetime.date.fromisoformat(d)
    if lang == 'kr':
        return f'{dt.year}년 {dt.month}월 {dt.day}일 ({WEEKDAY[dt.weekday()]})'
    return dt.strftime('%A, %B ') + str(dt.day) + dt.strftime(', %Y')


AUTHOR = PERSON

T = {
    'kr': dict(weekly='주간 뉴스레터', brief='뉴스 요약', weekly_s='주간', crumb='뉴스레터', published='발행',
               dated='이 글의 금리·시장 수치와 전망은 발행일 기준이며, 지금과 다를 수 있습니다. 최신 상황은 상담에서 확인해 주세요.',
               refs='참고 자료', refs_p='이 글은 아래 자료와 필자의 분석·의견을 함께 담고 있습니다.', checked='확인',
               prev='← 이전 호', next='다음 호', pager='이전·다음 호', suffix=' | 모기지아재 뉴스레터',
               month=lambda y, m: f'{y}년 {m}월', site='모기지아재',
               hero_h='금리·정책 변화,<br><span class="b">매주 정리해 드려요</span>',
               hero_p='매주 목요일 아침 카카오톡 단톡방에 올리는 모기지 뉴스레터를 모아 두었습니다. 각 글의 수치와 전망은 발행일 기준입니다.',
               list_title='주간 뉴스레터 | 모기지아재', list_name='모기지아재 주간 뉴스레터',
               list_desc='BC주 모기지 브로커 모기지아재가 매주 목요일 정리하는 캐나다 금리·BoC·국채금리·BC 주택정책 뉴스레터 모음. 각 호는 발행일 기준입니다.',
               translated=''),
    'en': dict(weekly='Weekly newsletter', brief='News brief', weekly_s='Weekly', crumb='Newsletter', published='published',
               dated='Rates, market figures and outlooks in this article reflect its publication date and may differ today. Ask us for the latest picture.',
               refs='References', refs_p='This article combines the sources below with the author\'s own analysis and opinion.', checked='checked',
               prev='← Previous', next='Next', pager='Previous and next issues', suffix=' | Mortgageajae Newsletter',
               month=lambda y, m: __import__('datetime').date(int(y), int(m), 1).strftime('%B %Y'), site='Mortgageajae',
               hero_h='Rates and policy,<br><span class="b">explained every week</span>',
               hero_p='Our weekly mortgage newsletter on the Bank of Canada, bond yields and BC housing policy, translated from the Korean edition. Each issue reflects its publication date.',
               list_title='Weekly Mortgage Newsletter | Mortgageajae', list_name='Mortgageajae Weekly Newsletter',
               list_desc='Weekly notes from BC mortgage broker Justin Bae on Bank of Canada decisions, bond yields, mortgage rates and BC housing policy. Each issue reflects its publication date.',
               translated='Translated from the <a href="{ko}">Korean original</a>.'),
}


def load(src, pattern):
    issues = []
    for p in sorted(glob.glob(os.path.join(src, pattern))):
        meta, body = parse_front(open(p, encoding='utf-8').read())
        if str(meta.get('web', 'yes')).lower() != 'yes':
            continue
        meta['body'] = body
        issues.append(meta)
    issues.sort(key=lambda m: m['date'])
    return issues


def short_date(d, lang):
    """목록용 날짜: 한글 2026.10.22 / 영문 Oct 22, 2026"""
    import datetime
    dt = datetime.date.fromisoformat(d)
    return f'{dt.year}.{dt.month}.{dt.day}' if lang == 'kr' else dt.strftime('%b ') + str(dt.day) + dt.strftime(', %Y')


def short(text, n):
    return text if len(text) <= n else text[:n - 3].rstrip() + '…'


def build(src, root, lang='kr', other=None):
    """lang 판 뉴스레터를 만든다. other = 다른 언어판에 있는 날짜 집합 (hreflang 연결용)."""
    L = T[lang]
    issues = load(src, '20??-??-??_*.md' if lang == 'kr' else '20??-??-??.md')
    other = other or set()
    alt_lang, alt_dir = ('en', 'en') if lang == 'kr' else ('ko', 'kr')
    base = f'/{lang}/newsletter/'
    outdir = os.path.join(root, lang, 'newsletter')
    os.makedirs(outdir, exist_ok=True)
    for i, m in enumerate(issues):
        d = m['date']
        url = f'{SITE}{base}{d}/'
        prev_i = issues[i - 1] if i > 0 else None
        next_i = issues[i + 1] if i + 1 < len(issues) else None
        kind = L['weekly'] if m.get('type') != 'brief' else L['brief']
        srcs = [s for s in m.get('sources', []) if isinstance(s, dict) and s.get('url')]
        src_html = ''
        if srcs:
            items = '\n'.join(f'<li><a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s.get("name") or s["url"])}</a>'
                              + (f' <span>({L["checked"]} {esc(s["checked"])})</span>' if s.get('checked') else '') + '</li>' for s in srcs)
            src_html = f'<section class="sources"><h2>{L["refs"]}</h2><p>{L["refs_p"]}</p><ol>\n{items}\n</ol></section>'
        pager = f'<nav class="pager" aria-label="{L["pager"]}">'
        pager += (f'<a class="prev" href="{base}{prev_i["date"]}/"><small>{L["prev"]} · {prev_i["date"]}</small>{esc(prev_i["title"])}</a>' if prev_i else '<span></span>')
        pager += (f'<a class="next" href="{base}{next_i["date"]}/"><small>{L["next"]} · {next_i["date"]} →</small>{esc(next_i["title"])}</a>' if next_i else '<span></span>')
        pager += '</nav>'
        pub = f'{kdate(d, lang)} {L["published"]}' if lang == 'kr' else f'Published {kdate(d, lang)}'
        tr = (' ' + L['translated'].format(ko=f'/kr/newsletter/{d}/')) if L['translated'] and d in other else ''
        body = f'''<div class="wrap crumb"><a href="{base}">{L["crumb"]}</a> › {d}</div>
<article class="article">
  <span class="chip">{kind}</span>
  <h1 class="disp">{esc(m['title'])}</h1>
  <p class="dated"><strong>{pub}</strong> · {L["dated"]}{tr}</p>
{body_html(m['body'])}
  <div class="sig"><b>Justin Bae, M.Sc., P.Eng.</b><br>Mortgage Broker (BCFSA MB610304) · Huntington Cross Mortgage</div>
  {src_html}
  {pager}
</article>'''
        ld = jsonld({'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': m['title'],
                     'description': m.get('summary', ''), 'datePublished': d, 'inLanguage': 'ko' if lang == 'kr' else 'en',
                     'mainEntityOfPage': url, 'author': AUTHOR,
                     'publisher': {'@type': 'Organization', 'name': L['site'], 'logo': {'@type': 'ImageObject', 'url': SITE + '/images/logo-face-160.png'}},
                     **({'citation': [s['url'] for s in srcs]} if srcs else {}),
                     **({'translationOfWork': {'@id': f'{SITE}/kr/newsletter/{d}/'}} if lang == 'en' and d in other else {})})
        alts = None
        if d in other:
            alts = {'ko': f'/kr/newsletter/{d}/', 'en': f'/en/newsletter/{d}/'}
        title = m['title'] if len(m['title']) > (40 if lang == 'kr' else 55) else m['title'] + L['suffix']
        os.makedirs(os.path.join(outdir, d), exist_ok=True)
        with open(os.path.join(outdir, d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(shell(lang=lang, title=title, description=short(m.get('summary', ''), 115 if lang == 'kr' else 160),
                          path=f'{base}{d}/', body=body, extra_head=ld, og_type='article', active=base, alternates=alts,
                          og_image=f'/images/og/og-newsletter-{"kr" if lang == "kr" else "en"}.png'))
    # 목록
    months = {}
    for m in reversed(issues):
        months.setdefault(m['date'][:7], []).append(m)
    blocks = []
    for ym, ms in months.items():
        y, mo = ym.split('-')
        items = '\n'.join(
            f'<li class="nl-item"><a href="{base}{m["date"]}/"><div class="nl-date">{short_date(m["date"], lang)}'
            f'<small>{L["weekly_s"] if m.get("type") != "brief" else L["brief"]}</small></div>'
            f'<div><h3>{esc(m["title"])}</h3><p>{esc(m.get("summary", ""))}</p></div></a></li>' for m in ms)
        blocks.append(f'<section class="nl-month"><h2 class="disp">{L["month"](y, int(mo))}</h2><ul class="nl-list">\n{items}\n</ul></section>')
    body = f'''<section class="nl-hero"><div class="wrap">
  <span class="chip">{L["weekly"]}</span>
  <h1 class="disp">{L["hero_h"]}</h1>
  <p>{L["hero_p"]}</p>
</div></section>
<div class="wrap">
{chr(10).join(blocks)}
</div>'''
    ld = jsonld({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': L['list_name'],
                 'url': f'{SITE}{base}', 'inLanguage': 'ko' if lang == 'kr' else 'en', 'author': AUTHOR,
                 'hasPart': [{'@type': 'BlogPosting', 'headline': m['title'], 'url': f'{SITE}{base}{m["date"]}/', 'datePublished': m['date']} for m in issues]})
    alts = {'ko': '/kr/newsletter/', 'en': '/en/newsletter/'} if other else None
    with open(os.path.join(outdir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(shell(lang=lang, title=L['list_title'], description=L['list_desc'], path=base, body=body, extra_head=ld,
                      active=base, alternates=alts, og_image=f'/images/og/og-newsletter-{"kr" if lang == "kr" else "en"}.png'))
    # 홈 화면·사이트맵에서 쓸 목록 데이터 (배포 제외 폴더)
    os.makedirs(os.path.join(root, 'tools', 'data'), exist_ok=True)
    with open(os.path.join(root, 'tools', 'data', f'newsletters{"" if lang == "kr" else "-en"}.json'), 'w', encoding='utf-8') as f:
        json.dump([{k: m.get(k) for k in ('date', 'type', 'title', 'summary')} for m in reversed(issues)], f, ensure_ascii=False, indent=1)
    return issues


if __name__ == '__main__':
    src, root = sys.argv[1], sys.argv[2]
    en_dir = os.path.join(src, 'en')
    en_dates = {m['date'] for m in load(en_dir, '20??-??-??.md')} if os.path.isdir(en_dir) else set()
    kr = build(src, root, 'kr', en_dates)
    print(len(kr), 'kr issues;', sum(1 for m in kr if m.get('sources')), 'with sources')
    if en_dates:
        en = build(en_dir, root, 'en', {m['date'] for m in kr})
        print(len(en), 'en issues')
