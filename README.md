# LiminarChecker

Fast, read-only Windows checker with a small CMD menu.

## Menu

```text
[1] Fast PC scan
[2] Hidden hitbox / fake AppleSkin scan
[3] Exit
```

Mode 1 scans accessible fixed drives for JAR files and checks ZIP entry names.
Mode 2 scans JAR files for hidden hitbox expansion mixins and the known fake
AppleSkin downloader class.

## Run

Download `LiminarChecker.exe` and launch it from CMD or PowerShell.

## Verified installer

The PowerShell bootstrapper downloads the published EXE over HTTPS and checks
its SHA-256 before launching it:

```powershell
irm https://raw.githubusercontent.com/atamancukmalt8-ai/liminar-checker/main/install.ps1 | iex
```

The checker does not delete, move, unpack, or modify scanned files.
