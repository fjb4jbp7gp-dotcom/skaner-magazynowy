#!/usr/bin/env python3
"""artefakt.html = zawartość index.html między znacznikami APP (bez szkieletu strony) – do publikacji jako artefakt claude.ai."""
import re
from pathlib import Path
d = Path(__file__).parent
s = (d / "index.html").read_text(encoding="utf-8")
a = s.index("<!--APP-START-->") + len("<!--APP-START-->"); b = s.index("<!--APP-END-->")
t = re.sub(r'products\.js\?v=[^"]+', "products.js", s[a:b].strip())
(d / "artefakt.html").write_text(t + "\n", encoding="utf-8")
print("artefakt.html", len(t))
