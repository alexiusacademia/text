# Reads a TeX hyphenation pattern file (\patterns{…} and \hyphenation{…}),
# and writes hyphen_en.tsl, the en-US patterns as Tessel source.
#
#   python3 tools/gen/hyph.py
#
# Author: Alexius Academia
# Date: 2026-10-30

import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
WIDTH = 96


def read(path):
    """The patterns and the exceptions of a TeX pattern file."""
    text = open(path, encoding="utf-8").read()
    header = []
    for line in text.splitlines():
        if line.startswith("%"):
            header.append(line)
        else:
            break
    body = "\n".join(l.split("%", 1)[0] for l in text.splitlines())
    pats = re.search(r"\\patterns\s*\{(.*?)\}", body, re.S).group(1).split()
    m = re.search(r"\\hyphenation\s*\{(.*?)\}", body, re.S)
    excs = m.group(1).split() if m else []
    return pats, excs


def notice(path):
    """The copyright and licence lines at the top of the file."""
    out = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("%"):
            break
        out.append(line.rstrip("\n"))
    return out


def lines_of(words):
    out, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > WIDTH:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        out.append(cur)
    return out


def main():
    src = os.path.join(HERE, "..", "hyph", "hyph-en-us.tex")
    pats, excs = read(src)
    head = notice(src)[:20]
    out = ["// text: the hyphenation patterns of American English, for",
           "// `englishHyphenator`. Made by tools/gen/hyph.py from hyph-en-us.tex of",
           "// the hyph-utf8 package (%d patterns, %d exceptions); don't change it by" % (len(pats), len(excs)),
           "// hand. The file's notice, which its licence asks to keep:",
           "//"]
    out += ["// " + l.lstrip("%").rstrip() if l.strip("%").strip() else "//" for l in head]
    out += ["//", "// Author: Alexius Academia", "// Date: 2026-10-30", ""]
    out.append("// The patterns, separated by spaces.")
    out.append("fn englishPatterns() -> [String] {")
    out.append("    [")
    for l in lines_of(pats):
        out.append('        "%s",' % l)
    out.append("    ]")
    out.append("}")
    out.append("")
    out.append("// Words hyphenated by hand, separated by spaces.")
    out.append("fn englishExceptions() -> String {")
    out.append('    "%s"' % " ".join(excs))
    out.append("}")
    out.append("")
    path = os.path.join(ROOT, "hyphen_en.tsl")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote %s: %d patterns, %d exceptions" % (os.path.normpath(path), len(pats), len(excs)))


if __name__ == "__main__":
    main()
