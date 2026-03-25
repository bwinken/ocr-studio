#!/usr/bin/env bash
# ──────────────────────────────────────────────────
# Deploy image-doc-translator to $HOME/opt/
# Usage:
#   ./deploy/deploy.sh              # first-time install + start
#   ./deploy/deploy.sh sync         # rsync update + restart
#   ./deploy/deploy.sh stop         # stop service
#   ./deploy/deploy.sh status       # check service status
#   ./deploy/deploy.sh logs         # tail logs
#   ./deploy/deploy.sh uninstall    # stop + remove service
# ──────────────────────────────────────────────────
set -euo pipefail

APP_NAME="image-doc-translator"
DEPLOY_DIR="$HOME/opt/$APP_NAME"
SERVICE_NAME="$APP_NAME"
SERVICE_FILE="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
PORT="${IDT_PORT:-8080}"
WORKERS="${IDT_WORKERS:-1}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Commands ──

cmd_install() {
    info "Installing $APP_NAME to $DEPLOY_DIR ..."

    mkdir -p "$DEPLOY_DIR"
    cmd_sync_files

    info "Installing dependencies ..."
    cd "$DEPLOY_DIR"
    uv sync

    # Copy .env if not exists
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        if [ -f "$DEPLOY_DIR/.env.example" ]; then
            cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
            warn ".env created from .env.example — edit it with your VLM endpoints"
        fi
    fi

    cmd_install_service
    info "Done. Edit $DEPLOY_DIR/.env then run: $0 sync"
}

cmd_sync_files() {
    info "Syncing files to $DEPLOY_DIR ..."
    rsync -av --delete \
        --exclude '.venv/' \
        --exclude '.git/' \
        --exclude '.env' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude 'app/storage/' \
        --exclude '.claude/' \
        "$PROJECT_DIR/" "$DEPLOY_DIR/"

    # Ensure storage dir exists
    mkdir -p "$DEPLOY_DIR/app/storage"
}

cmd_sync() {
    cmd_sync_files

    info "Syncing dependencies ..."
    cd "$DEPLOY_DIR"
    uv sync

    cmd_restart
}

cmd_install_service() {
    info "Installing systemd user service ..."
    mkdir -p "$(dirname "$SERVICE_FILE")"

    cat > "$SERVICE_FILE" <<UNIT
[Unit]
Description=Image Doc Translator
After=network.target

[Service]
Type=simple
WorkingDirectory=$DEPLOY_DIR
ExecStart=$DEPLOY_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers $WORKERS
Restart=on-failure
RestartSec=5
EnvironmentFile=$DEPLOY_DIR/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
UNIT

    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_NAME"
    info "Service installed: $SERVICE_NAME"
}

cmd_start() {
    info "Starting $SERVICE_NAME ..."
    systemctl --user start "$SERVICE_NAME"
    sleep 1
    cmd_status
}

cmd_stop() {
    info "Stopping $SERVICE_NAME ..."
    systemctl --user stop "$SERVICE_NAME" || true
}

cmd_restart() {
    info "Restarting $SERVICE_NAME ..."
    systemctl --user restart "$SERVICE_NAME"
    sleep 1
    cmd_status
}

cmd_status() {
    systemctl --user status "$SERVICE_NAME" --no-pager || true
}

cmd_logs() {
    journalctl --user -u "$SERVICE_NAME" -f --no-pager
}

cmd_uninstall() {
    warn "Uninstalling $SERVICE_NAME service ..."
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$SERVICE_FILE"
    systemctl --user daemon-reload
    info "Service removed. Files still at $DEPLOY_DIR"
}

# ── Main ──

case "${1:-install}" in
    install)    cmd_install ;;
    sync)       cmd_sync ;;
    start)      cmd_start ;;
    stop)       cmd_stop ;;
    restart)    cmd_restart ;;
    status)     cmd_status ;;
    logs)       cmd_logs ;;
    uninstall)  cmd_uninstall ;;
    *)          echo "Usage: $0 {install|sync|start|stop|restart|status|logs|uninstall}" ;;
esac
