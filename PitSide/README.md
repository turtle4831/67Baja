# Pitside app

Pit dashboard for the Baja car. Python 3.10+, [uv](https://docs.astral.sh/uv/), and Git. uv installs Python for you if the machine does not already have 3.10+.

The in-app terminal uses a PTY on Linux and ConPTY on Windows (Windows 10 1809 or later).

## Install

Fresh machine: system packages, then uv, then clone and `uv sync`. uv creates `.venv` and installs Flet (including the desktop client). You do not need a separate Python installer.

### Linux

1. Install Git, curl, and GTK 3 (the Flet desktop window needs `libgtk-3.so.0`):

   Debian / Ubuntu:

   ```bash
   sudo apt update
   sudo apt install -y git curl libgtk-3-0
   ```

   Fedora:

   ```bash
   sudo dnf install -y git curl gtk3
   ```

   Arch:

   ```bash
   sudo pacman -S --needed git curl gtk3
   ```

2. Install uv:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Close and reopen the terminal so `uv` is on `PATH`, or run `source $HOME/.local/bin/env`.

3. Clone the repo and install Python deps:

   ```bash
   git clone https://github.com/turtle4831/67Baja.git
   cd 67Baja/PitSide
   uv sync
   ```

4. Run:

   ```bash
   uv run flet run
   ```

On WSL 2 you also need a display (WSLg on Windows 11, or an X server). `cannot open display` means the GUI cannot reach one; `uv run flet run --web` still works in a browser.

To package a Linux binary (`flet build linux`), also install the [Flet Linux build packages](https://flet.dev/docs/publish/linux/) (GTK 3 headers, clang, cmake, ninja, and friends).

### Windows

64-bit Windows 10 or 11. The embedded terminal needs Windows 10 version 1809 or later. Flet does not need extra system libraries.

1. Install Git (includes Git Bash):

   ```powershell
   winget install --id Git.Git -e --source winget
   ```

   Or download from [git-scm.com](https://git-scm.com/download/win).

2. Install uv in PowerShell:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Close and reopen the terminal so `uv` is on `PATH`. (`winget install --id=astral-sh.uv -e` also works.)

3. Clone the repo and install Python deps:

   ```powershell
   git clone https://github.com/turtle4831/67Baja.git
   cd 67Baja\PitSide
   uv sync
   ```

4. Run from PowerShell, Command Prompt, or Git Bash:

   ```powershell
   uv run flet run
   ```

## Run the app

### uv

Run as a desktop app:

```bash
uv run flet run
```

Run as a web app:

```bash
uv run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/).

## Build the app

### Android

```bash
flet build apk -v
```

For more details on building and signing `.apk` or `.aab`, refer to the [Android Packaging Guide](https://flet.dev/docs/publish/android/).

### iOS

```bash
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://flet.dev/docs/publish/ios/).

### macOS

```bash
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://flet.dev/docs/publish/macos/).

### Linux

```bash
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### Windows

```bash
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).

### Web

```bash
flet build web -v
```

For more details on building Web app, refer to the [Web Packaging Guide](https://flet.dev/docs/publish/web/).
