import re
from pathlib import Path

# custom colours
colours = {
    "blue": "#3A7DFF",
    "yellow": "#FFC700",
    "grey": "#202429",
    "greyer": "#2F3338",
    "external": "#989898",
    "president": "#FDD835",
    "gaming": "#3D53FF",
    "treasurer": "#FD6035",
    "welfare": "#4F33DB",
    "gaming2": "#8135FD",
    "academic": "#EE4F4F",
    "tech": "#0EAD57",
    "secretary": "#1DC9FF",
    "social": "#B53DFF",
    "inclusivity": "#24D09D",
    "publicity": "#EF8A2C",
    "events": "#1DC9FF",
    "sports": "#B53DFF",
    "compcafe": "#358A4D",
    "milk": "#4BB3FF",
}

# custom icons from static/icons directory
custom_icons = [
    f.stem for f in Path("static/icons").iterdir() if f.is_file() and f.suffix == ".svg"
]

# phosphor icons from static/icons/phosphor-bold.css
phosphor_icons = sorted(
    set(
        re.findall(
            r"\.ph-([a-z0-9-]+)::before",
            Path("static/icons/phosphor-bold.css").read_text(),
        )
    )
)

icons = sorted(custom_icons + phosphor_icons)
