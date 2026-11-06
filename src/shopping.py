"""Danh sách đi chợ cho thực đơn ngày hoặc tuần, trừ phần thực phẩm đã có sẵn.

Khối lượng là khối lượng sống, phần ăn được (cùng đơn vị với công thức); làm tròn lên
bội số ROUND_G để dễ mua.
"""
import math
from collections import defaultdict

ROUND_G = 10


def shopping_list(menu_lines, ingredients, pantry=None):
    """menu_lines: [(mã nguyên liệu, gam)] gộp từ mọi món của thực đơn.
    pantry: mã -> gam đang có. Trả về danh sách dòng, món cần mua nhiều nhất trước."""
    pantry = pantry or {}
    need = defaultdict(float)
    for code, grams in menu_lines:
        need[code] += grams
    rows = []
    for code, g in need.items():
        have = pantry.get(code, 0.0)
        used = min(have, g)
        buy = math.ceil((g - used) / ROUND_G) * ROUND_G if g > used else 0
        rows.append({"code": code, "name": ingredients[code]["name"], "need_g": g, "from_pantry_g": used, "buy_g": buy})
    return sorted(rows, key=lambda r: -r["buy_g"])


def pantry_coverage(rows):
    """Tỉ lệ khối lượng nguyên liệu lấy từ đồ có sẵn."""
    need = sum(r["need_g"] for r in rows)
    return sum(r["from_pantry_g"] for r in rows) / need if need else 0.0
