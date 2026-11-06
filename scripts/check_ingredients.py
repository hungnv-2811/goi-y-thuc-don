"""Kiểm tra chất lượng bảng dinh dưỡng, gắn cờ các dòng không nên dùng trong công thức.

Quy tắc:
    THIEU_NANG_LUONG   ô năng lượng trống
    NANG_LUONG_VO_LY   năng lượng <= 1 kcal nhưng có đạm/béo/tinh bột > 1 g
    LECH_ATWATER       năng lượng ghi lệch hơn 30% so với 4*đạm + 4*tinh bột + 9*béo (chỉ xét >= 50 kcal)
Ô đạm/béo/tinh bột trống được coi là 0 (dầu, mỡ không có đạm), không gắn cờ.
"""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOL = 0.30


def num(x):
    return float(x) if x not in ("", None) else 0.0


def flags_for(row):
    out = []
    if row["energy_kcal"] == "":
        return ["THIEU_NANG_LUONG"]
    e = num(row["energy_kcal"])
    p, f, c = num(row["protein_g"]), num(row["fat_g"]), num(row["carb_g"])
    if e <= 1 and max(p, f, c) > 1:
        out.append("NANG_LUONG_VO_LY")
    atwater = 4 * p + 4 * c + 9 * f
    if e >= 50 and atwater > 0 and abs(e - atwater) / e > TOL:
        out.append("LECH_ATWATER")
    return out


def main():
    src = ROOT / "data" / "ingredients_vdd.csv"
    out = ROOT / "data" / "ingredients_flags.csv"
    counts = Counter()
    with open(src, encoding="utf-8-sig") as f, out.open("w", newline="", encoding="utf-8-sig") as g:
        w = csv.writer(g)
        w.writerow(["code", "name_vi", "category", "energy_kcal", "protein_g", "fat_g", "carb_g", "co"])
        for row in csv.DictReader(f):
            fl = flags_for(row)
            if fl:
                counts.update(fl)
                w.writerow([row["code"], row["name_vi"], row["category"], row["energy_kcal"],
                            row["protein_g"], row["fat_g"], row["carb_g"], "|".join(fl)])
    print(dict(counts), "->", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
