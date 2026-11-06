"""
build.py

Assembles the final, self-contained dashboard/index.html by embedding
dashboard/data.json into dashboard/template.html (as a JS const), so the
dashboard opens standalone: no local server, no fetch()/CORS issues.

Run this after etl/clean_and_load.py has produced data.json.
"""

import json

with open("data.json") as f:
    data = json.load(f)

with open("template.html") as f:
    template = f.read()

with open("index.html", "w") as f:
    f.write(template.replace("__DATA_JSON__", json.dumps(data)))

print("wrote index.html")
