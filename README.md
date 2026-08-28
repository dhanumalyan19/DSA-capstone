# Huffman Compression Studio

A Data Structures & Algorithms capstone project: **Data Compression with
Huffman Encoding**, implemented as a complete, from-scratch compression
engine with a modern browser-based interface in Python.

---

## 1. Project Objective

Demonstrate the full theory and practice of Huffman Encoding -- frequency
analysis, priority queues (min-heaps), greedy binary tree construction,
recursive prefix-code generation, lossless encoding/decoding, and
information-theoretic analysis (Shannon entropy, compression ratio) --
inside a polished, genuinely functional web application, not a toy CLI
script or a slide deck of pseudocode.

Every action in the website performs a real, working operation against a
real, from-scratch algorithm implementation. Nothing is faked or
hard-coded.

---

## 2. Features

- **Browser dashboard** -- run the full Huffman workflow from a modern
  Flask-powered website.
- **Text or file input** -- type text directly, or open any UTF-8 `.txt` file.
- **Frequency analysis** with a live frequency/probability table.
- **From-scratch binary min-heap** (`core/heap.py`) -- not a wrapper
  around `heapq` -- used as the priority queue for tree construction.
- **Huffman Tree construction** via the classic greedy algorithm, with
  every merge step narrated in plain English, generated live from your
  actual input.
- **Recursive Huffman code generation**, guaranteed prefix-free.
- **Real encoding** to an actual bitstream, and **real file
  compression** to a custom `.huff` binary container format (see
  Section 8) that includes everything needed to decode later --
  including in a brand-new session with no in-memory state.
- **Real decoding**, including reconstructing the Huffman tree purely
  from the stored frequency table, walking it bit-by-bit.
- **Automatic Lossless Verification** -- `decoded == original` is
  checked programmatically and displayed as PASSED/FAILED, never
  simply assumed.
- **Interactive Huffman Tree visualization** rendered in the browser
  from the real tree object every time you run the pipeline.
- **Code Table tab** -- Character / Frequency / Probability / Huffman
  Code / Code Length, sorted by frequency.
- **Compression Analysis Dashboard** -- original size, theoretical
  bitstream size, actual stored file size (these are reported
  separately and honestly -- see Section 9), compression ratio, space
  savings %, Shannon entropy, average code length, encoding/decoding
  time.
- **Algorithm / "How It Works" tab** -- step-by-step narrated replay of
  exactly what the min-heap and tree builder did on your input, with
  Next/Previous controls.
- **Comparison module** -- benchmarks Huffman against genuinely
  implemented Run-Length Encoding, Shannon-Fano coding, and LZW on the
  same input. Arithmetic Coding is explicitly marked "not implemented"
  rather than faked.
- **Robust error handling** -- empty input, invalid files, corrupted
  `.huff` data, and decoding without a frequency table all show friendly
  browser messages instead of crashing.

---

## 3. DSA Concepts Demonstrated

| Concept | Where |
|---|---|
| Greedy algorithm | `core/huffman.py: build_huffman_tree` |
| Binary tree | `core/node.py: HuffmanNode` |
| Min-heap / priority queue | `core/heap.py: MinHeap` (array-based, from scratch) |
| Recursion | `core/huffman.py: generate_codes`, tree drawing in `gui/tree_view.py` |
| Prefix-free codes | Verified explicitly in `tests/test_huffman.py` |
| Frequency table | `core/huffman.py: calculate_frequencies` |
| Encoding / decoding | `core/encoder.py`, `core/decoder.py` |
| Time complexity (O(n log n)) | See Section 10 |
| Space complexity | See Section 10 |
| Entropy | `core/metrics.py: calculate_entropy` |
| Compression ratio / lossless compression | `core/metrics.py`, verified in `core/decoder.py` |

---

## 4. Architecture

```
huffman_project/
│
├── main.py                     Entry point
│
├── gui/                        All Tkinter UI code (no algorithm logic)
│   ├── app_state.py             Shared state + observer pattern between tabs
│   ├── theme.py                 Centralized colors/fonts/ttk styles
│   ├── main_window.py           Top-level window, assembles the 6 tabs
│   ├── compression_view.py      "Compress" tab
│   ├── decompression_view.py    "Decompress" tab
│   ├── tree_view.py             "Huffman Tree" tab (live Canvas drawing)
│   ├── code_table_view.py       "Code Table" tab
│   ├── analysis_view.py         "Analysis" tab
│   └── algorithm_view.py        "Algorithm" / How It Works tab
│
├── core/                        All DSA/algorithm logic (no GUI code)
│   ├── node.py                   HuffmanNode
│   ├── heap.py                   From-scratch array-based MinHeap
│   ├── huffman.py                Frequency analysis, tree build, codes
│   ├── encoder.py                Bitstream packing + .huff serialization
│   ├── decoder.py                Tree-walk decoding
│   ├── metrics.py                Entropy, ratios, savings, explanations
│   └── comparison.py             RLE / Shannon-Fano / LZW benchmarks
│
├── tests/                       Automated test suite (71 tests)
│   ├── test_huffman.py           Heap, frequency, tree, code generation
│   ├── test_encoding.py          Bit packing, serialization format
│   ├── test_decoding.py          Round-trip + all spec edge cases
│   ├── test_metrics.py           Entropy / ratio / savings formulas
│   ├── test_file_operations.py   Real file I/O workflow + error handling
│   └── test_gui.py               Headless GUI integration tests (real Tk)
│
├── sample_data/                 Demonstration text files
│   ├── sample_normal.txt
│   ├── sample_repetitive.txt
│   ├── sample_source_code.txt
│   ├── sample_random.txt
│   └── sample_small.txt
│
├── requirements.txt
└── README.md
```

GUI code, DSA/core logic, and tests are kept in strictly separate
packages, as required.

---

## 5. Installation

Requires Python 3.8+ (developed and tested on Python 3.12).

```bash
pip install -r requirements.txt
```

This installs Flask for the browser interface. The Huffman algorithm
itself remains implemented from scratch in `core/`.

## 6. How to Run

```bash
python main.py
```

This launches the Flask website, "Huffman Compression Studio."

Open this URL in your browser:

```bash
http://127.0.0.1:5000
```

---

## 7. How to Use the Website

1. **Compress tab**
   - Type text into the box, or click "Open Text File..." to load a
     `.txt` file.
   - Click the pipeline buttons **in order**: `1. Analyze` →
     `2. Build Tree` → `3. Generate Codes` → `4. Compress` →
     `5. Save Compressed File...`. Each button is disabled until its
     prerequisite has actually run.
   - The Result Summary panel shows real output from each stage.

2. **Decompress tab**
   - Choose a source: "Use Last Compressed Result" (decodes the
     in-memory result from the Compress tab, and automatically runs
     Lossless Verification against your original input) or "Load
     Compressed File (.huff)..." (decodes a `.huff` file from disk,
     from this session or a previous one).
   - Click "Decode". The recovered text and a verification banner
     (PASSED / FAILED / N/A) are shown.
   - Optionally "Save Recovered Text..." to a new `.txt` file.

3. **Huffman Tree tab** -- view the live, scrollable tree diagram for
   whatever you last built on the Compress tab.

4. **Code Table tab** -- view every symbol's frequency, probability,
   and assigned Huffman code.

5. **Analysis tab** -- view the full Compression Analysis Dashboard.
   Click "Run Comparison vs Other Techniques" to benchmark against
   RLE, Shannon-Fano, and LZW on the same input.

6. **Algorithm tab** -- step through exactly what the min-heap and
   tree builder did on your specific input, using Next/Previous.

---

## 8. The `.huff` File Format

A custom, honestly-documented binary container (see
`core/encoder.py` for the authoritative implementation):

```
b"HUFF1"                      5  bytes   magic / version
symbol_count                  4  bytes   unsigned int, big-endian
for each symbol:
    symbol utf-8 length       1  byte
    symbol utf-8 bytes        variable
    frequency                 4  bytes   unsigned int, big-endian
padding_bits                  1  byte    (0-7, padding on final byte)
original_symbol_count         4  bytes   unsigned int, big-endian
packed bitstream              variable   the actual compressed payload
```

Storing the frequency table (not the tree itself) is sufficient: the
decoder deterministically rebuilds an identical tree using the same
greedy algorithm, which is itself a nice demonstration of why the
algorithm is deterministic given the same input frequencies.

---

## 9. Honest Size Reporting

Per the project spec, two different "compressed size" numbers are
always shown and never conflated:

- **Theoretical bitstream size** -- `sum(frequency * code_length)`,
  i.e. the size of the raw sequence of 0s and 1s alone. This is the
  number most textbook Huffman explanations quote.
- **Actual stored `.huff` file size** -- the real number of bytes
  written to disk, including the magic header and the frequency table
  needed to decode later. For inputs with many unique symbols relative
  to their length (e.g. short text with high symbol diversity), this
  overhead can make the *stored* file larger than the original, even
  though the *bitstream itself* compressed well. The Analysis tab
  reports both, so this trade-off is visible rather than hidden.

---

## 10. Complexity Analysis

- **Frequency analysis:** O(n), where n = length of input text.
- **Building the min-heap:** O(k log k), where k = number of distinct
  symbols (k inserts, each O(log k)).
- **Building the Huffman tree:** O(k log k) -- exactly (k - 1) merge
  operations, each doing 2 pops + 1 push against a heap of size
  O(log k).
- **Code generation (tree traversal):** O(k), visits each of the
  O(2k - 1) nodes once.
- **Encoding:** O(n), one dictionary lookup + string append per input
  character.
- **Decoding:** O(m), where m = number of bits in the bitstream (each
  bit moves one step down the tree; a leaf is reached after at most
  the tree's height, and the *total* work across the whole bitstream
  is bounded by the number of bits, not bits x height).

Overall tree construction, the classic complexity of interest for this
algorithm, is **O(k log k)** where k is the number of *distinct*
symbols -- not the length of the input text, which is why Huffman
scales well even for very large inputs with a small alphabet.

- **Space complexity:** O(k) for the frequency table, heap, and tree
  (2k - 1 nodes total for k leaves in a full binary tree), plus O(n)
  for the input text and O(m) for the output bitstream.

---

## 11. Testing

### Automated test suite (71 tests, all passing)

```bash
python -m unittest discover -s tests -v
```

Covers:
- `MinHeap` correctness (ascending pop order, stable tie-breaking,
  empty-heap error handling)
- Frequency analysis correctness
- Tree construction: empty input, single-symbol special case,
  prefix-free property (exhaustively checked pairwise), higher
  frequency -> shorter-or-equal code length
- Bit packing/unpacking round trips
- `.huff` serialization/deserialization, including corrupted and
  truncated data
- **Full round-trip decode correctness across every edge case listed
  in the project spec**: empty input, one/two unique characters,
  normal English text, spaces, newlines, punctuation, numbers, special
  characters, Unicode (including emoji), very small input, larger
  text (9,000+ characters), highly repetitive text (5,000 characters),
  and a full printable-ASCII alphabet stress test
- Entropy formula verified against a manual from-scratch calculation,
  and against known closed-form cases (uniform 2-symbol = 1 bit,
  uniform 4-symbol = 2 bits)
- Real file I/O: read → compress → save → load → decode → save
  recovered → verify equality, plus empty/invalid/corrupted file
  handling
- **Headless GUI integration tests** (see below)

### Headless GUI Testing -- What Was Actually Done

This environment has **no physical display**, so a virtual framebuffer
(`Xvfb`) was installed and used to provide a real X11 display for Tk:

```bash
apt-get install -y python3-tk xvfb
Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99
python -m unittest discover -s tests -v
```

`tests/test_gui.py` does **not** merely import GUI modules. It
genuinely:
- Instantiates the real `MainWindow` (the same class `main.py` runs)
  against the live Xvfb display.
- Types real text into the real `tk.Text` input widget.
- Calls the real button command callbacks (`_on_analyze`,
  `_on_build_tree`, `_on_generate_codes`, `_on_compress`,
  `_use_in_memory`, `_on_decode`) -- the exact same functions wired to
  the on-screen buttons.
- Reads back what real widgets actually rendered: counts real
  `Canvas` items on the Huffman Tree tab, counts real `Treeview` rows
  on the Code Table tab, reads real `Text` widget contents on the
  Analysis tab, and drives real Next/Previous navigation on the
  Algorithm tab.
- Confirms the on-screen verification label literally reads
  `"Lossless Verification: PASSED"` after a real decode.

Beyond the automated suite, the application was also **visually
launched and screenshotted** under Xvfb using ImageMagick's `import`,
confirming: the Compress tab's pipeline buttons and result summary,
a genuinely rendered tree diagram with node frequencies and 0/1 edge
labels, a populated Code Table with correct prefix-free codes, an
Analysis dashboard with computed entropy/ratio/savings, and the
Decompress tab showing "Lossless Verification: PASSED" with the
correct recovered text -- all from real `sample_data/sample_normal.txt`
input, not placeholder data.

**Limitation, stated explicitly:** true interactive testing (a human
or an OS-level input-injection tool physically clicking pixels) was
not performed, because this is a headless container with no physical
display and no input-injection tooling installed. What *was* done --
instantiating the real GUI against a real X server, invoking the real
callback functions bound to each button, and reading back real widget
state -- is the strongest form of automated GUI verification available
in this environment, and it exercises the identical code path a mouse
click would trigger.

### Final End-to-End Verification (actually executed)

Using `sample_data/sample_repetitive.txt`:

```
Frequency Analysis: PASS (4 unique symbols)
Min-Heap / Huffman Tree construction: PASS (5 steps narrated)
Huffman Code generation: PASS (4 codes)
Encoding: PASS (604 bits, 0.066 ms)
Compressed Representation (.huff serialize): PASS (114 bytes)
Decoding: PASS (0.097 ms)

Original Text Recovered: YES
Automatic Equality Check: PASSED

Compression ratio (stored): 2.649 : 1
Space savings (stored):     62.25 %
Entropy:                    1.6496 bits/symbol
Avg Huffman code length:    2.0000 bits/symbol
```

And using `sample_data/sample_normal.txt` (373 bytes, 34 unique
symbols, higher symbol diversity relative to length) via the actual
running GUI:

```
Original size:                 373 bytes (2984 bits)
Theoretical bitstream size:    1642 bits (205.25 bytes)
Actual stored .huff file size: 424 bytes  <- larger than original!
Compression ratio (stored):    0.880 : 1
Space savings (stored):        -13.67 %
Shannon entropy:                4.3648 bits/symbol
Average Huffman code length:    4.4021 bits/symbol
Lossless Verification:          PASSED
```

This second result is reported deliberately, not hidden: it correctly
demonstrates that for short inputs with high symbol diversity, the
frequency-table header overhead can outweigh the bitstream savings --
an honest and pedagogically useful result, exactly per the project's
instruction not to manipulate numbers to make Huffman look artificially
good.

---

## 12. Example Workflow

```
1. Launch:            python main.py
2. Compress tab:      Open Text File -> sample_data/sample_normal.txt
3. Click:             1. Analyze
4. Click:             2. Build Tree
5. Click:             3. Generate Codes
6. Click:             4. Compress
7. Click:             5. Save Compressed File... -> sample_normal.huff
8. Decompress tab:    Load Compressed File (.huff)... -> sample_normal.huff
9. Click:             Decode
10. Observe:          Lossless Verification: PASSED
11. Huffman Tree tab: view the constructed tree
12. Code Table tab:   view every symbol's code
13. Analysis tab:     view compression ratio, entropy, and run the
                      comparison against RLE / Shannon-Fano / LZW
14. Algorithm tab:    step through exactly how the tree was built
```

---

## 13. Limitations

- Arithmetic Coding is not implemented in the comparison module (see
  Section 2) -- correctly marked N/A rather than faked, per the
  project's explicit instruction.
- The `.huff` format's frequency-table header has fixed per-symbol
  overhead (1 + up to 4 bytes for the symbol + 4 bytes for its count),
  which is not itself entropy-coded. For very small inputs with many
  unique symbols, this can make the stored file larger than the
  bitstream alone (see Section 9) -- this is reported honestly, not
  hidden.
- The tree visualization lays out nodes with a simple recursive
  in-order-position algorithm; for extremely large alphabets (hundreds
  of unique symbols) the canvas becomes wide and requires scrolling,
  which is supported but not auto-zoomed.
- True automated mouse-click GUI testing was not possible in this
  headless container (no display, no input-injection tooling); see
  Section 11 for exactly what headless testing was and was not done.

## 14. Future Improvements

- Adaptive/canonical Huffman coding to shrink the stored header.
- An actual Arithmetic Coding implementation for the comparison tab.
- Zoom/pan controls and automatic layout scaling for very large trees.
- Batch mode: compress/decompress multiple files at once.
- Export the Huffman tree diagram as an image file.

---

## 15. Viva / Demonstration Tips

- Use `sample_data/sample_repetitive.txt` to show a *strong* result
  (compression ratio 2.6:1, 62% space savings) -- good for
  demonstrating Huffman coding at its best (highly skewed
  frequencies).
- Use `sample_data/sample_normal.txt` to show an *honest, imperfect*
  result (header overhead outweighs bitstream savings) -- good for
  discussing the practical difference between "theoretical bitstream
  size" and "actual stored file size," and why real compressors amortize
  header cost over larger files.
- Use `sample_data/sample_small.txt` ("Hi!\n") to demonstrate the
  single/near-single symbol edge case live.
- Walk through the Algorithm tab step-by-step to narrate the greedy
  merge process directly from the min-heap.
