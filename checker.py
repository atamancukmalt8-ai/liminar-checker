"""Read-only Liminar indicator checker for Windows.

The program never extracts, deletes, edits, or moves any file.  It walks all
accessible fixed drives, finds JAR files, and checks their ZIP entry names.
"""

from __future__ import annotations

import ctypes
import os
import time
import webbrowser
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True, convert=True)
except ImportError:
    class Fore:  # type: ignore[no-redef]
        RED = GREEN = CYAN = WHITE = YELLOW = LIGHTRED_EX = ""

    class Style:  # type: ignore[no-redef]
        BRIGHT = RESET_ALL = ""


TARGET_ENTRIES = frozenset(
    {
        "ru/hogoshi/Animation.class",
        "ru/hogoshi/AnimationType.class",
    }
)
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
SYSTEM_INFORMER_URL = "https://github.com/winsiderss/systeminformer/releases/latest"
PH_LEGACY_URL = "https://processhacker.sourceforge.io/downloads.php"
MEMORY_STRINGS = ("liminar", "liminarghost.fun", "Liminar 1.21.4")


def get_scan_roots() -> list[Path]:
    """Return all accessible fixed-drive roots (the whole PC, not just a profile)."""
    roots: list[Path] = []
    if os.name == "nt":
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        for index in range(26):
            if not mask & (1 << index):
                continue
            root = f"{chr(ord('A') + index)}:\\"
            # DRIVE_FIXED (3); network/removable drives are intentionally omitted.
            if ctypes.windll.kernel32.GetDriveTypeW(root) == 3:
                roots.append(Path(root))
    else:
        roots.append(Path(Path.home().anchor))

    return roots


def _path_key(path: Path, info: os.stat_result | None = None) -> tuple[object, ...]:
    """Use the file ID when available; fall back to a case-insensitive path."""
    if info is not None and getattr(info, "st_ino", 0):
        return ("id", info.st_dev, info.st_ino)
    return ("path", os.path.normcase(os.path.abspath(os.fspath(path))))


def _is_reparse_point(entry: os.DirEntry[str]) -> bool:
    """Inspect attributes only for directories, where a reparse point can loop."""
    try:
        attributes = entry.stat(follow_symlinks=False).st_file_attributes
        return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)
    except (OSError, PermissionError):
        return True


def find_jars(roots: list[Path]) -> list[Path]:
    """Fast iterative directory walk which neither follows links nor repeats files."""
    jars: list[Path] = []
    pending = [os.fspath(root) for root in roots]
    seen_dirs: set[tuple[object, ...]] = set()
    seen_files: set[tuple[object, ...]] = set()

    while pending:
        directory = pending.pop()
        try:
            directory_info = os.stat(directory, follow_symlinks=False)
            directory_key = _path_key(Path(directory), directory_info)
            if directory_key in seen_dirs:
                continue
            seen_dirs.add(directory_key)

            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        # Avoid stat() on every file: whole-drive scans encounter
                        # millions of non-JAR files, while only directories and
                        # matching JAR candidates need their metadata read.
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if not _is_reparse_point(entry):
                                pending.append(entry.path)
                        elif entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(".jar"):
                            file_info = entry.stat(follow_symlinks=False)
                            file_key = _path_key(Path(entry.path), file_info)
                            if file_key not in seen_files:
                                seen_files.add(file_key)
                                jars.append(Path(entry.path))
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            continue
    return jars


def check_jar(jar_path: Path) -> bool:
    """Check ZIP metadata only; no JAR is extracted or class contents read."""
    try:
        with zipfile.ZipFile(jar_path) as archive:
            names = set(archive.namelist())
            return TARGET_ENTRIES.issubset(names)
    except (PermissionError, OSError, zipfile.BadZipFile, zipfile.LargeZipFile, EOFError):
        return False
    except Exception:
        # Treat unusual/corrupt ZIP metadata as non-matches; never stop the scan.
        return False


def check_backup_json() -> Path | None:
    """Check the current profile's uTorrent backup file without hardcoding a name."""
    candidates = [
        Path.home() / "AppData" / "LocalLow" / "uTorrent" / "configs" / "backup.json",
    ]
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidates.append(Path(userprofile) / "AppData" / "LocalLow" / "uTorrent" / "configs" / "backup.json")
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except (OSError, PermissionError):
            continue
    return None


def print_banner() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.CYAN + Style.BRIGHT + r"""
 _     ___ __  __ ___ _   _    _    ____
| |   |_ _|  \/  |_ _| \ | |  / \  |  _ \
| |    | || |\/| || ||  \| | / _ \ | |_) |
| |___ | || |  | || || |\  |/ ___ \|  _ <
|_____|___|_|  |_|___|_| \_/_/   \_\_| \_\
""" + Fore.WHITE + "                           by yeh0b\n")


def print_menu() -> str:
    print(Fore.WHITE + Style.BRIGHT + "Choose mode:")
    print(Fore.CYAN + "  [1] Fast PC scan")
    print(Fore.CYAN + "  [2] Process Hacker / System Informer manual memory check")
    print(Fore.CYAN + "  [3] Exit")
    choice = input(Fore.WHITE + "\n> ").strip().lower()
    return choice


def show_process_hacker_manual() -> None:
    print_banner()
    print(Fore.CYAN + Style.BRIGHT + "Process Hacker / System Informer manual mode\n")
    print(Fore.WHITE + "Official download pages:")
    print(Fore.CYAN + f"  {SYSTEM_INFORMER_URL}")
    print(Fore.CYAN + f"  {PH_LEGACY_URL}")
    print()
    print(Fore.YELLOW + "I will open the official System Informer releases page in your browser.")
    print(Fore.YELLOW + "Download and run it manually, then check javaw.exe strings yourself.")
    print()
    print(Fore.WHITE + Style.BRIGHT + "Search strings:")
    for value in MEMORY_STRINGS:
        print(Fore.LIGHTRED_EX + f"  {value}")
    print()
    print(Fore.WHITE + "If any of these exact strings appear in javaw.exe memory, treat it as DETECT.")
    try:
        webbrowser.open(SYSTEM_INFORMER_URL)
    except Exception:
        pass
    input(Fore.WHITE + "\nPress Enter to return to menu...")


def _format_duration(seconds: float) -> str:
    """Render a concise, user-friendly duration for the progress line."""
    seconds = max(0, round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _print_progress(checked: int, total: int, started_at: float) -> None:
    """Update one compact CMD line with bar, rate and a rolling ETA."""
    if total == 0:
        return
    elapsed = max(time.monotonic() - started_at, 0.001)
    ratio = checked / total
    width = 28
    filled = round(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    rate = checked / elapsed
    remaining = (total - checked) / rate if rate else 0
    progress = (
        f"\r[{bar}] {ratio:6.2%} | JARs checked: {checked}/{total}"
        f" | {rate:.1f}/s | ETA: {_format_duration(remaining)}"
    )
    print(Fore.CYAN + progress + Style.RESET_ALL, end="", flush=True)


def run_scan() -> None:
    print_banner()
    print(Fore.CYAN + "Scanning all accessible fixed drives..." + Style.RESET_ALL)
    backup = check_backup_json()
    jars = find_jars(get_scan_roots())
    print(Fore.WHITE + f"Found JAR files: {len(jars)}. Starting parallel ZIP metadata check..." + Style.RESET_ALL)
    detected: list[Path] = []
    checked = 0
    workers = min(16, max(8, (os.cpu_count() or 4) * 2))
    started_at = time.monotonic()
    last_progress_update = 0.0

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="jar-check") as executor:
        futures = {executor.submit(check_jar, jar): jar for jar in jars}
        for future in as_completed(futures):
            jar = futures[future]
            try:
                if future.result():
                    detected.append(jar)
            except Exception:
                # A file can disappear/change while a whole-drive scan is running.
                pass
            checked += 1
            now = time.monotonic()
            if now - last_progress_update >= 0.10 or checked == len(jars):
                _print_progress(checked, len(jars), started_at)
                last_progress_update = now

    print()  # finish the single-line progress status
    for jar in sorted(detected, key=lambda p: os.path.normcase(os.fspath(p))):
        print(Fore.RED + Style.BRIGHT + f"[DETECTED] {jar}")
        print(Fore.RED + "  ru/hogoshi/Animation.class")
        print(Fore.RED + "  ru/hogoshi/AnimationType.class")
    if backup:
        print(Fore.YELLOW + Style.BRIGHT + "[SUSPICIOUS] backup.json (not a detection)")
        print(Fore.YELLOW + f"  {backup}")

    if detected:
        print("\n" + Fore.LIGHTRED_EX + Style.BRIGHT + "LIMINAR SUCKS")
    elif backup:
        print(Fore.YELLOW + "[SUSPICIOUS] No matching JAR detected; backup.json alone is only a suspicion signal.")
    else:
        print(Fore.GREEN + Style.BRIGHT + "[CLEAN] No detections found.")
    input(Fore.WHITE + "\nPress Enter to return to menu...")


def main() -> None:
    while True:
        print_banner()
        choice = print_menu()
        if choice in {"1", "scan", "s"}:
            run_scan()
        elif choice in {"2", "ph", "process", "process hacker", "system informer"}:
            show_process_hacker_manual()
        elif choice in {"3", "exit", "q", "quit"}:
            break
        else:
            print(Fore.RED + "Unknown option.")
            time.sleep(0.8)
    input(Fore.WHITE + "\nPress Enter to exit...")


if __name__ == "__main__":
    main()
