import sass
import os

scss_path = "app/static/scss/main.scss"
css_path = "app/static/css/main.css"

print("compiling scss")
css = sass.compile(filename=scss_path, include_paths=["app/static/scss"], output_style="compressed")

print("writing css")
os.makedirs(os.path.dirname(css_path), exist_ok=True)
with open(css_path, "w") as css_file:
    css_file.write(css)

print("done :)")