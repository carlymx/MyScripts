# Contributing

Thanks for your interest in improving FreeCAD Weekly / Stable.

## Reporting issues

- Search the existing issues first to avoid duplicates.
- Include your environment: distribution, desktop environment, session type
  (X11/Wayland), GPU and driver, and Mesa/libdrm versions.
- Say which script you use (`linux/FreeCAD-weekly.sh`,
  `linux/FreeCAD-stable.sh`, `win/FreeCAD-*.ps1` or `mac/FreeCAD-*.command`)
  and attach the output of `... --verbose` plus the relevant lines from the
  log (`.freecad-weekly.log` / `.freecad-stable.log` next to the script).

## Submitting changes

1. Fork the repository and create a branch.
2. Keep one implementation per system: bash for Linux (`linux/`),
   PowerShell 5.1 for Windows (`win/`), bash 3.2-compatible for macOS
   (`mac/`). x86_64 and ARM64 (arm64/aarch64) share the same file per
   channel; do not split per architecture.
3. Test your change before opening a pull request:
    - Linux/macOS: `bash -n` plus `shellcheck` on the touched script.
    - Windows: the PowerShell parser plus `PSScriptAnalyzer`
      (`Install-Module PSScriptAnalyzer -Scope CurrentUser`).
    - Try the main flows (first run, update, `--check`, `--uninstall`) in an
      isolated folder so you do not touch your real installation.
    - If you touch the libdrm workaround (Linux only), verify all three
      branches with `-v` and the log: weeklies `< 2026.09.30` (fix on),
      newer weeklies (fix off), and the stable AppImage (bundle inspection).
    - Pending end-to-end checklists live in `docs/E2E-windows.md` and
      `docs/E2E-macos.md`.
4. Describe the change and reference any related issue.

## Scope

This project offers launcher/updater wrappers around the official FreeCAD
builds (Linux AppImage, Windows `.7z` portable, macOS `.dmg`).
FreeCAD itself and its packaging live in the
[FreeCAD repository](https://github.com/FreeCAD/FreeCAD).
