# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `tests/smoke.sh`: fast, offline, read-only structural checks (bash syntax,
  cross-script `VERSION`/`SUITE` parity, per-script es/en key parity, macOS
  bash 3.2 compatibility, and Windows regressions such as the channel
  pattern and the fail-closed checksum), plus a minimal CI workflow
  (shellcheck + smoke on Linux, PSScriptAnalyzer on Windows).
- Project layout per system: Linux scripts moved to `linux/` (names
  unchanged), with empty `win/` and `mac/` folders for the ports. The
  deployed `~/AppImages/FreeCAD/` copies are untouched.
- `win/FreeCAD-stable.ps1` + `win/FreeCAD-weekly.ps1` (plus `.cmd`
  double-click launchers): Windows ports of both scripts with the same CLI
  and semantics (portable `.7z` bundle next to the script, SHA256 check,
  single installed version, Start Menu shortcut in HKCU without admin,
  `.FCStd` association, config backup to `.zip` with the same 10-minute
  guard and 3-copy rotation, Spanish/English messages). No libdrm workaround
  (Linux only). The `.7z` extraction is automatic: `tar.exe`, then an
  installed 7-Zip, then a portable `7zr.exe` download. Validation: PowerShell
  parser 0 errors, PSScriptAnalyzer 0 errors, and the versioned structural
  suite `tests/smoke.sh` passes (33 checks with shellcheck, 28 without);
  end-to-end validation on a real Windows 11 is green (9th `-Todo`: quick
  10/0 + 10/0, full 21/0 + 21/0 with `.lnk` + association and the reviewed
  channel/checksum/atomic-install paths; see `docs/PORTABILIDAD.md` §5).
- `mac/FreeCAD-stable.command` + `mac/FreeCAD-weekly.command`: macOS ports
  of both scripts (one file per channel covers Intel and Apple Silicon via
  `uname -m`) with the same CLI and semantics (`.dmg` download with Terminal
  progress, SHA256 check, single versioned `.app` in `/Applications` or
  `~/Applications` without admin, Desktop symlink shortcut, config backup of
  `~/Library/Preferences/FreeCAD` to `.tar.gz` with the same 10-minute guard
  and 3-copy rotation, Spanish/English messages from locale plus
  `AppleLanguages` fallback). No libdrm workaround (Linux only). The weekly
  `.dmg` name embeds the macOS version (`macOS10/11/15`), so it is discovered
  via the per-tag GitHub API and the newest build not newer than the host is
  picked; quarantine is stripped after install to avoid Gatekeeper blocks.
  Written for macOS bash 3.2 (BSD-only tools). Validation: `bash -n` +
  shellcheck clean and the versioned structural suite `tests/smoke.sh`
  passes (33 checks with shellcheck, 28 without); end-to-end validation on a
  real Mac (Intel) is still pending, Apple Silicon untested.
- macOS ports: on macOS 11 (Big Sur) or older the scripts install the last
  compatible FreeCAD (**1.0.2**, Qt 5.15) instead of the latest, because
  FreeCAD 1.1+ ships Qt 6.8, which requires macOS 12+ and crashes at launch
  on older systems (FreeCAD/FreeCAD#28392); the upstream Qt 6.7 build that
  would have kept macOS 11 alive was abandoned (FreeCAD/FreeCAD#27384). It
  affects both channels; a notification explains it, and `--check`/`--help`
  keep working. Detection via `sw_vers` (test hook `FC_SW_VERS`), with the
  E2E runner reporting `legacy-mac=`.
- Both scripts: automatic backup of `~/.config/FreeCAD` before every launch
  (timestamped `.tar.gz` in `.cfg-backup-<channel>/` next to the AppImage,
  skipped when a backup less than 10 minutes old already exists, rotated to
  keep the last 3 copies). See "Configuration backups" in the README and
  `TROUBLESHOOTING.md` for the restore procedure.
- `TROUBLESHOOTING.md`: diagnostic guide for slow startups and crashes
  (journal/coredump commands and the restore procedure for config backups).
- `FreeCAD-stable.sh`: all-in-one script for the stable channel. Version and
  asset URL come from the GitHub API `releases/latest` (with an Atom feed
  fallback that probes `py311`/plain asset names), SHA256 verification, its
  own files (`freecad-stable.svg`, `.freecad-stable.log`, `.freecad-stable.lock`,
  `.no-stable-shortcut`) and its own start menu shortcut
  (`freecad-stable.desktop`), so both scripts can share a folder.
- Optional **Desktop shortcut** on Linux and Windows: a second opt-in
  first-run question (`--create-desktop`/`--remove-desktop`, opt-out mark
  `.no-*-desktop`). Linux copies the same `.desktop` entry to the Desktop
  folder (honouring `xdg-user-dir DESKTOP`); Windows drops a `.lnk` in the
  user Desktop (`[Environment]::GetFolderPath('Desktop')`). macOS already
  installs its only shortcut on the Desktop, so it is unchanged.

### Changed

- Windows `FreeCAD-stable.ps1`: the local bundle is no longer matched with a
  broad `FreeCAD_*-Windows-*` pattern, which also caught the weekly folder.
  It now filters to numeric bundles (`Get-BundleDirs`, `Where-Object` on
  `^FreeCAD_[0-9]`) — `-Filter` itself only understands `*`/`?`, so the
  character class cannot live there. Both channels can now share one folder:
  stable no longer mistakes the weekly install for its own, and neither
  channel deletes the other's bundle on install/uninstall.
- SHA256 verification is now fail-closed on all three platforms: when the
  `-SHA256.txt` sidecar cannot be downloaded, the update aborts (`sha256
  sidecar unavailable` in the log) instead of installing unverified. No
  network still means "keep running the local version": the abort only
  happens after downloading something new.
- Windows `Install-FromArchive` (both channels) now stages the new version
  before removing the old ones (the previous install is moved aside as
  `.old` and restored if the move fails), so a failed install never leaves
  you with no version.
- Windows `--uninstall` (both channels) also removes the portable `.7zr.exe`
  extractor it may have downloaded.
- The libdrm workaround is now applied only when it is really needed:
  - weekly: only for builds **older than `2026.09.30`** (from that tag the
    bundle no longer ships libdrm, FreeCAD PR #33005), decided from the date
    in the AppImage file name instead of always preloading;
  - stable: the AppImage is inspected with `unsquashfs -ll`/`-cat` (nothing is
    extracted) to check whether it ships an outdated libdrm, and the decision
    is cached in `.freecad-stable.fix` per version.
- `FreeCAD-stable.sh`: the GitHub API path now rejects non-`X.Y.Z` tags
  (`rc`/`weekly-*`) and only matches `FreeCAD_<version>-Linux-...` assets,
  falling back to the Atom feed, which already filtered them.
- `-y`/`--yes` also skips the start menu shortcut prompt now (before it only
  affected `--uninstall`).
- Local AppImage detection ignores broken symbolic links, directories and
  partial `.part` downloads, and picks the highest version (`sort -V`).
- Windows/macOS shortcuts now point at the updater script (check, download
  if needed, then launch) instead of the installed app: the Start Menu
  `.lnk` runs `powershell -ExecutionPolicy Bypass -File <script>` (keeping
  the app icon when a version is installed; the `.FCStd` association still
  opens the app directly), and the macOS Desktop link is a symlink to the
  `.command` (old `*.app` links are cleaned up automatically).
- `.FCStd` association is now opt-in with its own first-run question on all
  three systems (off by default, like any portable): new
  `--associate`/`--remove-assoc` flags and `.no-*-assoc` opt-out marks.
  Linux writes `MimeType` + `xdg-mime default`; Windows splits the HKCU keys
  out of shortcut creation; macOS uses `duti` when available, otherwise
  `lsregister` (Open With only, honestly documented).
- Global `VERSION="0.8.6"` and suite name `SUITE="FreeCAD AutoUpdater Scripts"`
  in all six scripts, shown as the `--help` header above the channel line.
- On SHA256 mismatch the scripts now log the expected and actual hashes
  (`exp=`/`act=`) to ease diagnosis.

### Fixed

- Moving the script folder no longer silently breaks the shortcuts or the
  `.FCStd` association: on every launch they are re-pointed when they no
  longer match the current location (Linux rewrites the `.desktop` whose
  `Exec` is stale; Windows regenerates the `.lnk` target/working dir and the
  HKCU `open\command`; macOS recreates the Desktop symlink).
- After the update step both scripts left `stderr` permanently redirected to
  `/dev/null` (`exec 9>&- 2>/dev/null`), silently swallowing every later
  error message (e.g. "no local AppImage and download failed") and FreeCAD's
  own stderr.
- The weekly script now accepts an optional asset suffix in its file name
  pattern (`-py3xx`), like the stable script already did.
- Windows `Get-UrlText` (both products) no longer reads URLs with
  in-memory `Invoke-WebRequest`: on PowerShell 5.1 it advertises
  `Accept-Encoding: gzip`, the CDN compresses the tiny sidecar and
  `.Content` returns the raw gzip bytes, so every SHA256 check failed
  (`exp=52/57`) even though every download was byte-perfect. It now uses
  `HttpClient.GetStringAsync`, the same transport as the downloader.
- Windows on ARM64 is now rejected up front with "unsupported architecture":
  there is no Windows-ARM64 FreeCAD build, and the scripts previously slid
  past the architecture guard only to fail later with a misleading
  "could not check the latest version (offline?)".

## [0.1.0] - 2026-09-19

### Added

- All-in-one script: download, install, update and run the FreeCAD weekly
  AppImage with a single command.
- Automatic detection and workaround of the bundled-libdrm issue on systems
  with Mesa >= 26.2 (forces the host libdrm via `LD_PRELOAD` only when needed).
- Version check through the GitHub releases Atom feed.
- Download progress window (`kdialog` + `qdbus`, `zenity` fallback) with an
  anti-flicker delay and a specific "no local version" message.
- SHA256 verification before replacing the installed AppImage.
- Start menu shortcut creation on first run (with a prompt and a persistent
  opt-out marker).
- Command line options: `--no-update`, `--check`, `--reinstall`,
  `--create-shortcut`, `--remove-shortcut`, `--uninstall`, `--yes`,
  `--verbose`, `--help`, and `--` to forward arguments to FreeCAD.
- Multi-architecture support (x86_64, aarch64).
- Automatic Spanish/English messages based on the system locale.
