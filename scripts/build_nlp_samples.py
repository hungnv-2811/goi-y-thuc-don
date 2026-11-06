"""Chuyển câu mẫu đánh dấu thực thể sang JSONL (span + nhãn BIO theo âm tiết).

Cú pháp đánh dấu: [cụm từ](NHÃN). Mỗi câu kèm một ý định (intent).
Nhãn BIO ở đây tách theo khoảng trắng (âm tiết); khi huấn luyện PhoBERT sẽ tách từ
bằng VnCoreNLP rồi gióng lại nhãn theo span.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = re.compile(r"\[([^\]]+)\]\(([A-Z_]+)\)")

LABELS = ["GIOI_TINH", "TUOI", "CAN_NANG", "CHIEU_CAO", "VAN_DONG", "MUC_TIEU", "CHE_DO_AN",
          "KIENG", "MON", "SO_LUONG", "DON_VI", "BUA", "NGAN_SACH"]
INTENTS = ["YEU_CAU_THUC_DON", "GHI_NHAT_KY", "DOI_MON"]

SAMPLES = [
    ("YEU_CAU_THUC_DON", "Mình là [nữ](GIOI_TINH), [22 tuổi](TUOI), nặng [55kg](CAN_NANG), cao [1m60](CHIEU_CAO), muốn [giảm cân](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Tôi [nam](GIOI_TINH) [30 tuổi](TUOI) [70 cân](CAN_NANG) [1m75](CHIEU_CAO), [tập gym 4 buổi một tuần](VAN_DONG), cần [tăng cơ](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Lên thực đơn hôm nay giúp mình, mình [ăn chay](CHE_DO_AN) và muốn [giữ cân](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Gợi ý thực đơn [giảm cân](MUC_TIEU) nhưng mình [dị ứng hải sản](KIENG) nhé"),
    ("YEU_CAU_THUC_DON", "Mình [không ăn được thịt bò](KIENG), muốn [giảm 5 kg](MUC_TIEU) trong 2 tháng"),
    ("YEU_CAU_THUC_DON", "Thực đơn [ít đường](CHE_DO_AN) cho người [ngồi văn phòng cả ngày](VAN_DONG)"),
    ("YEU_CAU_THUC_DON", "Em [nữ](GIOI_TINH) [19 tuổi](TUOI) [48kg](CAN_NANG) muốn [tăng cân](MUC_TIEU), [không ăn hành](KIENG)"),
    ("YEU_CAU_THUC_DON", "Cho mình thực đơn khoảng [50 nghìn một ngày](NGAN_SACH) để [giảm cân](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Tôi [chạy bộ mỗi sáng](VAN_DONG), [ăn chay](CHE_DO_AN), muốn [giữ dáng](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Bố tôi [62 tuổi](TUOI), [ít vận động](VAN_DONG), cần thực đơn [ít muối](CHE_DO_AN)"),
    ("YEU_CAU_THUC_DON", "Làm thực đơn [tăng cơ](MUC_TIEU) với ngân sách [100k mỗi ngày](NGAN_SACH)"),
    ("YEU_CAU_THUC_DON", "Mình [kiêng tôm](KIENG) và [kiêng mực](KIENG), muốn ăn [nhiều rau](CHE_DO_AN)"),
    ("YEU_CAU_THUC_DON", "Mình [nam](GIOI_TINH), [cao 1m68](CHIEU_CAO), [nặng 80kg](CAN_NANG), cần [giảm mỡ](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Hôm nay mình muốn ăn [phở bò](MON) vào [bữa sáng](BUA), lên phần còn lại giúp mình"),
    ("YEU_CAU_THUC_DON", "Gợi ý [bữa tối](BUA) [nhẹ bụng](CHE_DO_AN) cho người đang [giảm cân](MUC_TIEU)"),
    ("YEU_CAU_THUC_DON", "Mình [không uống được sữa bò](KIENG), lên thực đơn [giữ cân](MUC_TIEU) nhé"),
    ("GHI_NHAT_KY", "[Sáng nay](BUA) mình ăn [1](SO_LUONG) [bát](DON_VI) [phở bò](MON)"),
    ("GHI_NHAT_KY", "[Trưa](BUA) ăn [2](SO_LUONG) [bát](DON_VI) [cơm](MON) với [cá rô phi kho](MON)"),
    ("GHI_NHAT_KY", "[Tối qua](BUA) mình ăn [một](SO_LUONG) [suất](DON_VI) [bún chả](MON)"),
    ("GHI_NHAT_KY", "Vừa uống [1](SO_LUONG) [hộp](DON_VI) [sữa chua](MON) và [1](SO_LUONG) [quả](DON_VI) [chuối](MON)"),
    ("GHI_NHAT_KY", "[Bữa sáng](BUA) có [1](SO_LUONG) [ổ](DON_VI) [bánh mỳ patê](MON)"),
    ("GHI_NHAT_KY", "[Trưa nay](BUA) ăn [nửa](SO_LUONG) [đĩa](DON_VI) [cơm rang](MON) thôi"),
    ("GHI_NHAT_KY", "Mình ăn [3](SO_LUONG) [cái](DON_VI) [nem rán](MON) vào [bữa tối](BUA)"),
    ("GHI_NHAT_KY", "[Chiều](BUA) ăn vặt [một](SO_LUONG) [gói](DON_VI) [xôi lạc](MON)"),
    ("GHI_NHAT_KY", "[Sáng](BUA) ăn [2](SO_LUONG) [quả](DON_VI) [trứng luộc](MON) với [1](SO_LUONG) [củ](DON_VI) [khoai lang](MON)"),
    ("GHI_NHAT_KY", "[Trưa](BUA) mình ăn [200 gam](SO_LUONG) [ức gà](MON) với [rau muống luộc](MON)"),
    ("GHI_NHAT_KY", "[Tối](BUA) ăn [1](SO_LUONG) [bát](DON_VI) [canh chua cá](MON) và [1](SO_LUONG) [bát](DON_VI) [cơm](MON)"),
    ("GHI_NHAT_KY", "Ăn [1](SO_LUONG) [cốc](DON_VI) [chè đỗ đen](MON) [buổi chiều](BUA)"),
    ("GHI_NHAT_KY", "[Sáng nay](BUA) ăn [bánh cuốn](MON), khoảng [1](SO_LUONG) [đĩa](DON_VI)"),
    ("GHI_NHAT_KY", "Hôm nay [trưa](BUA) đi đám cưới nên ăn nhiều, chắc khoảng [3](SO_LUONG) [bát](DON_VI) [cơm](MON)"),
    ("DOI_MON", "Đổi [cá rô phi kho](MON) sang món khác được không"),
    ("DOI_MON", "Mình không thích [canh cải](MON), thay bằng [canh bí](MON) đi"),
    ("DOI_MON", "Bỏ [trứng rán](MON) ở [bữa sáng](BUA) nhé"),
    ("DOI_MON", "Cho mình đổi [bữa tối](BUA) thành [bún bò](MON)"),
    ("DOI_MON", "[Gà áp chảo](MON) ăn chán rồi, gợi ý món khác"),
    ("DOI_MON", "Thay [cơm trắng](MON) bằng [khoai lang](MON) được không"),
    ("DOI_MON", "Không muốn ăn [tôm rang](MON) nữa"),
    ("DOI_MON", "[Bữa trưa](BUA) đổi sang món [không có thịt](KIENG) giúp mình"),
    ("DOI_MON", "Đổi [sữa chua chuối](MON) thành [cam](MON)"),
    ("DOI_MON", "Món [đậu phụ sốt cà chua](MON) nhiều dầu quá, đổi giúp mình"),
]


def parse(marked):
    text, spans, pos = "", [], 0
    for m in MARK.finditer(marked):
        text += marked[pos:m.start()]
        start = len(text)
        text += m.group(1)
        spans.append({"start": start, "end": len(text), "label": m.group(2), "text": m.group(1)})
        pos = m.end()
    text += marked[pos:]
    return text, spans


def bio(text, spans):
    tokens, tags = [], []
    for m in re.finditer(r"\w+|[^\w\s]", text):  # dấu câu là token riêng
        tag = "O"
        for s in spans:
            if s["start"] <= m.start() < s["end"]:
                tag = ("B-" if m.start() == s["start"] else "I-") + s["label"]
        tokens.append(m.group())
        tags.append(tag)
    return tokens, tags


def main():
    out = ROOT / "data" / "nlp" / "samples.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    labels, intents = Counter(), Counter()
    with out.open("w", encoding="utf-8") as f:
        for intent, marked in SAMPLES:
            assert intent in INTENTS, intent
            text, spans = parse(marked)
            for s in spans:
                assert s["label"] in LABELS, s["label"]
                assert text[s["start"]:s["end"]] == s["text"]
            tokens, tags = bio(text, spans)
            f.write(json.dumps({"text": text, "intent": intent, "entities": spans,
                                "tokens": tokens, "tags": tags}, ensure_ascii=False) + "\n")
            labels.update(s["label"] for s in spans)
            intents[intent] += 1
    print(f"{len(SAMPLES)} câu -> {out.relative_to(ROOT)}")
    print("Ý định:", dict(intents))
    print("Thực thể:", dict(labels.most_common()))


if __name__ == "__main__":
    main()
