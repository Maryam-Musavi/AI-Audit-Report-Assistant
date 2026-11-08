import re
import unicodedata

# ۱. جدول تبدیل اعداد فارسی و عربی به انگلیسی
_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "0123456789" * 2)

# ۲. جدول یکسان‌سازی حروف عربی و اشکال مختلف به فارسی استاندارد
_CHAR_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh
        "ى": "ی",  # alef maksura
        "ك": "ک",  # Arabic kaf
        "ھ": "ه",  # heh doachashmee
        "ۀ": "ه",  # heh with yeh above
        "ە": "ه",  # ae
    }
)


def normalize_fa(text: str) -> str:
    """
    نرمال‌سازی متن فارسی (حروف و اعداد) با حفظ خطوط جدید (\n).
    مناسب برای متون چندخطی و صفحات PDF.
    """
    text = unicodedata.normalize("NFKC", str(text))
    text = text.translate(_CHAR_MAP).translate(_DIGIT_MAP)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def norm(s: object) -> str:
    """
    نرمال‌سازی کامل و یک‌خطی‌سازی متن (حذف نیم‌فاصله‌ها و خطوط جدید).
    مناسب برای سلول‌های اکسل و جستجوی برچسب‌ها (Labels).
    """
    s_norm = normalize_fa(str(s))
    s_norm = s_norm.replace("\u200c", " ").replace("\u200f", " ")
    return re.sub(r"\s+", " ", s_norm).strip()
