"""
EPUB Real Page Number Inserter for Kindle (via lxml)

This script modifies XHTML files from an EPUB to insert or remove Kindle-compatible
page markers of the form <span id="pgepubid00001"/> based on in-file instructions.

HOW IT WORKS:
- The script scans each file for the **first <span>** with an id that starts with "pgepubid".
- If the id is exactly "pgepubid", this file is treated as **strip-only**:
    -> All pgepubid spans will be removed; no new ones inserted.
- If the id is of the form "pgepubid00023" or "pgepubid000xii", then:
    -> That span is kept.
    -> All other pgepubid spans are removed.
    -> New ones are inserted starting from the next logical number.
- If no such span exists, the file is skipped.

SPAN PLACEMENT:
- Spans are inserted every N words (default: 200).
- Spans are inserted **only at safe locations**, never inside an <a> tag or other sensitive inline context.
- Insertion points fall between elements (e.g., between <p> blocks), never mid-word.

USAGE:
    python paginate_epub.py /path/to/file.xhtml
    python paginate_epub.py /path/to/folder/

    - If a single .xhtml file is given, it will be modified in-place.
    - If a directory is given, all .xhtml files in it will be scanned and summarized.

Author: ChatGPT (OpenAI), structured with Steve Sudit's editorial logic.
License: MIT
"""

import os
import re
import sys
from lxml import etree

def int_to_roman(n):
    numerals = [
        (1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'),
        (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
        (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')
    ]
    result = ''
    for value, numeral in numerals:
        while n >= value:
            result += numeral
            n -= value
    return result

def roman_to_int(s):
    s = s.lower()
    roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6,
                 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11,
                 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15}
    return roman_map.get(s, None)

def strip_pgepubid(root):
    for el in list(root.iter()):
        if el.tag == 'span' and el.attrib.get('id', '').startswith('pgepubid'):
            el.getparent().remove(el)

def find_first_pgepubid(root):
    for el in root.iter():
        if etree.QName(el).localname == 'span' and el.attrib.get('id', '').startswith('pgepubid'):
            return el
    return None

def is_inside_anchor(el):
    while el is not None:
        if etree.QName(el).localname.lower() == "a":
            return True
        el = el.getparent()
    return False

def count_words(text):
    return len(re.findall(r'\b\w+\b', text or ""))

def process_file(path, interval=200):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(path, parser)
    root = tree.getroot()

    first = find_first_pgepubid(root)
    if first is None:
        print(f"[SKIP] {os.path.basename(path)} — no pgepubid span")
        return

    first_id = first.attrib.get("id", "")
    if first_id == "pgepubid":
        strip_pgepubid(root)
        print(f"[STRIP] {os.path.basename(path)} — removed all pgepubid spans")
        tree.write(path, encoding="utf-8", xml_declaration=True, pretty_print=False,
                   doctype='<!DOCTYPE html>')
        return

    # Get numeric or roman base value
    suffix = first_id[8:]  # after "pgepubid"
    if suffix.isdigit():
        base = int(suffix)
        is_roman = False
    else:
        base = roman_to_int(suffix)
        is_roman = True
        if base is None:
            print(f"[ERROR] {os.path.basename(path)} — could not parse numeral '{suffix}'")
            return

    # Remove all other spans
    for el in list(root.iter()):
        if el.tag == 'span' and el is not first and el.attrib.get('id', '').startswith('pgepubid'):
            el.getparent().remove(el)

    # Search for body tag regardless of namespace
    body = next((el for el in root.iter() if etree.QName(el).localname == "body"), None)
    if body is None:
        print(f"[ERROR] {os.path.basename(path)} — no <body>")
        return

    word_count = 0
    page_index = base + 1

    def make_span(n):
        id_val = f'pgepubid000{int_to_roman(n)}' if is_roman else f'pgepubid{n:05d}'
        return etree.Element("span", id=id_val)

    for el in list(body.iter()):
        if is_inside_anchor(el):
            continue
        if el.text:
            word_count += count_words(el.text)
        if word_count >= interval:
            if el.getparent() is not None:
                el.addprevious(make_span(page_index))
                page_index += 1
                word_count = 0
        if el.tail:
            word_count += count_words(el.tail)
            if word_count >= interval:
            parent = el.getparent()
            if parent is not None:
                tag = etree.QName(parent).localname.lower()
                if tag not in {"ul", "ol", "menu"}:
                    parent.insert(parent.index(el) + 1, make_span(page_index))
                    page_index += 1
                    word_count = 0

    tree.write(path, encoding="utf-8", xml_declaration=True, pretty_print=False,
               doctype='<!DOCTYPE html>')
    print(f"[ADD] {os.path.basename(path)} — paginated from {first_id} to {page_index - 1}")
    next_marker = f'pgepubid000{int_to_roman(page_index)}' if is_roman else f'pgepubid{page_index:05d}'
    print(f"[NEXT] Use <span id=\"{next_marker}\"/> to continue pagination in the next file.")

def list_ranges(folder):
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".xhtml"):
            continue
        path = os.path.join(folder, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            root = etree.fromstring(content.encode('utf-8'))
            spans = [el.attrib["id"] for el in root.iter("span") if el.attrib.get("id", "").startswith("pgepubid")]
            if not spans:
                print(f"[NONE]  {fname} — no page markers")
            else:
                print(f"[RANGE] {fname} — {spans[0]} to {spans[-1]}")
        except Exception as e:
            print(f"[ERROR] {fname} — {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: paginate_epub.py file.xhtml | folder/")
        sys.exit(1)

    arg = sys.argv[1]
    if arg.endswith(".xhtml") and os.path.isfile(arg):
        process_file(arg)
    elif os.path.isdir(arg):
        list_ranges(arg)
    else:
        print("[ERROR] Invalid file or folder.")

if __name__ == "__main__":
    main()
