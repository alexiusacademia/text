# Writes unicode_data.tsl: the Unicode properties text's functions need, as
# packed range lists that the library decodes once when a program starts.
#
#   python3 tools/fetch.py          (once: the Unicode files into tools/ucd)
#   python3 tools/gen/gen_tables.py
#
# Each code point gets one number with all its properties in bits:
#   0-4 General_Category (ucd.GC)     5-8 Grapheme_Cluster_Break (ucd.GCB)
#   9 Extended_Pictographic           10-11 Indic_Conjunct_Break (ucd.INCB)
#   12-16 Word_Break (ucd.WB)         17-20 Sentence_Break (ucd.SB)
#   21 White_Space
# The code points are cut into ranges where that number stays the same
# (5,403 of them for Unicode 17). A range is stored as its first code point
# and the index of its number in a palette of the distinct numbers.
#
# Author: Alexius Academia
# Date: 2026-10-30

import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ucd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
WIDTH = 96  # characters of encoded data per line of the source


def packed(gc, gcb, wb, sb, ep, incb, ws, c):
    return (ucd.GC.index(gc[c])
            | ucd.GCB.index(gcb[c]) << 5
            | (1 << 9 if ep[c] else 0)
            | ucd.INCB.index(incb[c]) << 10
            | ucd.WB.index(wb[c]) << 12
            | ucd.SB.index(sb[c]) << 17
            | (1 << 21 if ws[c] else 0))


def hexes(values, digits):
    return "".join(format(v, "x").rjust(digits, "0") for v in values)


def chunks(s):
    return [s[i:i + WIDTH] for i in range(0, len(s), WIDTH)]


def tessel_list(name, comment, s, digits):
    lines = ["// " + l for l in comment]
    lines.append("let %s: [Int] = unpackHex([" % name)
    for c in chunks(s):
        lines.append('    "%s",' % c)
    lines.append("], %d)" % digits)
    return "\n".join(lines)


def main():
    gc, gcb, wb, sb, ep, incb, ws = ucd.load()
    starts, values = [], []
    prev = None
    for c in range(ucd.N):
        v = packed(gc, gcb, wb, sb, ep, incb, ws, c)
        if v != prev:
            starts.append(c)
            values.append(v)
            prev = v
    palette = sorted(set(values))
    assert len(palette) < 4096, len(palette)
    index = [palette.index(v) for v in values]
    index_digits = 2 if len(palette) <= 256 else 3

    folds = ucd.case_folding()
    fold_from = sorted(folds)
    fold_to = []
    for c in fold_from:
        t = folds[c]
        assert 1 <= len(t) <= 3
        fold_to.append(len(t))
        fold_to.extend(t)

    out = []
    out.append("""// text: the Unicode %s properties that splitting text and the character
// functions use. Made by tools/gen/gen_tables.py from the Unicode Character
// Database; don't change it by hand.
//
// Each code point has one number holding all its properties (see
// unicode.tsl for the bits). The code points are cut into %d ranges where
// that number is the same; `ucdStarts` holds the first code point of each
// range and `ucdIndex` the place of its number in `ucdPalette`.
//
// Author: Alexius Academia
// Date: 2026-10-30
""" % (ucd.VERSION, len(starts)))
    out.append(tessel_list("ucdPalette", ["The distinct property numbers (%d)." % len(palette)], hexes(palette, 6), 6))
    out.append("")
    out.append(tessel_list("ucdStarts", ["The first code point of each range."], hexes(starts, 6), 6))
    out.append("")
    out.append(tessel_list("ucdIndex", ["For each range, the place of its number in ucdPalette."], hexes(index, index_digits), index_digits))
    out.append("")
    out.append(tessel_list("foldFrom", ["The code points that case folding changes (%d), in order." % len(fold_from)], hexes(fold_from, 6), 6))
    out.append("")
    out.append(tessel_list("foldTo", ["For each of foldFrom: how many code points it folds to (1 to 3), then those."], hexes(fold_to, 6), 6))
    out.append("")
    path = os.path.join(ROOT, "unicode_data.tsl")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote %s: %d ranges, palette %d, %d folds" % (path, len(starts), len(palette), len(fold_from)))


if __name__ == "__main__":
    main()
