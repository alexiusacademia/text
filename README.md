# text

Text tools for [Tessel](https://tessel-lang.syncster.dev) programs:
characters as a reader sees them, normalization, words and sentences,
hyphenation, spelling, fuzzy matching, stemming, full-text search and
readability scores. It follows Unicode 17's rules, and the results are checked
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
| `sameIgnoringCase(_ a: String, _ b: String) -> Bool` | Whether the texts are equal apart from case, however their accents are written. |
| `combiningClass(_ c: Int) -> Int` | The Canonical_Combining_Class: 0 for most characters, 230 for most accents above. |
| `unicodeVersion` | `"17.0.0"`. |

## Normalization

The same text can be stored as different code points. For example, "é"
can be one code point (U+00E9), or "e" followed by a combining accent
(U+0301):

```tessel
let typed = "Cafe" + text.fromCodePoints([769])
print(typed == "Café")              // false
print(text.nfc(typed) == "Café")    // true
print(text.nfkc("ﬁle №２"))          // file No2
```

`nfc` (composed: the usual form for storing text), `nfd` (decomposed),
`nfkc` and `nfkd` follow [UAX #15](https://www.unicode.org/reports/tr15/).
The K forms also turn ligatures, full-width letters, superscripts and the
like into plain characters, which is useful for searching and comparing.
All 20,034 cases of Unicode's `NormalizationTest.txt` pass, and every other
code point is left as it is.

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

## Spelling

```tessel
var sp = text.speller(text.systemWordList(), user: "Tessel\n")
sp.isCorrect("reinforcement")       // true
sp.isCorrect("recieve")             // false
for m in sp.misspellings("Teh beam was stoped by Tessel's sensor.") {
    print("{m.word} at {m.from}-{m.to}: {sp.suggest(m.word, limit: 3)}")
}
// Teh at 0-3: ["The", "Ten", "Tea"]
// stoped at 13-19: ["stopped", "stiped", "stooped"]
let line = sp.addWord("Syncster")   // "Syncster\n": append it to the user's dictionary file
text.autocorrect(text.autocorrectDefaults(), "Teh")   // "The"
```

A `Speller` is built from a word list with one word per line.
`systemWordList()` reads `/usr/share/dict/words` (236,000 words, built in
about 17 ms) and gives `""` on Windows. A word also counts as right when it
is a listed word with a regular ending (-s, -ed, -ing, -er, -est, -ly,
-ness, un-), following the usual spelling rules: "stopping" is right but
"stoping" isn't, and "shelves" is right but "shelfs" isn't. Capitals,
contractions, possessives, hyphenated words, acronyms, numbers and web
addresses are handled too. `suggest` ranks words one or two edits away by
how likely the slip is: swapped and doubled letters, letters left out,
neighbouring keys and wrong vowels. It also fixes endings ("basicly" →
"basically") and splits words run together ("alot" → "a lot").
`addWord`, `ignoreAll`, `ignoreOnce` and `resetIgnored` work like the
same commands in Word. `autocorrect` fixes about 140 common typing slips
and keeps their capitals.

This is the spell checker from the Quill word processor. With the system's
list, Quill's tests flag nothing in 1,548 words of ordinary prose, and
offer the intended word first for 42 of 42 common misspellings and 62 of
62 harder ones. It checks words at about 4 million a second.

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

## Stemming

```tessel
text.stem("running")        // "run"
text.stems("The engineers were checking the bending of reinforced beams")
// ["the", "engin", "were", "check", "the", "bend", "of", "reinforc", "beam"]
```

This is Snowball's English (Porter2) stemmer. It gives the same stem as
Snowball for all 42,649 words of Snowball's own test list. A stem isn't
always a word ("engin", "happi"), so compare stems with stems.

## Search

```tessel
var help = text.SearchIndex()
let pages = [
    "Simply supported beams: bending moment and shear force diagrams.",
    "Reinforced concrete columns under axial load and bending.",
    "Steel beam connections: bolted and welded.",
    "The moment of inertia of a section.",
]
for p in pages {
    let ignored = help.add(p)                     // gives the document's number: 0, 1, 2…
}
for hit in help.search("beam bending") {
    print("{hit.document} {hit.score.formatted(decimals: 3)}  {pages[hit.document]}")
}
print(help.search("\"bending moment\"").count)    // a phrase: 1
print(help.search("reinf", prefix: true)[0].document)   // while typing: 1
```

```text
0 0.531  Simply supported beams: bending moment and shear force diagrams.
2 0.327  Steel beam connections: bolted and welded.
1 0.304  Reinforced concrete columns under axial load and bending.
1
1
```

Results are ranked by BM25, as in Lucene and Elasticsearch (k1 = 1.2,
b = 0.75). The scores match Python's bm25s. Documents and queries are cut
into words, case folded, stripped of Snowball's 174 English stopwords and
stemmed, so "beam" finds "beams". `SearchIndex(stemming: false, stopwords: [])`
matches whole words only. A "phrase in quotes" must appear with its words
in order. `prefix: true` lets the last word be cut short, for searching as
you type. `addTerms` and `searchTerms` take terms that you split up
yourself.

## Readability

```tessel
let st = text.textStats("The cat sat on the mat. It was happy. Readability formulas estimate the education needed to understand a passage.")
print("{st.sentences} sentences, {st.words} words, {st.syllables} syllables")   // 3 sentences, 19 words, 35 syllables
print(st.fleschReadingEase().formatted(decimals: 1))                             // 44.6
print(st.fleschKincaidGrade().formatted(decimals: 1))                            // 8.6
```

`TextStats` holds the counts and has `fleschReadingEase`,
`fleschKincaidGrade`, `gunningFog`, `smogIndex`, `colemanLiauIndex`,
`automatedReadabilityIndex` and `readingMinutes`. `syllables(word)` counts
by English spelling rules. On the 35,627 words that the CMU Pronouncing
Dictionary shares with `/usr/share/dict/words`, the count matches CMU's for
93.6% of them, and for 97.5% of the words of ordinary prose. That is close
enough for formulas that average over a whole text. It does get some words
wrong ("created" counts as 2).

## Tests

`tessel run tests` checks:

- the category of all 1,114,112 code points against `UnicodeData.txt`, and White_Space against `PropList.txt`;
- all 20,034 cases of Unicode's `NormalizationTest.txt`, and that every other code point stays as it is;
- case folding against `CaseFolding.txt` and Python's `str.casefold`;
- all 3,222 cases of Unicode's `GraphemeBreakTest.txt`, `WordBreakTest.txt` and `SentenceBreakTest.txt`;
- hyphenation of 14,000 words against [pyphen](https://pyphen.org) with the same patterns;
- 1,509 pairs of distances against [rapidfuzz](https://github.com/rapidfuzz/RapidFuzz);
- stems of Snowball's whole English test list (42,649 words);
- BM25 scores of 400 queries over 300 documents against [bm25s](https://github.com/xhluca/bm25s);
- syllable counts of 35,627 words, against the rules' first version in Python and against the CMU dictionary;
- the spelling tests from Quill, including the system word list;
- the rest by hand, plus speed.

`tests/cases.json` is made by `tools/oracle/oracle.py`. Running it needs
the downloaded files (`python3 tools/fetch.py`) and a venv with pyphen,
rapidfuzz, snowballstemmer, bm25s and cmudict. `tools/gen/gen_tables.py` and `tools/gen/hyph.py` write
`unicode_data.tsl` and `hyphen_en.tsl` from the same files.

## Licence

MIT. The English hyphenation patterns in `hyphen_en.tsl` are © Gerard D.C.
Kuiken, and may be copied and changed as long as their notice (kept at the
top of that file) stays with them. The stopword list is Snowball's (BSD
licence).
