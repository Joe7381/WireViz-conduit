# -*- coding: utf-8 -*-

from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

padding_amount = 1

ColorOutputMode = Enum(
    "ColorOutputMode", "EN_LOWER EN_UPPER DE_LOWER DE_UPPER HTML_LOWER HTML_UPPER"
)

color_output_mode = ColorOutputMode.EN_UPPER

KnownColor = namedtuple("KnownColor", "html code_de full_en full_de")

known_colors = {  #                   v--------v--------- for future use
    "BK": KnownColor("#000000", "sw", "black", "schwarz"),
    "WH": KnownColor("#ffffff", "ws", "white", "weiß"),
    "GY": KnownColor("#999999", "gr", "grey", "grau"),
    "PK": KnownColor("#ff66cc", "rs", "pink", "rosa"),
    "RD": KnownColor("#ff0000", "rt", "red", "rot"),
    "OG": KnownColor("#ff8000", "or", "orange", "orange"),
    "YE": KnownColor("#ffff00", "ge", "yellow", "gelb"),
    "OL": KnownColor("#708000", "ol", "olive green", "olivgrün"),
    "GN": KnownColor("#00aa00", "gn", "green", "grün"),
    "TQ": KnownColor("#00ffff", "tk", "turquoise", "türkis"),
    "LB": KnownColor("#a0dfff", "hb", "light blue", "hellblau"),
    "BU": KnownColor("#0066ff", "bl", "blue", "blau"),
    "VT": KnownColor("#8000ff", "vi", "violet", "violett"),
    "BN": KnownColor("#895956", "br", "brown", "braun"),
    "BG": KnownColor("#ceb673", "bg", "beige", "beige"),
    "IV": KnownColor("#f5f0d0", "eb", "ivory", "elfenbein"),
    "SL": KnownColor("#708090", "si", "slate", "schiefer"),
    "CU": KnownColor("#d6775e", "ku", "copper", "Kupfer"),
    "SN": KnownColor("#aaaaaa", "vz", "tin", "verzinkt"),
    "SR": KnownColor("#84878c", "ag", "silver", "Silber"),
    "GD": KnownColor("#ffcf80", "au", "gold", "Gold"),
}


def convert_case(inp):
    if "_LOWER" in color_output_mode.name:
        return inp.lower()
    elif "_UPPER" in color_output_mode.name:
        return inp.upper()
    else:  # currently not used
        return inp


def get_color_by_colorcode_index(color_code: str, index: int) -> str:
    num_colors_in_code = len(COLOR_CODES[color_code])
    actual_index = index % num_colors_in_code  # wrap around if index is out of bounds
    return COLOR_CODES[color_code][actual_index]


@dataclass
class SingleColor:
    _code_en: str
    _html: str

    @property
    def code_en(self):
        return convert_case(self._code_en) if self._code_en else None

    @property
    def code_de(self):
        return (
            convert_case(known_colors[self._code_en.upper()].code_de)
            if self._code_en
            else None
        )

    @property
    def html(self):
        return convert_case(self._html) if self._code_en else None

    @property
    def known(self):
        # treat None as a known color
        return self.code_en.upper() in known_colors.keys() if self._code_en else True

    def __init__(self, inp):
        if inp is None:
            self._html = None
            self._code_en = None
        elif isinstance(inp, int):
            hex_str = f"#{inp:06x}"
            self._html = hex_str
            self._code_en = hex_str  # do not perform reverse lookup - why not?
        elif not isinstance(inp, str):
            raise Exception(f"Unknown single color {inp}!")
        else:
            inp_upper = inp.upper()
            if inp_upper in known_colors.keys():
                self._code_en = inp_upper
                self._html = known_colors[inp_upper].html
            else:
                try:  # Maybe inp is an int as string?
                    inp = f"#{int(inp, 0):06x}"
                except ValueError:
                    pass  # assume it's a valid HTML color name
                self._html = inp
                self._code_en = inp

    @property
    def html_padded(self):
        return ":".join([self.html] * padding_amount)

    def __bool__(self):
        return self._code_en is not None

    def __str__(self):
        if self._html is None:
            return ""
        elif self.known and "EN_" in color_output_mode.name:
            return self.code_en
        elif self.known and "DE_" in color_output_mode.name:
            return self.code_de
        else:
            return self.html


@dataclass
class MultiColor:
    colors: List[SingleColor] = field(default_factory=list)

    def __init__(self, inp):
        self.colors = []
        if inp is None:
            pass
        elif isinstance(inp, List):  # input is already a list
            for item in inp:
                if item is None:
                    pass
                elif isinstance(item, SingleColor):
                    self.colors.append(item)
                else:  # string or integer (type check done inside)
                    self.colors.append(SingleColor(item))
        elif isinstance(inp, SingleColor):  # single color
            self.colors = [inp]
        elif isinstance(inp, int):
            self.colors = [SingleColor(inp)]
        elif not isinstance(inp, str):
            raise Exception(f"Unknown multi-color {inp}!")
        elif ":" in inp:  # split input into list
            self.colors = [SingleColor(item) for item in inp.split(":")]
        else:
            if len(inp) % 2 == 0:
                items = [inp[i : i + 2] for i in range(0, len(inp), 2)]
                known = [item.upper() in known_colors.keys() for item in items]
                if all(known):
                    self.colors = [SingleColor(item) for item in items]
                    return
            # assume it's a valid HTML color name
            self.colors = [SingleColor(inp)]

    def __len__(self):
        return len(self.colors)

    def __bool__(self):
        return len(self.colors) >= 1

    def __str__(self):
        if "EN_" in color_output_mode.name or "DE_" in color_output_mode.name:
            joiner = "" if self.all_known else ":"
        elif "HTML_" in color_output_mode.name:
            joiner = ":"
        else:
            joiner = "???"
        return joiner.join([str(color) for color in self.colors])

    @property
    def all_known(self):
        return all([color.known for color in self.colors])

    @property
    def html(self):
        return ":".join([color.html for color in self.colors])

    @property
    def html_padded_list(self):
        # padding only properly works for padding_amount 1 or 3
        if padding_amount == 1:
            out = [color.html for color in self.colors]
        elif len(self) == 0:
            out = []
        elif len(self) == 1:
            out = [self.colors[0].html for i in range(3)]
        elif len(self) == 2:
            out = [self.colors[0].html, self.colors[1].html, self.colors[0].html]
        elif len(self) == 3:
            out = [color.html for color in self.colors]
        else:
            raise Exception(f"Padding not supported for len {len(self)}")
        return [str(color) for color in out]

    @property
    def html_padded(self):
        return ":".join(self.html_padded_list)


COLOR_CODES = {
    # fmt: off
    "DIN": [
        "WH", "BN", "GN", "YE", "GY", "PK", "BU", "RD", "BK", "VT", "GYPK", "RDBU",
        "WHGN", "BNGN", "WHYE", "YEBN", "WHGY", "GYBN", "WHPK", "PKBN", "WHBU", "BNBU",
        "WHRD", "BNRD", "WHBK", "BNBK", "GYGN", "YEGY", "PKGN", "YEPK", "GNBU", "YEBU",
        "GNRD", "YERD", "GNBK", "YEBK", "GYBU", "PKBU", "GYRD", "PKRD", "GYBK", "PKBK",
        "BUBK", "RDBK", "WHBNBK", "YEGNBK", "GYPKBK", "RDBUBK", "WHGNBK", "BNGNBK",
        "WHYEBK", "YEBNBK", "WHGYBK", "GYBNBK", "WHPKBK", "PKBNBK", "WHBUBK",
        "BNBUBK", "WHRDBK", "BNRDBK",
    ],
    # fmt: on
    "IEC": ["BN", "RD", "OG", "YE", "GN", "BU", "VT", "GY", "WH", "BK"],
    "BW": ["BK", "WH"],
    # 25-pair color code - see also https://en.wikipedia.org/wiki/25-pair_color_code
    # 5 major colors (WH,RD,BK,YE,VT) combined with 5 minor colors (BU,OG,GN,BN,SL).
    # Each POTS pair tip (+) had major/minor color, and ring (-) had minor/major color.
    # fmt: off
    "TEL": [  # 25x2: Ring and then tip of each pair
        "BUWH", "WHBU", "OGWH", "WHOG", "GNWH", "WHGN", "BNWH", "WHBN", "SLWH", "WHSL",
        "BURD", "RDBU", "OGRD", "RDOG", "GNRD", "RDGN", "BNRD", "RDBN", "SLRD", "RDSL",
        "BUBK", "BKBU", "OGBK", "BKOG", "GNBK", "BKGN", "BNBK", "BKBN", "SLBK", "BKSL",
        "BUYE", "YEBU", "OGYE", "YEOG", "GNYE", "YEGN", "BNYE", "YEBN", "SLYE", "YESL",
        "BUVT", "VTBU", "OGVT", "VTOG", "GNVT", "VTGN", "BNVT", "VTBN", "SLVT", "VTSL",
    ],
    "TELALT": [  # 25x2: Tip and then ring of each pair
        "WHBU", "BU",   "WHOG", "OG",   "WHGN", "GN",   "WHBN", "BN",   "WHSL", "SL",
        "RDBU", "BURD", "RDOG", "OGRD", "RDGN", "GNRD", "RDBN", "BNRD", "RDSL", "SLRD",
        "BKBU", "BUBK", "BKOG", "OGBK", "BKGN", "GNBK", "BKBN", "BNBK", "BKSL", "SLBK",
        "YEBU", "BUYE", "YEOG", "OGYE", "YEGN", "GNYE", "YEBN", "BNYE", "YESL", "SLYE",
        "VTBU", "BUVT", "VTOG", "OGVT", "VTGN", "GNVT", "VTBN", "BNVT", "VTSL", "SLVT",
    ],
    # fmt: on
    "T568A": ["WHGN", "GN", "WHOG", "BU", "WHBU", "OG", "WHBN", "BN"],
    "T568B": ["WHOG", "OG", "WHGN", "BU", "WHBU", "GN", "WHBN", "BN"],
}

# Convention: Color names should be 2 letters long, to allow for multicolored wires

_color_hex = {
    "BK": "#000000",
    "WH": "#ffffff",
    "GY": "#999999",
    "PK": "#ff66cc",
    "RD": "#ff0000",
    "OG": "#ff8000",
    "YE": "#ffff00",
    "OL": "#708000",  # olive green
    "GN": "#00ff00",
    "TQ": "#00ffff",
    "LB": "#a0dfff",  # light blue
    "BU": "#0066ff",
    "VT": "#8000ff",
    "BN": "#895956",
    "BG": "#ceb673",  # beige
    "IV": "#f5f0d0",  # ivory
    "SL": "#708090",
    "CU": "#d6775e",  # Faux-copper look, for bare CU wire
    "SN": "#aaaaaa",  # Silvery look for tinned bare wire
    "SR": "#84878c",  # Darker silver for silvered wire
    "GD": "#ffcf80",  # Golden color for gold
}

_color_full = {
    "BK": "black",
    "WH": "white",
    "GY": "grey",
    "PK": "pink",
    "RD": "red",
    "OG": "orange",
    "YE": "yellow",
    "OL": "olive green",
    "GN": "green",
    "TQ": "turquoise",
    "LB": "light blue",
    "BU": "blue",
    "VT": "violet",
    "BN": "brown",
    "BG": "beige",
    "IV": "ivory",
    "SL": "slate",
    "CU": "copper",
    "SN": "tin",
    "SR": "silver",
    "GD": "gold",
}

_color_ger = {
    "BK": "sw",
    "WH": "ws",
    "GY": "gr",
    "PK": "rs",
    "RD": "rt",
    "OG": "or",
    "YE": "ge",
    "OL": "ol",  # olivgrün
    "GN": "gn",
    "TQ": "tk",
    "LB": "hb",  # hellblau
    "BU": "bl",
    "VT": "vi",
    "BN": "br",
    "BG": "bg",  # beige
    "IV": "eb",  # elfenbeinfarben
    "SL": "si",  # Schiefer
    "CU": "ku",  # Kupfer
    "SN": "vz",  # verzinkt
    "SR": "ag",  # Silber
    "GD": "au",  # Gold
}


color_default = "#ffffff"

_hex_digits = set("0123456789abcdefABCDEF")


# Literal type aliases below are commented to avoid requiring python 3.8
Color = str  # Two-letter color name = Literal[_color_hex.keys()]
Colors = str  # One or more two-letter color names (Color) concatenated into one string
ColorMode = (
    str  # = Literal['full', 'FULL', 'hex', 'HEX', 'short', 'SHORT', 'ger', 'GER']
)
ColorScheme = str  # Color scheme name = Literal[COLOR_CODES.keys()]


def get_color_hex(input: Colors, pad: bool = False) -> List[str]:
    """Return list of hex colors from either a string of color names or :-separated hex colors."""
    if input is None or input == "":
        return [color_default]
    elif input[0] == "#":  # Hex color(s)
        output = input.split(":")
        for i, c in enumerate(output):
            if c[0] != "#" or not all(d in _hex_digits for d in c[1:]):
                if c != input:
                    c += f" in input: {input}"
                print(f"Invalid hex color: {c}")
                output[i] = color_default
    else:  # Color name(s)

        def lookup(c: str) -> str:
            try:
                return _color_hex[c]
            except KeyError:
                if c != input:
                    c += f" in input: {input}"
                print(f"Unknown color name: {c}")
                return color_default

        output = [lookup(input[i : i + 2]) for i in range(0, len(input), 2)]

    if len(output) == 2:  # Give wires with EXACTLY 2 colors that striped look.
        output += output[:1]
    elif pad and len(output) == 1:  # Hacky style fix: Give single color wires
        output *= 3  #              a triple-up so that wires are the same size

    return output


def get_color_translation(translate: Dict[Color, str], input: Colors) -> List[str]:
    """Return list of colors translations from either a string of color names or :-separated hex colors."""

    def from_hex(hex_input: str) -> str:
        for color, hex in _color_hex.items():
            if hex == hex_input:
                return translate[color]
        return f'({",".join(str(int(hex_input[i:i+2], 16)) for i in range(1, 6, 2))})'

    return (
        [from_hex(h) for h in input.lower().split(":")]
        if input[0] == "#"
        else [translate.get(input[i : i + 2], "??") for i in range(0, len(input), 2)]
    )


def translate_color(input: Colors, color_mode: ColorMode) -> str:
    if input == "" or input is None:
        return ""
    upper = color_mode.isupper()
    if not (color_mode.isupper() or color_mode.islower()):
        raise Exception("Unknown color mode capitalization")

    color_mode = color_mode.lower()
    if color_mode == "full":
        output = "/".join(get_color_translation(_color_full, input))
    elif color_mode == "hex":
        output = ":".join(get_color_hex(input, pad=False))
    elif color_mode == "ger":
        output = "".join(get_color_translation(_color_ger, input))
    elif color_mode == "short":
        output = input
    else:
        raise Exception("Unknown color mode")
    if upper:
        return output.upper()
    else:
        return output.lower()
