import svg

from config import colours
from exec.calendar.config import (
    BLUE_RX,
    BLUE_RY,
    BLUE_Y,
    LOGO_TRANSLATE_X,
    LOGO_TRANSLATE_Y,
    POST_HEIGHT,
    POST_WIDTH,
)
from exec.calendar.events import get_events
from exec.calendar.renderer.term import create_multi_week
from exec.calendar.renderer.week import create_single_week
from exec.calendar.svg_utils import convert_path_to_list, get_b64_font, random_dots
from schema import Week


def create_svg(start: Week, end: Week, for_figma: bool) -> str:
    """Create publicity SVG calendar for events between two weeks (inclusive)"""

    # base64 encode fonts to make svg self-contained
    # cairosvg only supports ttf and otf fonts
    montserrat_500 = get_b64_font("static/fonts/montserrat-bold.ttf") if not for_figma else None
    montserrat_600 = get_b64_font("static/fonts/montserrat-semibold.ttf") if not for_figma else None

    elements = [
        # define fonts
        svg.Style(
            text=(
                """
                .title {
                    font-family: 'Montserrat';
                    font-weight: bold;
                    fill: white;
                }
                .text {
                    font-family: 'Montserrat';
                    font-weight: semibold;
                    fill: white;
                }
                """
                if for_figma
                else f"""
                @font-face {{
                    font-family: 'montserrat-bold';
                    src: url({montserrat_600}) format('truetype');
                }}

                .title {{
                    font-family: 'montserrat-bold';
                    font-weight: 600;
                    fill: white;
                }}

                @font-face {{
                    font-family: 'montserrat-semibold';
                    src: url({montserrat_500}) format('truetype');
                }}

                .text {{
                    font-family: 'montserrat-semibold';
                    font-weight: 500;
                    fill: white;
                }}
            """
            )
        ),
        # background
        svg.Rect(width=POST_WIDTH, height=POST_HEIGHT, fill=colours["grey"]),
        *random_dots(),  # add dots
        # blue background with curved top
        svg.Ellipse(cx=POST_WIDTH / 2, cy=BLUE_Y, rx=BLUE_RX, ry=BLUE_RY, fill=colours["blue"]),
        # uwcs logo
        svg.G(
            elements=[
                # i am so sorry for this
                svg.Path(
                    d=convert_path_to_list(
                        "M74.1765 54.1966C68.8169 54.1966 63.5777 52.6073 59.1214 49.6297C54.6651 46.6521 51.1919 42.42 49.1409 37.4684C47.0899 32.5168 46.5532 27.0683 47.5988 21.8117C48.6444 16.5552 51.2253 11.7267 55.015 7.93693C58.8048 4.14716 63.6333 1.56629 68.8898 0.520697C74.1464 -0.524898 79.595 0.0117467 84.5465 2.06275C89.4981 4.11376 93.7303 7.58702 96.7079 12.0433C99.6855 16.4996 101.275 21.7388 101.275 27.0983C101.269 34.2833 98.4116 41.1723 93.331 46.2529C88.2505 51.3335 81.3615 54.1905 74.1765 54.1966V54.1966Z",  # noqa: E501
                    )[0],
                    fill=colours["yellow"],
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M27.0983 101.509C42.0643 101.509 54.1966 89.3768 54.1966 74.4108C54.1966 59.4448 42.0643 47.3125 27.0983 47.3125C12.1323 47.3125 0 59.4448 0 74.4108C0 89.3768 12.1323 101.509 27.0983 101.509Z"  # noqa: E501
                    )[0],
                    fill=colours["yellow"],
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M74.1764 151.06C89.1424 151.06 101.275 138.928 101.275 123.962C101.275 108.996 89.1424 96.8633 74.1764 96.8633C59.2105 96.8633 47.0781 108.996 47.0781 123.962C47.0781 138.928 59.2105 151.06 74.1764 151.06Z"  # noqa: E501
                    )[0],
                    fill=colours["blue"],
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M121.745 198.626C136.711 198.626 148.843 186.494 148.843 171.528C148.843 156.562 136.711 144.43 121.745 144.43C106.779 144.43 94.6465 156.562 94.6465 171.528C94.6465 186.494 106.779 198.626 121.745 198.626Z"  # noqa: E501
                    )[0],
                    fill=colours["blue"],
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M196.583 121.433C198.197 123.084 200.136 124.38 202.278 125.238C204.42 126.096 206.717 126.497 209.023 126.416C211.239 126.497 213.446 126.097 215.492 125.244C217.539 124.391 219.378 123.105 220.883 121.475C224.057 117.817 225.692 113.069 225.444 108.229V56.9062H248.209V108.229C248.331 115.158 246.644 122 243.316 128.077C240.165 133.731 235.4 138.314 229.632 141.24C223.192 144.423 216.079 146.004 208.899 145.849C201.638 146.007 194.444 144.427 187.916 141.24C182.081 138.319 177.234 133.741 173.984 128.077C170.619 122.014 168.93 115.163 169.091 108.229V56.9062H191.856V108.229C191.727 110.634 192.079 113.041 192.89 115.308C193.702 117.575 194.958 119.658 196.583 121.433V121.433Z"  # noqa: E501
                    )[0],
                    fill="white",
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M382.933 56.9062H406.32L376.837 144.105H353.45L336.863 84.6851L320.277 144.105H296.724L267.365 56.9062H291.872L309.039 120.686L326.248 56.9062H348.516L365.932 120.686L382.933 56.9062Z"  # noqa: E501
                    )[0],
                    fill="white",
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M478.598 77.9989C475.068 75.9875 471.089 74.902 467.028 74.8432C462.793 74.7908 458.627 75.9271 455.003 78.1235C451.475 80.3564 448.611 83.4969 446.71 87.217C444.665 91.2063 443.598 95.6259 443.598 100.11C443.598 104.594 444.665 109.014 446.71 113.003C448.611 116.723 451.475 119.863 455.003 122.096C458.624 124.305 462.789 125.456 467.028 125.418C470.916 125.341 474.739 124.405 478.224 122.678C482.132 120.843 485.674 118.31 488.674 115.204L501.985 129.529C497.185 134.55 491.452 138.585 485.108 141.405C478.381 144.575 470.996 146.089 463.566 145.822C456.137 145.555 448.879 143.514 442.397 139.868C435.496 136.032 429.763 130.392 425.81 123.55C421.788 116.5 419.726 108.499 419.839 100.38C419.716 92.4137 421.777 84.5664 425.799 77.6918C429.82 70.8172 435.647 65.1786 442.646 61.3897C449.22 57.8816 456.496 55.8962 463.939 55.58C471.381 55.2637 478.8 56.6248 485.647 59.5628C491.7 62.0958 497.164 65.8564 501.695 70.6078L488.508 86.5527C485.816 83.06 482.445 80.1501 478.598 77.9989V77.9989Z"  # noqa: E501
                    )[0],
                    fill="white",
                ),
                svg.Path(
                    d=convert_path_to_list(
                        "M569.326 76.4645C565.079 74.9119 560.616 74.0294 556.098 73.8485C553.773 73.7249 551.46 74.2572 549.422 75.3849C548.649 75.8603 548.018 76.5352 547.595 77.3388C547.172 78.1423 546.972 79.0451 547.017 79.9524C547.001 80.8546 547.181 81.7495 547.547 82.5744C547.912 83.3993 548.453 84.1342 549.132 84.7276C550.661 86.0871 552.434 87.1438 554.357 87.8418C556.43 88.6307 559.499 89.6688 563.562 90.9145C568.663 92.3241 573.663 94.072 578.532 96.1464C582.534 97.9259 586.027 100.681 588.691 104.16C591.632 108.275 593.094 113.266 592.838 118.32C592.989 123.648 591.37 128.876 588.235 133.185C585.047 137.398 580.735 140.622 575.795 142.486C570.097 144.625 564.05 145.682 557.964 145.6C550.598 145.568 543.292 144.276 536.36 141.78C529.59 139.477 523.295 135.96 517.783 131.399L526.616 113.586C531.24 117.635 536.51 120.877 542.207 123.178C547.251 125.449 552.687 126.719 558.213 126.915C561.004 127.063 563.779 126.415 566.216 125.046C567.153 124.481 567.92 123.674 568.438 122.71C568.956 121.745 569.206 120.659 569.16 119.565C569.177 118.625 568.99 117.692 568.61 116.831C568.23 115.971 567.668 115.204 566.963 114.583C565.369 113.163 563.508 112.076 561.489 111.385C559.291 110.596 556.223 109.683 552.242 108.603C547.198 107.256 542.251 105.563 537.438 103.537C533.514 101.821 530.069 99.1697 527.403 95.8142C524.465 91.8561 522.999 86.9952 523.257 82.0701C523.114 77.0177 524.565 72.0487 527.403 67.8692C530.482 63.6235 534.714 60.352 539.595 58.4435C545.441 56.1441 551.685 55.0291 557.964 55.1631C564.279 55.1553 570.562 56.0501 576.624 57.8206C582.333 59.4215 587.78 61.8411 592.796 65.0041L584.213 83.1912C579.504 80.4246 574.513 78.1696 569.326 76.4645V76.4645Z"  # noqa: E501
                    )[0],
                    fill="white",
                ),
            ],
            # transform and position correctly
            transform=[
                svg.Translate(LOGO_TRANSLATE_X, LOGO_TRANSLATE_Y),
            ],
        ),
    ]

    events = get_events(start, end)
    if start == end:
        elements.extend(create_single_week(events, start))
    else:
        elements.extend(create_multi_week(events, start, end, for_figma))

    return str(svg.SVG(elements=elements, viewBox=svg.ViewBoxSpec(0, 0, POST_WIDTH, POST_HEIGHT)))
