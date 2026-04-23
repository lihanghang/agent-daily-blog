#!/usr/bin/env bash
# memect-ppx 跨平台安装脚本
# 支持: Linux, macOS, Windows (Git Bash / WSL)
# 用法: ./scripts/install-memect-ppx.sh

set -e

echo "==================================="
echo "  memect-ppx 跨平台安装脚本"
echo "==================================="
echo ""

# 颜色定义（Windows Git Bash 可能不支持）
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
fi

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="Linux";;
        Darwin*)    OS="macOS";;
        CYGWIN*)    OS="Windows (Cygwin)";;
        MINGW*)     OS="Windows (MinGW)";;
        MSYS*)      OS="Windows (MSYS)";;
        *)          OS="Unknown";;
    esac
    echo -e "${YELLOW}检测到操作系统: $OS${NC}"
}

detect_os

# 获取脚本所在目录
get_script_dir() {
    local source="${BASH_SOURCE[0]}"
    while [ -h "$source" ]; do
        local dir="$(cd -P "$(dirname "$source")" && pwd)"
        source="$(readlink "$source")"
        [[ $source != /* ]] && source="$dir/$source"
    done
    local dir="$(cd -P "$(dirname "$source")" && pwd)"
    echo "$dir"
}

SCRIPT_DIR=$(get_script_dir)
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$WORKSPACE_DIR/venv-ppx"

echo -e "${YELLOW}脚本目录: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}工作目录: $WORKSPACE_DIR${NC}"
echo -e "${YELLOW}虚拟环境: $VENV_DIR${NC}"
echo ""

# 检查 Python
check_python() {
    echo "检查 Python 版本..."
    
    # 优先使用 python3
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}错误: 未找到 Python${NC}"
        echo "请先安装 Python 3.12 或更高版本"
        echo "下载地址: https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    echo -e "${GREEN}Python 版本: $PYTHON_VERSION${NC}"
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
        echo -e "${RED}错误: 需要 Python 3.12 或更高版本${NC}"
        echo "当前版本: $PYTHON_VERSION"
        echo "请升级 Python: https://www.python.org/downloads/"
        exit 1
    fi
}

check_python

# 检查是否已安装
check_installed() {
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/ppx" ] || [ -f "$VENV_DIR/Scripts/ppx.exe" ]; then
        echo -e "${YELLOW}检测到 memect-ppx 已安装${NC}"
        read -p "是否重新安装？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "取消安装"
            exit 0
        fi
        echo "删除旧安装..."
        rm -rf "$VENV_DIR"
    fi
}

check_installed

# 创建虚拟环境
create_venv() {
    echo ""
    echo "创建 Python 虚拟环境..."
    
    # 使用 python3 -m venv 创建虚拟环境
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    # 确定激活脚本路径
    if [[ "$OS" == "Windows"* ]]; then
        ACTIVATE="$VENV_DIR/Scripts/activate"
    else
        ACTIVATE="$VENV_DIR/bin/activate"
    fi
    
    # 激活虚拟环境
    source "$ACTIVATE"
    
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
}

create_venv

# 升级 pip
upgrade_pip() {
    echo "升级 pip..."
    pip install --upgrade pip -q
    echo -e "${GREEN}✓ pip 升级完成${NC}"
}

upgrade_pip

# 安装 memect-ppx
install_memect_ppx() {
    echo ""
    echo "安装 memect-ppx（可能需要几分钟）..."
    pip install --no-deps memect-ppx -q
    echo -e "${GREEN}✓ memect-ppx 安装完成${NC}"
}

install_memect_ppx

# 安装依赖
install_dependencies() {
    echo ""
    echo "安装依赖包..."
    
    # 基础依赖
    pip install 'numpy<2.0.0' -q
    pip install rapid-layout rapid-latex-ocr -q
    pip install onnxruntime -q
    pip install pillow pdf-oxide orjson pydantic fastapi openai httpx -q
    
    # 额外依赖
    pip install beautifulsoup4 concurrent-log-handler filetype fonttools -q
    pip install freetype-py pptx-ea-font psutil pymupdf pypdf -q
    pip install python-multipart python-pptx rapidocr shapely table-cls -q
    pip install 'uvicorn[standard]' -q
    pip install opencv-python-headless -q
    pip install httpx[socks] -q
    
    echo -e "${GREEN}✓ 依赖包安装完成${NC}"
}

install_dependencies

# 创建配置文件
create_config() {
    echo ""
    echo "创建配置文件..."
    
    cat > "$WORKSPACE_DIR/xdebug.py" << 'EOF'
# memect-ppx debug configuration

setting = {
    "ocr": "auto",
    "table": "auto",
    "backend": "default",
    "mode": "page"
}
EOF
    
    echo -e "${GREEN}✓ 配置文件创建完成${NC}"
}

create_config

# 创建 wrapper 脚本
create_wrapper() {
    echo "创建便捷启动脚本..."
    
    # 根据操作系统创建不同的 wrapper 脚本
    if [[ "$OS" == "Windows"* ]]; then
        # Windows batch 文件
        cat > "$SCRIPT_DIR/ppx-wrapper.bat" << EOF
@echo off
REM memect-ppx wrapper script for Windows

setlocal
set SCRIPT_DIR=%~dp0
set WORKSPACE_DIR=%SCRIPT_DIR:~0,-1%
set VENV_DIR=%WORKSPACE_DIR%\venv-ppx

REM 激活虚拟环境并运行 ppx
call "%VENV_DIR%\Scripts\activate.bat" && ppx %*
endlocal
EOF
        echo -e "${GREEN}✓ Windows 脚本创建完成: ppx-wrapper.bat${NC}"
    fi
    
    # Unix-like 系统的 shell 脚本
    cat > "$SCRIPT_DIR/ppx-wrapper.sh" << 'EOF'
#!/usr/bin/env bash
# memect-ppx wrapper script for Unix-like systems

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$WORKSPACE_DIR/venv-ppx"

# 激活虚拟环境并运行 ppx
source "$VENV_DIR/bin/activate" && ppx "$@"
EOF
    
    chmod +x "$SCRIPT_DIR/ppx-wrapper.sh"
    echo -e "${GREEN}✓ Unix 脚本创建完成: ppx-wrapper.sh${NC}"
}

create_wrapper

# 验证安装
verify_installation() {
    echo ""
    echo "验证安装..."
    
    # 确定激活脚本路径
    if [[ "$OS" == "Windows"* ]]; then
        ACTIVATE="$VENV_DIR/Scripts/activate"
        PPX_CMD="$VENV_DIR/Scripts/ppx.exe"
    else
        ACTIVATE="$VENV_DIR/bin/activate"
        PPX_CMD="$VENV_DIR/bin/ppx"
    fi
    
    # 激活并测试
    if source "$ACTIVATE" && "$PPX_CMD" --help &> /dev/null; then
        echo -e "${GREEN}✓ memect-ppx 安装成功！${NC}"
    else
        echo -e "${RED}✗ memect-ppx 安装失败${NC}"
        exit 1
    fi
}

verify_installation

# 显示使用说明
show_usage() {
    echo ""
    echo "==================================="
    echo -e "${GREEN}安装完成！${NC}"
    echo "==================================="
    echo ""
    echo "操作系统: $OS"
    echo "Python 版本: $PYTHON_VERSION"
    echo "安装位置: $VENV_DIR"
    echo ""
    
    if [[ "$OS" == "Windows"* ]]; then
        echo "使用方法（Windows）："
        echo ""
        echo "  # 解析 PDF"
        echo "  ppx-wrapper.bat parse document.pdf -o output"
        echo ""
        echo "  # 解析图片"
        echo "  ppx-wrapper.bat parse image.png -o output"
        echo ""
        echo "  # 强制使用 CPU（推荐）"
        echo "  ppx-wrapper.bat parse file.pdf -o output --cpu"
        echo ""
    else
        echo "使用方法（Linux/macOS）："
        echo ""
        echo "  # 解析 PDF"
        echo "  ./scripts/ppx-wrapper.sh parse document.pdf -o output"
        echo ""
        echo "  # 解析图片"
        echo "  ./scripts/ppx-wrapper.sh parse image.png -o output"
        echo ""
        echo "  # 强制使用 CPU（推荐）"
        echo "  ./scripts/ppx-wrapper.sh parse file.pdf -o output --cpu"
        echo ""
    fi
    
    echo "查看帮助："
    echo "  ./scripts/ppx-wrapper.sh parse --help"
    echo ""
    echo "示例："
    echo "  ./scripts/ppx-wrapper.sh parse document.pdf -o /tmp/output/ --cpu"
    echo ""
    echo "更多信息请访问：https://github.com/memect/memect-ppx"
    echo ""
}

show_usage
