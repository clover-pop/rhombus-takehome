import re
from pathlib import Path

obs = Path("observations")
missing = []
for md in sorted(obs.glob("*.md")):
    text = md.read_text()
    for link in re.findall(r"(?:evidence/|datasets/)[\w\-./]+\.(?:png|txt|json|csv)", text):
        base = obs if link.startswith("evidence/") else Path(".")
        if not (base / link).exists():
            missing.append((md.name, link))

for name, link in missing:
    print("MISSING:", name, "->", link)
print("all links found" if not missing else str(len(missing)) + " missing link(s)")
