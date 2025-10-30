# Shell Completion for Make Targets

This project includes platform-agnostic shell completion for all Makefile targets, making it easy to discover and use available commands.

## Supported Platforms

- macOS (bash/zsh)
- Linux (bash/zsh)
- WSL (Windows Subsystem for Linux)
- VS Code Dev Containers (automatic setup)

## Installation

### One-Command Install

```bash
make install-completion
```

Then activate it:

```bash
# For bash
source ~/.bashrc
# or
source ~/.bash_profile

# For zsh
source ~/.zshrc
```

### Manual Installation

If you prefer to set it up manually:

1. Add this line to your `~/.bashrc`, `~/.bash_profile`, or `~/.zshrc`:

```bash
[ -f "/path/to/need_a_job/.make-completion.sh" ] && source "/path/to/need_a_job/.make-completion.sh"
```

2. Reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc
```

## Usage

Once installed, you can use TAB completion with make:

```bash
make <TAB><TAB>
```

This will show all available targets:

```
start           stop            restart         status
logs            setup           dev-api         dev-frontend
build           clean           health          ...
```

You can also use partial completion:

```bash
make dev-<TAB>
```

Shows:
```
dev-api         dev-frontend    dev-setup       dev-test
dev-worker      dev-test-cov    dev-lint        dev-format
```

## Uninstallation

To remove the completion:

```bash
make uninstall-completion
```

Then reload your shell.

## How It Works

The completion script:
1. Parses the Makefile when you press TAB
2. Extracts all target names
3. Filters out internal targets (those starting with `_`)
4. Provides intelligent completion based on what you've typed

## Troubleshooting

### Completion not working

1. Make sure you've reloaded your shell after installation
2. Verify the completion script is sourced:
   ```bash
   grep ".make-completion.sh" ~/.bashrc  # or ~/.zshrc
   ```

3. Test the completion script directly:
   ```bash
   source .make-completion.sh
   ```

### WSL-specific issues

On WSL, make sure you're using the Linux paths, not Windows paths. The Makefile and completion script must be in the WSL filesystem (e.g., `/home/user/...` not `/mnt/c/...`).

### Permission issues

If you get permission errors:

```bash
chmod +x .make-completion.sh
```

## For Team Members

When new team members clone the repository:

1. They'll get the `.make-completion.sh` file automatically
2. They just need to run `make install-completion`
3. Then reload their shell

This ensures everyone has the same developer experience across all platforms!

## Dev Container Support

If you're using VS Code Dev Containers, the completion is automatically installed when the container is created!

The `.devcontainer/loader_script.sh` automatically:
- Copies the completion script to the container
- Sources it in the bash configuration
- Makes it available immediately

No manual setup required when using dev containers!
