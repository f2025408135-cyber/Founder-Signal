#!/bin/bash
# Start both servers, wait for readiness, take screenshots, then analyze
set -e

echo "=== Killing existing processes ==="
pkill -f "next dev" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 2

echo "=== Starting backend ==="
cd /home/z/my-project/vc-brain/backend
export DATABASE_URL="postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
export DATABASE_SYNC_URL="postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"
export OPENAI_API_KEY="test-key"
export GITHUB_TOKEN=""
export PRODUCTHUNT_TOKEN=""
export LANGFUSE_ENABLED="false"
export APP_ENV="development"
/home/z/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

echo "=== Starting frontend ==="
cd /home/z/my-project/vc-brain/frontend-next
node node_modules/.bin/next dev -p 3000 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo "=== Waiting for both servers ==="
for i in $(seq 1 30); do
  sleep 2
  bstatus=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/ping 2>/dev/null || echo "000")
  fstatus=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/inbox 2>/dev/null || echo "000")
  echo "  Attempt $i: Backend=$bstatus Frontend=$fstatus"
  if [ "$bstatus" = "200" ] && [ "$fstatus" = "200" ]; then
    echo "=== Both servers ready! ==="
    break
  fi
done

if [ "$bstatus" != "200" ] || [ "$fstatus" != "200" ]; then
  echo "ERROR: Servers not ready. Backend=$bstatus Frontend=$fstatus"
  exit 1
fi

echo "=== Taking screenshots ==="
mkdir -p /home/z/my-project/vc-brain/screenshots
agent-browser set viewport 1440 900

echo "--- Inbox ---"
agent-browser open http://localhost:3000/inbox
sleep 5
agent-browser eval "getComputedStyle(document.body).backgroundColor"
agent-browser screenshot /home/z/my-project/vc-brain/screenshots/inbox-final.png --full

echo "--- Thesis ---"
agent-browser open http://localhost:3000/thesis
sleep 3
agent-browser screenshot /home/z/my-project/vc-brain/screenshots/thesis-final.png --full

echo "--- Funnel ---"
agent-browser open http://localhost:3000/funnel
sleep 3
agent-browser screenshot /home/z/my-project/vc-brain/screenshots/funnel-final.png --full

echo "--- Network ---"
agent-browser open http://localhost:3000/network
sleep 3
agent-browser screenshot /home/z/my-project/vc-brain/screenshots/network-final.png --full

echo "=== Screenshot sizes ==="
ls -la /home/z/my-project/vc-brain/screenshots/*final*

echo "=== Done ==="
