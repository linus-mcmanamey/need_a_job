#!/usr/bin/env bash
# =============================================================================
# Make Completion Script - Platform Agnostic
# Works on macOS, Linux, and WSL
# =============================================================================

_make_targets() {
    local cur prev targets
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Extract targets from Makefile
    if [ -f Makefile ]; then
        targets=$(make -qp 2>/dev/null | \
                  awk -F':' '/^[a-zA-Z0-9][^$#\/\t=]*:([^=]|$)/ {split($1,A,/ /);for(i in A)print A[i]}' | \
                  grep -v -e '^_' -e '\.PHONY' | \
                  sort -u)
    fi

    COMPREPLY=( $(compgen -W "$targets" -- "$cur") )
    return 0
}

# Register completion for make
complete -F _make_targets make
