# gets phosphor icons from folder
# extract font files and svg paths

import json
import re
from pathlib import Path

icons_path = Path("scripts/phosphor-icons/Fonts/bold")


def update_fonts() -> None:
    """updates font files and css for html use"""

    out = Path("static/icons")

    for f in icons_path.glob("*"):
        if f.suffix in [".ttf", ".woff", ".woff2"]:
            # copy font files and convert to lowercase
            out_f = out / f.name.lower()
            out_f.write_bytes(f.read_bytes())
            print(f"Copied {f} to {out_f}")
        elif f.suffix == ".css":
            # copy css file (remove @font-face)
            out_f = out / "phosphor-bold.css"
            css_file = f.read_text()
            css_file = re.sub(r"@font-face\s*{[^}]*}", "", css_file, flags=re.DOTALL)
            out_f.write_text(css_file)


def update_svgs() -> None:
    """updates path dict for svg use"""

    selection = json.loads((icons_path / "selection.json").read_text())
    paths = {}
    for icon in selection["icons"]:
        name = icon["properties"]["name"].removesuffix("-bold")
        path = icon["icon"]["paths"][0]
        paths[name] = path

    out_path = Path("icons.json")
    out_path.write_text(json.dumps(paths, indent=2))
    print(f"Wrote {len(paths)} icons to {out_path}")


if __name__ == "__main__":
    update_fonts()
    update_svgs()
    print("you can now safely delete the phosphor-icons folder")
    print("done :)")
