# Downloads the files text is made from and checked against into tools/ucd
# (Unicode 17.0.0) and tools/hyph (the en-US hyphenation patterns). They are
# not kept in the repository.
#
#   python3 tools/fetch.py
#
# Author: Alexius Academia
# Date: 2026-10-30

import os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UNICODE = "https://www.unicode.org/Public/17.0.0/ucd/"
FILES = {
    "ucd": [UNICODE + p for p in [
        "UnicodeData.txt", "CaseFolding.txt", "NormalizationTest.txt", "DerivedNormalizationProps.txt", "PropList.txt", "DerivedCoreProperties.txt",
        "extracted/DerivedGeneralCategory.txt", "emoji/emoji-data.txt",
        "auxiliary/GraphemeBreakProperty.txt", "auxiliary/WordBreakProperty.txt",
        "auxiliary/SentenceBreakProperty.txt", "auxiliary/GraphemeBreakTest.txt",
        "auxiliary/WordBreakTest.txt", "auxiliary/SentenceBreakTest.txt",
    ]],
    "stem": ["https://raw.githubusercontent.com/snowballstem/snowball-data/master/english/voc.txt",
             "https://raw.githubusercontent.com/snowballstem/snowball-data/master/english/output.txt"],
    "hyph": ["https://raw.githubusercontent.com/hyphenation/tex-hyphen/master/"
             "hyph-utf8/tex/generic/hyph-utf8/patterns/tex/hyph-en-us.tex"],
}

for folder, urls in FILES.items():
    os.makedirs(os.path.join(HERE, folder), exist_ok=True)
    for url in urls:
        path = os.path.join(HERE, folder, url.rsplit("/", 1)[1])
        if not os.path.exists(path):
            print("fetching", url)
            urllib.request.urlretrieve(url, path)
print("done")
