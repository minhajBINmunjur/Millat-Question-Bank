#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failed = False


def fail(msg):
    global failed
    failed = True
    print("FAIL:", msg)


def ok(msg):
    print("OK:", msg)


html = (ROOT / "index.html").read_text(encoding="utf-8")
vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))

required_snippets = [
    "Millat Question Bank",
    "তা'মীরুল মিল্লাত প্রশ্ন ব্যাংক",
    "তোমার ক্যাম্পাসে ক্লিক মারো",
    "প্রশ্ন পাঠাও",
    "প্রশ্ন না পাঠাইলে যুক্ত করব কিভাবে ??",
    "খোঁজা হচ্ছে...",
    "selectCampus('tongi')",
    "selectCampus('mohila')",
    "selectCampus('dhaka')",
    "selectSubject('Alim', 'Physics 1st')",
    "selectSubject('Dakhil', 'Physics')",
    "openQuestionModal('1st semester/half yearly', '2021')",
    "openQuestionModal('test', '2026')",
    "toggleTheme()",
    "openSubmitQuestionModal()",
    "function submitViaWhatsApp()",
    "function handleSearch(query)",
    "https://docs.google.com/forms/d/e/1FAIpQLSfhZ9Yj1JVnkt_hM0OxAnrzQimjn32Kt9djoxPNvyk2lEcyTg/viewform?usp=header",
    "pdfs/${campus}_${sub}_${exam}_${year}.pdf",
    "mqb-theme",
    "paperExistsCache",
]

for snippet in required_snippets:
    if snippet not in html:
        fail(f"missing required snippet: {snippet}")
    else:
        ok(f"snippet present: {snippet[:60]}")

required_files = [
    "styles.css",
    "tailwind.css",
    "vercel.json",
    "images/hero.webp",
    "images/tongi.webp",
    "images/mohila.webp",
    "images/dhaka.webp",
    "pdfs/tongi_chemistry-2nd_test_2024.pdf",
    "pdfs/tongi_physics-2nd_test_2024.pdf",
]
for rel in required_files:
    if not (ROOT / rel).exists():
        fail(f"missing file: {rel}")
    else:
        ok(f"file present: {rel}")

header_blob = json.dumps(vercel.get("headers") or [])
for key in [
    "X-Content-Type-Options",
    "Content-Security-Policy",
    "Cache-Control",
    "/pdfs/(.*)",
    "/images/(.*)",
]:
    if key not in header_blob:
        fail(f"vercel.json missing {key}")
    else:
        ok(f"vercel.json has {key}")

if 'href="styles.css"' in html:
    fail("styles.css unexpectedly linked (would change cascade)")
else:
    ok("styles.css remains unlinked, matching original behavior")

if failed:
    print("\nRegression failed.")
    sys.exit(1)
print("\nAll static regression checks passed.")
