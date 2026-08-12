#!/bin/bash
# Cyberboss watchdog — checks if Claude Code is hung (D state) and restarts
# Deploy: crontab -e → */2 * * * * bash /home/ubuntu/cyberboss-watchdog.sh >> /tmp/watchdog.log 2>&1

LOCK_FILE="/tmp/cyberboss-watchdog.lock"
PID_FILE="/home/ubuntu/.cyberboss/logs/shared-wechat.pid"
RESTART_COOLDOWN=180  # 3 min between restarts to avoid storm
LAST_RESTART_FILE="/tmp/cyberboss-watchdog-last-restart"

# ---- lock ----
if [ -f "$LOCK_FILE" ]; then
  exit 0
fi
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# ---- check cooldown ----
if [ -f "$LAST_RESTART_FILE" ]; then
  LAST=$(cat "$LAST_RESTART_FILE" 2>/dev/null)
  NOW=$(date +%s)
  if [ -n "$LAST" ] && [ $((NOW - LAST)) -lt $RESTART_COOLDOWN ]; then
    exit 0
  fi
fi

NEED_RESTART=false

# ---- check 1: any claude process in D state? ----
D_COUNT=$(ps aux 2>/dev/null | grep -E '[c]laude ' | awk '$8 ~ /D/ {print $2}' | wc -l)
if [ "$D_COUNT" -gt 0 ]; then
  echo "$(date): WATCHDOG: found $D_COUNT claude process(es) in D state"
  NEED_RESTART=true
fi

# ---- check 2: cyberboss readyz health check (5s timeout) ----
READYZ=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8765/readyz 2>/dev/null)
if [ "$READYZ" != "200" ]; then
  echo "$(date): WATCHDOG: readyz returned ${READYZ:-timeout}, not 200"
  NEED_RESTART=true
fi

# ---- check 3: cyberboss PID file stale? ----
if [ -f "$PID_FILE" ]; then
  BRIDGE_PID=$(cat "$PID_FILE" 2>/dev/null)
  if [ -n "$BRIDGE_PID" ] && ! kill -0 "$BRIDGE_PID" 2>/dev/null; then
    echo "$(date): WATCHDOG: bridge PID $BRIDGE_PID is dead, pidfile stale"
    NEED_RESTART=true
  fi
else
  echo "$(date): WATCHDOG: no bridge pid file at $PID_FILE"
  NEED_RESTART=true
fi

# ---- restart if needed ----
if [ "$NEED_RESTART" = true ]; then
  echo "$(date): WATCHDOG: restarting cyberboss"

  # hard-kill any hung claude processes
  ps aux 2>/dev/null | grep -E '[c]laude ' | awk '{print $2}' | while read pid; do
    kill -9 "$pid" 2>/dev/null
  done

  # hard-kill any cyberboss processes
  ps aux 2>/dev/null | grep -E '[c]yberboss\.js start' | awk '{print $2}' | while read pid; do
    kill -9 "$pid" 2>/dev/null
  done

  sleep 2
  systemctl stop cyberboss 2>/dev/null
  sleep 1
  systemctl reset-failed cyberboss 2>/dev/null
  systemctl start cyberboss 2>/dev/null

  date +%s > "$LAST_RESTART_FILE"
  echo "$(date): WATCHDOG: restart complete"
else
  echo "$(date): WATCHDOG: all clear"
fi
