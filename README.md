# LiminarChecker

Fast, read-only Windows JAR indicator checker.

## Run

Download `LiminarChecker.exe` and launch it from CMD or PowerShell.

## Verified installer

The PowerShell bootstrapper downloads the published EXE over HTTPS and checks
its SHA-256 before launching it:

```powershell
irm https://raw.githubusercontent.com/atamancukmalt8-ai/liminar-checker/main/install.ps1 | iex
```

The checker does not delete, move, unpack, or modify scanned files.
