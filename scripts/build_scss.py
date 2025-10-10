from pathlib import Path

import sass

scss_path = "sass/main.scss"
css_path = "static/css/main.css"

print("compiling scss")
css = sass.compile(filename=scss_path, include_paths=["sass"], output_style="compressed")

print("writing css")
path = Path(css_path)
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("w", encoding="utf-8") as f:
    f.write(css)

print("done :)")
