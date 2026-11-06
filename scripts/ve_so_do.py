"""Vẽ các sơ đồ phân tích thiết kế (SVG + PNG) vào docs/so-do/.

Cần pymupdf (đo độ rộng chữ, chuyển SVG sang PNG) và font Arial của Windows.
Chạy: python scripts/ve_so_do.py [tên_sơ_đồ ...]   (không truyền tên = vẽ tất cả)
"""
import math
import sys
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "so-do"

FONT_R = fitz.Font(fontfile="C:/Windows/Fonts/arial.ttf")
FONT_B = fitz.Font(fontfile="C:/Windows/Fonts/arialbd.ttf")

INK = "#1F1F1F"
MUTED = "#595959"
BLUE = "#2F5597"
BLUE_FILL = "#DEEAF6"
GROUP_FILL = "#BDD7EE"
ORANGE = "#C55A11"
ORANGE_FILL = "#FBE5D6"
GREEN = "#548235"
GREEN_FILL = "#E2F0D9"
GRAY = "#7F7F7F"
GRAY_FILL = "#F2F2F2"


def tw(s, size, bold=False):
    return (FONT_B if bold else FONT_R).text_length(s, fontsize=size)


def wrap(s, size, maxw, bold=False):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if cur and tw(trial, size, bold) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Canvas:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    # ---- hình cơ bản ----
    def rect(self, x, y, w, h, fill="#FFFFFF", stroke=BLUE, sw=1.5, rx=6, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def ellipse(self, cx, cy, rx, ry, fill="#FFFFFF", stroke=BLUE, sw=1.5):
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, cx, cy, r, fill="#FFFFFF", stroke=BLUE, sw=1.5):
        self.ellipse(cx, cy, r, r, fill, stroke, sw)

    def polygon(self, pts, fill="#FFFFFF", stroke=BLUE, sw=1.5):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, pts, stroke=INK, sw=1.4, dash=None):
        if dash:  # tự chia nét: trình chuyển SVG sang PNG bỏ qua stroke-dasharray
            on, off = (float(v) for v in dash.split())
            d = []
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                L = math.hypot(x2 - x1, y2 - y1)
                t = 0.0
                while t < L:
                    t2 = min(t + on, L)
                    d.append(f"M{x1 + (x2 - x1) * t / L:.1f},{y1 + (y2 - y1) * t / L:.1f}"
                             f"L{x1 + (x2 - x1) * t2 / L:.1f},{y1 + (y2 - y1) * t2 / L:.1f}")
                    t += on + off
            self.add(f'<path d="{"".join(d)}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>')
            return
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=15, anchor="middle", bold=False, fill=INK, italic=False):
        st = ' font-weight="bold"' if bold else ""
        it = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{st}{it}>{esc(s)}</text>')

    def block(self, cx, cy, lines, size=15, bold=False, fill=INK, lh=1.28, anchor="middle", x=None):
        """Nhiều dòng chữ, căn giữa theo chiều dọc quanh cy."""
        total = (len(lines) - 1) * size * lh
        y0 = cy - total / 2 + size * 0.36
        for i, l in enumerate(lines):
            self.text(cx if x is None else x, y0 + i * size * lh, l, size, anchor, bold, fill)

    def label(self, x, y, s, size=13, fill=MUTED, italic=False, bg="#FFFFFF", anchor="middle"):
        w = tw(s, size) + 8
        lx = x - w / 2 if anchor == "middle" else (x - 4 if anchor == "start" else x - w + 4)
        self.add(f'<rect x="{lx:.1f}" y="{y - size * 0.95:.1f}" width="{w:.1f}" height="{size * 1.3:.1f}" fill="{bg}" stroke="none"/>')
        self.text(x, y, s, size, anchor, False, fill, italic)

    # ---- mũi tên ----
    def head(self, p, q, size=11, fill=INK, open_=False, sw=1.4):
        """Đầu mũi tên tại q, hướng từ p tới q."""
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        bx, by = q[0] - size * math.cos(ang), q[1] - size * math.sin(ang)
        px, py = -math.sin(ang) * size * 0.45, math.cos(ang) * size * 0.45
        pts = [(bx + px, by + py), q, (bx - px, by - py)]
        if open_:
            self.line(pts, fill, sw)
        else:
            self.polygon(pts, fill, fill, 1)

    def arrow(self, pts, stroke=INK, sw=1.4, dash=None, open_=False, both=False, size=11):
        self.line(pts, stroke, sw, dash)
        self.head(pts[-2], pts[-1], size, stroke, open_, sw)
        if both:
            self.head(pts[1], pts[0], size, stroke, open_, sw)

    def save(self, name, dpi=192):
        OUT.mkdir(parents=True, exist_ok=True)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
               f'<rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>' + "".join(self.items) + "</svg>")
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        doc = fitz.open(OUT / f"{name}.svg")
        doc[0].get_pixmap(dpi=dpi).save(OUT / f"{name}.png")
        print(f"{name}: {self.w}x{self.h}")


# ---- hình học: cắt đường thẳng tại biên hình ----
def rect_shape(x, y, w, h):
    return {"kind": "rect", "x": x, "y": y, "w": w, "h": h, "cx": x + w / 2, "cy": y + h / 2}


def circle_shape(cx, cy, r):
    return {"kind": "circle", "cx": cx, "cy": cy, "r": r}


def ellipse_shape(cx, cy, rx, ry):
    return {"kind": "ellipse", "cx": cx, "cy": cy, "rx": rx, "ry": ry}


def inside(s, x, y):
    if s["kind"] == "rect":
        return s["x"] <= x <= s["x"] + s["w"] and s["y"] <= y <= s["y"] + s["h"]
    if s["kind"] == "circle":
        return (x - s["cx"]) ** 2 + (y - s["cy"]) ** 2 <= s["r"] ** 2
    return ((x - s["cx"]) / s["rx"]) ** 2 + ((y - s["cy"]) / s["ry"]) ** 2 <= 1


def clip(a, b, offset=0.0, gap=2.0):
    """Đoạn nối tâm a -> tâm b, dịch song song `offset`, cắt tại biên hai hình."""
    ax, ay, bx, by = a["cx"], a["cy"], b["cx"], b["cy"]
    L = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / L, (bx - ax) / L
    ax, ay, bx, by = ax + nx * offset, ay + ny * offset, bx + nx * offset, by + ny * offset
    n = int(L * 2)
    pts = [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n + 1)]
    start = next(p for p in pts if not inside(a, *p))
    end = next(p for p in reversed(pts) if not inside(b, *p))
    ux, uy = (bx - ax) / L, (by - ay) / L
    return (start[0] + ux * gap, start[1] + uy * gap), (end[0] - ux * gap, end[1] - uy * gap)


# =====================================================================
# 1. Sơ đồ phân rã chức năng
# =====================================================================
def bfd():
    groups = [
        ("Quản lý hồ sơ người dùng", ["Đăng ký, đăng nhập", "Nhập hồ sơ cá nhân", "Chọn chế độ ăn (10 kiểu), món kiêng, ngân sách",
                                      "Chọn số bữa mỗi ngày (2–6)", "Tính BMR, TDEE và macro"]),
        ("Lập thực đơn", ["Phân tích yêu cầu tiếng Việt (M1)", "Chấm điểm món phù hợp (M2)", "Tối ưu chọn món và định lượng gam (M3)",
                          "Lập thực đơn theo ngày", "Lập thực đơn theo tuần"]),
        ("Đồ có sẵn và đi chợ", ["Khai báo thực phẩm có sẵn", "Ưu tiên dùng thực phẩm có sẵn", "Lập danh sách đi chợ theo ngày, tuần"]),
        ("Nhật ký ăn uống", ["Ghi nhật ký bằng câu tiếng Việt", "Quy đổi khẩu phần ra gam", "Tính lại các bữa còn lại", "Xem lịch sử, tổng kết ngày"]),
        ("Phản hồi và cá nhân hóa", ["Giữ, đổi, bỏ món", "Gợi ý món thay thế tương đương", "Cập nhật sở thích (M4)"]),
        ("Quản lý dữ liệu", ["Quản lý nguyên liệu và dinh dưỡng", "Quản lý món và công thức", "Quản lý chế độ ăn và quy tắc",
                             "Quản lý bảng quy đổi khẩu phần", "Kiểm tra chất lượng dữ liệu"]),
        ("Huấn luyện và đánh giá mô hình", ["Huấn luyện M1, M2", "Đánh giá, so sánh với baseline", "Triển khai, cập nhật mô hình"]),
    ]
    CW, GAP, M = 200, 16, 24
    W = M * 2 + len(groups) * CW + (len(groups) - 1) * GAP
    c = Canvas(W, 100)
    rw, rh, ry = 560, 58, 24
    c.rect(W / 2 - rw / 2, ry, rw, rh, fill=BLUE, stroke=BLUE, sw=1.5)
    c.block(W / 2, ry + rh / 2, ["HỆ THỐNG GỢI Ý THỰC ĐƠN CÁ NHÂN HÓA"], 19, True, "#FFFFFF")
    bus_y, gy, gh = 122, 148, 66
    c.line([(W / 2, ry + rh), (W / 2, bus_y)], BLUE, 1.6)
    centers, ymax = [], 0
    for i, (title, children) in enumerate(groups):
        x = M + i * (CW + GAP)
        cx = x + CW / 2
        centers.append(cx)
        c.line([(cx, bus_y), (cx, gy)], BLUE, 1.6)
        c.rect(x, gy, CW, gh, fill=GROUP_FILL, stroke=BLUE, sw=1.6)
        c.block(cx, gy + gh / 2, wrap(f"{i + 1}. {title}", 15.5, CW - 18, True), 15.5, True)
        spine = x + 14
        y, last = gy + gh + 16, None
        for j, s in enumerate(children):
            bx, bw = x + 30, CW - 30
            lines = wrap(f"{i + 1}.{j + 1}. {s}", 14.5, bw - 16)
            h = max(46, len(lines) * 14.5 * 1.28 + 18)
            c.rect(bx, y, bw, h, fill="#FFFFFF", stroke=BLUE, sw=1.2)
            c.block(bx + bw / 2, y + h / 2, lines, 14.5)
            c.line([(spine, y + h / 2), (bx, y + h / 2)], BLUE, 1.2)
            last = y + h / 2
            y += h + 12
        c.line([(spine, gy + gh), (spine, last)], BLUE, 1.2)
        ymax = max(ymax, y)
    c.line([(centers[0], bus_y), (centers[-1], bus_y)], BLUE, 1.6)
    c.h = int(ymax + 14)
    c.save("1-phan-ra-chuc-nang")


# =====================================================================
# 2. Sơ đồ use case
# =====================================================================
def usecase():
    W, H = 1240, 1290
    c = Canvas(W, H)
    bx, by, bw, bh = 250, 30, 960, 1240
    c.rect(bx, by, bw, bh, fill="#FAFBFD", stroke=GRAY, sw=1.4, rx=10)
    c.text(bx + bw / 2, by + 30, "Hệ thống gợi ý thực đơn cá nhân hóa", 17, bold=True, fill=MUTED)
    RX, RY = 128, 30
    col1, col2 = 480, 950

    def uc(cx, cy, name, fill="#FFFFFF"):
        c.ellipse(cx, cy, RX, RY, fill=fill, stroke=BLUE, sw=1.5)
        c.block(cx, cy, wrap(name, 14.5, RX * 1.6), 14.5)
        return ellipse_shape(cx, cy, RX, RY)

    login = uc(col1, 120, "Đăng nhập")
    U = [uc(col1, y, n) for y, n in zip([200, 280, 360, 440, 520, 600, 680, 760], [
        "Cập nhật hồ sơ", "Chọn chế độ ăn, số bữa", "Xem nhu cầu năng lượng", "Lập thực đơn ngày hoặc tuần",
        "Khai báo thực phẩm có sẵn", "Ghi nhật ký ăn uống", "Đổi, bỏ món", "Xem lịch sử ăn uống"])]
    A = [uc(col1, y, n) for y, n in zip([880, 960, 1040, 1120, 1200], [
        "Quản lý nguyên liệu", "Quản lý món và công thức", "Quản lý chế độ ăn",
        "Huấn luyện, cập nhật mô hình", "Xem báo cáo đánh giá mô hình"])]
    I = {k: uc(col2, y, n, BLUE_FILL) for k, y, n in [
        ("energy", 250, "Tính nhu cầu năng lượng"), ("shop", 390, "Xem danh sách đi chợ"), ("nlp", 520, "Phân tích câu tiếng Việt"),
        ("replan", 640, "Tính lại các bữa còn lại"), ("pref", 740, "Cập nhật sở thích")]}

    def stick(x, y, name):
        c.circle(x, y - 46, 14, fill="#FFFFFF", stroke=INK, sw=1.6)
        c.line([(x, y - 32), (x, y + 4)], INK, 1.6)
        c.line([(x - 22, y - 20), (x + 22, y - 20)], INK, 1.6)
        c.line([(x - 18, y + 34), (x, y + 4), (x + 18, y + 34)], INK, 1.6)
        c.text(x, y + 56, name, 16, bold=True)

    ux, uy, ax, ay = 110, 440, 110, 1040
    stick(ux, uy, "Người dùng")
    stick(ax, ay, "Quản trị viên")
    for t in [login] + U:
        c.line([(ux + 26, uy - 14), (t["cx"] - RX, t["cy"])], INK, 1.3)
    for t in A:
        c.line([(ax + 26, ay - 14), (t["cx"] - RX, t["cy"])], INK, 1.3)
    c.line([(ax, ay - 62), (ax, uy + 78)], INK, 1.4)
    c.polygon([(ax, uy + 64), (ax - 9, uy + 80), (ax + 9, uy + 80)], fill="#FFFFFF", stroke=INK, sw=1.4)

    def rel(a, b, kind):
        p, q = clip(a, b)
        c.arrow([p, q], MUTED, 1.3, dash="7 5", open_=True)
        c.label((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 4, f"«{kind}»", 12.5, italic=True)

    rel(U[0], I["energy"], "include")
    rel(U[1], I["energy"], "include")
    rel(U[2], I["energy"], "include")
    rel(U[3], I["energy"], "include")
    rel(I["shop"], U[3], "extend")
    rel(U[3], I["nlp"], "include")
    rel(U[5], I["nlp"], "include")
    rel(U[5], I["replan"], "include")
    rel(U[6], I["pref"], "include")
    c.save("2-use-case")


# =====================================================================
# 3. DFD mức ngữ cảnh
# =====================================================================
def entity(c, x, y, w, h, lines, size=15.5):
    c.rect(x, y, w, h, fill=ORANGE_FILL, stroke=ORANGE, sw=1.6, rx=2)
    c.block(x + w / 2, y + h / 2, lines, size, True)
    return rect_shape(x, y, w, h)


def flow_label(c, p, q, text, side=1, dist=16, size=13, maxw=230):
    """Nhãn luồng đặt cạnh đoạn p-q, lệch sang một phía."""
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    nx, ny = -(q[1] - p[1]) / L * side, (q[0] - p[0]) / L * side
    lines = wrap(text, size, maxw)
    cx, cy = mx + nx * (dist + len(lines) * size * 0.6), my + ny * (dist + len(lines) * size * 0.6)
    for i, l in enumerate(lines):
        c.label(cx, cy - (len(lines) - 1) * size * 0.65 + i * size * 1.3 + size * 0.35, l, size)


def dfd_context():
    W, H = 1440, 760
    c = Canvas(W, H)
    P = circle_shape(720, 390, 128)
    c.circle(720, 390, 128, fill=BLUE_FILL, stroke=BLUE, sw=2)
    c.block(720, 390, ["0", "Hệ thống gợi ý", "thực đơn cá nhân hóa"], 17, True)
    user = entity(c, 40, 355, 190, 70, ["Người dùng"])
    admin = entity(c, 1210, 355, 190, 70, ["Quản trị viên"])
    vdd = entity(c, 230, 50, 250, 70, ["Viện Dinh dưỡng"])
    usda = entity(c, 960, 50, 250, 70, ["USDA FoodData", "Central"])
    fc = entity(c, 595, 640, 250, 70, ["Food.com (Kaggle)"])

    def flow(a, b, text, off, side, maxw=230):
        p, q = clip(a, b, off)
        c.arrow([p, q], INK, 1.5)
        straight = abs(p[1] - q[1]) < 2 or abs(p[0] - q[0]) < 2
        flow_label(c, p, q, text, side, dist=16 if straight else 34, maxw=maxw)

    flow(user, P, "Hồ sơ, yêu cầu, nhật ký ăn uống, phản hồi về món", -18, -1)
    flow(P, user, "Nhu cầu năng lượng, thực đơn, định lượng gam, danh sách đi chợ", -18, -1)
    flow(admin, P, "Dữ liệu món, công thức, lệnh huấn luyện", 18, 1)
    flow(P, admin, "Báo cáo dữ liệu, kết quả đánh giá mô hình", 18, 1)
    flow(vdd, P, "Bảng thành phần 853 thực phẩm", 0, 1, 200)
    flow(usda, P, "Thực phẩm bổ sung (ức gà, cơm chín)", 0, -1, 200)
    flow(fc, P, "Tương tác người dùng – công thức", 0, -1, 200)
    c.save("3-dfd-muc-ngu-canh")


# =====================================================================
# 4. DFD mức 0
# =====================================================================
def process(c, x, y, w, h, num, name):
    c.rect(x, y, w, h, fill=BLUE_FILL, stroke=BLUE, sw=1.6, rx=14)
    c.line([(x, y + 26), (x + w, y + 26)], BLUE, 1.2)
    c.text(x + w / 2, y + 19, num, 14, bold=True, fill=BLUE)
    c.block(x + w / 2, y + 26 + (h - 26) / 2, wrap(name, 14.5, w - 16, True), 14.5, True)
    return rect_shape(x, y, w, h)


def store(c, x, y, w, h, num, name):
    c.rect(x, y, w, h, fill=GRAY_FILL, stroke=GRAY, sw=1.4, rx=0)
    c.line([(x + 46, y), (x + 46, y + h)], GRAY, 1.4)
    c.text(x + 23, y + h / 2 + 5, num, 14, bold=True)
    c.text(x + 46 + (w - 46) / 2, y + h / 2 + 5, name, 14.5)
    return rect_shape(x, y, w, h)


def dfd_level0():
    W, H = 1700, 1000
    c = Canvas(W, H)
    entity(c, 30, 700, 170, 66, ["Người dùng"])
    entity(c, 1300, 920, 160, 60, ["Quản trị viên"], 15)
    entity(c, 1490, 920, 170, 60, ["Nguồn dữ liệu", "ngoài"], 14)

    process(c, 300, 60, 230, 92, "1.0", "Quản lý hồ sơ, tính nhu cầu năng lượng")
    process(c, 300, 300, 230, 92, "2.0", "Phân tích ngôn ngữ (M1)")
    process(c, 300, 540, 230, 92, "5.0", "Ghi nhật ký ăn uống")
    process(c, 300, 780, 230, 92, "6.0", "Học từ phản hồi (M4)")
    process(c, 680, 400, 230, 92, "4.0", "Tối ưu thực đơn (M3)")
    process(c, 1000, 780, 230, 92, "3.0", "Gợi ý món (M2)")
    process(c, 1360, 780, 240, 92, "7.0", "Quản lý dữ liệu dinh dưỡng")
    store(c, 680, 84, 230, 44, "D1", "Người dùng")
    store(c, 300, 660, 230, 44, "D5", "Nhật ký")
    store(c, 680, 804, 230, 44, "D6", "Sở thích, phản hồi")
    store(c, 1000, 540, 230, 44, "D4", "Thực đơn")
    store(c, 1360, 200, 240, 44, "D2", "Nguyên liệu")
    store(c, 1360, 600, 260, 44, "D3", "Món ăn và công thức")

    def f(pts, text=None, at=None, anchor="middle"):
        c.arrow(pts, INK, 1.4)
        if text:
            c.label(at[0], at[1], text, 13, anchor=anchor)

    # Người dùng
    f([(115, 700), (115, 106), (300, 106)], "Hồ sơ", (115, 300))
    f([(200, 716), (250, 716), (250, 346), (300, 346)], "Câu yêu cầu, nhật ký", (250, 470))
    f([(115, 766), (115, 826), (300, 826)], "Giữ / đổi / bỏ món", (205, 816))
    f([(760, 492), (760, 742), (200, 742)], "Thực đơn, danh sách đi chợ", (600, 734))
    # 1.0, 2.0, 5.0
    f([(530, 106), (680, 106)], "Hồ sơ, mục tiêu", (605, 97))
    f([(530, 135), (620, 135), (620, 418), (680, 418)], "Mục tiêu kcal, macro", (620, 260))
    f([(415, 300), (415, 152)], "Thông tin hồ sơ", (415, 232))
    f([(530, 365), (590, 365), (590, 446), (680, 446)], "Ràng buộc", (635, 470))
    f([(415, 392), (415, 540)], "Món, số lượng, đơn vị", (415, 470))
    f([(415, 632), (415, 660)])
    f([(530, 586), (700, 586), (700, 492)], "Calo đã ăn", (612, 578))
    # 6.0 -> D6 -> 3.0 -> 4.0
    f([(530, 826), (680, 826)], "Sở thích", (605, 818))
    f([(910, 826), (1000, 826)])
    f([(1230, 800), (1260, 800), (1260, 476), (910, 476)], "Điểm món", (1000, 468))
    # D2, D3 -> 4.0 ; D3 -> 3.0 ; 4.0 -> D4
    f([(1360, 222), (1320, 222), (1320, 412), (910, 412)], "Dinh dưỡng", (1180, 404))
    f([(1360, 612), (1290, 612), (1290, 446), (910, 446)], "Công thức, khoảng gam", (1110, 438))
    f([(1360, 636), (1300, 636), (1300, 846), (1230, 846)], "Đặc trưng món", (1308, 742), "start")
    f([(880, 492), (880, 562), (1000, 562)], "Thực đơn", (940, 554))
    # 7.0
    f([(1480, 780), (1480, 644)], "Món, công thức", (1490, 714), "start")
    f([(1600, 800), (1650, 800), (1650, 222), (1600, 222)], "Nguyên liệu", (1650, 500))
    f([(1380, 920), (1380, 872)], "Dữ liệu món, nguyên liệu", (1386, 900), "start")
    f([(1575, 920), (1575, 872)])
    c.text(1583, 904, "Bảng dinh dưỡng", 13, anchor="start", fill=MUTED)
    c.save("4-dfd-muc-0")


# =====================================================================
# 5. ERD
# =====================================================================
ENTITIES = {
    "NGUOI_DUNG": [("ma_nd", "PK"), ("ma_cda", "FK"), ("ho_ten", ""), ("gioi_tinh", ""), ("ngay_sinh", ""), ("can_nang", ""),
                   ("chieu_cao", ""), ("muc_van_dong", ""), ("muc_tieu", ""), ("so_bua", ""), ("ngan_sach", "")],
    "CHE_DO_AN": [("ma_cda", "PK"), ("ten", ""), ("ty_le_beo", ""), ("ty_le_tinh_bot", ""), ("tran_tinh_bot", ""),
                  ("nhom_loai_tru", ""), ("gioi_han_tuan", "")],
    "THUC_PHAM_CO_SAN": [("ma_nd", "PK, FK"), ("ma_nl", "PK, FK"), ("so_gam", ""), ("han_dung", "")],
    "KIENG": [("ma_nd", "PK, FK"), ("ma_nl", "PK, FK")],
    "NGUYEN_LIEU": [("ma_nl", "PK"), ("ten", ""), ("nhom", ""), ("kcal", ""), ("dam", ""), ("beo", ""), ("tinh_bot", ""), ("xo", ""),
                    ("nguon", ""), ("co_canh_bao", "")],
    "CONG_THUC": [("ma_mon", "PK, FK"), ("ma_nl", "PK, FK"), ("gam_mac_dinh", ""), ("gam_min", ""), ("gam_max", "")],
    "DINH_LUONG": [("ma_td", "PK, FK"), ("bua", "PK, FK"), ("ma_mon", "PK, FK"), ("ma_nl", "PK, FK"), ("gam", "")],
    "THUC_DON": [("ma_td", "PK"), ("ma_nd", "FK"), ("ngay", ""), ("ma_tuan", ""), ("kcal_muc_tieu", ""), ("kcal_dat", "")],
    "CHI_TIET_THUC_DON": [("ma_td", "PK, FK"), ("bua", "PK"), ("ma_mon", "PK, FK")],
    "MON_AN": [("ma_mon", "PK"), ("ten", ""), ("nhom", ""), ("bua_phu_hop", ""), ("chay", ""), ("thuy_san", ""), ("ma_vdd_mon", "")],
    "NHAT_KY": [("ma_nk", "PK"), ("ma_nd", "FK"), ("ma_mon", "FK"), ("thoi_gian", ""), ("bua", ""), ("so_luong", ""), ("don_vi", ""),
                ("gam_quy_doi", "")],
    "PHAN_HOI": [("ma_ph", "PK"), ("ma_nd", "FK"), ("ma_mon", "FK"), ("hanh_dong", ""), ("thoi_gian", "")],
    "QUY_DOI": [("ma_mon", "PK, FK"), ("don_vi", "PK"), ("gam", "")],
}


def entity_box(c, name, x, y, w):
    attrs = ENTITIES[name]
    hh, rh = 34, 23
    h = hh + rh * len(attrs) + 8
    c.rect(x, y, w, h, fill="#FFFFFF", stroke=BLUE, sw=1.6, rx=4)
    c.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{hh}" rx="4" fill="{BLUE}" stroke="{BLUE}" stroke-width="1.6"/>')
    c.add(f'<rect x="{x:.1f}" y="{y + hh - 6:.1f}" width="{w:.1f}" height="6" fill="{BLUE}"/>')
    c.text(x + w / 2, y + 23, name, 15, bold=True, fill="#FFFFFF")
    for i, (a, key) in enumerate(attrs):
        ty = y + hh + 4 + rh * i + 16
        c.text(x + 12, ty, a, 14, anchor="start", bold="PK" in key)
        if key:
            c.text(x + w - 10, ty, key, 12, anchor="end", fill=ORANGE if "FK" in key else BLUE, bold=True)
    return {"x": x, "y": y, "w": w, "h": h}


def crow(c, p, direction, kind):
    """Ký hiệu chân chim tại điểm p; direction = hướng từ thực thể đi ra (đơn vị)."""
    dx, dy = direction
    px, py = -dy, dx
    if kind == "many":
        tip = (p[0] + dx * 16, p[1] + dy * 16)
        for s in (-9, 0, 9):
            c.line([tip, (p[0] + px * s, p[1] + py * s)], INK, 1.4)
        b = (p[0] + dx * 22, p[1] + dy * 22)
        c.line([(b[0] + px * 8, b[1] + py * 8), (b[0] - px * 8, b[1] - py * 8)], INK, 1.4)  # bắt buộc: ít nhất 1
    else:
        for d in (10, 16):
            b = (p[0] + dx * d, p[1] + dy * d)
            c.line([(b[0] + px * 8, b[1] + py * 8), (b[0] - px * 8, b[1] - py * 8)], INK, 1.4)


def rel(c, pts, one_end, many_end, label=None, at=None):
    """pts: đường gấp khúc từ phía 'một' tới phía 'nhiều'."""
    c.line(pts, INK, 1.4)
    d1 = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
    L1 = math.hypot(*d1)
    crow(c, pts[0], (d1[0] / L1, d1[1] / L1), one_end)
    d2 = (pts[-2][0] - pts[-1][0], pts[-2][1] - pts[-1][1])
    L2 = math.hypot(*d2)
    crow(c, pts[-1], (d2[0] / L2, d2[1] / L2), many_end)
    if label:
        c.label(at[0], at[1], label, 12.5, italic=True)


def erd():
    W, H = 1500, 1150
    c = Canvas(W, H)
    w = 250
    col = [40, 410, 780, 1150]
    E = {}
    E["KIENG"] = entity_box(c, "KIENG", col[1], 40, w)
    E["THUC_PHAM_CO_SAN"] = entity_box(c, "THUC_PHAM_CO_SAN", col[1], 165, w)
    E["CHE_DO_AN"] = entity_box(c, "CHE_DO_AN", 30, 40, 200)
    E["NGUYEN_LIEU"] = entity_box(c, "NGUYEN_LIEU", col[2], 40, w)
    E["CONG_THUC"] = entity_box(c, "CONG_THUC", col[3], 40, w)
    E["DINH_LUONG"] = entity_box(c, "DINH_LUONG", col[2], 345, w)
    E["NGUOI_DUNG"] = entity_box(c, "NGUOI_DUNG", col[0], 330, w)
    E["THUC_DON"] = entity_box(c, "THUC_DON", col[1], 560, w)
    E["CHI_TIET_THUC_DON"] = entity_box(c, "CHI_TIET_THUC_DON", col[2], 590, w)
    E["MON_AN"] = entity_box(c, "MON_AN", col[3], 560, w)
    E["NHAT_KY"] = entity_box(c, "NHAT_KY", col[1], 860, w)
    E["PHAN_HOI"] = entity_box(c, "PHAN_HOI", col[2], 860, w)
    E["QUY_DOI"] = entity_box(c, "QUY_DOI", col[3], 920, w)

    def mid_l(e, dy=None):
        return (e["x"], e["y"] + (e["h"] / 2 if dy is None else dy))

    def mid_r(e, dy=None):
        return (e["x"] + e["w"], e["y"] + (e["h"] / 2 if dy is None else dy))

    def top(e, dx=None):
        return (e["x"] + (e["w"] / 2 if dx is None else dx), e["y"])

    def bot(e, dx=None):
        return (e["x"] + (e["w"] / 2 if dx is None else dx), e["y"] + e["h"])

    nd, nl = E["NGUOI_DUNG"], E["NGUYEN_LIEU"]
    # CHE_DO_AN 1 - n NGUOI_DUNG
    cda = E["CHE_DO_AN"]
    rel(c, [bot(cda, 100), (cda["x"] + 100, nd["y"])], "one", "many", "theo", (cda["x"] + 100, (cda["y"] + cda["h"] + nd["y"]) / 2))
    # NGUOI_DUNG 1 - n KIENG, THUC_PHAM_CO_SAN ; NGUYEN_LIEU 1 - n mỗi bảng
    rel(c, [top(nd, 210), (nd["x"] + 210, 84), (E["KIENG"]["x"], 84)], "one", "many", "kiêng", (330, 76))
    tp = E["THUC_PHAM_CO_SAN"]
    tp_mid = tp["y"] + tp["h"] / 2
    rel(c, [top(nd, 235), (nd["x"] + 235, tp_mid), (tp["x"], tp_mid)], "one", "many", "có sẵn", (340, tp_mid - 8))
    rel(c, [mid_l(nl, tp_mid - nl["y"]), mid_r(tp, tp["h"] / 2)], "one", "many")
    rel(c, [mid_l(nl, 60), mid_r(E["KIENG"], 60)], "one", "many")
    # NGUYEN_LIEU 1 - n CONG_THUC ; MON_AN 1 - n CONG_THUC
    rel(c, [mid_r(nl, 60), mid_l(E["CONG_THUC"], 60)], "one", "many")
    rel(c, [top(E["MON_AN"]), bot(E["CONG_THUC"])], "one", "many", "gồm", (1275, 420))
    # NGUYEN_LIEU 1 - n DINH_LUONG ; CHI_TIET 1 - n DINH_LUONG
    rel(c, [bot(nl), top(E["DINH_LUONG"])], "one", "many")
    rel(c, [top(E["CHI_TIET_THUC_DON"]), bot(E["DINH_LUONG"])], "one", "many")
    # NGUOI_DUNG 1 - n THUC_DON ; THUC_DON 1 - n CHI_TIET ; MON_AN 1 - n CHI_TIET
    rel(c, [mid_r(nd, 280), (E["THUC_DON"]["x"], nd["y"] + 280)], "one", "many", "lập", (350, nd["y"] + 272))
    rel(c, [mid_r(E["THUC_DON"], 60), mid_l(E["CHI_TIET_THUC_DON"], 30)], "one", "many")
    rel(c, [mid_l(E["MON_AN"], 60), mid_r(E["CHI_TIET_THUC_DON"], 30)], "one", "many")
    # NGUOI_DUNG 1 - n NHAT_KY, PHAN_HOI
    nk_mid = E["NHAT_KY"]["y"] + E["NHAT_KY"]["h"] / 2
    rel(c, [bot(nd, 170), (nd["x"] + 170, nk_mid), (E["NHAT_KY"]["x"], nk_mid)], "one", "many", "ghi", (330, nk_mid - 8))
    rel(c, [bot(nd, 80), (nd["x"] + 80, 1120), (E["PHAN_HOI"]["x"] + w / 2, 1120), bot(E["PHAN_HOI"])], "one", "many", "phản hồi", (600, 1112))
    # MON_AN 1 - n NHAT_KY, PHAN_HOI, QUY_DOI
    mh = E["MON_AN"]
    rel(c, [bot(mh, 40), (mh["x"] + 40, 815), (E["NHAT_KY"]["x"] + w / 2, 815), top(E["NHAT_KY"])], "one", "many")
    rel(c, [bot(mh, 90), (mh["x"] + 90, 900), mid_r(E["PHAN_HOI"], 40)], "one", "many")
    rel(c, [bot(mh, 180), top(E["QUY_DOI"], 180)], "one", "many", "quy đổi", (1370, 880))
    c.save("5-erd")


# =====================================================================
# 6. Sơ đồ tuần tự: lập thực đơn
# =====================================================================
def sequence():
    parts = ["Người dùng", "Giao diện web", "API (FastAPI)", "M1 Hiểu ngôn ngữ", "Mô-đun TDEE", "M2 Gợi ý món", "M3 Tối ưu", "Cơ sở dữ liệu"]
    U, UI, API, M1, TD, M2, M3, DB = range(8)
    messages = [
        (U, UI, "Nhập câu yêu cầu và hồ sơ", False), (UI, API, "POST /api/plan", False),
        (API, M1, "Phân tích câu", False), (M1, API, "Ý định, ràng buộc (kiêng, chay…)", True),
        (API, TD, "Tính nhu cầu năng lượng", False), (TD, API, "kcal mục tiêu, macro, chia bữa", True),
        (API, M2, "Chấm điểm món theo ràng buộc", False), (M2, DB, "Đọc món, lịch sử, sở thích", False),
        (DB, M2, "Dữ liệu món, sở thích", True), (M2, API, "Điểm phù hợp của từng món", True),
        (API, M3, "Tối ưu (mục tiêu, điểm món)", False), (M3, DB, "Đọc công thức, dinh dưỡng", False),
        (DB, M3, "Công thức, khoảng gam", True), (M3, M3, "Giải MILP; nới ràng buộc nếu vô nghiệm", False),
        (M3, API, "Thực đơn 4 bữa, gam từng nguyên liệu", True), (API, DB, "Lưu thực đơn", False),
        (API, UI, "Thực đơn, danh sách đi chợ", True), (UI, U, "Hiển thị thực đơn", True),
    ]
    GAP = 46
    W = 1520
    top_y, box_h = 24, 50
    first = top_y + box_h + 46
    H = int(first + GAP * len(messages) + 20 + 10)
    bottom = H - 12
    c = Canvas(W, H)
    step = (W - 120) / (len(parts) - 1)
    xs = [60 + i * step for i in range(len(parts))]
    for i, (x, p) in enumerate(zip(xs, parts)):
        bw = 150
        fill = ORANGE_FILL if i == 0 else (GRAY_FILL if i == len(parts) - 1 else BLUE_FILL)
        stroke = ORANGE if i == 0 else (GRAY if i == len(parts) - 1 else BLUE)
        bx = min(max(x - bw / 2, 8), W - bw - 8)
        c.rect(bx, top_y, bw, box_h, fill=fill, stroke=stroke, sw=1.5)
        c.block(bx + bw / 2, top_y + box_h / 2, wrap(p, 14.5, bw - 14, True), 14.5, True)
        c.line([(x, top_y + box_h), (x, bottom)], GRAY, 1.2, dash="6 5")
    y = first
    for n, (a, b, text, ret) in enumerate(messages, 1):
        x1, x2 = xs[a], xs[b]
        if a == b:  # tự gọi
            c.arrow([(x1, y), (x1 + 60, y), (x1 + 60, y + 26), (x1 + 4, y + 26)], INK, 1.4)
            for k, part in enumerate(wrap(f"{n}. {text}", 13, W - x1 - 80)):
                c.label(x1 + 68, y + 8 + k * 17, part, 13, anchor="start")
            y += GAP + 20
            continue
        c.arrow([(x1, y), (x2, y)], INK, 1.4, dash="7 5" if ret else None, open_=ret)
        c.label((x1 + x2) / 2, y - 7, f"{n}. {text}", 13, fill=MUTED if ret else INK)
        y += GAP
    c.save("6-tuan-tu-lap-thuc-don")


# =====================================================================
# 7. Sơ đồ hoạt động: ghi nhật ký và tính lại bữa
# =====================================================================
def activity():
    W, H = 1000, 1240
    c = Canvas(W, H)
    cx, RX, FX = 280, 740, 930
    aw, ah = 330, 54

    def action(y, text, x=None, w=aw, fill=BLUE_FILL):
        x = cx if x is None else x
        c.rect(x - w / 2, y - ah / 2, w, ah, fill=fill, stroke=BLUE, sw=1.5, rx=22)
        c.block(x, y, wrap(text, 14.5, w - 24), 14.5)
        return (x, y)

    def decision(y, text, x=None, r=46):
        x = cx if x is None else x
        c.polygon([(x, y - r), (x + r * 1.9, y), (x, y + r), (x - r * 1.9, y)], fill="#FFF2CC", stroke="#BF9000", sw=1.5)
        c.block(x, y, wrap(text, 13.5, r * 2.6), 13.5)
        return (x, y)

    def down(y1, y2, x=None, guard=None):
        x = cx if x is None else x
        c.arrow([(x, y1), (x, y2)], INK, 1.4)
        if guard:
            c.label(x + 10, (y1 + y2) / 2 + 4, guard, 13, anchor="start")

    c.circle(cx, 40, 14, fill=INK, stroke=INK)
    down(54, 95)
    action(122, "Người dùng gõ câu nhật ký (“trưa ăn 1 bát phở”)")
    down(149, 190)
    action(217, "M1 nhận diện ý định và trích món, số lượng, đơn vị")
    down(244, 292)
    decision(338, "Ý định là GHI_NHAT_KY?")
    action(338, "Chuyển sang xử lý ý định khác", x=RX, w=300, fill=GRAY_FILL)
    c.arrow([(cx + 87, 338), (RX - 150, 338)], INK, 1.4)
    c.label((cx + 87 + RX - 150) / 2, 330, "[không]", 13)
    down(384, 430, guard="[có]")
    action(457, "Tra món trong danh mục 100 món")
    down(484, 530)
    decision(576, "Tìm thấy món?")
    action(576, "Gợi ý các món gần nhất, người dùng chọn", x=RX, w=300, fill=GRAY_FILL)
    c.arrow([(cx + 87, 576), (RX - 150, 576)], INK, 1.4)
    c.label((cx + 87 + RX - 150) / 2, 568, "[không]", 13)
    c.arrow([(RX, 549), (RX, 480), (cx + aw / 2, 480)], INK, 1.4)
    down(622, 668, guard="[có]")
    action(695, "Quy đổi khẩu phần ra gam (bảng QUY_DOI)")
    down(722, 762)
    action(789, "Lưu nhật ký; cộng calo và macro đã ăn")
    down(816, 862)
    decision(908, "Còn bữa chưa ăn?")
    action(908, "Hiển thị tổng kết ngày", x=RX, w=300)
    c.arrow([(cx + 87, 908), (RX - 150, 908)], INK, 1.4)
    c.label((cx + 87 + RX - 150) / 2, 900, "[không]", 13)
    down(954, 1000, guard="[có]")
    action(1027, "Trừ phần đã ăn khỏi mục tiêu; M3 giải lại các bữa còn lại")
    down(1054, 1094)
    action(1121, "Hiển thị thực đơn mới cho các bữa còn lại")
    # điểm kết thúc
    for (ex, ey) in [(cx, 1190), (RX, 1190)]:
        c.circle(ex, ey, 15, fill="#FFFFFF", stroke=INK, sw=1.6)
        c.circle(ex, ey, 9, fill=INK, stroke=INK)
    down(1148, 1175)
    c.arrow([(RX, 935), (RX, 1175)], INK, 1.4)
    c.arrow([(RX, 365), (RX, 400), (FX, 400), (FX, 1190), (RX + 15, 1190)], INK, 1.4)
    c.save("7-hoat-dong-ghi-nhat-ky")


# =====================================================================
# 8. Quy trình dữ liệu và huấn luyện
# =====================================================================
def pipeline():
    W, H = 1560, 640
    c = Canvas(W, H)
    cols = [30, 330, 650, 960, 1270]
    bw, bh = 260, 92
    heads = ["Nguồn dữ liệu", "Tiền xử lý", "Mô hình", "Đánh giá", "Triển khai"]
    for x, h in zip(cols, heads):
        c.text(x + bw / 2, 36, h, 17, bold=True, fill=BLUE)
    rows = [
        ("Viện Dinh dưỡng (853) + USDA (2)", "Làm sạch, gắn cờ 19 dòng lỗi, bổ sung mục thiếu", "M3: MILP chọn món, tính gam", "% thực đơn đạt ±5% calo, ±10% macro; thời gian giải"),
        ("Food.com: 1,13 triệu đánh giá", "Phản hồi ẩn, lọc 5-core, chia train/val/test", "M2: Hybrid content-based + MF/Two-Tower", "Recall@10, NDCG@10 so với baseline phổ biến"),
        ("Câu tiếng Việt: 40 câu mẫu + LLM sinh thêm", "Gán nhãn BIO, tách từ VnCoreNLP", "M1: PhoBERT ý định + thực thể", "F1 theo nhãn; so với luật, LLM few-shot"),
        ("Người dùng mô phỏng", "Sinh hồ sơ và sở thích ẩn", "M4: LinUCB", "Cumulative regret so với ngẫu nhiên, ε-greedy"),
    ]
    ys = [70 + i * 140 for i in range(4)]
    fills = [(ORANGE_FILL, ORANGE), (GRAY_FILL, GRAY), (BLUE_FILL, BLUE), (GREEN_FILL, GREEN)]
    for y, r in zip(ys, rows):
        for k, (x, t) in enumerate(zip(cols[:4], r)):
            f, s = fills[k]
            c.rect(x, y, bw, bh, fill=f, stroke=s, sw=1.5, rx=8)
            c.block(x + bw / 2, y + bh / 2, wrap(t, 14.5, bw - 22, k == 2), 14.5, k == 2)
            if k < 3:
                c.arrow([(x + bw, y + bh / 2), (cols[k + 1], y + bh / 2)], INK, 1.4)
    dx, dy, dh = cols[4], ys[0], ys[3] + bh - ys[0]
    c.rect(dx, dy, bw, dh, fill="#FFFFFF", stroke=BLUE, sw=1.8, rx=10)
    c.block(dx + bw / 2, dy + dh / 2, ["Tích hợp 4 mô-đun", "vào FastAPI", "", "Ứng dụng web", "(Hugging Face Spaces", "hoặc Render)"], 15, True)
    for y in ys:
        c.arrow([(cols[3] + bw, y + bh / 2), (dx, y + bh / 2)], INK, 1.4)
    c.save("8-quy-trinh-du-lieu-huan-luyen")


ALL = {"bfd": bfd, "usecase": usecase, "dfd0": dfd_context, "dfd1": dfd_level0, "erd": erd,
       "sequence": sequence, "activity": activity, "pipeline": pipeline}

if __name__ == "__main__":
    for name in (sys.argv[1:] or ALL):
        ALL[name]()
