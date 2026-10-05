# 로고·배너 SVG 생성. 색·집 모양을 한 곳에서 관리한다.
NAVY, TEAL, ORANGE, CREAM, SAND = "#1F3A5F", "#3F7A8C", "#F08A3C", "#FBF5EA", "#EADFCB"

def house(x, y, w, h, color, roof_h=None, window=True, door=True):
    """(x,y)=몸통 왼쪽 위. 지붕은 몸통 위로 roof_h."""
    rh = roof_h or w * 0.55
    ov = w * 0.09
    s = [f'<polygon points="{x-ov},{y+2} {x+w/2},{y-rh} {x+w+ov},{y+2}" fill="{color}"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>']
    if window:
        ww = w * 0.30
        wx, wy = x + w * 0.17, y + h * 0.18
        s.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{ww}" rx="{ww*0.08}" fill="{ORANGE}"/>')
        s.append(f'<path d="M{wx+ww/2} {wy} V{wy+ww} M{wx} {wy+ww/2} H{wx+ww}" stroke="{color}" stroke-width="{ww*0.08}"/>')
    if door:
        dw, dh = w * 0.22, h * 0.42
        s.append(f'<rect x="{x+w*0.62}" y="{y+h-dh}" width="{dw}" height="{dh}" rx="{dw*0.15}" fill="{CREAM}" opacity="0.9"/>')
    return "\n".join(s)

def logo(with_text=True):
    hy, hh, w = (300, 210, 210) if with_text else (360, 250, 240)
    gap = 14
    total = 2 * w + gap
    x0 = 400 - total / 2
    parts = [f'<rect width="800" height="800" fill="{CREAM}"/>',
             f'<circle cx="400" cy="400" r="400" fill="{CREAM}"/>',
             house(x0, hy, w, hh, NAVY), house(x0 + w + gap, hy, w, hh, TEAL),
             f'<rect x="{x0-40}" y="{hy+hh}" width="{total+80}" height="14" rx="7" fill="{SAND}"/>']
    if with_text:
        parts.append(f'<text x="400" y="{hy+hh+150}" text-anchor="middle" font-family="Gowun Batang" font-weight="700" font-size="104" fill="{NAVY}" letter-spacing="2">이웃의 노후</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">{"".join(parts)}</svg>'

def banner():
    W, H, G = 2560, 1440, 900  # G = 땅 높이(데스크톱 보이는 띠 508~931 안)
    p = [f'<rect width="{W}" height="{H}" fill="{CREAM}"/>',
         f'<rect y="{G}" width="{W}" height="{H-G}" fill="{SAND}"/>',
         f'<circle cx="2190" cy="600" r="40" fill="{ORANGE}" opacity="0.85"/>']
    # 왼쪽·오른쪽 마을 (안전 영역 507~2053 밖, 데스크톱 띠 안)
    left = [(60, 110, TEAL), (195, 140, NAVY), (350, 105, TEAL)]
    right = [(2105, 105, TEAL), (2235, 140, NAVY), (2395, 110, TEAL)]
    for x, w, c in left + right:
        h = w * 0.95
        p.append(house(x, G - h, w, h, c))
    p.append(f'<text x="{W/2}" y="715" text-anchor="middle" font-family="Gowun Batang" font-weight="700" font-size="170" fill="{NAVY}" letter-spacing="4">이웃의 노후</text>')
    p.append(f'<text x="{W/2}" y="830" text-anchor="middle" font-family="Gowun Dodum" font-size="62" fill="{NAVY}">옆집 이야기로 풀어 보는 연금 · 건강보험료 · 지원금</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(p)}</svg>'

if __name__ == "__main__":
    import cairosvg
    for name, svg, size in [("logo", logo(True), 800), ("logo-icon", logo(False), 800), ("banner", banner(), None)]:
        open(f"{name}.svg", "w").write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{name}.png")
    print("ok")
