# text

Text tools for [Tessel](https://tessel-lang.syncster.dev) programs:
characters as a reader sees them, words and sentences, hyphenation, and
fuzzy matching. It follows Unicode 17's rules, and the results are checked
against Unicode's own test files and against Python libraries.

```tessel
import text

fn main() {
    let note = "Don't skip it: the beam's depth is 3.5 m. Check e.g. the 1,000 kN case first! 👨‍👩‍👧 approves."
    print(text.words(note))
    print(text.wordCount(note))
    print(text.sentences(note))
    print("👨‍👩‍👧".count)
    print(text.graphemeCount("👨‍👩‍👧"))

    let h = text.englishHyphenator()
    print(h.hyphenate("reinforcement"))
    print(h.parts("hyphenation"))

    print(text.levenshtein("kitten", "sitting"))
    print(text.closest("lenght", ["length", "height", "width"]))
    print(text.fuzzyFilter("opfl", ["Open File", "Open Folder", "Copy File", "Toggle Fold"]))
}
```

prints

```text
["Don't", "skip", "it", "the", "beam's", "depth", "is", "3.5", "m", "Check", "e.g", "the", "1,000", "kN", "case", "first", "approves"]
17
["Don't skip it: the beam's depth is 3.5 m. ", "Check e.g. the 1,000 kN case first! ", "👨‍👩‍👧 approves."]
5
1
re-in-force-ment
["hy", "phen", "ation"]
3
["length", "height"]
["Open File", "Open Folder", "Copy File"]
```

Add it to a program with `tessel add text`, then `import text`.

## Positions

Tessel's strings count characters as Unicode code points: `count`,
`substring` and `character(at:)` all work that way. Every position this
library gives or takes is a code point index, so it can go straight into
`substring`. Code points aren't always what a reader calls a character,
though. The family emoji above is 5 code points but one grapheme cluster,
so carets and Backspace should move by `nextGrapheme` and
`previousGrapheme`.

## Characters

| Function | |
|---|---|
| `codePoints(_ s: String) -> [Int]` | The code points of `s`. |
| `codePoint(_ ch: String) -> Int` | The code point of the first character, -1 for `""`. |
| `fromCodePoints(_ cps: [Int]) -> String` | The text of some code points (U+FFFD for numbers that aren't code points). |
| `category(_ c: Int) -> String` | The General_Category: `"Lu"`, `"Ll"`, `"Nd"`, `"Po"`, `"Sc"`, `"So"`… |
| `isLetter`, `isUppercase`, `isLowercase`, `isMark`, `isDigit`, `isNumber`, `isPunctuation`, `isSymbol`, `isSpace`, `isAlphanumeric` | `(_ c: Int) -> Bool`, by the Unicode properties. |
| `caseFold(_ s: String) -> String` | The form for comparing without case: "Straße" and "STRASSE" both fold to "strasse". |
| `sameIgnoringCase(_ a: String, _ b: String) -> Bool` | Whether the folded texts are equal. |
| `unicodeVersion` | `"17.0.0"`. |

## Grapheme clusters, words and sentences

These follow the default rules of [UAX #29](https://www.unicode.org/reports/tr29/).
A list of breaks starts at 0 and ends at the text's count.

| Function | |
|---|---|
| `graphemes(_ s) -> [String]`, `graphemeCount(_ s) -> Int`, `graphemeBreaks(_ s) -> [Int]` | Characters as a reader counts them: an accented letter, a flag, an emoji with a skin tone, CR LF. |
| `nextGrapheme(_ s, _ at) -> Int`, `previousGrapheme(_ s, _ at) -> Int` | Where the caret goes with the arrow keys, and how far Backspace deletes. |
| `words(_ s) -> [String]`, `wordCount(_ s) -> Int` | The words: pieces with a letter or number in them. "don't", "e.g", "3.5", "1,000" and "foo_bar" each count as one word. Chinese and Japanese ideographs count one each. |
| `wordPieces(_ s) -> [Piece]`, `wordBreaks(_ s) -> [Int]` | All the pieces, words and the rest, with `from`, `to` and `isWord`. |
| `wordAt(_ s, _ at) -> Piece` | The piece at a position: what a double click selects. |
| `nextWordEnd`, `nextWordStart`, `previousWordStart` | `(_ s, _ at) -> Int`: Option/Ctrl+arrow movement. |
| `sentences(_ s) -> [String]`, `sentenceBreaks(_ s) -> [Int]` | Sentences, each with the spaces after it. No break after the full stop in "3.5" or in "e.g. this". The rules can't tell that "Mr. Smith" doesn't end a sentence. |

Speed: a 342,000-character text (about 100 pages) is word-counted in 10 ms
and split into sentences in 6 ms.

## Hyphenation

```tessel
let h = text.englishHyphenator()           // make once and keep: about 4 ms
h.hyphenate("hyphenation")                 // "hy-phen-ation"
h.points("structural")                     // [5]
h.hyphenateText("Reinforced concrete")     // soft hyphens (U+00AD) wherever a word may break
```

This is Liang's method, the one TeX uses. `englishHyphenator` has TeX's
American English patterns (`hyph-en-us.tex`, 4,938 patterns and Knuth's
exceptions). It keeps at least 2 letters before the first break and 3 after
the last; `englishHyphenator(left:right:)` changes that. For other
languages, give `hyphenatorFromTex` a pattern file from
[hyph-utf8](https://github.com/hyphenation/tex-hyphen), or give `hyphenator`
the patterns and exceptions themselves. Words containing anything other
than letters ("don't", "3rd") aren't hyphenated.

## Fuzzy matching

| Function | |
|---|---|
| `levenshtein(_ a, _ b) -> Int` | Insertions, deletions and substitutions. |
| `damerauLevenshtein(_ a, _ b) -> Int` | The same, also counting a swap of two neighbouring characters as one edit (the "optimal string alignment" version). |
| `similarity(_ a, _ b) -> Float` | 0 to 1: 1 − (insertions + deletions) / (both lengths). This is rapidfuzz's `ratio` / 100. |
| `jaro`, `jaroWinkler(_ a, _ b, prefixWeight: 0.1)` | For short texts such as names. |
| `closest(_ word, _ choices, limit: 3, cutoff: 0.6) -> [String]` | "Did you mean…": the most similar choices, ignoring case. |
| `fuzzyMatch(_ pattern, _ item) -> FuzzyMatch?` | Whether the pattern's letters appear in the item in order. Gives a `score` and the matched `positions`, for showing them in bold. |
| `fuzzyFilter(_ pattern, _ items) -> [String]` | The matching items, best first, as in a command palette. |

`fuzzyMatch` scores a matched letter higher when it starts a word (after a
space or punctuation, or a capital after a small letter) or follows the
previous match directly. Each letter skipped costs a point, so "opfl" ranks
"Open File" before "Open Folder".

## Tests

`tessel run tests` checks:

- the category of all 1,114,112 code points against `UnicodeData.txt`, and White_Space against `PropList.txt`;
- case folding against `CaseFolding.txt` and Python's `str.casefold`;
- all 3,222 cases of Unicode's `GraphemeBreakTest.txt`, `WordBreakTest.txt` and `SentenceBreakTest.txt`;
- hyphenation of 33,000 words against [pyphen](https://pyphen.org) with the same patterns;
- 1,509 pairs of distances against [rapidfuzz](https://github.com/rapidfuzz/RapidFuzz);
- the rest by hand, plus speed.

`tests/cases.json` is made by `tools/oracle/oracle.py`. Running it needs
the Unicode files (`python3 tools/fetch.py`) and a venv with pyphen and
rapidfuzz. `tools/gen/gen_tables.py` and `tools/gen/hyph.py` write
`unicode_data.tsl` and `hyphen_en.tsl` from the same files.

## Licence

MIT. The English hyphenation patterns in `hyphen_en.tsl` are © Gerard D.C.
Kuiken, and may be copied and changed as long as their notice (kept at the
top of that file) stays with them.
