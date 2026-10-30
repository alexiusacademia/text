# Reads the Unicode Character Database files in tools/ucd into per-code-point
# property arrays, for gen_tables.py and the oracle.
#
# Author: Alexius Academia
# Date: 2026-10-30

import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
UCD = os.path.join(HERE, "..", "ucd")
N = 0x110000
VERSION = "17.0.0"

def ranges(name):
    """(first, last, value) for each data line of a UCD property file."""
    out = []
    for line in open(os.path.join(UCD, name), encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(";")]
        cps = parts[0]
        if ".." in cps:
            a, b = cps.split("..")
            a, b = int(a, 16), int(b, 16)
        else:
            a = b = int(cps, 16)
        out.append((a, b, parts[1:]))
    return out

def prop(name, default, pick=lambda v: v[0], only=None):
    arr = [default] * N
    for a, b, v in ranges(name):
        if only and not only(v):
            continue
        val = pick(v)
        for c in range(a, b + 1):
            arr[c] = val
    return arr

GC = ["Cn", "Lu", "Ll", "Lt", "Lm", "Lo", "Mn", "Mc", "Me", "Nd", "Nl", "No",
      "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk", "So",
      "Zs", "Zl", "Zp", "Cc", "Cf", "Cs", "Co"]
GCB = ["Other", "CR", "LF", "Control", "Extend", "ZWJ", "Regional_Indicator",
       "Prepend", "SpacingMark", "L", "V", "T", "LV", "LVT"]
INCB = ["None", "Linker", "Consonant", "Extend"]
WB = ["Other", "CR", "LF", "Newline", "Extend", "ZWJ", "Regional_Indicator",
      "Format", "Katakana", "Hebrew_Letter", "ALetter", "Single_Quote",
      "Double_Quote", "MidNumLet", "MidLetter", "MidNum", "Numeric",
      "ExtendNumLet", "WSegSpace"]
SB = ["Other", "CR", "LF", "Extend", "Sep", "Format", "Sp", "Lower", "Upper",
      "OLetter", "Numeric", "ATerm", "SContinue", "STerm", "Close"]

def load():
    gc = prop("DerivedGeneralCategory.txt", "Cn")
    gcb = prop("GraphemeBreakProperty.txt", "Other")
    wb = prop("WordBreakProperty.txt", "Other")
    sb = prop("SentenceBreakProperty.txt", "Other")
    ep = prop("emoji-data.txt", False, pick=lambda v: True, only=lambda v: v[0] == "Extended_Pictographic")
    incb = prop("DerivedCoreProperties.txt", "None", pick=lambda v: v[1], only=lambda v: v[0] == "InCB")
    ws = prop("PropList.txt", False, pick=lambda v: True, only=lambda v: v[0] == "White_Space")
    return gc, gcb, wb, sb, ep, incb, ws

def case_folding():
    """Full case folding (statuses C and F): code point -> list of code points."""
    out = {}
    for a, b, v in ranges("CaseFolding.txt"):
        if v[0] in ("C", "F"):
            out[a] = [int(x, 16) for x in v[1].split()]
    return out
