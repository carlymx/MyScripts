# FreeCAD AutoUpdater Scripts
## FreeCAD Weekly / Stable (all-in-one scripts)
**v0.8.6**

**English** | [Español](README_ES.md)

Two shell scripts that **download, install, update and run** FreeCAD AppImages
on Linux with a single click (in `linux/`):

| Script | Channel |
|---|---|
| `linux/FreeCAD-weekly.sh` | Development builds (`weekly-YYYY.MM.DD`) |
| `linux/FreeCAD-stable.sh` | Stable releases (`1.1.4`, `1.2.0`, ...) |

Both store everything (AppImage, icon, log, markers and configuration
backups) next to the script, and both apply the `libdrm` workaround on
systems with recent Mesa **only when it is really needed** (see below). The
two scripts can live in the same folder without interfering with each other.

## Requirements

- Linux x86_64 or aarch64.
- `curl`.
- KDE Plasma recommended (`kdialog` + `qdbus`) for the progress window;
  `zenity` works as a fallback. Notifications use `notify-send`.
- FUSE (libfuse2) to run AppImages.
- `unsquashfs` (squashfs-tools) is optional and only used by
  `FreeCAD-stable.sh` to inspect the AppImage before applying the libdrm fix.
  Without it the fix is applied as a precaution (harmless).

## Quick start

1. Copy `FreeCAD-weekly.sh` (or `FreeCAD-stable.sh`) to a writable folder
   (for example `~/AppImages/FreeCAD/`).
2. Make it executable:
   ```sh
   chmod +x FreeCAD-weekly.sh FreeCAD-stable.sh
   ```
3. Run it:
   ```sh
   ./FreeCAD-weekly.sh     # development build
   ./FreeCAD-stable.sh     # stable release
   ```

On first run it downloads the latest build of its channel and asks whether to
create a start menu shortcut, whether to also add a Desktop shortcut and
whether to associate `.FCStd` files (like any portable, it associates nothing
unless you say so). On later runs it checks for updates and launches FreeCAD.

Everything (AppImage, icon, log, markers and configuration backups) is stored next to the script.

## Demo

[![Demo](media/demo-poster.png)](media/demo.mp4)

_Click the image to watch the demo (MP4, ~85 s)._

## Options

The same options work in both scripts (`./FreeCAD-stable.sh --check`, etc.):

| Option | Effect |
|---|---|
| (none) | Check/update and run |
| `--no-update` | Run without checking for updates |
| `--check` | Only check for a new version (no download) |
| `--reinstall` | Remove the local version and download the latest again |
| `--create-shortcut` | Create the start menu shortcut |
| `--remove-shortcut` | Remove the start menu shortcut |
| `--create-desktop` | Create a Desktop shortcut |
| `--remove-desktop` | Remove the Desktop shortcut |
| `--associate` | Associate `.FCStd` files (open on double click) |
| `--remove-assoc` | Remove the `.FCStd` association |
| `--uninstall` | Uninstall (AppImage, shortcut, association, icon, log) |
| `-y`, `--yes` | Do not prompt (assume yes) |
| `-v`, `--verbose` | Show extra information |
| `-h`, `--help` | Show help |
| `--` | Everything after it is passed to FreeCAD |

To pass arguments to FreeCAD, use `--`:

```sh
./FreeCAD-weekly.sh -- my_file.FCStd
./FreeCAD-weekly.sh -- --help
```

## About the libdrm workaround

Some FreeCAD AppImages bundle their own `libdrm` (2.4.125). On systems with
**Mesa >= 26.2**, the host driver needs symbols that bundled libdrm does not
export, so FreeCAD fails to start with `Could not initialize GLX`.

The scripts only force the host `libdrm` libraries with `LD_PRELOAD` when
that problem can actually occur, and each channel decides it differently:

- **`FreeCAD-weekly.sh`**: the date is in the file name, so nothing is
  inspected. Only weeklies **older than `2026.09.30`** get the fix (from that
  tag on the bundle no longer includes libdrm, thanks to
  [FreeCAD PR #33005](https://github.com/FreeCAD/FreeCAD/pull/33005)), and
  only if the host libdrm is recent enough.
- **`FreeCAD-stable.sh`**: it inspects the AppImage itself
  (`unsquashfs -ll`/`-cat`, nothing is extracted): if the bundle does not ship
  an active libdrm, or ships a recent one, no fix is applied. The decision is
  cached next to the AppImage (`.freecad-stable.fix`) and recalculated on
  every new version.

More info: [FreeCAD issue #32061](https://github.com/FreeCAD/FreeCAD/issues/32061).

## Configuration backups

Before every launch, each script saves a timestamped backup of the FreeCAD
configuration (`~/.config/FreeCAD`) next to the script:

- stable: `.cfg-backup-stable/freecad-cfg-YYYYMMDD-HHMMSS.tar.gz`
- weekly: `.cfg-backup-weekly/freecad-cfg-YYYYMMDD-HHMMSS.tar.gz`

A backup is skipped when one less than 10 minutes old already exists, and
only the 3 most recent copies are kept. Every backup is logged as
`config backup saved` in `.freecad-stable.log` / `.freecad-weekly.log`.

To restore a backup (with FreeCAD closed):

```sh
mv ~/.config/FreeCAD ~/.config/FreeCAD.old
tar -xzf .cfg-backup-stable/freecad-cfg-YYYYMMDD-HHMMSS.tar.gz -C ~/.config/
```

(Use `.cfg-backup-weekly` for the weekly channel.) If FreeCAD starts slowly
or crashes, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Uninstall

```sh
./FreeCAD-weekly.sh --uninstall
./FreeCAD-stable.sh --uninstall
```

## Windows port (experimental)

`win/` contains PowerShell ports of both scripts with the same options and
semantics: portable `.7z` bundle next to the script, SHA256 check, Start Menu
shortcut (no admin needed), optional `.FCStd` association (asked on first run,
off by default) and configuration backups
(`.zip` instead of `.tar.gz`). There is no libdrm workaround (Linux only).

1. Copy the `win/` folder to a writable folder.
2. Double-click `FreeCAD-stable.cmd` (or `FreeCAD-weekly.cmd`).

Requirements: Windows 10/11 x86_64, no dependencies (the `.7z` extractor is
`tar.exe`, an installed 7-Zip, or a portable `7zr.exe` downloaded
automatically). The logic is validated (parser + PSScriptAnalyzer clean and
the versioned `tests/smoke.sh` suite passes, 33 checks with shellcheck / 28
without); end-to-end validation on a real Windows 11 is green (E2E quick
10/0, full 21/0 per channel). See [PORTABILIDAD.md](docs/PORTABILIDAD.md).

## macOS port (experimental)

`mac/` contains bash ports of both scripts (double-clickable `.command`
files) with the same options and semantics: `.dmg` download with progress in
Terminal, SHA256 check, versioned `.app` installed in `/Applications`
(`~/Applications` without admin), Desktop shortcut, optional `.FCStd`
association (`duti` if installed, otherwise Open With registration) and
configuration backups
(`~/Library/Preferences/FreeCAD` to `.tar.gz`). There is no libdrm workaround
(Linux only). The weekly `.dmg` name embeds the macOS version, so it is
discovered via the GitHub API and the build closest to your system is picked.

1. Copy the `mac/` folder to a writable folder.
2. Double-click `FreeCAD-stable.command` (or `FreeCAD-weekly.command`).

Requirements: macOS 12+ (Intel or Apple Silicon), no dependencies (everything
used —`curl`, `shasum`, `hdiutil`, `osascript`— ships with the system).
On first run macOS will block the file (unidentified developer): right-click
→ *Open* → *Open*. The logic is validated (bash + shellcheck clean and the
versioned `tests/smoke.sh` suite passes, 33 checks with shellcheck / 28
without); end-to-end validation on a real Mac is still pending. See
[PORTABILIDAD.md](docs/PORTABILIDAD.md).

## Troubleshooting

- If it does not start, run `./FreeCAD-weekly.sh --verbose` (or
  `./FreeCAD-stable.sh --verbose`) and check `.freecad-weekly.log` /
  `.freecad-stable.log`. The stable log tells you why the libdrm fix was (or
  was not) applied.
- To check the version without downloading: `./FreeCAD-weekly.sh --check` or
  `./FreeCAD-stable.sh --check`.
- Slow startups or crashes: see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are tracked in
[CHANGELOG.md](CHANGELOG.md).
