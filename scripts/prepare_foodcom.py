"""Tiền xử lý Food.com Recipes and Interactions (Majumder và cộng sự, EMNLP 2019) cho mô-đun M2.

Đầu vào : data/foodcom/raw/RAW_interactions.csv, RAW_recipes.csv
          (giải nén từ archive.zip tải ở trang Kaggle shuyangli94/food-com-recipes-and-user-interactions)
Đầu ra  : data/foodcom/processed/
            train.csv, val.csv, test.csv   (user, recipe, date) - phản hồi ẩn, chia leave-one-out theo thời gian
            recipes.csv                    đặc trưng món cho nhánh content-based
            stats.json                     số liệu trước/sau từng bước lọc

Các bước:
    1. Bỏ dòng rating = 0 (chỉ bình luận, không chấm điểm).
    2. Coi rating >= 4 là tương tác tích cực (phản hồi ẩn).
    3. Lọc k-core lặp: mỗi người dùng và mỗi món có ít nhất K tương tác tích cực.
    4. Với mỗi người dùng: tương tác mới nhất -> test, kế cuối -> val, còn lại -> train.
Không đọc ingr_map.pkl (định dạng pickle có thể chạy mã khi mở).
"""
import ast
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "foodcom" / "raw"
OUT = ROOT / "data" / "foodcom" / "processed"
K = 5
POSITIVE = 4

csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)

# Thứ tự trường nutrition trong RAW_recipes (theo mô tả bộ dữ liệu trên Kaggle)
NUTRITION = ["calories", "total_fat_pdv", "sugar_pdv", "sodium_pdv", "protein_pdv", "sat_fat_pdv", "carbs_pdv"]


def read_interactions():
    rows = []
    with open(RAW / "RAW_interactions.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append((r["user_id"], r["recipe_id"], r["date"], int(r["rating"])))
    return rows


def k_core(pairs, k):
    pairs = list(pairs)
    while True:
        uc = Counter(u for u, _, _ in pairs)
        ic = Counter(i for _, i, _ in pairs)
        kept = [p for p in pairs if uc[p[0]] >= k and ic[p[1]] >= k]
        if len(kept) == len(pairs):
            return kept
        pairs = kept


def main():
    stats = {}
    rows = read_interactions()
    stats["raw"] = {"interactions": len(rows), "users": len({r[0] for r in rows}), "recipes": len({r[1] for r in rows}),
                    "rating_counts": dict(sorted(Counter(r[3] for r in rows).items()))}

    rated = [r for r in rows if r[3] > 0]
    stats["rated"] = {"interactions": len(rated)}

    # một người dùng có thể đánh giá lại một món: giữ lần mới nhất
    latest = {}
    for u, i, d, s in rated:
        if (u, i) not in latest or d > latest[(u, i)][0]:
            latest[(u, i)] = (d, s)
    positives = [(u, i, d) for (u, i), (d, s) in latest.items() if s >= POSITIVE]
    stats["positive"] = {"interactions": len(positives), "share_of_rated": round(len(positives) / len(latest), 4)}

    core = k_core(positives, K)
    users = {u for u, _, _ in core}
    items = {i for _, i, _ in core}
    stats[f"{K}_core"] = {"interactions": len(core), "users": len(users), "recipes": len(items),
                          "density": round(len(core) / (len(users) * len(items)), 6)}

    by_user = defaultdict(list)
    for u, i, d in core:
        by_user[u].append((d, i))
    split = {"train": [], "val": [], "test": []}
    for u, hist in by_user.items():
        hist.sort()
        split["test"].append((u, hist[-1][1], hist[-1][0]))
        split["val"].append((u, hist[-2][1], hist[-2][0]))
        split["train"].extend((u, i, d) for d, i in hist[:-2])
    stats["split"] = {k: len(v) for k, v in split.items()}

    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in split.items():
        with open(OUT / f"{name}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["user_id", "recipe_id", "date"])
            w.writerows(sorted(data))

    n_feat = 0
    with open(RAW / "RAW_recipes.csv", encoding="utf-8", newline="") as f, \
            open(OUT / "recipes.csv", "w", encoding="utf-8", newline="") as g:
        w = csv.writer(g)
        w.writerow(["recipe_id", "name", "minutes", "n_ingredients", "ingredients", "tags", *NUTRITION])
        for r in csv.DictReader(f):
            if r["id"] not in items:
                continue
            nut = ast.literal_eval(r["nutrition"])  # chuỗi danh sách số, literal_eval không chạy mã
            w.writerow([r["id"], r["name"], r["minutes"], r["n_ingredients"],
                        "|".join(ast.literal_eval(r["ingredients"])), "|".join(ast.literal_eval(r["tags"])), *nut])
            n_feat += 1
    stats["recipes_with_features"] = n_feat

    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
