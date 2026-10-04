import re
from pathlib import Path

FILES = [Path("README.md")] + sorted(Path("observations").glob("*.md")) + sorted(Path("docs").glob("*.md"))
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")
BARE = re.compile(r"(?:evidence|datasets)/[\w\-./]+\.(?:png|jpg|txt|json|jsonl|csv)")
PLACEHOLDER = re.compile(r"TODO-REPLACE|\[(?:to fill|fill in|edit this|Say |describe|adjust|delete this|number)")

missing, placeholders = set(), []
for md in FILES:
    if not md.exists():
        continue
    text = md.read_text(encoding="utf-8")
    for link in MD_LINK.findall(text):
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (md.parent / link.split("#")[0]).exists():
            missing.add((md.name, link))
    for ref in BARE.findall(text):
        base = Path("observations") if ref.startswith("evidence/") else Path(".")
        if not (base / ref).exists():
            missing.add((md.name, ref))
    for number, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER.search(line):
            placeholders.append((md.name, number, line.strip()[:90]))

for name, link in sorted(missing):
    print("MISSING LINK:", name, "->", link)
for name, number, line in placeholders:
    print("PLACEHOLDER:", name + ":" + str(number), line)
print("all links found" if not missing else str(len(missing)) + " missing link(s)")
print("no placeholders" if not placeholders else str(len(placeholders)) + " placeholder line(s)")
