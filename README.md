# EPUB Real Page Number Inserter

This script (`paginate_epub.py`) modifies XHTML files in an EPUB to insert or strip Amazon Kindle-compatible **Real Page Numbers**, using a word-count-based heuristic. It is particularly useful for authors and publishers who:

- Want precise control over what Kindle considers a "page"
- Wish to exclude glossary or back matter from skewing page counts
- Need to maintain pagination stability across updates

## ✨ Features

- Supports **both Arabic and Roman numeral** page numbering
- XHTML/EPUB3.3-compliant: passes [EPUBCheck](https://www.w3.org/publishing/epubcheck/)
- Idempotent: can be safely rerun on already-processed files
- Avoids inserting spans into invalid or disruptive locations (e.g. inside hyperlinks or list containers)
- Offers a dual mode: **strip-only** or **paginate from given number**

## 🔧 Usage

Run on a single XHTML file:

```bash
python paginate_epub.py path/to/section-chapter-1.xhtml
```

Or scan all `.xhtml` files in a directory to report current pagination:

```bash
python paginate_epub.py path/to/OEBPS/sections/
```

### Behavior
- If the first `<span>` in the file has `id="pgepubid00042"`, pagination begins at 43
- If the first `<span>` is `id="pgepubid"` (no number), **all pagination spans are removed**
- If there is **no `pgepubid` span**, the file is skipped

After processing, you'll see:

```text
[ADD] section-chapter-1.xhtml — paginated from pgepubid00042 to 101
[NEXT] Use <span id="pgepubid00102"/> to continue pagination in the next file.
```

## 📄 How Page Markers Work

Markers are inserted like so:
```html
<span id="pgepubid00001"/>
```
They occur every 200 words by default (you can change this in the script).

### Arabic Example:
```html
<span id="pgepubid00001"/> → page 1
<span id="pgepubid00002"/> → page 2
```

### Roman Example:
```html
<span id="pgepubid000iv"/> → page iv
<span id="pgepubid000v"/> → page v
```

To begin Roman pagination in a section, use:
```html
<span id="pgepubid000i"/>
```

## ✅ EPUB Safety
- Page spans are **not inserted inside `<a>` tags**
- Insertion is **skipped inside `<ul>`, `<ol>`, `<menu>`** to preserve structural validity
- Passes [EPUBCheck](https://github.com/w3c/epubcheck) cleanly

## ✍️ Credits
- Script by [ChatGPT](https://openai.com/chatgpt), refined with direction and quality control by [Steve Sudit](https://github.com/SteveSudit)
- Licensed under the MIT License

---
Feel free to fork, file issues, or request enhancements via GitHub.

