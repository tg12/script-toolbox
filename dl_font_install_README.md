# dl_font_install.py

Production-style Nerd Fonts downloader and installer for macOS, Linux, and Windows.

## Author

- James Sawyer

## What it does

- Detects the current operating system.
- Reads the official Nerd Fonts downloads page.
- Collects release ZIP URLs.
- Downloads ZIPs with retry and resume support.
- Extracts `.ttf`, `.otf`, and `.ttc` files.
- Installs fonts to user or system directories.
- Refreshes Linux font cache when `fc-cache` is available.
- Registers Windows user fonts in `HKCU`.

## Important disclaimers

- This project is unofficial and is not affiliated with the Nerd Fonts maintainers.
- You are responsible for compliance with Nerd Fonts and upstream font licenses.
- Use at your own risk. Review install paths and overwrite behavior before running.
- System-level installs may require elevated permissions.
- Download volume can be large; ensure enough bandwidth and disk space.

## Requirements

- Python 3.9+
- `requests`
- Optional: `colorlog` for colored logs

Install dependencies:

```bash
python3 -m pip install requests colorlog
```

## Configuration

Edit constants at the top of `dl_font_install.py`.

Most important settings:

- `USE_TEMP_DIR`: use an ephemeral working directory.
- `SYSTEM_INSTALL`: install to system font directories.
- `FONT_NAMES`: optional font family filtering by metadata.
- `MAX_FONTS`: limit number of font packs processed.
- `WORKERS`: parallel download and extract workers.
- `DRY_RUN`: preview actions without making changes.
- `OVERWRITE_MODE`: `ask_once`, `overwrite_all`, or `skip_all`.

## Run

```bash
python3 dl_font_install.py
```

## Typical workflow for safe sharing and testing

1. Set `DRY_RUN = True`.
2. Set `MAX_FONTS` to a small number.
3. Run and confirm output.
4. Disable dry run when ready.

## Output and behavior

- Logs progress and per-pack results.
- Produces a final install summary with counts:
  - total
  - installed
  - overwritten
  - skipped_existing
  - failed

## Security and operational notes

- The script downloads files from links parsed from the Nerd Fonts download page.
- If page structure changes, ZIP discovery may fail.
- Review and monitor downloads in sensitive environments before production use.
