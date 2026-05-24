---
layout: post
title: "hello - the first post"
date: 2026-5-23 21:09 +0800
categories: uv update article pacakge
---

# hello world!

this is the first post on my blog.
<br>

# Some usage of uv - a powerful python environment manager

## Installation

- ### on windows

  - using winget

    ```powershell
    winget install uv
    ```

  - using Scoop

    ```powershell
    scoop install main/uv
    ```

  - using official script

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

- ### on Linux / MacOS X (darwin)

  - using official script

    ```sh
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    or

    ```sh
    wget -qO- https://astral.sh/uv/install.sh | sh
    ```

  - using package manager
    - homebrew (MacOS X)
      `brew install uv`

    - MacPorts
      `sudo port install uv`

    - Termux
      `apt install uv`

    - pacman
      `pacman -S uv`

- ### using pipx
  ```sh
  pipx install uv
  ```

- ### using pip
  ```sh
  pip install uv
  ```

- ### using cargo
  ```sh
  cargo install --locked uv
  ```

- ### binary on GitHub Release
  [GitHub Release](https://github.com/astral-sh/uv/releases)

---

## manage python versions

### show available python versions
```sh
uv python list
```

### install specific version of python (include pypy)
```sh
# install python3.12
uv python install 3.12

# install PyPy
uv python install pypy3.10
```

### set global default python version
```sh
uv python default <version>
```

### set default python of the project (create .python-version file)
```sh
uv python pin <version>
```

## manage virtual environment
### create
```sh
# create virtual env named .venv at current directory
uv venv
```
# create virtuan environment of specific python version
```sh
uv venv --python <version>
```

### activate
```sh
# macOS / Linux
source .venv/bin/activate

# Windows（PowerShell）
.venv\Scripts\activate
```

### deactivate
```sh
deactivate
```

