#!/bin/sh
# 계산기별 Tailwind CSS 생성: src/css/calc/<slug>.css → assets/css/calc/<slug>.css
# Tailwind 실행파일: .claude/tools/bin/tailwindcss (v3.4.17, git 제외) 또는 PATH 의 tailwindcss
set -e
cd "$(dirname "$0")/.."
TW=.claude/tools/bin/tailwindcss
[ -x "$TW" ] || TW=tailwindcss
mkdir -p assets/css/calc
for f in src/css/calc/*.css; do
  slug=$(basename "$f" .css)
  page=$(ls src/*/*/"$slug".html src/*/"$slug".html 2>/dev/null | paste -sd, -)
  "$TW" -c tools/tailwind.config.js -i "$f" -o "assets/css/calc/$slug.css" --content "$page" --minify 2>/dev/null
  echo "$slug: $(wc -c < assets/css/calc/$slug.css) bytes"
done
