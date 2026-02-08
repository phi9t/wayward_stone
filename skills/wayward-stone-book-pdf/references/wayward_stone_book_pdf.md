# Wayward Stone Book PDF (Reference)

This reference describes a run-root-based PDF workflow.

Known run roots: `gpt53/`, `kimi25/`, `kimi25_blend/`.
Also accept any new directory with chapter files.

## Resolve scripts

Discover script paths before running:

```bash
PDF_BUILDER_SCRIPT=$(rg --files | rg 'build_book_pdf.py' | head -n 1)
PDF_RENDERER_SCRIPT=$(rg --files | rg 'render_pdf_pages.py' | head -n 1)
```

## Recommended outputs

- PDF: `<OUTPUT_DIR>/wayward_stone_day_three_<RUN_ROOT_NAME>.pdf`
- Renders: `<OUTPUT_DIR>/renders/`

## Dependency setup

The PDF scripts may require Python deps (for example `reportlab`, `pypdf`, `pdfplumber`).
Use an isolated local venv when needed.

Minimal venv pattern:

```bash
python -m venv tmp/pdfs/.venv
tmp/pdfs/.venv/bin/pip install --upgrade pip
tmp/pdfs/.venv/bin/pip install reportlab pypdf pdfplumber
```

Then run:

```bash
tmp/pdfs/.venv/bin/python <PDF_BUILDER_SCRIPT> --input-dir <RUN_ROOT> --out <OUTPUT_DIR>/wayward_stone_day_three_<RUN_ROOT_NAME>.pdf
```

## Validate TOC + outline (quick)

- Open the PDF and confirm:
  - a Contents/TOC page exists
  - chapters are listed
  - navigation outline exists (if supported by the viewer)

If you want programmatic validation, use `pypdf` in the same venv to check outlines and entry count.

## Rendering spot-check

```bash
python <PDF_RENDERER_SCRIPT> <OUTPUT_DIR>/wayward_stone_day_three_<RUN_ROOT_NAME>.pdf --out-dir <OUTPUT_DIR>/renders --pages 1 --dpi 170
```
