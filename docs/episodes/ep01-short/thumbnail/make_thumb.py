# EP01 짧은 판 썸네일 시안 2종 (1280x720). 시니어 가독성: 글자 크게, 두 줄 이내, 강한 대비.
import sys
sys.path.insert(0, "../../../brand")
from make_brand import house, NAVY, TEAL, ORANGE, CREAM
YELLOW, WHITE = "#FFD54A", "#FFFFFF"

def card(x, y, who, amount, color, big=False):
    w, h = 400, 190
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{WHITE}" stroke="{color}" stroke-width="8"/>'
            f'<text x="{x+30}" y="{y+62}" font-family="Black Han Sans" font-size="44" fill="{color}">{who}</text>'
            f'<text x="{x+30}" y="{y+150}" font-family="Black Han Sans" font-size="{78 if big else 70}" fill="{NAVY}">{amount}</text>')

def thumb_a():
    p = [f'<rect width="1280" height="720" fill="{NAVY}"/>',
         f'<text x="60" y="165" font-family="Black Han Sans" font-size="128" fill="{WHITE}">30년 냈는데</text>',
         f'<text x="60" y="320" font-family="Black Han Sans" font-size="128" fill="{YELLOW}">기초연금 깎였다</text>',
         card(60, 400, "30년 낸 앞집", "25만 7천", ORANGE),
         f'<text x="500" y="525" font-family="Black Han Sans" font-size="64" fill="{WHITE}">vs</text>',
         card(600, 400, "안 낸 옆집", "34만 9천", TEAL),
         f'<g transform="translate(1060,470) scale(0.9)">{house(0, 0, 150, 150, CREAM)}</g>',
         f'<text x="60" y="680" font-family="Gowun Dodum" font-size="30" fill="{CREAM}">※예시 · 2026년 기준 기초연금(월)</text>']
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">{"".join(p)}</svg>'

def thumb_b():
    p = [f'<rect width="1280" height="720" fill="{CREAM}"/>',
         f'<rect x="0" y="0" width="1280" height="380" fill="{NAVY}"/>',
         f'<text x="640" y="165" text-anchor="middle" font-family="Black Han Sans" font-size="120" fill="{WHITE}">국민연금 낸 사람</text>',
         f'<text x="640" y="320" text-anchor="middle" font-family="Black Han Sans" font-size="140" fill="{YELLOW}">손해일까?</text>',
         f'<g transform="translate(250,510)">{house(0, 0, 200, 170, NAVY)}</g>',
         f'<g transform="translate(830,510)">{house(0, 0, 200, 170, TEAL)}</g>',
         f'<text x="640" y="555" text-anchor="middle" font-family="Black Han Sans" font-size="80" fill="{ORANGE}">합치면?</text>',
         f'<text x="640" y="640" text-anchor="middle" font-family="Black Han Sans" font-size="54" fill="{NAVY}">짧게 계산</text>']
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">{"".join(p)}</svg>'

if __name__ == "__main__":
    import cairosvg
    for n, svg in [("thumb-a", thumb_a()), ("thumb-b", thumb_b())]:
        cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{n}.png")
    print("ok")
