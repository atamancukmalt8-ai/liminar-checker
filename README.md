# LiminarChecker

Fast, read-only Windows checker with a small CMD menu.

## Menu

```text
[1] Fast PC scan
[2] Process Hacker / System Informer manual memory check
[3] Exit
```

Mode 1 scans accessible fixed drives for JAR files and checks ZIP entry names.
Mode 2 opens the official System Informer releases page and prints the manual
strings to check in `javaw.exe`:

```text
liminar
liminarghost.fun
Liminar 1.21.4
```

The checker does not auto-download or auto-run Process Hacker/System Informer.

## Run

Download `LiminarChecker.exe` and launch it from CMD or PowerShell.

## Verified installer

The PowerShell bootstrapper downloads the published EXE over HTTPS and checks
its SHA-256 before launching it:

```powershell
irm https://raw.githubusercontent.com/atamancukmalt8-ai/liminar-checker/main/install.ps1 | iex
```

The checker does not delete, move, unpack, or modify scanned files.
