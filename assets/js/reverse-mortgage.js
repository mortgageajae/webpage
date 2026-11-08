/* 리버스모기지 예상 한도 계산기 (kr/en 공용).
 * 계산 근거: BC 주요 리버스모기지 렌더 4곳의 브로커 계산기를 2026-11-06~07 조사한 값(나이·지역 등급·주택 유형·주택가별).
 * 렌더 이름은 쓰지 않고 "예상 범위"로만 보여준다. 실제 한도는 감정평가·심사로 정해진다.
 */
(function () {
  'use strict';
  var KO = document.documentElement.lang === 'ko';

  // ---- 조사 데이터 (LTV %, 주택가 $1M 단독주택 기준) -------------------------------
  // 렌더 A·B(같은 표): 지역 등급 1~3, 나이 기준점 사이는 직선 보간, 85세 이상 동일
  var AGES = [55, 60, 65, 70, 75, 80, 85];
  var A_STD = { 1: [20, 37, 40, 44.05, 51, 55, 55], 2: [16, 29, 34, 40, 46, 52, 52], 3: [10, 22, 25, 31, 39, 45, 51] };
  var A_PLUS = { 1: [null, null, null, 48.46, 56, 59, 59], 2: [null, null, null, 44, 51, 57, 57], 3: [null, null, null, 35, 43, 53, 56] };
  // 렌더 C: 나이별 [일반, 70+ 고한도], 지역은 우편번호별 차감(0/5/13, 고한도는 13→18)
  var C_STD = [20, 20, 20, 20, 20, 39, 39, 39, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 53, 55, 56]; // 55~80, 이후 56
  var C_PLUS = { 70: 50, 71: 51, 72: 52, 73: 53, 74: 54, 75: 55, 76: 56, 77: 57, 78: 58, 79: 59 }; // 80+ 60
  // 렌더 D: 지역 A~D. A는 나이별(1세 단위), B~D는 기준점 보간. 70세 미만은 다른 렌더와 차이가 커서 확인 전까지 범위에서 제외
  var D_A = [40.75, 41.15, 41.65, 42.05, 42.45, 42.95, 43.35, 43.75, 44.25, 44.65, 45.05, 45.55, 46.15, 46.65, 47.05, 47.55, 48.15, 48.95, 49.75, 50.75, 51.75, 52.85, 53.6]; // 55~77, 이후 53.6
  var D_ANCH = { B: [28.45, 32, 35.55, 40.75, 47.65, 55, 55], C: [22.75, 25.9, 29.05, 34.65, 42.05, 50.25, 53.9], D: [19.95, 22.8, 25.65, 30.75, 37.55, 45.05, 52.25] };
  var D_CAP = { A: 55, B: 55, C: 53.9, D: 52.25 };
  var D_PLUS = { A: [null, null, null, 54.55, 59, 59, 59], B: [null, null, null, 45.35, 51.65, 59, 59] };

  // 도시: [표시 이름 ko, en, 렌더A 등급(0=취급 안 함), 렌더C 차감, 렌더D 등급]
  var CITIES = [
    ['밴쿠버', 'Vancouver', 1, 0, 'A'], ['노스밴쿠버', 'North Vancouver', 1, 0, 'A'], ['웨스트밴쿠버', 'West Vancouver', 1, 0, 'A'],
    ['버나비', 'Burnaby', 1, 0, 'A'], ['리치먼드', 'Richmond', 1, 0, 'A'], ['써리', 'Surrey', 1, 0, 'A'], ['델타', 'Delta', 1, 0, 'A'],
    ['화이트락', 'White Rock', 1, 0, 'A'], ['랭리', 'Langley', 1, 0, 'A'], ['코퀴틀람', 'Coquitlam', 1, 0, 'A'],
    ['포트코퀴틀람', 'Port Coquitlam', 1, 0, 'A'], ['포트무디', 'Port Moody', 1, 0, 'A'], ['뉴웨스트민스터', 'New Westminster', 1, 0, 'A'],
    ['메이플릿지', 'Maple Ridge', 1, 0, 'A'], ['핏메도스', 'Pitt Meadows', 1, 0, 'A'],
    ['애버츠퍼드', 'Abbotsford', 2, 0, 'A'], ['미션', 'Mission', 2, 0, 'A'], ['칠리왁', 'Chilliwack', 2, 0, 'A'], ['스쿼미시', 'Squamish', 2, 0, 'C'],
    ['빅토리아', 'Victoria', 1, 0, 'A'], ['사니치', 'Saanich', 1, 0, 'A'], ['오크베이', 'Oak Bay', 1, 0, 'A'], ['에스퀴말트', 'Esquimalt', 1, 0, 'A'],
    ['랭포드', 'Langford', 1, 0, 'A'], ['콜우드', 'Colwood', 1, 0, 'A'], ['시드니', 'Sidney', 1, 5, 'A'], ['수크', 'Sooke', 3, 5, 'B'],
    ['켈로나', 'Kelowna', 1, 5, 'A'], ['웨스트켈로나', 'West Kelowna', 1, 5, 'B'], ['레이크컨트리', 'Lake Country', 2, 5, 'B'],
    ['버논', 'Vernon', 3, 5, 'C'], ['펜틱턴', 'Penticton', 3, 5, 'C'], ['서머랜드', 'Summerland', 3, 13, 'B'],
    ['캠룹스', 'Kamloops', 2, 5, 'B'], ['나나이모', 'Nanaimo', 2, 5, 'B'], ['팍스빌', 'Parksville', 3, 5, 'B'], ['퀄리컴비치', 'Qualicum Beach', 3, 5, 'B'],
    ['코트니', 'Courtenay', 3, 5, 'B'], ['코목스', 'Comox', 3, 5, 'B'], ['캠벨리버', 'Campbell River', 3, 5, 'C'], ['던컨', 'Duncan', 3, 5, 'C'],
    ['레이디스미스', 'Ladysmith', 3, 13, 'C'], ['휘슬러', 'Whistler', 3, 5, 'B'], ['시셸트', 'Sechelt', 3, 0, 'B'], ['깁슨스', 'Gibsons', 3, 0, 'B'],
    ['호프', 'Hope', 3, 13, 'B'], ['새먼암', 'Salmon Arm', 0, 13, 'C'], ['파월리버', 'Powell River', 0, 13, 'B'], ['포트앨버니', 'Port Alberni', 0, 13, 'C'],
    ['넬슨', 'Nelson', 0, 13, 'B'], ['캐슬가', 'Castlegar', 0, 13, 'B'], ['트레일', 'Trail', 0, 13, 'B'], ['크랜브룩', 'Cranbrook', 0, 13, 'C'],
    ['레벨스토크', 'Revelstoke', 0, 13, 'C'], ['골든', 'Golden', 0, 13, 'C'], ['메릿', 'Merritt', 0, 13, 'C'], ['오소유스', 'Osoyoos', 0, 13, 'B'],
    ['프린스조지', 'Prince George', 0, 13, 'C'], ['퀘스넬', 'Quesnel', 0, 13, 'C'], ['윌리엄스레이크', 'Williams Lake', 0, 13, 'B'],
    ['포트세인트존', 'Fort St. John', 0, 13, 'D'], ['도슨크릭', 'Dawson Creek', 0, 13, 'D'], ['테라스', 'Terrace', 0, 13, 'C'],
    ['프린스루퍼트', 'Prince Rupert', 0, 13, 'C'], ['스미더스', 'Smithers', 0, 13, 'C'], ['그 밖의 BC 지역', 'Other BC area', 0, 13, 'C']
  ];

  var COSTS = 995 + 1500; // 셋업 수수료 + 법무비(등기 약 $1,000 + ILA 약 $500), 감정비 별도

  function interp(points, age) {
    if (age <= AGES[0]) return points[0];
    for (var i = 1; i < AGES.length; i++) {
      if (age <= AGES[i]) {
        var a = points[i - 1], b = points[i];
        if (a == null || b == null) return b == null ? null : (age === AGES[i] ? b : null);
        return a + (b - a) * (age - AGES[i - 1]) / (AGES[i] - AGES[i - 1]);
      }
    }
    return points[points.length - 1];
  }

  // 주택가가 $2M를 넘으면 렌더들이 LTV를 줄인다: $500k마다 약 1.5%p, 최대 6%p
  function valuePenalty(v) { return v > 2e6 ? Math.min(6, 1.5 * Math.ceil((v - 2e6) / 5e5)) : 0; }

  // 공동명의: 렌더 A·B는 min(평균, 최연소+10), C는 최연소, D는 최연소보다 약 2세 낮게 계산됨
  function ages(a1, a2) {
    var young = a2 ? Math.min(a1, a2) : a1;
    return { young: young, avgRule: a2 ? Math.min((a1 + a2) / 2, young + 10) : a1, d: a2 ? Math.max(55, young - 2) : a1 };
  }

  function estimate(inp) {
    var city = CITIES[inp.city], ag = ages(inp.age1, inp.age2), pen = valuePenalty(inp.value);
    var typeAdj = { house: 0, town: 2.4, condo: 5 }[inp.type]; // 등급을 나누는 렌더(D)에만 적용
    var std = [], plus = [];
    if (city[2]) std.push(interp(A_STD[city[2]], ag.avgRule) - pen);
    var cAge = Math.min(Math.round(ag.young), 80);
    std.push((ag.young >= 80 ? 56 : C_STD[cAge - 55]) - city[3] - pen);
    if (ag.young >= 70) {
      var dt = city[4], d = dt === 'A' ? D_A[Math.min(Math.round(ag.d), 77) - 55] : interp(D_ANCH[dt], ag.d);
      std.push(Math.min(d, D_CAP[dt]) - typeAdj - pen);
      if (city[2]) plus.push(interp(A_PLUS[city[2]], ag.avgRule) - pen);
      plus.push((ag.young >= 80 ? 60 : C_PLUS[Math.round(ag.young)]) - (city[3] === 13 ? 18 : city[3]) - pen);
      if (D_PLUS[dt]) plus.push(interp(D_PLUS[dt], ag.d) - typeAdj - pen);
    }
    function range(list) {
      list = list.filter(function (x) { return x != null && x > 0; });
      if (!list.length) return null;
      var lo = Math.min.apply(null, list), hi = Math.max.apply(null, list);
      var amt = function (p) { return Math.floor(inp.value * p / 100 / 500) * 500; };
      return { lo: lo, hi: hi, loAmt: amt(lo), hiAmt: amt(hi), n: list.length };
    }
    return { std: range(std), plus: range(plus), young: ag.young, cityRural: !city[2] };
  }

  // ---- 화면 ---------------------------------------------------------------------
  var T = KO ? {
    choose: '도시 선택', needAge: '가장 어린 명의자가 만 55세 이상이어야 신청할 수 있습니다.',
    needValue: '대부분의 렌더는 감정가 $250,000 이상 주택만 취급합니다.', std: '일반 상품 예상 한도', plus: '70세 이상 고한도 상품',
    plusNote: '한도가 더 크지만 금리가 보통 1%p가량 높습니다.', ltv: '집값의', of: '', lenders: '곳의 기준을 비교한 범위',
    rural: '이 지역은 취급하는 렌더가 적어 선택지가 제한됩니다. 실제 가능 여부는 상담으로 확인하세요.',
    young: '70세 미만은 렌더마다 차이가 커서, 일부 금융기관은 이보다 높게 나올 수 있습니다.',
    net: '기존 모기지·비용을 빼고 손에 남는 돈', short: '기존 모기지가 예상 한도보다 많아 리버스모기지만으로는 상환이 어렵습니다.',
    netNote: '비용 약 $2,500(셋업 수수료 약 $995 + 법무비 약 $1,500) 차감, 감정비 별도',
    projTitle: '시간이 지나면 어떻게 될까', projYear: '년 후', bal: '대출 잔액', home: '예상 집값', eq: '남는 자산',
    projNote: '매달 갚지 않으면 이자가 잔액에 더해집니다(반기 복리). No negative equity 보장으로 집을 팔 때 갚을 금액은 그때 집값을 넘지 않고, 표의 "남는 자산"은 본인 또는 상속인의 몫입니다.',
    taken: '받는 금액', calc: '예상 한도 계산하기'
  } : {
    choose: 'Select a city', needAge: 'The youngest owner on title must be at least 55.',
    needValue: 'Most lenders require an appraised value of at least $250,000.', std: 'Estimated limit, standard products', plus: 'Higher-limit products for age 70+',
    plusNote: 'A larger limit, but the rate is usually about 1 percentage point higher.', ltv: '', of: 'of home value', lenders: 'lenders compared',
    rural: 'Few lenders serve this area, so options are limited. Talk to us to confirm what is possible.',
    young: 'Under 70, lenders differ a lot, and some may offer more than this range.',
    net: 'Cash left after paying off your mortgage and costs', short: 'Your mortgage is larger than the estimated limit, so a reverse mortgage alone may not pay it off.',
    netNote: 'About $2,500 in costs deducted (set-up fee ~$995 + legal ~$1,500); appraisal extra',
    projTitle: 'How it changes over time', projYear: ' yrs', bal: 'Loan balance', home: 'Home value', eq: 'Equity left',
    projNote: 'With no payments, interest is added to the balance (compounded semi-annually). The no negative equity guarantee means you never owe more than the home is worth when it is sold, and the equity left belongs to you or your heirs.',
    taken: 'Amount taken', calc: 'Estimate my limit'
  };

  function $(id) { return document.getElementById(id); }
  function money(n) { return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(Math.round(n)); }
  function pct(p) { return p.toFixed(1).replace(/\.0$/, '') + '%'; }
  function num(id) { var v = parseFloat(String($(id).value).replace(/[,$\s]/g, '')); return isNaN(v) ? 0 : v; }

  function fillCities() {
    var sel = $('rm-city');
    if (!sel) return;
    sel.innerHTML = CITIES.map(function (c, i) { return '<option value="' + i + '">' + (KO ? c[0] : c[1]) + '</option>'; }).join('');
  }

  function rangeBox(title, r, note) {
    return '<div class="rm-box"><p class="rm-k">' + title + '</p><p class="rm-v">' + money(r.loAmt) +
      (r.hiAmt > r.loAmt ? ' ~ ' + money(r.hiAmt) : '') + '</p><p class="rm-s">' + (KO ? T.ltv + ' ' : '') +
      pct(r.lo) + (r.hi > r.lo ? ' ~ ' + pct(r.hi) : '') + (KO ? '' : ' ' + T.of) + ' · ' + r.n + (KO ? '' : ' ') + T.lenders + '</p>' +
      (note ? '<p class="rm-s">' + note + '</p>' : '') + '</div>';
  }

  function projection(taken, value, rate, growth) {
    var rows = [], yrs = [0, 5, 10, 15, 20], max = 0;
    yrs.forEach(function (y) {
      var b = taken * Math.pow(1 + rate / 200, 2 * y), h = value * Math.pow(1 + growth / 100, y);
      rows.push({ y: y, b: Math.min(b, h), h: h, e: Math.max(0, h - b) });
      max = Math.max(max, h);
    });
    var W = 560, H = 220, bw = 34, gap = (W - 40) / yrs.length;
    var svg = '<svg viewBox="0 0 ' + W + ' ' + (H + 30) + '" class="rm-chart" role="img" aria-label="' + T.projTitle + '">';
    rows.forEach(function (r, i) {
      var x = 30 + i * gap, hh = H * r.h / max, bh = H * r.b / max;
      svg += '<rect x="' + x + '" y="' + (H - hh) + '" width="' + bw + '" height="' + (hh - bh) + '" fill="#9DB0E8"></rect>' +
        '<rect x="' + x + '" y="' + (H - bh) + '" width="' + bw + '" height="' + bh + '" fill="#324CA8"></rect>' +
        '<text x="' + (x + bw / 2) + '" y="' + (H + 18) + '" text-anchor="middle" font-size="13" fill="#555">' + (r.y ? r.y + T.projYear : (KO ? '지금' : 'Now')) + '</text>';
    });
    svg += '</svg><p class="rm-legend"><span style="background:#324CA8"></span>' + T.bal + ' <span style="background:#9DB0E8"></span>' + T.eq + '</p>';
    var table = '<table class="rm-table"><thead><tr><th></th><th>' + T.bal + '</th><th>' + T.home + '</th><th>' + T.eq + '</th></tr></thead><tbody>' +
      rows.slice(1).map(function (r) { return '<tr><td>' + r.y + T.projYear + '</td><td>' + money(r.b) + '</td><td>' + money(r.h) + '</td><td>' + money(r.e) + '</td></tr>'; }).join('') +
      '</tbody></table>';
    return svg + table;
  }

  function run() {
    var out = $('rm-result'), inp = {
      age1: num('rm-age1'), age2: num('rm-age2') || 0, value: num('rm-value'), city: +$('rm-city').value,
      type: $('rm-type').value, mortgage: num('rm-mortgage')
    };
    var msg = [];
    if (!inp.age1 || inp.age1 < 55 || (inp.age2 && inp.age2 < 55)) msg.push(T.needAge);
    if (inp.value < 250000) msg.push(T.needValue);
    if (msg.length) { out.innerHTML = '<div class="rm-warn">' + msg.join('<br>') + '</div>'; out.hidden = false; return; }
    var r = estimate(inp), html = '';
    if (!r.std) { out.innerHTML = '<div class="rm-warn">' + T.rural + '</div>'; out.hidden = false; return; }
    html += rangeBox(T.std, r.std, r.young < 70 ? T.young : (r.cityRural ? T.rural : ''));
    if (r.plus) html += rangeBox(T.plus, r.plus, T.plusNote);
    var best = r.plus ? Math.max(r.plus.hiAmt, r.std.hiAmt) : r.std.hiAmt;
    var round = function (n) { return Math.floor(n / 500) * 500; };
    var netLo = round(r.std.loAmt - inp.mortgage - COSTS), netHi = round(best - inp.mortgage - COSTS);
    html += netHi <= 0 ? '<div class="rm-warn">' + T.short + '</div>' :
      '<div class="rm-box rm-net"><p class="rm-k">' + T.net + '</p><p class="rm-v">' + money(Math.max(0, netLo)) + (netHi > netLo ? ' ~ ' + money(netHi) : '') + '</p><p class="rm-s">' + T.netNote + '</p></div>';
    var taken = num('rm-taken') || r.std.loAmt;
    if (!$('rm-taken').value) $('rm-taken').value = r.std.loAmt;
    html += '<h3 class="rm-h">' + T.projTitle + ' (' + T.taken + ' ' + money(taken) + ')</h3>' +
      projection(taken, inp.value, num('rm-rate') || 6.3, num('rm-growth')) + '<p class="rm-s">' + T.projNote + '</p>';
    out.innerHTML = html;
    out.hidden = false;
  }

  function prefill() {
    var q = new URLSearchParams(location.search), map = { age: 'rm-age1', age2: 'rm-age2', value: 'rm-value', mortgage: 'rm-mortgage', type: 'rm-type' };
    Object.keys(map).forEach(function (k) { if (q.get(k)) $(map[k]).value = q.get(k); });
    if (q.get('city')) {
      var c = q.get('city').toLowerCase();
      CITIES.forEach(function (x, i) { if (x[1].toLowerCase() === c) $('rm-city').value = i; });
    }
    if (q.get('age') && q.get('value')) run();
  }

  window.RM = { estimate: estimate, CITIES: CITIES };
  document.addEventListener('DOMContentLoaded', function () {
    if (!$('rm-form')) return;
    fillCities();
    $('rm-form').addEventListener('submit', function (e) { e.preventDefault(); $('rm-taken').value = ''; run(); });
    ['rm-taken', 'rm-rate', 'rm-growth'].forEach(function (id) { $(id).addEventListener('change', function () { if (!$('rm-result').hidden) run(); }); });
    prefill();
  });
})();
