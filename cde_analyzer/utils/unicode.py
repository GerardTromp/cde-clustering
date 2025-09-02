import re

# It is likely that most "Latin" translations in the table are superfluous
# encode.decode should substitute these automatically.
UNICODE_SUBSTITUTIONS = {
    "\u0092": "",  # unprintable
    "\u0096": "",  # unprintable
    "\u00a0": " ",  # non-breaking space
    "\u00a7": "section",
    "\u00a9": "(C)",
    "\u00ae": "(R)",
    "\u00b0": " degree ",
    "\u00b5": "u",  # micro
    "\u00bd": ".5",  # half as 1/2
    "\u00c9": "E",  # Latin E with accent acute / accent aigu
    "\u00d6": "O",  # Latin O with diaresis (umlaut)
    "\u00d8": "O",  # Latin O with stroke -- Norwegian O
    "\u00df": "beta",  # Latin small letter sharp S, but used incorrectly as beta
    "\u00e4": "a",  # Latin small a with diaresis (umlaut)
    "\u00e5": "a",  # Latin small a with ring -- Swedish o
    "\u00e9": "e",  # Latin small e with accent acute
    "\u00ef": "i",  # Latin small i with diaresis
    "\u00f6": "o",  # Latin small o with diaresis
    "\u00fc": "u",  # Latin small u with diaresis
    "\u03b1": "alpha",  # Greek alpha
    "\u03b2": "beta",  # Greek beta
    "\u03bc": "u",  # Greek mu -- context mostly in terms of amounts/concentrations
    "\u2009": " ",  # thin space
    "\u2011": "-",  # non-breaking hyphen
    "\u2012": "-",  # figure dash
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2022": "-",  # bullet
    "\u2026": "...",  # ellipsis
    "\u2122": "(TM)",  # trademark
    "\u2228": "|",  # logical OR
    "\u2265": ">=",  # greater than or equal to
    "\ufffd": "",  # replacement character
}

_unicode_sub_re = re.compile(
    "|".join(re.escape(k) for k in UNICODE_SUBSTITUTIONS.keys())
)


def normalize_unicode(text: str) -> str:
    # First replace known substitutions
    def replace_match(match):
        return UNICODE_SUBSTITUTIONS[match.group(0)]

    text = _unicode_sub_re.sub(replace_match, text)

    # Then remove any remaining diacritics or odd encodings
    # e.g., é -> e, ü -> u, etc.
    text = text.encode("ascii", "ignore").decode("ascii")

    return text
