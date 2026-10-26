/** 계산기용 Tailwind 설정 — 색·글꼴은 카드뉴스 brand.json 과 같게 */
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: { light: '#EEF0F8', DEFAULT: '#324CA8', dark: '#263B87' },
      },
      fontFamily: {
        sans: ['"Gowun Dodum"', '"Noto Sans KR"', 'sans-serif'],
      },
    },
  },
};
