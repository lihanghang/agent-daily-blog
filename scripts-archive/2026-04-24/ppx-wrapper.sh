#!/bin/bash
# memect-ppx wrapper script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$WORKSPACE_DIR/venv-ppx"

# 激活虚拟环境并运行 ppx
source "$VENV_DIR/bin/activate" && ppx "$@"
