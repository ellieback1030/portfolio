#!/usr/bin/env python3
"""
백연우 Portfolio PDF Generator
=============================
Usage:
  python3 generate_pdf.py

Requirements:
  pip install reportlab Pillow fonttools

Font setup (run once):
  python3 generate_pdf.py --setup-fonts

Output:
  백연우_포트폴리오_2026.pdf  (same folder as this script)
"""

import os
import sys
import io
import copy
import argparse

# ── Dependency check ────────────────────────────────────
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PILImage
except ImportError:
    print("Missing packages. Run:  pip install reportlab Pillow fonttools")
    sys.exit(1)


# ── Paths ───────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR    = SCRIPT_DIR
OUT_PDF    = os.path.join(SCRIPT_DIR, '백연우_포트폴리오_2026.pdf')
FONT_DIR   = os.path.join(SCRIPT_DIR, '.fonts')
FONT_VAR   = os.path.join(FONT_DIR, 'NotoSansKR.ttf')
FONT_400   = os.path.join(FONT_DIR, 'NotoKR-400.ttf')
FONT_700   = os.path.join(FONT_DIR, 'NotoKR-700.ttf')
FONT_900   = os.path.join(FONT_DIR, 'NotoKR-900.ttf')

VAR_FONT_URL = (
    'https://github.com/google/fonts/raw/main/ofl/notosanskr/'
    'NotoSansKR%5Bwght%5D.ttf'
)


# ── Font setup ──────────────────────────────────────────
def setup_fonts():
    """Download Noto Sans KR variable font and extract weight instances."""
    import urllib.request
    from fontTools.ttLib import TTFont as FTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    os.makedirs(FONT_DIR, exist_ok=True)

    if not os.path.exists(FONT_VAR):
        print("Downloading Noto Sans KR variable font...")
        urllib.request.urlretrieve(VAR_FONT_URL, FONT_VAR)
        print(f"  Saved: {FONT_VAR}")
    else:
        print("Variable font already exists, skipping download.")

    for weight, path in [(400, FONT_400), (700, FONT_700), (900, FONT_900)]:
        if not os.path.exists(path):
            print(f"  Extracting weight {weight}...")
            vf = FTFont(FONT_VAR)
            inst = instantiateVariableFont(copy.deepcopy(vf), {'wght': weight})
            inst.save(path)
            print(f"  Saved: {path}")
        else:
            print(f"  Weight {weight} already extracted.")

    print("\nFont setup complete. Run without --setup-fonts to generate PDF.")


def register_fonts():
    if not all(os.path.exists(p) for p in [FONT_400, FONT_700, FONT_900]):
        print("Fonts not found. Run:  python3 generate_pdf.py --setup-fonts")
        sys.exit(1)
    pdfmetrics.registerFont(TTFont('KR',   FONT_400))
    pdfmetrics.registerFont(TTFont('KR-M', FONT_400))
    pdfmetrics.registerFont(TTFont('KR-B', FONT_700))
    pdfmetrics.registerFont(TTFont('KR-X', FONT_900))


# ── Colors ──────────────────────────────────────────────
C_WHITE    = HexColor('#FFFFFF')
C_LAV_BG   = HexColor('#EEE8FF')
C_LAV      = HexColor('#E6E6FA')
C_LAV_MID  = HexColor('#C4B5F4')
C_LAV_DARK = HexColor('#7C6FCD')
C_LAV_DEEP = HexColor('#5B4FBE')
C_COVER1   = HexColor('#1a1040')
C_FG       = HexColor('#1a1630')
C_MUTED    = HexColor('#6b6b80')
C_BORDER   = HexColor('#E5E7EB')
C_ALT      = HexColor('#F5F3FF')

# ── Page constants ──────────────────────────────────────
W, H   = A4   # 595.28 x 841.89 pts
MARGIN = 44
COL_W  = W - MARGIN * 2


# ── Image helpers ───────────────────────────────────────
_img_cache = {}

def compressed_reader(name, max_dim=1600, quality=72):
    path = os.path.join(IMG_DIR, name)
    if path in _img_cache:
        return _img_cache[path]
    im = PILImage.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        bg = PILImage.new('RGB', im.size, (255, 255, 255))
        if im.mode == 'P':
            im = im.convert('RGBA')
        bg.paste(im, mask=im.split()[-1] if im.mode in ('RGBA', 'LA') else None)
        im = bg
    elif im.mode != 'RGB':
        im = im.convert('RGB')
    w, h = im.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        im = im.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format='JPEG', quality=quality, optimize=True)
    buf.seek(0)
    reader = ImageReader(buf)
    _img_cache[path] = reader
    return reader

def img_ratio(name):
    path = os.path.join(IMG_DIR, name)
    im = PILImage.open(path)
    return im.width / im.height

def draw_img_fit(c, name, x, y, max_w, max_h, radius=6):
    path = os.path.join(IMG_DIR, name)
    if not os.path.exists(path):
        c.setFillColor(C_LAV_BG)
        c.roundRect(x, y, max_w, max_h, radius, fill=1, stroke=0)
        c.setFillColor(C_LAV_DARK)
        c.setFont('KR', 10)
        c.drawCentredString(x + max_w / 2, y + max_h / 2 - 5, '이미지 없음')
        return
    ir = compressed_reader(name)
    ratio = img_ratio(name)
    if max_w / max_h > ratio:
        dh = max_h; dw = dh * ratio
    else:
        dw = max_w; dh = dw / ratio
    dx = x + (max_w - dw) / 2
    dy = y + (max_h - dh) / 2
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, max_w, max_h, radius)
    c.clipPath(p, stroke=0)
    c.drawImage(ir, dx, dy, dw, dh, preserveAspectRatio=True, mask='auto')
    c.restoreState()


# ── Drawing helpers ─────────────────────────────────────
def rounded_rect(c, x, y, w, h, r, fill=None, stroke=None, sw=0.5):
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(sw)
    c.roundRect(x, y, w, h, r,
                fill=1 if fill else 0,
                stroke=1 if stroke else 0)

def draw_chips(c, chips, x, y, font='KR-M', size=9, bg=None, fg=None, gap=6, max_w=None):
    bg = bg or C_LAV_BG; fg = fg or C_LAV_DEEP
    cx = x
    for chip in chips:
        c.setFont(font, size)
        tw = c.stringWidth(chip, font, size)
        bw = tw + 18; bh = size + 8
        if max_w and cx - x + bw > max_w:
            cx = x; y -= bh + 4
        rounded_rect(c, cx, y - 4, bw, bh, 9, fill=bg)
        c.setFillColor(fg)
        c.drawString(cx + 9, y + 2, chip)
        cx += bw + gap
    return y

def section_label(c, x, y, text):
    c.setFont('KR-M', 8.5)
    c.setFillColor(C_LAV_DARK)
    tw = c.stringWidth(text, 'KR-M', 8.5)
    rounded_rect(c, x, y - 3, tw + 16, 14, 4, fill=C_LAV_BG)
    c.drawString(x + 8, y, text)
    return y - 20

def sec_title(c, x, y, text, size=22):
    c.setFont('KR-B', size)
    c.setFillColor(C_FG)
    c.drawString(x, y, text)
    return y - size - 6

def hline(c, x, y, w, color=None):
    c.setStrokeColor(color or C_BORDER)
    c.setLineWidth(0.5)
    c.line(x, y, x + w, y)

def page_header(c, page_num, section=''):
    c.setFillColor(C_LAV_DEEP)
    c.rect(0, H - 3, W, 3, fill=1, stroke=0)
    c.setFont('KR-B', 8.5); c.setFillColor(C_FG)
    c.drawString(MARGIN, H - 20, '백연우 Portfolio 2026')
    if section:
        c.setFont('KR', 8); c.setFillColor(C_MUTED)
        c.drawRightString(W - MARGIN, H - 20, section)
    c.setFont('KR', 8); c.setFillColor(C_MUTED)
    c.drawCentredString(W / 2, 20, str(page_num))

def page_footer(c):
    c.setFillColor(C_LAV_BG)
    c.rect(0, 0, W, 32, fill=1, stroke=0)
    c.setFont('KR', 7.5); c.setFillColor(C_MUTED)
    c.drawString(MARGIN, 11, 'ellieback1030@gmail.com  ·  @dinong.official')
    c.drawRightString(W - MARGIN, 11, '© 2026 Back Yeonwoo')


# ── Page builders ───────────────────────────────────────

def page_cover(c):
    c.setFillColor(C_COVER1)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor('#2d1b6b'))
    c.circle(W + 40, H + 20, 300, fill=1, stroke=0)
    c.setFillColor(HexColor('#261556'))
    c.circle(-40, -20, 200, fill=1, stroke=0)

    lx = MARGIN; y = H - 90
    c.setFont('KR-M', 8); c.setFillColor(C_LAV_MID)
    c.drawString(lx, y, 'PORTFOLIO · 2026')
    y -= 18
    c.setFont('KR-X', 52); c.setFillColor(white)
    c.drawString(lx, y - 44, '백  연  우')
    y -= 60
    c.setFont('KR', 14); c.setFillColor(HexColor('#C4B5F4'))
    c.drawString(lx, y - 14, 'Baek Yeon Woo')
    y -= 32
    c.setStrokeColor(C_LAV_DARK); c.setLineWidth(1)
    c.line(lx, y, lx + 200, y); y -= 20
    c.setFont('KR-M', 15); c.setFillColor(white)
    c.drawString(lx, y, '2D 캐릭터 디자이너'); y -= 22
    c.setFont('KR', 12); c.setFillColor(HexColor('#C4B5F4'))
    c.drawString(lx, y, '교육 게임  ·  캐릭터  ·  웹툰  ·  브랜드 콘텐츠')
    y -= 40

    stats = [('6년 4개월', '총 실무경력'), ('3개', '수상 이력'), ('6K+', '인스타 팔로워')]
    sx = lx
    for val, label in stats:
        rounded_rect(c, sx, y - 54, 100, 54, 8, fill=HexColor('#FFFFFF18'))
        c.setFont('KR-B', 17); c.setFillColor(white)
        c.drawCentredString(sx + 50, y - 28, val)
        c.setFont('KR', 8); c.setFillColor(HexColor('#C4B5F4'))
        c.drawCentredString(sx + 50, y - 42, label)
        sx += 110
    y -= 84

    for icon, text in [('✉', 'ellieback1030@gmail.com'), ('📷', '@dinong.official')]:
        c.setFont('KR', 10); c.setFillColor(HexColor('#C4B5F4'))
        c.drawString(lx, y, f'{icon}  {text}'); y -= 18

    y -= 16
    chips = ['Illustrator', 'Photoshop', 'Figma', 'Adobe XD', 'Blender', 'Unity', 'After Effects']
    cx = lx
    for chip in chips:
        c.setFont('KR', 8.5)
        tw = c.stringWidth(chip, 'KR', 8.5)
        bw = tw + 16
        rounded_rect(c, cx, y - 4, bw, 16, 8, fill=HexColor('#FFFFFF15'))
        c.setStrokeColor(HexColor('#FFFFFF30')); c.setLineWidth(0.5)
        c.roundRect(cx, y - 4, bw, 16, 8, fill=0, stroke=1)
        c.setFillColor(HexColor('#E0D4FF'))
        c.drawString(cx + 8, y, chip)
        cx += bw + 6
        if cx > lx + 290:
            cx = lx; y -= 22

    # Right card
    rx = W / 2 + 20; rw = W - MARGIN - rx
    ry_top = H - 60; rh = 580
    rounded_rect(c, rx, ry_top - rh, rw, rh, 14, fill=HexColor('#FFFFFF12'))
    c.setStrokeColor(HexColor('#FFFFFF25')); c.setLineWidth(0.8)
    c.roundRect(rx, ry_top - rh, rw, rh, 14, fill=0, stroke=1)

    cy = ry_top - 28
    c.setFont('KR-X', 11); c.setFillColor(C_LAV_MID)
    c.drawCentredString(rx + rw / 2, cy, '✦  DESIGNER CARD  ✦'); cy -= 22

    rounded_rect(c, rx + 20, cy - 170, rw - 40, 170, 10, fill=HexColor('#3d2a8a'))
    c.setFont('KR-X', 44); c.setFillColor(HexColor('#7C6FCD'))
    c.drawCentredString(rx + rw / 2, cy - 100, '🎨'); cy -= 188

    c.setFont('KR-B', 16); c.setFillColor(white)
    c.drawCentredString(rx + rw / 2, cy, '백연우'); cy -= 16
    c.setFont('KR', 9); c.setFillColor(C_LAV_MID)
    c.drawCentredString(rx + rw / 2, cy, '2D Character & Brand Designer'); cy -= 22

    badge_w = 80
    rounded_rect(c, rx + rw / 2 - 40, cy - 4, badge_w, 16, 8, fill=HexColor('#14532d30'))
    c.setStrokeColor(HexColor('#86efac')); c.setLineWidth(0.5)
    c.roundRect(rx + rw / 2 - 40, cy - 4, badge_w, 16, 8, fill=0, stroke=1)
    c.setFillColor(HexColor('#22c55e'))
    c.circle(rx + rw / 2 - 30, cy + 4, 3, fill=1, stroke=0)
    c.setFont('KR-M', 8); c.setFillColor(HexColor('#4ade80'))
    c.drawString(rx + rw / 2 - 22, cy, '구직 중'); cy -= 28

    c.setStrokeColor(HexColor('#FFFFFF20')); c.setLineWidth(0.5)
    c.line(rx + 20, cy, rx + rw - 20, cy); cy -= 16

    for icon, title, sub in [
        ('🎯', '소프트플렉스 디자인팀 과장', '팀 리드 · 교육 게임 총괄'),
        ('🏛️', '행정안전부 장관상 수상', '2021 실패박람회 서포터즈'),
        ('🤖', 'Anthropic Claude 11개 수료', 'AI 협업 전문 역량'),
        ('📊', 'GAIQ 인증 · JLPT N2', '마케팅 & 어학 역량'),
    ]:
        c.setFont('KR', 11); c.setFillColor(white)
        c.drawString(rx + 24, cy, icon)
        c.setFont('KR-M', 9); c.setFillColor(white)
        c.drawString(rx + 40, cy, title)
        c.setFont('KR', 7.5); c.setFillColor(C_LAV_MID)
        c.drawString(rx + 40, cy - 11, sub)
        cy -= 30

    c.showPage()


def page_about(c):
    page_header(c, 2, 'About & Skills')
    y = H - 44
    y = section_label(c, MARGIN, y, 'About')
    y = sec_title(c, MARGIN, y, '소개 & 스킬')
    y -= 8; hline(c, MARGIN, y, COL_W); y -= 24

    col1 = MARGIN; col2 = MARGIN + COL_W / 2 + 10
    cw = COL_W / 2 - 10

    c.setFont('KR-B', 12); c.setFillColor(C_FG)
    c.drawString(col1, y, '다양한 디자인 경력을 갖춘 백연우입니다')
    yb = y - 16

    for line in [
        '6년 이상의 실무 경험을 바탕으로 교육 · 게임 · 콘텐츠',
        '분야에서 그래픽과 캐릭터 디자인을 전문으로 수행해 온',
        '디자이너입니다.', '',
        '교육용 게임과 학습 앱, 마케팅 콘텐츠 등 다양한 프로젝트를',
        '경험하며 UI 디자인, 캐릭터·일러스트, 배경 및 타일맵 디자인',
        '까지 전반적인 2D 그래픽 업무를 담당해 왔습니다.', '',
        '현재 AI 도구를 적극적으로 실험하며 Anthropic Claude',
        '교육과정 11개를 수료했고 GAIQ 인증도 보유하고 있습니다.',
    ]:
        c.setFont('KR', 9.5); c.setFillColor(C_MUTED)
        c.drawString(col1, yb, line); yb -= 14

    yb -= 14
    for val, label in [
        ('6년 4개월', '총 실무 경력'),
        ('행정안전부 장관상', '2021 실패박람회 우수서포터즈'),
        ('11개 AI 과정 수료', 'Anthropic Claude 전문 역량'),
        ('6,000+ 팔로워', '@dinong.official 인스타그램 운영'),
    ]:
        rounded_rect(c, col1, yb - 34, cw - 10, 40, 6, fill=C_WHITE, stroke=C_BORDER)
        c.setFillColor(C_LAV_MID)
        c.rect(col1, yb - 34, 3, 40, fill=1, stroke=0)
        c.setFont('KR-B', 11); c.setFillColor(C_LAV_DEEP)
        c.drawString(col1 + 12, yb - 14, val)
        c.setFont('KR', 8); c.setFillColor(C_MUTED)
        c.drawString(col1 + 12, yb - 26, label)
        yb -= 46

    cy = y
    for icon, title, desc in [
        ('🎯', '디테일 중심 디자인', '표정, UI 흐름, 시선까지 꼼꼼하게'),
        ('🤝', '원활한 협업 능력', '기획/개발/마케팅 팀 소통 및 제안'),
        ('📊', '마케팅 이해 보유', 'GAIQ 취득, 데이터 기반 크리에이티브'),
        ('🎨', '폭넓은 작업 영역', '캐릭터·UI·배경·웹툰·마스코트'),
        ('🤖', 'AI 도구 활용', 'Claude 11개 과정 수료, 워크플로우 적용'),
    ]:
        rounded_rect(c, col2, cy - 30, cw, 36, 5, fill=C_WHITE, stroke=C_BORDER)
        c.setFont('KR', 11); c.setFillColor(C_FG)
        c.drawString(col2 + 10, cy - 11, icon)
        c.setFont('KR-M', 9.5); c.setFillColor(C_FG)
        c.drawString(col2 + 26, cy - 10, title)
        c.setFont('KR', 8); c.setFillColor(C_MUTED)
        c.drawString(col2 + 26, cy - 21, desc)
        cy -= 42

    cy -= 10
    c.setFont('KR-B', 11); c.setFillColor(C_FG)
    c.drawString(col2, cy, '사용 도구 & 스킬'); cy -= 18

    for group, chips in [
        ('디자인 툴', ['Illustrator', 'Photoshop', 'Figma', 'Adobe XD']),
        ('3D & 게임', ['Blender', 'Unity', 'Tilemap', 'Sprite']),
        ('콘텐츠', ['인스타툰', '웹툰', 'GAIQ', '마케팅 배너']),
        ('AI & 기타', ['Claude API', 'MCP', '일본어 N2', '팀 리드']),
    ]:
        c.setFont('KR-M', 7.5); c.setFillColor(C_LAV_DARK)
        c.drawString(col2, cy, group.upper()); cy -= 14
        cx = col2
        for chip in chips:
            c.setFont('KR', 8.5)
            tw = c.stringWidth(chip, 'KR', 8.5)
            bw = tw + 14
            if cx - col2 + bw > cw:
                cx = col2; cy -= 18
            rounded_rect(c, cx, cy - 5, bw, 14, 7, fill=C_LAV_BG)
            c.setFillColor(C_LAV_DEEP)
            c.drawString(cx + 7, cy - 1, chip)
            cx += bw + 5
        cy -= 22

    page_footer(c); c.showPage()


def page_career(c):
    page_header(c, 3, 'Career')
    y = H - 44
    y = section_label(c, MARGIN, y, 'Career History')
    y = sec_title(c, MARGIN, y, '경력 사항')
    c.setFont('KR', 9); c.setFillColor(C_MUTED)
    c.drawString(MARGIN, y, '총 6년 4개월  ·  교육 게임 / 브랜드 콘텐츠 / 팀 매니지먼트')
    y -= 10; hline(c, MARGIN, y, COL_W); y -= 28

    tl_x = MARGIN + 90
    careers = [
        ('2025.04', '2025.11', '8개월', '소프트플렉스', '디자인팀 과장',
         '디자인팀 전반 총괄, 교육용 게임·앱 디자인 리드, 팀원 일정 관리 및 산출물 검수.',
         ['팀 리드', '캐릭터 디자인', 'UI 디자인', 'Tilemap']),
        ('2022.12', '2024.09', '1년 10개월', '소프트플렉스', '디자인팀 대리',
         '영어·수학 학습용 게임 앱 캐릭터·일러스트 디자인, 학습 콘텐츠 앱 UI 작업.',
         ['캐릭터 디자인', '앱 UI', '배경 디자인', 'Tilemap']),
        ('2021.06', '2022.12', '1년 7개월', '주식회사 조이스터디', '디자이너',
         '교육용 RPG 게임 캐릭터 컨셉 및 Sprite 디자인, 배경·Tilemap·마스코트 제작.',
         ['RPG 캐릭터', 'Sprite', '마스코트', 'UI']),
        ('2020.12', '2021.06', '7개월', '소프트플렉스', '디자인 대리',
         '교육용 게임 캐릭터·배경·UI 디자인.',
         ['캐릭터', '배경', 'UI']),
        ('2020.11', '2020.12', '2개월', '품게임즈', '그래픽디자이너 사원',
         '게임 전반적 그래픽 디자인 참여.',
         ['게임 그래픽']),
        ('2018.11', '2020.07', '1년 9개월', '주식회사 에덴파트너스코리아', '2D 디자이너',
         '블록체인 HTML 게임 11종 UI 디자인, 마스코트 캐릭터 4종, GS Retail·삼성전자·경기도청 등 브랜드 콘텐츠.',
         ['게임 UI', '마스코트', '브랜드 콘텐츠', '마케팅 배너']),
    ]

    ys = y
    for start, end, dur, co, role, desc, tags in careers:
        c.setFont('KR-M', 8); c.setFillColor(C_LAV_DARK)
        c.drawRightString(tl_x - 14, ys, start)
        c.setFont('KR', 7.5); c.setFillColor(C_MUTED)
        c.drawRightString(tl_x - 14, ys - 11, dur)
        c.setFillColor(C_LAV_DEEP)
        c.circle(tl_x, ys + 3, 4, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.circle(tl_x, ys + 3, 2, fill=1, stroke=0)

        bx = tl_x + 16; by = ys
        c.setFont('KR-B', 11); c.setFillColor(C_FG)
        c.drawString(bx, by, co); by -= 15

        c.setFont('KR-M', 8); c.setFillColor(C_LAV_DARK)
        rw2 = c.stringWidth(role, 'KR-M', 8) + 12
        rounded_rect(c, bx, by - 3, rw2, 13, 3, fill=C_LAV_BG)
        c.drawString(bx + 6, by, role); by -= 18

        c.setFont('KR', 8.5); c.setFillColor(C_MUTED)
        c.drawString(bx, by, desc[:52])
        if len(desc) > 52:
            c.drawString(bx, by - 12, desc[52:104])
            by -= 12
        by -= 14

        tx = bx
        for tag in tags:
            c.setFont('KR', 7.5)
            tw = c.stringWidth(tag, 'KR', 7.5) + 10
            rounded_rect(c, tx, by - 3, tw, 12, 3, fill=C_WHITE, stroke=C_BORDER, sw=0.4)
            c.setFillColor(C_MUTED)
            c.drawString(tx + 5, by, tag)
            tx += tw + 4

        ys -= (ys - by) + 30

    c.setStrokeColor(C_LAV_MID); c.setLineWidth(1.2)
    c.line(tl_x, y + 6, tl_x, ys + 34)
    page_footer(c); c.showPage()


def page_awards(c):
    page_header(c, 4, 'Awards & Certifications')
    y = H - 44
    y = section_label(c, MARGIN, y, 'Awards')
    y = sec_title(c, MARGIN, y, '수상 이력')
    y -= 4; hline(c, MARGIN, y, COL_W); y -= 20

    aw = (COL_W - 20) / 3; ax = MARGIN
    for icon, year, title, org in [
        ('🏛️', '2021년', '행정안전부 장관상', '2021 실패박람회 우수서포터즈 크리에이터 · 행정안전부'),
        ('🏆', '2022년', '다함께 술술 웹툰 공모전 장려상', '한국산업인력공단 글로벌숙련기술진흥원'),
        ('🎖️', '2025년', '안성경찰서 감사장', '안전캠페인 웹툰 재능기부 · 안성경찰서'),
    ]:
        rounded_rect(c, ax, y - 80, aw, 86, 8, fill=C_WHITE, stroke=C_BORDER)
        c.setFont('KR', 22); c.setFillColor(C_FG)
        c.drawString(ax + 14, y - 28, icon)
        c.setFont('KR-M', 8); c.setFillColor(C_LAV_DARK)
        c.drawString(ax + 14, y - 42, year)
        c.setFont('KR-B', 10); c.setFillColor(C_FG)
        c.drawString(ax + 14, y - 55, title)
        c.setFont('KR', 7.5); c.setFillColor(C_MUTED)
        if len(org) > 28:
            c.drawString(ax + 14, y - 67, org[:28])
            c.drawString(ax + 14, y - 78, org[28:])
        else:
            c.drawString(ax + 14, y - 67, org)
        ax += aw + 10
    y -= 100

    c.setFont('KR-B', 11); c.setFillColor(C_FG)
    c.drawString(MARGIN, y, '대외 활동'); y -= 16
    aw2 = (COL_W - 10) / 2; ax2 = MARGIN; ay = y
    for i, (icon, title, desc) in enumerate([
        ('📢', '행정안전부 실패박람회 다시인 서포터즈', '2021.05~2021.11 · 서포터즈 50인 선정 · 재도전 정책 홍보 인스타툰 SNS 확산'),
        ('📷', '인스타그램 활동 @dinong.official', '팔로워 6,000+ · 752게시물 · 일상 인스타툰 · 리뷰툰 · 협찬 콘텐츠 연재'),
        ('🎪', '캐릭터 관련 행사 참가', 'K-일러스트레이션페어 2021·2022 · 마플샵·다꾸페·마겟키리브 등 참가'),
        ('🏅', '공모전 수상', 'EaseUS 4천만 공모전 수상'),
    ]):
        if i == 2:
            ax2 = MARGIN; ay -= 52
        rounded_rect(c, ax2, ay - 44, aw2, 50, 6, fill=C_WHITE, stroke=C_BORDER)
        c.setFillColor(C_LAV_MID)
        c.rect(ax2, ay - 44, 2.5, 50, fill=1, stroke=0)
        c.setFont('KR', 10); c.setFillColor(C_FG)
        c.drawString(ax2 + 12, ay - 16, icon)
        c.setFont('KR-M', 9); c.setFillColor(C_FG)
        c.drawString(ax2 + 28, ay - 16, title)
        c.setFont('KR', 8); c.setFillColor(C_MUTED)
        c.drawString(ax2 + 12, ay - 30, desc[:50])
        ax2 += aw2 + 10
    y = ay - 60

    hline(c, MARGIN, y, COL_W); y -= 16
    y = section_label(c, MARGIN, y, 'Certifications')
    c.setFont('KR-B', 14); c.setFillColor(C_FG)
    c.drawString(MARGIN, y, '자격증 & 수료'); y -= 22

    certs = [
        ('Anthropic Education', 'Teaching AI Fluency'),
        ('Anthropic Education', 'Model Context Protocol: Advanced'),
        ('Anthropic Education', 'Claude Code in Action'),
        ('Anthropic Education', 'Building with the Claude API'),
        ('Anthropic Education', 'AI Fluency: Framework & Foundations'),
        ('Anthropic Education', 'Intro to Model Context Protocol'),
        ('Anthropic Education', 'Claude 101 · Intro to agent skills'),
        ('Anthropic Education', 'AI Fluency for students & educators'),
        ('Google', 'GAIQ — Google Analytics IQ'),
        ('일본국제교육협회', '新JLPT N2급 (2013.08)'),
        ('교육부', '중등학교정교사 (2014.02)'),
        ('더조은아카데미', '게임그래픽전문가양성과정 (2018)'),
    ]
    cols = 3; cw2 = (COL_W - (cols - 1) * 8) / cols; row_h = 38
    for i, (issuer, name) in enumerate(certs):
        col_i = i % cols; row_i = i // cols
        bx = MARGIN + col_i * (cw2 + 8)
        by = y - row_i * (row_h + 6)
        rounded_rect(c, bx, by - row_h, cw2, row_h, 5, fill=C_WHITE, stroke=C_LAV)
        c.setFont('KR-M', 7); c.setFillColor(C_LAV_DARK)
        c.drawString(bx + 8, by - 13, issuer.upper())
        c.setFont('KR-M', 8.5); c.setFillColor(C_FG)
        if len(name) > 22:
            c.drawString(bx + 8, by - 24, name[:22])
            c.drawString(bx + 8, by - 34, name[22:])
        else:
            c.drawString(bx + 8, by - 24, name)

    page_footer(c); c.showPage()


def project_divider(c, page_num, category, title, subtitle, client=''):
    c.setFillColor(C_COVER1)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor('#2d1b6b'))
    c.circle(W + 60, H / 2, 280, fill=1, stroke=0)
    c.setFillColor(HexColor('#1e1050'))
    c.circle(-60, H / 2, 200, fill=1, stroke=0)

    c.setFont('KR-X', 8); c.setFillColor(C_LAV_MID)
    c.drawCentredString(W / 2, H - 60, 'PROJECT SHOWCASE')
    c.setStrokeColor(C_LAV_DARK); c.setLineWidth(0.5)
    c.line(MARGIN + 40, H - 70, W - MARGIN - 40, H - 70)

    c.setFont('KR-M', 9); c.setFillColor(C_LAV_MID)
    tw = c.stringWidth(category, 'KR-M', 9)
    rounded_rect(c, W / 2 - (tw + 20) / 2, H / 2 + 80, tw + 20, 18, 9,
                 fill=HexColor('#FFFFFF15'))
    c.drawCentredString(W / 2, H / 2 + 89, category)

    c.setFont('KR-X', 32); c.setFillColor(white)
    c.drawCentredString(W / 2, H / 2 + 38, title)
    c.setFont('KR', 12); c.setFillColor(HexColor('#C4B5F4'))
    c.drawCentredString(W / 2, H / 2 + 14, subtitle)
    if client:
        c.setFont('KR-M', 9); c.setFillColor(HexColor('#FFFFFF60'))
        c.drawCentredString(W / 2, H / 2 - 8, client)

    c.setFont('KR', 8); c.setFillColor(HexColor('#FFFFFF40'))
    c.drawCentredString(W / 2, 24, str(page_num))
    c.showPage()


def project_page(c, page_num, section, proj_title, proj_sub, imgs,
                 client='', two_col=False, alt_bg=False):
    bg = C_ALT if alt_bg else C_WHITE
    c.setFillColor(bg); c.rect(0, 0, W, H, fill=1, stroke=0)
    page_header(c, page_num, section)
    y = H - 50

    if client:
        c.setFont('KR-M', 8); c.setFillColor(C_LAV_DARK)
        tw = c.stringWidth(client, 'KR-M', 8)
        rounded_rect(c, MARGIN, y - 3, tw + 14, 14, 4, fill=C_LAV_BG)
        c.drawString(MARGIN + 7, y, client); y -= 20

    c.setFont('KR-B', 18); c.setFillColor(C_FG)
    c.drawString(MARGIN, y, proj_title); y -= 22
    c.setFont('KR', 10); c.setFillColor(C_MUTED)
    c.drawString(MARGIN, y, proj_sub); y -= 18
    hline(c, MARGIN, y, COL_W); y -= 16

    avail_h = y - 50
    if not imgs:
        pass
    elif len(imgs) == 1:
        draw_img_fit(c, imgs[0], MARGIN, y - avail_h, COL_W, avail_h, radius=10)
    elif len(imgs) == 2:
        if two_col:
            hw = (COL_W - 10) / 2
            draw_img_fit(c, imgs[0], MARGIN, y - avail_h, hw, avail_h, radius=8)
            draw_img_fit(c, imgs[1], MARGIN + hw + 10, y - avail_h, hw, avail_h, radius=8)
        else:
            h1 = avail_h * 0.52; h2 = avail_h - h1 - 10
            draw_img_fit(c, imgs[0], MARGIN, y - h1, COL_W, h1, radius=10)
            draw_img_fit(c, imgs[1], MARGIN, y - h1 - 10 - h2, COL_W, h2, radius=10)

    page_footer(c); c.showPage()


def page_back_cover(c):
    c.setFillColor(C_COVER1); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor('#2d1b6b'))
    c.circle(W / 2, H / 2, 320, fill=1, stroke=0)
    c.setFillColor(C_COVER1)
    c.circle(W / 2, H / 2, 280, fill=1, stroke=0)

    c.setFont('KR-X', 36); c.setFillColor(white)
    c.drawCentredString(W / 2, H / 2 + 30, '백연우')
    c.setFont('KR', 13); c.setFillColor(C_LAV_MID)
    c.drawCentredString(W / 2, H / 2 - 2, '2D Character & Brand Designer')
    c.setStrokeColor(C_LAV_DARK); c.setLineWidth(0.8)
    c.line(MARGIN + 80, H / 2 - 20, W - MARGIN - 80, H / 2 - 20)

    cy = H / 2 - 40
    for ct in ['✉  ellieback1030@gmail.com', '📷  @dinong.official']:
        c.setFont('KR', 10); c.setFillColor(HexColor('#C4B5F4'))
        c.drawCentredString(W / 2, cy, ct); cy -= 18

    c.setFont('KR', 8); c.setFillColor(HexColor('#FFFFFF40'))
    c.drawCentredString(W / 2, 30, '© 2026 Back Yeonwoo. All rights reserved.')
    c.showPage()


# ── Main ────────────────────────────────────────────────

def build_pdf():
    register_fonts()
    cv = canvas.Canvas(OUT_PDF, pagesize=A4)
    cv.setTitle('백연우 Portfolio 2026')
    cv.setAuthor('Baek Yeon Woo')
    cv.setSubject('2D Character & Brand Designer Portfolio')

    page_cover(cv)
    page_about(cv)
    page_career(cv)
    page_awards(cv)

    projects = [
        # (divider args, content args)
        (
            ("교육 게임 디자인", "교육컨텐츠 제작회사 'S'사", "영어교육용 게임 캐릭터 / 배경 / UI 디자인", "소프트플렉스 · 6년"),
            ("소프트플렉스 'S'사", "영어 학습 게임 캐릭터 & Sprite", "캐릭터 디자인 · Tilemap · 배경 · UI 디자인", ["p17.png", "p18.png"], "소프트플렉스", False, False),
        ),
        (
            ("교육 게임 디자인", "교육컨텐츠 제작회사 'J'사", "수학교육용 게임 배경 / UI / 캐릭터 디자인", "주식회사 조이스터디"),
            ("조이스터디 'J'사", "수학 학습 RPG 게임 디자인", "배경 디자인 · Tilemap · UI · 마스코트 캐릭터", ["p19.png", "p20.png"], "주식회사 조이스터디", False, True),
        ),
        (
            ("브랜드 마케팅", "GS리테일 〈어바웃펫〉", "네발가족 인스타툰 캐릭터디자인 · 연재", "GS Retail About Pet"),
            ("GS리테일 어바웃펫", "네발가족 인스타툰 캐릭터 & 콘텐츠", "캐릭터 컨셉 디자인 · 인스타툰 연재", ["p13.png", "p14.png"], "GS Retail", True, False),
        ),
        (
            ("브랜드 마케팅", "메가MGC커피", "협찬 인스타툰 제작", "Mega MGC Coffee"),
            ("메가MGC커피", "협찬 인스타툰 콘텐츠", "브랜드 후원 마케팅 콘텐츠 제작", ["p15.png"], "Mega MGC Coffee", False, True),
        ),
        (
            ("마케팅 · 캐릭터", "블록체인회사 'E'사", "Dorothy 마스코트 캐릭터 7종 · 마케팅 디자인", "에덴파트너스코리아"),
            ("에덴파트너스코리아 'E'사", "Dorothy 마스코트 캐릭터", "블록체인 게임 UI 11종 · 마스코트 캐릭터 제작", ["p07.png"], "에덴파트너스코리아", False, False),
        ),
        (
            ("공공기관 마스코트", "경기도청 〈봉공이〉", "G-FAIR 마스코트 캐릭터 바리에이션 디자인", "경기도청 G-FAIR"),
            ("경기도청 봉공이 G-FAIR", "공공기관 마스코트 캐릭터 디자인", "경기도청 G-FAIR 마스코트 봉공이 바리에이션", ["p16.png"], "경기도청 G-FAIR", False, True),
        ),
        (
            ("외주 캐릭터", "디담커뮤니케이션 〈물드리미〉", "캐릭터 디자인 · 다양한 감정 표현 8종", "디담커뮤니케이션"),
            ("물드리미 캐릭터", "외주 캐릭터 디자인", "다양한 감정 표현 캐릭터 8종 제작", ["p12.png"], "디담커뮤니케이션", False, False),
        ),
        (
            ("공공기관 웹툰", "행정안전부 실패박람회", "다시인 서포터즈 · 재도전 다이어리 인스타툰 · 장관상", "행정안전부 · 2021"),
            ("실패박람회 인스타툰", "행정안전부 실패박람회 다시인 서포터즈", "재도전 다이어리 인스타툰 · 행정안전부 장관상 수상", ["p11.png"], "행정안전부", False, True),
        ),
        (
            ("개인작업 · 인스타툰", "인스타툰 연재", "@dinong.official · 후쿠오카에 가다 · 일상툰 · 리뷰툰", "팔로워 6,000+ · 752게시물"),
            ("인스타툰 연재 @dinong.official", "개인 인스타툰 창작 활동", "후쿠오카에 가다 · 일상 인스타툰 · 리뷰툰 연재", ["p10.png"], "@dinong.official", False, False),
        ),
        (
            ("개인작업 · 캐릭터", "조선호랑이 〈강산이〉", "호랑이 캐릭터 원화 · 굿즈 디자인", "아크릴 키링 · 카드 · 개인 굿즈"),
            ("조선호랑이 강산이", "개인 캐릭터 디자인 & 굿즈", "호랑이 캐릭터 원화 · 아크릴 키링 · 카드 등 굿즈", ["p08.png", "p09.png"], "개인작업", True, True),
        ),
    ]

    page_num = 5
    for div_args, cont_args in projects:
        project_divider(cv, page_num, *div_args)
        page_num += 1
        t, s, d, imgs, client, two_col, alt = cont_args
        project_page(cv, page_num, div_args[0], t, s, imgs,
                     client=client, two_col=two_col, alt_bg=alt)
        page_num += 1

    page_back_cover(cv)
    cv.save()
    print(f"✓ PDF saved: {OUT_PDF}")
    print(f"  Pages: {page_num - 1}  |  File: {os.path.getsize(OUT_PDF) / 1024 / 1024:.1f} MB")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='백연우 Portfolio PDF Generator')
    parser.add_argument('--setup-fonts', action='store_true',
                        help='Download and extract font files (run once)')
    args = parser.parse_args()

    if args.setup_fonts:
        setup_fonts()
    else:
        build_pdf()
