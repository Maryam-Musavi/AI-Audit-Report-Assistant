"""مسیرهای مشترک پروژه (همه نسبت به ریشهٔ ریپو)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"      # ورودی‌ها (Excel / PDF)
GENERATED = ROOT / "data" / "generated"  # خروجی‌ها (در .gitignore)
GENERATED.mkdir(parents=True, exist_ok=True)

EXCEL_PATH = SAMPLES / "Table.xlsx"
PDF_PATH = SAMPLES / "seo-codal-report.pdf"
