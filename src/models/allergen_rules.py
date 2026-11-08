"""An toàn dị ứng: khớp theo ranh giới từ + danh mục nhóm + cụm ngoại lệ.

So khớp chuỗi con (substring) không an toàn trong tiếng Việt:

- ``cá`` nằm trong ``rau giấp cá`` (rau thơm, không phải hải sản).
- ``bơ`` nằm trong ``quả bơ`` (trái cây) và ``bơ thực vật`` (dầu thực vật).
- ``đậu`` nằm trong ``đậu bắp`` / ``đậu cô ve`` (rau củ), ``đậu hũ`` (đậu nành).

Module này map token người dùng nhập (tự do, tiếng Việt hoặc tiếng Anh) về một
nhóm dị ứng đã tuyển chọn, rồi khớp tên món bằng regex ranh giới từ sau khi đã
loại bỏ các cụm ngoại lệ đã biết.

Giới hạn dữ liệu: dataset hiện tại chỉ có tên món và thành phần dinh dưỡng,
KHÔNG có bảng nguyên liệu / allergen. Vì vậy kết quả khớp là "best-effort"
theo tên món, không phải kết luận an toàn lâm sàng.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


def _words(*items: str) -> re.Pattern[str]:
    """Regex khớp nguyên từ (không khớp khi dính ký tự chữ khác)."""
    body = "|".join(re.escape(item) for item in items)
    return re.compile(rf"(?<!\w)(?:{body})(?!\w)", re.IGNORECASE)


@dataclass(frozen=True)
class AllergenGroup:
    """Một nhóm dị ứng: token người dùng, regex tên món, cụm ngoại lệ."""

    key: str
    tokens: tuple[str, ...]
    pattern: re.Pattern[str]
    exclusions: tuple[str, ...] = ()


ALLERGEN_TAXONOMY: dict[str, AllergenGroup] = {
    "seafood": AllergenGroup(
        key="seafood",
        tokens=(
            "hải sản", "hai san", "seafood", "đồ biển",
            "tôm", "tom", "prawn", "shrimp",
            "cua", "crab", "ghẹ", "ghe",
            "cá", "ca", "fish", "cá biển", "cá đồng",
            "mực", "muc", "squid", "bạch tuộc", "bach tuoc", "octopus",
            "nghêu", "ngheu", "ngao", "sò", "so", "hến", "hen", "ốc", "oc", "hàu", "hau",
            "tép", "tep", "lươn", "luon",
            "cá hồi", "ca hoi", "salmon", "cá ngừ", "ca ngu", "tuna",
            "cá basa", "basa", "cá lóc", "ca loc", "cá thu", "ca thu",
            "cá chép", "ca chep", "cá rô", "ca ro", "cá trắm", "ca tram",
        ),
        pattern=_words(
            "tôm", "cua", "ghẹ", "cá", "mực", "bạch tuộc", "nghêu", "ngao",
            "sò", "hến", "ốc", "hàu", "tép", "lươn",
            "shrimp", "prawn", "crab", "fish", "squid", "octopus",
            "salmon", "tuna", "basa", "seafood",
        ),
        exclusions=(
            "rau giấp cá", "giấp cá", "rau giấp", "dầu cám", "cám gạo",
            "cá ngừ đại dương",  # vẫn là cá, giữ lại để tài liệu rõ ràng
        ),
    ),
    "peanut": AllergenGroup(
        key="peanut",
        tokens=(
            "đậu phộng", "dau phong", "đậu phụng", "dau phung",
            "lạc", "lac", "peanut", "peanuts", "groundnut",
            "đậu tây", "dau tay", "củ lạc", "cu lac",
        ),
        pattern=_words(
            "đậu phộng", "đậu phụng", "lạc", "peanut", "peanuts",
            "groundnut", "đậu tây", "củ lạc",
        ),
        exclusions=(),
    ),
    "dairy": AllergenGroup(
        key="dairy",
        tokens=(
            "sữa", "sua", "dairy", "milk", "lactose",
            "sữa bò", "sữa tươi", "sữa đặc", "váng sữa",
            "sữa chua", "yogurt", "yoghurt",
            "phô mai", "pho mai", "phô-mai", "pho mát", "phô mát", "phomai", "cheese",
            "kem", "kem sữa",
        ),
        # "kem" chỉ là token (người dùng chủ động khai báo), không đưa vào
        # pattern vì "kem dừa"/"kem đậu xanh" không chứa sữa động vật.
        pattern=_words(
            "sữa", "phô mai", "pho mai", "phô-mai", "pho mát", "phô mát",
            "phomai", "cheese", "yogurt", "yoghurt", "váng sữa", "milk", "dairy",
        ),
        exclusions=(
            "sữa đậu nành", "sữa đậu", "sữa đậu phộng", "sữa bắp",
            "sữa ngô", "sữa hạt sen", "sữa hạt", "sữa gạo",
            "sữa yến mạch", "sữa dừa", "nước cốt dừa",
            "bơ thực vật", "quả bơ", "bơ sáp", "bơ đậu phộng",
        ),
    ),
    "egg": AllergenGroup(
        key="egg",
        tokens=(
            "trứng", "trung", "egg", "eggs",
            "trứng gà", "trứng vịt", "trứng cút", "lòng đỏ trứng",
        ),
        pattern=_words("trứng", "egg", "eggs"),
        exclusions=("cà tím", "cà tím nướng"),
    ),
}


# token đã chuẩn hóa -> nhóm dị ứng
_TOKEN_TO_GROUP: dict[str, AllergenGroup] = {
    token: group
    for group in ALLERGEN_TAXONOMY.values()
    for token in group.tokens
}


def normalize_allergen_text(value: object) -> str:
    """Chuẩn hóa chuỗi: bỏ khoảng trắng thừa, chữ thường."""
    return " ".join(str(value or "").strip().lower().split())


def allergen_group_for(token: str) -> AllergenGroup | None:
    """Trả về nhóm dị ứng tương ứng token người dùng, nếu có."""
    return _TOKEN_TO_GROUP.get(normalize_allergen_text(token))


def _strip_exclusions(name: str, exclusions: Iterable[str]) -> str:
    """Loại các cụm ngoại lệ khỏi tên món trước khi khớp."""
    for phrase in exclusions:
        if phrase in name:
            name = name.replace(phrase, " ")
    return name


def is_allergen_conflict(food_name: str, user_allergies: Iterable[str]) -> bool:
    """True nếu tên món xung đột với bất kỳ dị ứng nào của người dùng.

    - Token thuộc ``ALLERGEN_TAXONOMY``: khớp cả nhóm theo ranh giới từ,
      sau khi đã loại cụm ngoại lệ.
    - Token chưa phân loại: giữ hành vi cũ (khớp chuỗi con) để không bỏ sót
      dị ứng do người dùng tự nhập.
    """
    name = normalize_allergen_text(food_name)
    if not name:
        return False

    for raw in user_allergies or []:
        token = normalize_allergen_text(raw)
        if not token:
            continue
        group = _TOKEN_TO_GROUP.get(token)
        if group is not None:
            candidate = _strip_exclusions(name, group.exclusions)
            if group.pattern.search(candidate):
                return True
        elif token in name:
            return True
    return False


def conflicting_allergens(food_name: str, user_allergies: Iterable[str]) -> list[str]:
    """Danh sách token người dùng xung đột với tên món (để báo lỗi rõ ràng)."""
    hits: list[str] = []
    for raw in user_allergies or []:
        if is_allergen_conflict(food_name, [raw]):
            hits.append(str(raw))
    return hits


def match_phrase_word_boundary(text: str, phrase: str) -> bool:
    """Khớp từ hoặc cụm từ theo ranh giới từ (word boundary).

    Tránh việc từ ngắn bị khớp nhầm vào từ dài hơn (substring matching).
    Ví dụ: 'cá' không khớp 'cà chua', 'cải bắp'; 'bò' không khớp 'bơ'.
    """
    cleaned_text = normalize_allergen_text(text)
    cleaned_phrase = normalize_allergen_text(phrase)
    if not cleaned_text or not cleaned_phrase:
        return False
    pattern = rf"(?<!\w){re.escape(cleaned_phrase)}(?!\w)"
    return bool(re.search(pattern, cleaned_text, re.IGNORECASE))


def is_dislike_conflict(food_name: str, dislikes: Iterable[str]) -> bool:
    """True nếu món ăn xung đột với danh sách không thích (dislikes) của người dùng.

    Khớp theo ranh giới từ (word boundary) hoặc nhóm dị ứng tương ứng để không
    bắt nhầm chuỗi con (false-positive).
    """
    name = normalize_allergen_text(food_name)
    if not name:
        return False
    for raw in dislikes or []:
        token = normalize_allergen_text(raw)
        if not token:
            continue
        group = _TOKEN_TO_GROUP.get(token)
        if group is not None:
            candidate = _strip_exclusions(name, group.exclusions)
            if group.pattern.search(candidate):
                return True
        elif match_phrase_word_boundary(name, token):
            return True
    return False


def conflicting_dislikes(food_name: str, dislikes: Iterable[str]) -> list[str]:
    """Danh sách token món không thích bị vi phạm (để báo lỗi rõ ràng)."""
    hits: list[str] = []
    for raw in dislikes or []:
        if is_dislike_conflict(food_name, [raw]):
            hits.append(str(raw))
    return hits

