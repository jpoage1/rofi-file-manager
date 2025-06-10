# Workspace Manager

A Python-based workspace manager designed to facilitate file and workspace management through a combination of clipboard operations, file selection, and editor integration.

`workspace-manager.py` is a Python utility designed to manage a dynamic workspace environment through clipboard operations, file selection, and editor integration. It employs a client-server model using UNIX sockets for inter-process communication and utilizes `fzf` for interactive file selection.


A Python toolset for interactive workspace state management, file selection, clipboard operations and editor integration. Implements a client–server model over a UNIX socket.

## Features

- **File Selection**: Utilize `fzf` for interactive file selection.
- **Editor Integration**: Open selected files in a terminal-based editor.
- **Workspace Management**: Manage workspace state via a UNIX socket server-client model.



- **Clipboard Queue**: Add, remove, and commit files to the clipboard.
- **Interactive File Selection**: Use `fzf` for selecting files from the workspace.
- **Workspace State Management**: Maintain workspace state via a UNIX socket server-client model.

## Installation

1. Clone the repository:

```bash
   git clone https://github.com/yourusername/workspace-manager.git
   cd workspace-manager
````

2. Install dependencies:

```bash
   pip install -r requirements.txt
```

   Ensure `fzf` is installed on your system.

## Usage

Usage:

```bash
# start server
python workspace-manager.py server

# in another shell, start client
python workspace-manager.py client
```
### Server

Start the workspace server:

```bash
python workspace-manager.py
```

### Client

Run the client to interact with the server:

```bash
python workspace-manager.py
```

## Requirements

* Python 3.7+
* `fzf` for file selection
* `pyperclip` for clipboard operations
* `nvim` or another terminal-based editor
* A POSIX-compliant shell (bash, zsh, etc.)  
* X11 server for `xterm` (or adapt `edit_files` to your terminal emulator)
* `pathspec`  
* UNIX-like operating system

---
## License

MIT License. See LICENSE for details.
MIT License. See LICENSE for details.

```
::contentReference[oaicite:0]{index=0}
 ```

## Components

### Clipboard Management

The `Clipboard` class manages a queue of files. It provides methods to add, remove, and commit files to the clipboard. Committed files are concatenated and copied to the system clipboard.

### File Selection

The `run_fzf_socket_loop` function facilitates interactive file selection using `fzf`. It communicates with the server via a UNIX socket, sending selected entries back to the client.

### Editor Integration

The `edit_files` function opens selected files in a terminal-based editor, such as `nvim`, within an `xterm` window.

### Workspace Server

The `WorkspaceServer` class manages the workspace state. It listens for client connections, handles incoming messages to add or remove files, and broadcasts state changes to all connected clients.

## Installation

```bash
git clone https://github.com/<username>/workspace-manager.git
cd workspace-manager
pip install pyperclip pathspec
chmod +x workspace-manager.py
```

---

## Configurable Options

* Adjust `SOCKET_PATH` in `core/core_service.py` or export `WORKSPACE_MANAGER_SOCKET` to override socket location.
* Modify `search_config.py` defaults:

```python
use_gitignore        # filter via .gitignore
include_dotfiles     # include leading-dot files
directory_expansion  # expand directories
expansion_recursion  # recurse into subdirectories
expansion_depth      # max recursion depth (None = unlimited)
regex_mode           # enable regex filtering
regex_pattern        # pattern to match
```

---

## Modules

### `search_config.py`

Holds `SearchConfig` class. Controls inclusion of dotfiles, gitignore filtering, directory expansion and regex filtering.

### `clipboard/clipboard.py`

`Clipboard` class:

* `add_files(list[str])`
* `remove_files(list[str])`
* `clear()`
* `snapshot() → list[Path]`
* `restore(snapshot)`
* `commit()` → concatenates file contents, copies to system clipboard via `pyperclip`.

### `core/core.py`

* `filter_file_entries(selection)` → strips fzf separators
* `edit_files(files: list[str], editor="nvim")` → spawns `xterm` session running editor on given files.

### `core/core_service.py`

Implements server and client over UNIX socket:

* **Server** (`WorkspaceServer`):

  * Binds to `SOCKET_PATH`
  * Accepts new clients
  * Maintains `self.workspace: set[str]`
  * Handles JSON messages with `"action": "add_file"` or `"remove_file"`
  * Broadcasts workspace state to all clients

* **Client** (`WorkspaceClient`):

  * Connects to server socket
  * Listens for `"type":"state"` messages
  * Methods: `add_file(path)`, `remove_file(path)`


### `filesystem/filesystem.py`

* `list_directories(base_dir)` → names of immediate subdirectories
* `list_files(base_dir)` → immediate files
* `list_dir_recursive(base_path)` → all files and directories under `base_path`

### `filesystem/tree_utils.py`

* `build_tree(paths: List[str]) → dict`
* `flatten_tree(tree: dict, prefix="") → List[str]`

### `filters/filtering.py` & `filters/gitignore.py`

* Load `.gitignore` specs via `pathspec`
* `filter_ignored(entries, use_gitignore, specs)`
* `matches_filters(path, state)` enforces dotfile and regex rules
* `filter_entries(entries, state)` combines filters

---

## Usage Examples

### 1. Server + Client

```bash
# shell A
python workspace-manager.py server

# shell B
python workspace-manager.py client
sleep 1              # wait for initial state
python - <<'EOF'     # send commands via client object
from core.core_service import WorkspaceClient
c = WorkspaceClient("/tmp/workspace_manager.sock")
c.add_file("/home/user/foo.txt")
c.remove_file("/home/user/foo.txt")
EOF
```

State updates print on client console.

### 2. File Selection + Editing

```python
from core.core import edit_files, filter_file_entries
from core.tracer import OutputTracer
from clipboard.clipboard import Clipboard
from filters.filtering import filter_entries
from search_config import SearchConfig
from filesystem.filesystem import list_dir_recursive

conf = SearchConfig()
all_entries = list_dir_recursive(".")
filtered = filter_entries([Path(e) for e in all_entries], conf)
clipboard = Clipboard()
# invoke interactive fzf loop (in separate script)
entries = [str(p) for p in filtered]
run_fzf_socket_loop(entries, prompt="Select files> ", multi_select=True)
# after selection, open in editor
edit_files(filter_file_entries(entries_selected))
```

### 3. Clipboard Commit

```python
from clipboard.clipboard import Clipboard
cb = Clipboard()
cb.add_files(["foo.py","bar.txt"])
cb.commit()  # copies contents to system clipboard
```

---

## Extensibility

* Plugins may hook into server (`WorkspaceServer.handle_message`)
* Customize `edit_files` to use alternative GUI or terminal
* Extend `SearchConfig` with new filtering criteria

---

## Possible features
Essential features for a functional and extensible workspace manager beyond what you've described:

**1. SSH Integration**

* Remote workspace management
* Persistent SSH session support (e.g. via `tmux`, `screen`, or mosh)
* Key forwarding, agent support, known\_hosts verification

**2. Workspace Persistence / Resume**

* Save and restore open windows, panes, and context
* Auto-reopen projects with editor state

**3. Search and Indexing**

* Fuzzy search (file, project, symbol)
* Grep or ripgrep integration
* Cross-workspace global search

**4. Custom Commands / Hooks**

* Pre/post-launch hooks per workspace
* Per-project `.workspace.rc` or equivalent
* User-defined menus or actions

**5. Tagging and Filtering**

* Tag-based organization
* Filters by language, project type, recent, active

**6. Workspace Sync / Portability**

* Config export/import
* Dotfile repo integration
* Encrypted workspace state (e.g. for syncing across machines)

**7. Task/Process Awareness**

* View background processes per workspace
* Kill, restart, or isolate processes
* Notifications on process completion/failure

**8. Git Integration**

* Status indicators
* Branch switching per workspace
* Auto-fetch, auto-pull on open (optional)

**9. System Resource Views**

* Per-workspace CPU/mem/disk usage
* I/O stats
* Top-style summary view

**10. Notifications / Alerts**

* Reminders, time limits, task alerts
* External alert hooks (email, D-Bus, etc.)

**11. Project Templates / Init**

* Scaffold new workspaces
* Customizable init templates (e.g. Python, Rust, Web)

**12. Multi-Display / TTY Awareness**

* Smart placement per monitor/TTY
* Restore last layout per terminal or X display

**13. Interop APIs**

* D-Bus, Unix socket, or HTTP API for integration
* Allow external tools to list/select/launch workspaces

**14. Integration with Editors/IDEs**

* Vim/Emacs/VSCode session restore
* Workspace-specific editor configuration (e.g. `.editorconfig` per workspace)

**15. Modal or Command Palette**

* Quick command runner (inspired by Sublime/VSCode)
* Indexed access to actions

Extend based on user type (developer, sysadmin, writer, etc).
