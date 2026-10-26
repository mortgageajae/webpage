"""(1회용) kr/*.html 계산기 → src/kr/calculators/<slug>.html 조각 + src/css/calc/<slug>.css.

iframe 안에서 돌던 옛 계산기 파일을 단독 페이지용 조각으로 바꾼다. 옛 파일은 지우지 않는다.
사용: python3 -I tools/migrate_calculators.py kr|en
이미 있는 src 조각은 덮어쓰지 않는다 (옮긴 뒤 고친 내용 보호).
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 옛 파일 → (새 주소 조각, 제목, 설명)
PAGES = {
    'budget-calculator': ('calculators/budget', '주택구매 종합 예산 계산기',
        'BC주 주택 구매 시 다운페이, 취득세(PTT), 모기지 보험료(CMHC), 제반 비용까지 클로징에 필요한 총 현금과 월 페이먼트를 계산합니다.'),
    'core-tools': ('calculators/affordability', '대출한도·페이먼트 계산기',
        'GDS/TDS와 스트레스 테스트 기준으로 받을 수 있는 최대 모기지 한도와 상환 주기별(월납·격주납) 페이먼트를 계산합니다.'),
    'benefit-diagnosis': ('calculators/government-benefits', '정부혜택 자격진단',
        'BC 첫 주택 구매자·신축 취득세(PTT) 면제, 신축 GST 리베이트, FHSA, RRSP HBP, Eco Plus 환급 자격과 금액을 점검합니다.'),
    'insured-analysis': ('calculators/insured-vs-conventional', 'Insured 수익성 분석',
        '다운페이 20% 이상이 가능해도 Insured(보험) 모기지로 낮은 금리를 받는 것이 유리한지 보험료와 이자를 비교합니다.'),
    'rate-diagnosis': ('calculators/rate-check', '모기지 금리진단',
        '제안받은 모기지 금리가 BC 시장 조건과 비교해 좋은 조건인지 진단하고 맞춤 리포트를 받아 보세요.'),
    'varvsfix': ('calculators/fixed-vs-variable', '변동 vs 고정 금리 비교',
        '프라임 금리 변화 시나리오별로 변동금리와 고정금리의 페이먼트와 총 이자비용, 트리거 레이트를 비교합니다.'),
    'switch': ('calculators/switch', '모기지 환승(스위치) 분석',
        '기존 모기지를 다른 금융기관으로 옮길 때 페널티와 남은 기간 이자 절감액을 비교하고 Insurable 여부를 확인합니다.'),
    'debt-consolidation': ('calculators/debt-consolidation', '부채통합 분석',
        '신용카드·자동차 할부 등 고금리 부채를 모기지 리파이낸스로 합칠 때 페널티를 감안한 월 현금흐름 변화를 계산합니다.'),
    'retirement': ('calculators/retirement', '은퇴 재정설계',
        '모기지 상환, 주택 자산, CPP·OAS·RRIF와 세금을 함께 고려해 은퇴 후 현금흐름을 시뮬레이션합니다.'),
    'discovery': ('consultation', '1:1 상담 예약',
        '모기지아재 Justin Bae와의 1:1 화상 사전상담을 예약하세요. 상황을 미리 알려주시면 맞춤 전략을 준비해 드립니다.'),
    'board': ('columns', '모기지 칼럼',
        'BC주 부동산 시장 동향과 모기지 정보를 정리한 모기지아재 칼럼.'),
    'bank-links': ('bank-rates', '주요 은행 금리 바로가기',
        '캐나다 주요 은행의 공식 모기지 금리 페이지 모음.'),
}
EN = {
    'budget-calculator': ('Home Purchase Budget Calculator', 'Calculate the total cash you need to close on a BC home: down payment, property transfer tax, CMHC insurance premium and closing costs, plus your monthly payment.'),
    'core-tools': ('Mortgage Affordability & Payment Calculator', 'Find your maximum mortgage under GDS/TDS and the stress test, and compare monthly, bi-weekly and accelerated payments.'),
    'benefit-diagnosis': ('Government Benefits Eligibility Check', 'Check eligibility and amounts for BC first-time buyer and newly built PTT exemptions, the new-home GST rebate, FHSA, RRSP Home Buyers\' Plan and Eco Plus refunds.'),
    'insured-analysis': ('Insured vs Conventional Mortgage Analysis', 'Even with 20% down available, see whether an insured mortgage at a lower rate beats a 20%-down conventional mortgage after the premium.'),
    'rate-diagnosis': ('Mortgage Rate Check', 'See whether the mortgage rate you were offered is competitive for BC and get a personalized report.'),
    'varvsfix': ('Fixed vs Variable Rate Comparison', 'Compare fixed and variable mortgages under prime-rate scenarios: payments, total interest and trigger rate.'),
    'switch': ('Mortgage Switch Analysis', 'Compare the penalty and the interest saved when switching your mortgage to another lender, and check whether it stays insurable.'),
    'debt-consolidation': ('Debt Consolidation Analysis', 'See how rolling credit-card and car-loan debt into a mortgage refinance changes your monthly cash flow, including the prepayment penalty.'),
    'retirement': ('Retirement Planning Calculator', 'Model retirement cash flow with your mortgage, home equity, CPP, OAS, RRIF withdrawals and taxes.'),
    'discovery': ('Book a 1:1 Consultation', 'Book a 1:1 video discovery call with Justin Bae, BC mortgage broker. Share your situation ahead of time so we can prepare a strategy.'),
    'board': ('Mortgage Columns', 'BC housing market and mortgage notes from Mortgageajae.'),
    'bank-links': ('Major Bank Rate Links', 'Links to the official mortgage rate pages of Canada\'s major banks.'),
}


def links(lang):
    m = {'bank-links.html': f'/{lang}/bank-rates/', 'discovery.html': f'/{lang}/consultation/'}
    for old, (new, _, _) in PAGES.items():
        m.setdefault(old + '.html', f'/{lang}/{new}/')
    return m


def migrate(old, new, title, desc, lang='kr'):
    s = open(os.path.join(ROOT, lang, old + '.html'), encoding='utf-8').read()
    head, body = s.split('<body', 1)
    body = body.split('>', 1)[1].rsplit('</body>', 1)[0]
    tw = '\n'.join(re.findall(r'<style type="text/tailwindcss">(.*?)</style>', head, re.S))
    plain = '\n'.join(re.findall(r'<style>(.*?)</style>', head, re.S))
    ext = [u for u in re.findall(r'<script src="([^"]+)"', head) if 'tailwindcss' not in u and 'googletagmanager' not in u]
    ext = [u.replace('npm/chart.js"', 'npm/chart.js@4.4.1/dist/chart.umd.min.js"') if u.endswith('npm/chart.js') else u for u in ext]
    ext = ['https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js' if u == 'https://cdn.jsdelivr.net/npm/chart.js' else
           'https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js' if u == 'https://cdn.jsdelivr.net/npm/marked/marked.min.js' else u for u in ext]
    # head 의 인라인 스크립트 중 gtag·tailwind 설정이 아닌 것
    inl = [x for x in re.findall(r'<script>(.*?)</script>', head, re.S) if 'gtag(' not in x and 'tailwind.config' not in x]
    for a, b in links(lang).items():
        body = body.replace(f'href="{a}"', f'href="{b}"')
    slug = new.split('/')[-1]
    head_html = f'<link rel="stylesheet" href="/assets/css/calc/{slug}.css">\n'
    head_html += ''.join(f'<script src="{u}"></script>\n' for u in ext)
    if plain.strip():
        head_html += f'<style>{plain}</style>\n'
    head_html += ''.join(f'<script>{x}</script>\n' for x in inl)
    site = '모기지아재' if lang == 'kr' else 'Mortgageajae'
    meta = {'out': f'{lang}/{new}/index.html', 'lang': lang, 'path': f'/{lang}/{new}/', 'title': f'{title} | {site}',
            'description': desc, 'head': head_html, 'calc_css': slug,
            'alternates': {'ko': f'/kr/{new}/', 'en': f'/en/{new}/'}}
    dst = os.path.join(ROOT, 'src', lang, new + '.html')
    if os.path.exists(dst):
        print('이미 있음, 건너뜀:', dst)
        return slug
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('<!--meta ' + json.dumps(meta, ensure_ascii=False) + ' -->\n<div class="calc-page">\n' + body.strip() + '\n</div>\n')
    os.makedirs(os.path.join(ROOT, 'src', 'css', 'calc'), exist_ok=True)
    if lang != 'kr':  # CSS 입력 파일은 한글판 것을 공용으로 사용
        return slug
    with open(os.path.join(ROOT, 'src', 'css', 'calc', slug + '.css'), 'w', encoding='utf-8') as f:
        f.write('@tailwind base;\n@tailwind components;\n@tailwind utilities;\n' + tw + '\n')
    return slug


if __name__ == '__main__':
    import sys
    lang = sys.argv[1] if len(sys.argv) > 1 else 'kr'
    for old, (new, title, desc) in PAGES.items():
        if lang == 'en':
            if not os.path.exists(os.path.join(ROOT, 'en', old + '.html')):
                continue
            title, desc = EN[old]
        print(old, '→', migrate(old, new, title, desc, lang))
