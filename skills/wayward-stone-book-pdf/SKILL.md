---
name: wayward-stone-book-pdf
description: Generate a book-quality PDF from Wayward Stone chapters for any novel-gen run root using the repo PDF builder scripts (TOC + outline + running headers).
---

# Wayward Stone Book PDF

Use this skill when the user asks to generate a beautiful, book-like PDF for a manuscript run root.

## Run-root model (novel-gen)

- Known run roots: `gpt53/`, `kimi25/`, `kimi25_blend/`.
- Any new directory with chapter files is also a valid run root.
- Select one `RUN_ROOT` per PDF build.

## Script resolution

- Resolve PDF scripts by discovery:
  - builder script filename: `build_book_pdf.py`
  - renderer script filename: `render_pdf_pages.py`
- If multiple candidates exist, prefer the scripts already used by the active run-root workflow.

## Workflow

1. Build a PDF from `RUN_ROOT`:

```bash
mkdir -p <OUTPUT_DIR>
python <PDF_BUILDER_SCRIPT> \
  --input-dir <RUN_ROOT> \
  --out <OUTPUT_DIR>/wayward_stone_day_three_<RUN_ROOT_NAME>.pdf
```

2. Spot-check rendering:

```bash
python <PDF_RENDERER_SCRIPT> \
  <OUTPUT_DIR>/wayward_stone_day_three_<RUN_ROOT_NAME>.pdf \
  --out-dir <OUTPUT_DIR>/renders \
  --pages 1 --dpi 170
```

3. If chapter naming differs, pass `--chapters-glob` explicitly.

## Reference

Read `references/wayward_stone_book_pdf.md` for dependency setup, TOC/outline validation, and troubleshooting.
