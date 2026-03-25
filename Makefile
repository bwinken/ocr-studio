.PHONY: dev lock install sync start stop restart status logs uninstall

# ── Local Development ──
dev:
	uv run uvicorn app.main:app --reload --port 8080

lock:
	uv lock

# ── Deployment (delegates to deploy/deploy.sh) ──
install:
	bash deploy/deploy.sh install

sync:
	bash deploy/deploy.sh sync

start:
	bash deploy/deploy.sh start

stop:
	bash deploy/deploy.sh stop

restart:
	bash deploy/deploy.sh restart

status:
	bash deploy/deploy.sh status

logs:
	bash deploy/deploy.sh logs

uninstall:
	bash deploy/deploy.sh uninstall
