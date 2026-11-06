"""Chạy trên dữ liệu thật: chế độ ăn phù hợp của 15 công thức và danh sách đi chợ cho thực đơn mẫu.

In ra JSON để đưa vào báo cáo.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from check_sample_day import MENU  # noqa: E402
from diets import DIETS, compatible, dish_groups  # noqa: E402
from dish_nutrition import load_catalog, load_ingredients, load_recipes  # noqa: E402
from shopping import pantry_coverage, shopping_list  # noqa: E402

# Đồ có sẵn trong bếp của người dùng ví dụ (gam)
PANTRY = {"1004": 2000, "6010": 500, "13017": 300, "12014": 500, "9012": 100}

if __name__ == "__main__":
    ing, rec, cat = load_ingredients(), load_recipes(), load_catalog()
    diets = {}
    for code, lines in rec.items():
        g = dish_groups(lines, ing)
        diets[code] = {"ten": cat[code]["ten_mon"], "nhom": sorted(g), "hop": [k for k in DIETS if compatible(g, k)]}
    per_diet = {k: sum(k in d["hop"] for d in diets.values()) for k in DIETS}

    lines = [ln for dishes in MENU.values() for d in dishes for ln in rec[d]]
    rows = shopping_list(lines, ing, PANTRY)
    print(json.dumps({"diets": diets, "per_diet": per_diet,
                      "shopping": [{k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()} for r in rows],
                      "pantry": {ing[c]["name"]: g for c, g in PANTRY.items()},
                      "coverage": round(pantry_coverage(rows), 3)}, ensure_ascii=False, indent=1))
