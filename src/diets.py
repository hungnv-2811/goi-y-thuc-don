"""10 kiểu chế độ ăn: tỉ lệ macro, nhóm thực phẩm bị loại và giới hạn theo tuần.

Nhóm thực phẩm suy ra từ nhóm của bảng Viện Dinh dưỡng và tên nguyên liệu, nên mọi
công thức có mã nguyên liệu đều tự xác định được chế độ ăn phù hợp.
"""
from dataclasses import dataclass, field

# ---- phân nhóm nguyên liệu ----
RED_MEAT = ("bò", "lợn", "trâu", "dê", "cừu", "ngựa")


def food_groups(name, category):
    """Trả về tập nhóm của một nguyên liệu (tên tiếng Việt, nhóm Viện Dinh dưỡng)."""
    n = name.lower()
    g = set()
    if category == "Thịt và sản phẩm chế biến":
        g.add("thit")
        if any(k in n for k in RED_MEAT):
            g.add("thit_do")
    if category == "Thủy sản và sản phẩm chế biến" or "mắm" in n:
        g.add("thuy_san")
    if category == "Trứng và sản phẩm chế biến" or n.startswith("trứng"):
        g.add("trung")
    if category == "Sữa và sản phẩm chế biến":
        g.add("sua")
    if category == "Dầu, mỡ, bơ":
        if "mỡ" in n:
            g.add("mo_dong_vat")
        if n.startswith("bơ"):
            g.add("sua")
    if category == "Ngũ cốc và sản phẩm chế biến" or "cơm" in n:
        g.add("ngu_coc")
    if category == "Khoai củ và sản phẩm chế biến":
        g.add("khoai_cu")
    if category == "Hạt, quả giàu đạm, béo và sản phẩm chế biến" and any(k in n for k in ("đậu", "đỗ", "lạc")):
        g.add("dau_do")
    if category == "Đồ ngọt (đường, bánh, mứt, kẹo)" or n.startswith("đường"):
        g.add("do_ngot")
    if category == "Quả chín":
        g.add("qua_chin")
    if category in ("Đồ hộp", "Nước giải khát") or any(
            k in n for k in ("chả", "xúc xích", "lạp xường", "ăn liền", "patê", "giò ", "mỳ chính")):
        g.add("che_bien_san")
    return g


@dataclass
class Diet:
    key: str
    name: str
    description: str
    exclude: frozenset = frozenset()       # nhóm nguyên liệu không được dùng
    carb_share: float | None = None        # cố định % năng lượng từ tinh bột (ít tinh bột, keto)
    carb_cap_g: float | None = None        # trần tinh bột tuyệt đối (keto: 50 g/ngày)
    fat_share: float = 0.25                # % năng lượng từ chất béo khi không cố định tinh bột
    weekly_limits: dict = field(default_factory=dict)  # nhóm -> số bữa tối đa mỗi tuần


DIETS = {d.key: d for d in [
    Diet("can_bang", "Cân bằng", "Đủ các nhóm chất; mặc định"),
    Diet("an_chay", "Ăn chay", "Không thịt, không thủy sản; có trứng, sữa",
         frozenset({"thit", "thuy_san", "mo_dong_vat"})),
    Diet("thuan_chay", "Thuần chay", "Không mọi sản phẩm động vật, kể cả nước mắm",
         frozenset({"thit", "thuy_san", "trung", "sua", "mo_dong_vat"})),
    Diet("chay_co_ca", "Chay có cá", "Không thịt; có cá, hải sản, trứng, sữa",
         frozenset({"thit", "mo_dong_vat"})),
    Diet("linh_hoat", "Linh hoạt", "Chủ yếu thực vật; thịt tối đa 4 bữa mỗi tuần",
         weekly_limits={"thit": 4}),
    Diet("it_tinh_bot", "Ít tinh bột", "Tinh bột khoảng 25% năng lượng", carb_share=0.25),
    Diet("keto", "Keto", "Tinh bột 8% năng lượng, tối đa 50 g/ngày; không ngũ cốc, khoai củ, đồ ngọt",
         frozenset({"ngu_coc", "khoai_cu", "do_ngot", "qua_chin"}), carb_share=0.08, carb_cap_g=50),
    Diet("dia_trung_hai", "Địa Trung Hải", "Nhiều cá, rau, đậu, dầu thực vật; thịt đỏ tối đa 2 bữa mỗi tuần",
         frozenset({"mo_dong_vat", "che_bien_san"}), fat_share=0.35, weekly_limits={"thit_do": 2}),
    Diet("paleo", "Paleo", "Không ngũ cốc, đậu đỗ, sữa, đường, thực phẩm chế biến sẵn",
         frozenset({"ngu_coc", "dau_do", "sua", "do_ngot", "che_bien_san"}), fat_share=0.35),
    Diet("nguyen_chat", "Thực phẩm nguyên chất", "Không đồ hộp, đồ ngọt, nước ngọt, thực phẩm chế biến sẵn",
         frozenset({"che_bien_san", "do_ngot"})),
]}


def dish_groups(lines, ingredients):
    """lines: [(mã nguyên liệu, gam)]; ingredients: mã -> {'name', 'category'}."""
    g = set()
    for code, _ in lines:
        ing = ingredients[code]
        g |= food_groups(ing["name"], ing["category"])
    return g


def compatible(groups, diet_key):
    return not (groups & DIETS[diet_key].exclude)
