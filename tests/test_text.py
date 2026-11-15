from backend.utils.text import normalize_fa

def test_normalize_arabic_letters():
    result = normalize_fa("شركت ملي")
    assert result == "شرکت ملی"

def test_normalize_preserves_newlines():
    result = normalize_fa("دارایی\nبدهی")
    assert result == "دارایی\nبدهی"

def test_normalize_extra_spaces():
    result = normalize_fa("  جمع   دارایی  ")
    assert result == "جمع دارایی"
