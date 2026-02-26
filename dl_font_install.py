#!/usr/bin/env python3
"""
Nerd Fonts bulk downloader + installer (macOS / Linux / Windows)

Author:
- James Sawyer

Purpose:
- Detect OS
- Fetch Nerd Fonts download page
- Parse Nerd Fonts ZIP asset links
- Download ZIP files with resume and retry support
- Extract font files
- Install fonts to a user or system location

Default install paths:
- macOS user:    ~/Library/Fonts
- macOS system:  /Library/Fonts
- Linux user:    ~/.local/share/fonts
- Linux system:  /usr/local/share/fonts
- Windows user:  %LOCALAPPDATA%\Microsoft\Windows\Fonts (registered in HKCU)

Important disclaimers:
- This script is an unofficial helper and is not affiliated with Nerd Fonts.
- Review and comply with the Nerd Fonts license terms before redistribution.
- Run at your own risk. Verify target paths before enabling system-wide installs.
- Large downloads are expected. Ensure sufficient bandwidth and disk space.

Operational notes:
- If FONT_NAMES is set, filtering is performed using extracted font metadata.
- OVERWRITE_MODE controls conflict handling for existing installed fonts.
- Set DRY_RUN = True to preview actions without modifying the system.
- Optional dependency: colorlog for colored logging output.
"""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import html
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

try:
    import requests
except ModuleNotFoundError as exc:
    raise RuntimeError("Missing dependency 'requests'. Install with: python3 -m pip install requests") from exc

# ------------------------- Configuration -------------------------

WORK_DIR = Path.home() / "Downloads" / "nerdfonts"
USE_TEMP_DIR = True
SYSTEM_INSTALL = False
FONT_NAMES: set[str] = set()
MAX_FONTS: Optional[int] = None
WORKERS = 4
TIMEOUT_SECONDS = 60
RETRY_COUNT = 4
KEEP_ZIPS = False
LOG_LEVEL = "INFO"
USE_COLOR_LOGGING = True
DRY_RUN = False
OVERWRITE_MODE = "ask_once"  # ask_once | overwrite_all | skip_all

# ------------------------- Logging -------------------------


def configure_logging(level: str, use_color: bool) -> None:
    """Configure application logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    if use_color:
        try:
            import colorlog  # type: ignore

            handler = colorlog.StreamHandler()
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s %(levelname)s%(reset)s %(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                },
            )
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
            return
        except ModuleNotFoundError:
            pass

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


logger = logging.getLogger("nerdfonts")


def log_runtime_disclaimers(log: logging.Logger) -> None:
    """Log key operational and safety notices before execution."""
    log.info("Unofficial utility. Not affiliated with Nerd Fonts.")
    log.info("Review Nerd Fonts license terms before redistribution.")
    log.info("Run at your own risk. Verify install mode and destination paths.")

# ------------------------- Core -------------------------

NERD_FONTS_PAGE = "https://www.nerdfonts.com/font-downloads"

ZIP_URL_RE = re.compile(
    r"""https://github\.com/ryanoasis/nerd-fonts/releases/download/[^"'\s>]+\.zip""",
    re.IGNORECASE,
)

FONT_FILE_RE = re.compile(r".*\.(ttf|otf|ttc)$", re.IGNORECASE)


@dataclass(frozen=True)
class DetectedOS:
    """Container for OS detection results."""

    name: str  # "macos" | "linux" | "windows"
    pretty: str


def detect_os() -> DetectedOS:
    """Detect the current OS in a normalized form."""
    sp = sys.platform.lower()
    if sp.startswith("darwin"):
        return DetectedOS("macos", "macOS")
    if sp.startswith("linux"):
        return DetectedOS("linux", "Linux")
    if sp.startswith("win"):
        return DetectedOS("windows", "Windows")
    return DetectedOS("linux", f"Unknown({sp}) treated as Linux")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http_get_text(url: str, timeout: int, log: logging.Logger) -> str:
    """Fetch URL content as text with basic error handling."""
    log.debug("GET %s", url)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def parse_zip_links(page_html: str, log: logging.Logger) -> list[str]:
    """Parse all Nerd Fonts ZIP asset links from HTML content."""
    page_html = html.unescape(page_html)
    links = sorted(set(ZIP_URL_RE.findall(page_html)))
    log.info("Found %s .zip links on Nerd Fonts page", len(links))
    return links


def pick_fonts(
    all_links: list[str],
    wanted: Optional[set[str]],
    max_n: Optional[int],
    log: logging.Logger,
) -> list[str]:
    """Filter the available ZIP links using the requested names and max count."""
    if not wanted and not max_n:
        return all_links

    def font_name_from_url(u: str) -> str:
        return Path(u).name.rsplit(".", 1)[0]

    wanted_norm = {w.lower() for w in wanted} if wanted else set()
    selected: list[str] = []
    for u in all_links:
        name = font_name_from_url(u)
        if wanted:
            # Normalize common variations: allow case-insensitive exact matches.
            if name.lower() not in wanted_norm:
                continue
        selected.append(u)
        if max_n and len(selected) >= max_n:
            break

    log.info("Selected %s fonts to process", len(selected))
    return selected


def _progress_bar(completed: int, total: int, width: int = 24) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "]"
    ratio = min(max(completed / total, 0.0), 1.0)
    filled = int(round(ratio * width))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def ensure_dir(p: Path) -> None:
    """Create a directory if it does not exist."""
    p.mkdir(parents=True, exist_ok=True)


def download_with_resume(
    url: str,
    dest: Path,
    timeout: int,
    retries: int,
    log: logging.Logger,
) -> None:
    """Download a URL to a file with resume and retry support."""
    ensure_dir(dest.parent)

    headers: dict[str, str] = {}
    existing = dest.exists()
    if existing:
        size = dest.stat().st_size
        if size > 0:
            headers["Range"] = f"bytes={size}-"
            log.debug("Resuming %s from byte %s", dest.name, size)

    attempt = 0
    while True:
        attempt += 1
        try:
            with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
                if r.status_code not in (200, 206):
                    r.raise_for_status()

                mode = "ab" if r.status_code == 206 and dest.exists() else "wb"
                total = r.headers.get("Content-Length")
                total_i = int(total) if total and total.isdigit() else None

                bytes_written = 0
                with dest.open(mode) as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        f.write(chunk)
                        bytes_written += len(chunk)

                log.debug(
                    "Downloaded %s (+%s bytes)%s",
                    dest.name,
                    bytes_written,
                    f" content-length={total_i}" if total_i else "",
                )
            return
        except requests.RequestException as exc:
            if attempt > retries:
                raise
            backoff = min(30, 2 ** (attempt - 1))
            log.warning(
                "Download failed (%s): %s. Retry in %ss [%s/%s]",
                dest.name,
                exc,
                backoff,
                attempt,
                retries,
            )
            time.sleep(backoff)


def extract_fonts_from_zip(zip_path: Path, out_dir: Path, log: logging.Logger) -> list[Path]:
    """Extract font files from a ZIP archive into a directory."""
    ensure_dir(out_dir)
    fonts: list[Path] = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if not FONT_FILE_RE.match(name):
                continue

            # Avoid weird paths.
            safe_name = Path(name).name
            target = out_dir / safe_name

            # If file already exists with same size, skip extract.
            if target.exists() and target.stat().st_size == info.file_size:
                fonts.append(target)
                continue

            with z.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            fonts.append(target)

    log.debug("Extracted %s fonts from %s", len(fonts), zip_path.name)
    return fonts


def _decode_name_string(platform_id: int, encoding_id: int, raw: bytes) -> str:
    if platform_id == 3:
        return raw.decode("utf-16-be", errors="ignore")
    if platform_id == 0:
        return raw.decode("utf-16-be", errors="ignore")
    if platform_id == 1:
        return raw.decode("mac_roman", errors="ignore")
    return raw.decode("latin-1", errors="ignore")


def extract_font_names(font_path: Path) -> set[str]:
    """Extract human-readable font names from a font file name table."""
    names: set[str] = set()
    try:
        with font_path.open("rb") as f:
            header = f.read(12)
            if len(header) != 12:
                return names
            num_tables = int.from_bytes(header[4:6], "big")
            name_table_offset = None
            name_table_length = None
            for _ in range(num_tables):
                record = f.read(16)
                if len(record) != 16:
                    return names
                tag = record[0:4]
                if tag == b"name":
                    name_table_offset = int.from_bytes(record[8:12], "big")
                    name_table_length = int.from_bytes(record[12:16], "big")
                    break
            if name_table_offset is None or name_table_length is None:
                return names
            f.seek(name_table_offset)
            table = f.read(name_table_length)
            if len(table) < 6:
                return names
            count = int.from_bytes(table[2:4], "big")
            string_offset = int.from_bytes(table[4:6], "big")
            for i in range(count):
                rec_offset = 6 + (i * 12)
                rec = table[rec_offset : rec_offset + 12]
                if len(rec) != 12:
                    continue
                platform_id = int.from_bytes(rec[0:2], "big")
                encoding_id = int.from_bytes(rec[2:4], "big")
                name_id = int.from_bytes(rec[6:8], "big")
                length = int.from_bytes(rec[8:10], "big")
                offset = int.from_bytes(rec[10:12], "big")
                if name_id not in {1, 4, 6}:
                    continue
                str_start = string_offset + offset
                str_end = str_start + length
                if str_end > len(table):
                    continue
                raw = table[str_start:str_end]
                decoded = _decode_name_string(platform_id, encoding_id, raw).strip()
                if decoded:
                    names.add(decoded)
    except OSError:
        return names
    return names


def filter_fonts_by_metadata(
    fonts: Iterable[Path],
    wanted: Optional[set[str]],
    log: logging.Logger,
) -> list[Path]:
    """Filter fonts using name metadata when names are provided."""
    if not wanted:
        return list(fonts)
    wanted_norm = {w.lower() for w in wanted}
    selected: list[Path] = []
    for font_path in fonts:
        names = extract_font_names(font_path)
        if not names:
            continue
        if any(name.lower() in wanted_norm for name in names):
            selected.append(font_path)
    log.info("Selected %s font files by metadata", len(selected))
    return selected


def all_font_dirs(osd: DetectedOS) -> list[Path]:
    """Return all known font directories for the current OS."""
    if osd.name == "macos":
        return [Path.home() / "Library" / "Fonts", Path("/Library/Fonts")]
    if osd.name == "linux":
        return [
            Path.home() / ".local" / "share" / "fonts",
            Path("/usr/local/share/fonts"),
            Path("/usr/share/fonts"),
        ]
    if osd.name == "windows":
        local = os.environ.get("LOCALAPPDATA")
        user_dir = (
            Path(local) / "Microsoft" / "Windows" / "Fonts"
            if local
            else Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"
        )
        win_dir = os.environ.get("WINDIR")
        system_dir = Path(win_dir) / "Fonts" if win_dir else Path("C:/Windows/Fonts")
        return [user_dir, system_dir]
    return []


def build_installed_font_index(
    font_dirs: Iterable[Path],
    log: logging.Logger,
) -> tuple[dict[str, set[Path]], dict[str, dict[int, set[Path]]]]:
    """Build indexes for installed fonts by name metadata and filename+size."""
    name_index: dict[str, set[Path]] = {}
    file_index: dict[str, dict[int, set[Path]]] = {}
    scanned = 0
    for base in font_dirs:
        if not base.exists():
            continue
        for font_path in base.rglob("*"):
            if not font_path.is_file():
                continue
            if not FONT_FILE_RE.match(font_path.name):
                continue
            scanned += 1
            try:
                size = font_path.stat().st_size
            except OSError:
                continue

            file_entry = file_index.setdefault(font_path.name.lower(), {})
            file_entry.setdefault(size, set()).add(font_path)

            for name in extract_font_names(font_path):
                name_index.setdefault(name.lower(), set()).add(font_path)
    log.info("Indexed %s installed font files", scanned)
    return name_index, file_index


def font_is_installed(
    font_path: Path,
    name_index: dict[str, set[Path]],
    file_index: dict[str, dict[int, set[Path]]],
) -> bool:
    """Check if a font is already installed using metadata then filename+size."""
    for name in extract_font_names(font_path):
        if name.lower() in name_index:
            return True
    try:
        size = font_path.stat().st_size
    except OSError:
        return False
    return size in file_index.get(font_path.name.lower(), {})


def resolve_overwrite_decision(conflict_count: int, log: logging.Logger) -> str:
    """Resolve overwrite policy when conflicts exist."""
    if conflict_count <= 0:
        return "overwrite"
    mode = OVERWRITE_MODE
    if mode == "overwrite_all":
        return "overwrite"
    if mode == "skip_all":
        return "skip"
    if mode != "ask_once":
        log.warning("Unknown OVERWRITE_MODE '%s'; defaulting to skip", mode)
        return "skip"

    prompt = (
        f"{conflict_count} fonts already installed. Overwrite? "
        "[y]es / [s]kip all / [q]uit: "
    )
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return "overwrite"
        if answer in {"s", "skip"}:
            return "skip"
        if answer in {"q", "quit"}:
            return "abort"
        log.info("Please enter y, s, or q.")


def macos_font_dir(system: bool) -> Path:
    """Return the macOS font install directory."""
    return Path("/Library/Fonts") if system else Path.home() / "Library" / "Fonts"


def linux_font_dir(system: bool) -> Path:
    """Return the Linux font install directory."""
    return Path("/usr/local/share/fonts") if system else Path.home() / ".local" / "share" / "fonts"


def windows_user_font_dir() -> Path:
    """Return the Windows per-user font install directory."""
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"
    return Path(local) / "Microsoft" / "Windows" / "Fonts"


@dataclass
class InstallSummary:
    """Track installation outcomes for reporting."""

    total: int = 0
    installed: int = 0
    overwritten: int = 0
    skipped_existing: int = 0
    failed: int = 0


def _install_fonts_to_dir(
    fonts: Iterable[Path],
    target_dir: Path,
    name_index: dict[str, set[Path]],
    file_index: dict[str, dict[int, set[Path]]],
    log: logging.Logger,
    register_fn: Optional[Callable[[Path], None]] = None,
) -> InstallSummary:
    ensure_dir(target_dir)
    summary = InstallSummary()
    fonts_list = list(fonts)
    summary.total = len(fonts_list)

    conflict_count = sum(1 for f in fonts_list if font_is_installed(f, name_index, file_index))
    decision = resolve_overwrite_decision(conflict_count, log)
    if decision == "abort":
        log.error("Aborted by user.")
        raise RuntimeError("Aborted by user")

    for f in fonts_list:
        dest = target_dir / f.name
        already_installed = font_is_installed(f, name_index, file_index)
        if already_installed and decision == "skip":
            summary.skipped_existing += 1
            continue

        if DRY_RUN:
            if already_installed:
                summary.overwritten += 1
            else:
                summary.installed += 1
            continue

        try:
            if dest.exists() and dest.stat().st_size == f.stat().st_size:
                summary.skipped_existing += 1
                continue
            shutil.copy2(f, dest)
            if register_fn is not None:
                register_fn(dest)
            if already_installed:
                summary.overwritten += 1
            else:
                summary.installed += 1
        except OSError as exc:
            log.warning("Failed to install %s: %s", f.name, exc)
            summary.failed += 1

    return summary


def install_fonts_macos(
    fonts: Iterable[Path],
    system: bool,
    name_index: dict[str, set[Path]],
    file_index: dict[str, dict[int, set[Path]]],
    log: logging.Logger,
) -> InstallSummary:
    """Install fonts on macOS."""
    target_dir = macos_font_dir(system)
    summary = _install_fonts_to_dir(fonts, target_dir, name_index, file_index, log)
    log.info("Installed %s font files into %s", summary.installed, target_dir)
    return summary


def install_fonts_linux(
    fonts: Iterable[Path],
    system: bool,
    name_index: dict[str, set[Path]],
    file_index: dict[str, dict[int, set[Path]]],
    log: logging.Logger,
) -> InstallSummary:
    """Install fonts on Linux."""
    target_dir = linux_font_dir(system)
    summary = _install_fonts_to_dir(fonts, target_dir, name_index, file_index, log)

    # Refresh font cache if available.
    fc = shutil.which("fc-cache")
    if fc and not DRY_RUN:
        try:
            subprocess.run([fc, "-f"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.debug("Ran fc-cache -f")
        except (OSError, subprocess.SubprocessError) as exc:
            log.warning("fc-cache failed: %s", exc)

    log.info("Installed %s font files into %s", summary.installed, target_dir)
    return summary


def _win_reg_add_font(font_path: Path, log: logging.Logger) -> None:
    """Register a font file in the current user's Windows registry."""
    # Register under HKCU so admin isn't required.
    # Key: HKCU\Software\Microsoft\Windows NT\CurrentVersion\Fonts
    # Value name: "<FontFileName> (TrueType)" -> "<FullPath>"
    # Some apps ignore non-system fonts; still generally works on Win 10/11.
    try:
        import winreg  # type: ignore
    except ModuleNotFoundError:
        log.warning("winreg not available; cannot register fonts in registry")
        return

    key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            value_name = f"{font_path.name} (TrueType)"
            winreg.SetValueEx(k, value_name, 0, winreg.REG_SZ, str(font_path))
    except OSError as exc:
        log.warning("Registry add failed for %s: %s", font_path.name, exc)


def install_fonts_windows(
    fonts: Iterable[Path],
    name_index: dict[str, set[Path]],
    file_index: dict[str, dict[int, set[Path]]],
    log: logging.Logger,
) -> InstallSummary:
    """Install fonts on Windows for the current user."""
    target_dir = windows_user_font_dir()

    def register(dest: Path) -> None:
        _win_reg_add_font(dest, log)

    summary = _install_fonts_to_dir(fonts, target_dir, name_index, file_index, log, register_fn=register)
    log.info("Installed %s font files into %s (HKCU registered)", summary.installed, target_dir)
    return summary


def human_name_from_url(u: str) -> str:
    """Return the font pack name derived from a download URL."""
    return Path(u).name.rsplit(".", 1)[0]


def process_one_zip(
    url: str,
    download_dir: Path,
    extract_root: Path,
    timeout: int,
    retries: int,
    keep_zips: bool,
    log: logging.Logger,
) -> tuple[str, int, str]:
    """Download, extract, and report one font pack."""
    name = human_name_from_url(url)
    zip_path = download_dir / f"{name}.zip"

    download_with_resume(url, zip_path, timeout=timeout, retries=retries, log=log)
    digest = sha256_file(zip_path)

    extract_dir = extract_root / name
    fonts = extract_fonts_from_zip(zip_path, extract_dir, log=log)

    if not keep_zips:
        try:
            zip_path.unlink(missing_ok=True)
        except OSError:
            pass

    return name, len(fonts), digest


def iter_all_extracted_fonts(extract_root: Path) -> list[Path]:
    """Return a list of all extracted font files under a root directory."""
    if not extract_root.exists():
        return []
    out: list[Path] = []
    for p in extract_root.rglob("*"):
        if p.is_file() and FONT_FILE_RE.match(p.name):
            out.append(p)
    return out


def main() -> int:
    """Run the download, extract, and install workflow."""
    configure_logging(LOG_LEVEL, use_color=USE_COLOR_LOGGING)
    log = logger
    log_runtime_disclaimers(log)
    osd = detect_os()
    log.info("Detected OS: %s", osd.pretty)

    work_dir = WORK_DIR.expanduser().resolve()
    wanted = FONT_NAMES if FONT_NAMES else None
    max_n = MAX_FONTS if MAX_FONTS and MAX_FONTS > 0 else None

    try:
        page = http_get_text(NERD_FONTS_PAGE, timeout=TIMEOUT_SECONDS, log=log)
    except requests.RequestException as exc:
        log.error("Failed to fetch Nerd Fonts page: %s", exc)
        return 2

    all_links = parse_zip_links(page, log=log)
    if not all_links:
        log.error("No zip links found; page structure may have changed.")
        return 3

    links = pick_fonts(all_links, wanted=None, max_n=max_n, log=log)
    if not links:
        log.error("No fonts selected. Update configuration.")
        return 4

    def run_with_dirs(base_dir: Path) -> int:
        download_dir = base_dir / "zips"
        extract_root = base_dir / "extracted"
        ensure_dir(download_dir)
        ensure_dir(extract_root)

        # Download + extract in parallel.
        failures: list[tuple[str, str]] = []

        total_packs = len(links)
        completed_packs = 0
        log.info("Processing %s font packs with %s workers", total_packs, WORKERS)
        with cf.ThreadPoolExecutor(max_workers=max(1, WORKERS)) as ex:
            futs = {
                ex.submit(
                    process_one_zip,
                    url,
                    download_dir,
                    extract_root,
                    TIMEOUT_SECONDS,
                    RETRY_COUNT,
                    KEEP_ZIPS,
                    log,
                ): url
                for url in links
            }
            for fut in cf.as_completed(futs):
                url = futs[fut]
                try:
                    name, n_fonts, digest = fut.result()
                    log.info("OK  %s: %s fonts (zip sha256 %s...)", name, n_fonts, digest[:12])
                except Exception as exc:
                    failures.append((url, str(exc)))
                    log.error("FAIL %s: %s", human_name_from_url(url), exc)
                completed_packs += 1
                log.info(
                    "Progress %s %s/%s",
                    _progress_bar(completed_packs, total_packs),
                    completed_packs,
                    total_packs,
                )

        extracted_fonts = iter_all_extracted_fonts(extract_root)
        log.info("Total extracted font files: %s", len(extracted_fonts))

        selected_fonts = filter_fonts_by_metadata(extracted_fonts, wanted=wanted, log=log)
        if wanted and not selected_fonts:
            log.error("No extracted fonts matched FONT_NAMES metadata.")
            return 4

        name_index, file_index = build_installed_font_index(all_font_dirs(osd), log)

        # Install.
        summary: Optional[InstallSummary] = None
        try:
            if osd.name == "macos":
                summary = install_fonts_macos(
                    selected_fonts,
                    system=SYSTEM_INSTALL,
                    name_index=name_index,
                    file_index=file_index,
                    log=log,
                )
            elif osd.name == "linux":
                summary = install_fonts_linux(
                    selected_fonts,
                    system=SYSTEM_INSTALL,
                    name_index=name_index,
                    file_index=file_index,
                    log=log,
                )
            elif osd.name == "windows":
                summary = install_fonts_windows(
                    selected_fonts,
                    name_index=name_index,
                    file_index=file_index,
                    log=log,
                )
            else:
                summary = install_fonts_linux(
                    selected_fonts,
                    system=SYSTEM_INSTALL,
                    name_index=name_index,
                    file_index=file_index,
                    log=log,
                )
        except PermissionError as exc:
            log.error("Permission error during install: %s", exc)
            return 5
        except Exception as exc:
            log.error("Install failed: %s", exc)
            return 6

        if summary is not None:
            log.info(
                "Summary total=%s installed=%s overwritten=%s skipped=%s failed=%s dry_run=%s",
                summary.total,
                summary.installed,
                summary.overwritten,
                summary.skipped_existing,
                summary.failed,
                DRY_RUN,
            )

        if failures:
            log.warning("%s packs failed. Working dir preserved at: %s", len(failures), base_dir)
            return 7

        installed_count = summary.installed if summary else 0
        log.info("Done. Installed %s font files. Working dir: %s", installed_count, base_dir)
        return 0

    if USE_TEMP_DIR:
        if KEEP_ZIPS:
            log.warning("KEEP_ZIPS ignored when USE_TEMP_DIR is enabled")
        with tempfile.TemporaryDirectory(prefix="nerdfonts_") as tmp:
            return run_with_dirs(Path(tmp))

    return run_with_dirs(work_dir)


if __name__ == "__main__":
    raise SystemExit(main())
