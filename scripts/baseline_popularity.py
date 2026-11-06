"""Kiểm tra tập chia Food.com bằng baseline gợi ý theo độ phổ biến (Recall@K, NDCG@K).

Mỗi người dùng nhận K món phổ biến nhất trong train mà họ chưa tương tác (train + val);
một lần trúng khi món ở test nằm trong K món đó. Đây là mốc thấp nhất M2 phải vượt.
"""
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "foodcom" / "processed"


def load(name):
    with open(DATA / f"{name}.csv", encoding="utf-8", newline="") as f:
        return [(r["user_id"], r["recipe_id"]) for r in csv.DictReader(f)]


def evaluate(k_values=(10, 20)):
    train, val, test = load("train"), load("val"), load("test")
    seen = defaultdict(set)
    for u, i in train + val:
        seen[u].add(i)
    ranking = [i for i, _ in Counter(i for _, i in train).most_common()]
    kmax = max(k_values)

    hits = {k: 0 for k in k_values}
    ndcg = {k: 0.0 for k in k_values}
    for u, target in test:
        top = []
        for i in ranking:
            if i not in seen[u]:
                top.append(i)
                if len(top) == kmax:
                    break
        if target in top:
            rank = top.index(target) + 1
            for k in k_values:
                if rank <= k:
                    hits[k] += 1
                    ndcg[k] += 1 / math.log2(rank + 1)
    n = len(test)
    return {k: (hits[k] / n, ndcg[k] / n) for k in k_values}, n


if __name__ == "__main__":
    res, n = evaluate()
    print(f"{n} người dùng trong tập test")
    for k, (r, g) in res.items():
        print(f"Recall@{k} = {r:.4f}   NDCG@{k} = {g:.4f}")
