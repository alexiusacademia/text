# Writes tests/cases.json: what text's functions must give, from sources
# other than text itself.
#
#   python3 tools/fetch.py                     (once)
#   tools/oracle/.venv/bin/python tools/oracle/oracle.py
#
# The venv has pyphen and rapidfuzz:
#   python3 -m venv tools/oracle/.venv
#   tools/oracle/.venv/bin/pip install pyphen rapidfuzz
#
# - categories: the General_Category of every code point, as runs, read
#   from UnicodeData.txt (not from the files the tables are made from).
# - spaces: the White_Space code points, from PropList.txt.
# - folds: case folding of each CaseFolding.txt entry and of words, the
#   words also checked with Python's str.casefold().
# - graphemes, words, sentences: Unicode's GraphemeBreakTest.txt,
#   WordBreakTest.txt and SentenceBreakTest.txt. Cases with a surrogate
#   code point are left out: a Tessel string can't hold one.
# - hyphens: pyphen (an independent Liang implementation) with the same
#   en-US patterns, on the words of /usr/share/dict/words.
# - distances: rapidfuzz's Levenshtein, OSA, Indel ratio and Jaro-Winkler.
#
# Author: Alexius Academia
# Date: 2026-10-30

import json, os, random, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..")
ROOT = os.path.join(TOOLS, "..")
UCD = os.path.join(TOOLS, "ucd")
sys.path.insert(0, os.path.join(TOOLS, "gen"))
import hyph  # noqa: E402

random.seed(20261030)


def categories():
    """Runs of General_Category over all code points, from UnicodeData.txt."""
    gc = ["Cn"] * 0x110000
    first = None
    for line in open(os.path.join(UCD, "UnicodeData.txt"), encoding="utf-8"):
        f = line.split(";")
        c = int(f[0], 16)
        if f[1].endswith(", First>"):
            first = c
            continue
        if f[1].endswith(", Last>"):
            for x in range(first, c + 1):
                gc[x] = f[2]
            continue
        gc[c] = f[2]
    runs = []
    for c in range(0x110000):
        if not runs or runs[-1]["category"] != gc[c]:
            runs.append({"from": c, "category": gc[c]})
    return runs


def spaces():
    out = []
    for line in open(os.path.join(UCD, "PropList.txt"), encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line or line.split(";")[1].strip() != "White_Space":
            continue
        cps = line.split(";")[0].strip()
        a, _, b = cps.partition("..")
        for c in range(int(a, 16), int(b or a, 16) + 1):
            out.append(c)
    return out


def folds():
    table = {}
    for line in open(os.path.join(UCD, "CaseFolding.txt"), encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        f = [x.strip() for x in line.split(";")]
        if f[1] in ("C", "F"):
            table[int(f[0], 16)] = "".join(chr(int(x, 16)) for x in f[2].split())
    out = [{"text": chr(c), "folded": t} for c, t in sorted(table.items())]
    # Words and sentences, checked with Python's casefold too (its Unicode
    # is older, so only characters it knows).
    samples = ["Straße", "STRASSE", "ΣΊΣΥΦΟΣ", "Ǆemal", "İstanbul", "ﬁne ﬂow", "Ꭰ Cherokee",
               "ÀÉÎÕÜ àéîõü", "Kelvin K and Å", "MAĞARA", "ǅ ǈ ǋ", "ΐ ΰ", "ʼn", "ẞ capital sharp s",
               "Hello, World! 123", "already folded", ""]
    for s in samples:
        t = "".join(table.get(ord(ch), ch) for ch in s)
        assert t == s.casefold(), (s, t, s.casefold())
        out.append({"text": s, "folded": t})
    return out


def break_tests(name):
    out = []
    skipped = 0
    for line in open(os.path.join(UCD, name), encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        cps = []
        breaks = []
        for tok in line.split():
            if tok == "÷":
                breaks.append(len(cps))
            elif tok == "×":
                pass
            else:
                cps.append(int(tok, 16))
        if any(0xD800 <= c <= 0xDFFF for c in cps):
            skipped += 1
            continue
        out.append({"text": "".join(chr(c) for c in cps), "breaks": breaks})
    print("%s: %d cases, %d with surrogates left out" % (name, len(out), skipped))
    return out


def dictionary_words():
    words = [w.strip() for w in open("/usr/share/dict/words", encoding="utf-8") if w.strip()]
    return words


def hyphens():
    import pyphen
    dic = os.path.join(HERE, ".hyph_en_us.dic")
    patterns, exceptions = hyph.read(os.path.join(TOOLS, "hyph", "hyph-en-us.tex"))
    with open(dic, "w", encoding="utf-8") as f:
        f.write("UTF-8\n")
        for p in patterns:
            f.write(p + "\n")
    p = pyphen.Pyphen(filename=dic, left=2, right=3)
    words = [w for w in dictionary_words() if w.isalpha() and w.isascii()]
    exc = {e.replace("-", "") for e in exceptions}
    sample = random.sample(words, 30000)
    out = []
    for w in sample:
        if w.lower() in exc:
            continue
        out.append({"word": w, "hyphenated": p.inserted(w, hyphen="-")})
    # Other minimums, on fewer words.
    p1 = pyphen.Pyphen(filename=dic, left=1, right=1)
    other = []
    for w in random.sample(words, 3000):
        if w.lower() in exc:
            continue
        other.append({"word": w, "hyphenated": p1.inserted(w, hyphen="-")})
    os.remove(dic)
    print("hyphens: %d words (left 2, right 3), %d (left 1, right 1)" % (len(out), len(other)))
    return out, other


def distances():
    from rapidfuzz.distance import Levenshtein, OSA, Indel, JaroWinkler, Jaro
    words = dictionary_words()
    pairs = []
    alphabet = "abcdeéñ😀 "
    for _ in range(1500):
        a = random.choice(words)
        if random.random() < 0.5:
            b = random.choice(words)
        else:
            # A few edits away.
            b = list(a)
            for _ in range(random.randint(1, 3)):
                op = random.randint(0, 3)
                i = random.randint(0, max(0, len(b) - 1))
                if op == 0 and b:
                    del b[i]
                elif op == 1:
                    b.insert(i, random.choice(alphabet))
                elif op == 2 and b:
                    b[i] = random.choice(alphabet)
                elif len(b) > 1 and i + 1 < len(b):
                    b[i], b[i + 1] = b[i + 1], b[i]
            b = "".join(b)
        pairs.append((a, b))
    pairs += [("", ""), ("", "abc"), ("abc", ""), ("ca", "abc"), ("kitten", "sitting"),
              ("martha", "marhta"), ("dixon", "dicksonx"), ("café", "cafe"), ("😀😃", "😃😀")]
    out = []
    for a, b in pairs:
        out.append({
            "a": a, "b": b,
            "levenshtein": Levenshtein.distance(a, b),
            "osa": OSA.distance(a, b),
            "ratio": Indel.normalized_similarity(a, b),
            "jaro": Jaro.similarity(a, b),
            "jaroWinkler": JaroWinkler.similarity(a, b),
        })
    print("distances: %d pairs" % len(out))
    return out


def main():
    hy, hy1 = hyphens()
    cases = {
        "categories": categories(),
        "spaces": spaces(),
        "folds": folds(),
        "graphemes": break_tests("GraphemeBreakTest.txt"),
        "words": break_tests("WordBreakTest.txt"),
        "sentences": break_tests("SentenceBreakTest.txt"),
        "hyphens": hy,
        "hyphensShort": hy1,
        "distances": distances(),
    }
    path = os.path.join(ROOT, "tests", "cases.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", os.path.normpath(path), os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
