#!/bin/bash
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  IP=$(ipconfig getifaddr en0 2>/dev/null)
  if [ -z "$IP" ]; then
    IP=$(ipconfig getifaddr en1 2>/dev/null)
  fi
  HOSTNAME=$(scutil --get LocalHostName 2>/dev/null)
  if [ -n "$HOSTNAME" ]; then
    LOCAL_DOMAIN="${HOSTNAME}.local"
  fi
else
  # Linux
  IP=$(hostname -I | awk '{print $1}')
  HOSTNAME=$(hostname)
  if [[ "$HOSTNAME" == *.local ]]; then
    LOCAL_DOMAIN="$HOSTNAME"
  else
    LOCAL_DOMAIN="${HOSTNAME}.local"
  fi
fi

echo "------------------------------------------------------"
echo "Frontend will be available at:"
echo "  http://localhost:3000"
if [ -n "$IP" ]; then
  echo "  http://$IP:3000"
fi
if [ -n "$LOCAL_DOMAIN" ]; then
  echo "  http://$LOCAL_DOMAIN:3000"
fi
echo
echo "API server will be available at:"
echo "  http://localhost:8000"
if [ -n "$IP" ]; then
  echo "  http://$IP:8000"
fi
if [ -n "$LOCAL_DOMAIN" ]; then
  echo "  http://$LOCAL_DOMAIN:8000"
fi
echo
echo "API interactive documentation will be available at:"
echo "  http://localhost:8000/docs"
if [ -n "$IP" ]; then
  echo "  http://$IP:8000/docs"
fi
if [ -n "$LOCAL_DOMAIN" ]; then
  echo "  http://$LOCAL_DOMAIN:8000/docs"
fi
echo "------------------------------------------------------"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
  echo "❌ Virtual environment not found. Please run ./scripts/install.sh first."
  exit 1
fi

source venv/bin/activate

# Check if ports 8000 or 3000 are in use
if lsof -i :8000 | grep LISTEN; then
  echo "⚠️  Port 8000 is already in use. The API server may not start correctly."
fi
if lsof -i :3000 | grep LISTEN; then
  echo "⚠️  Port 3000 is already in use. The frontend may not start correctly."
fi

# start backend in background
uvicorn src.api_server:app --reload --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Build frontend if not already built
if [ ! -d "examples/example-frontend/.next" ]; then
  echo "Building frontend..."
  npm --prefix examples/example-frontend run build
fi

# Start frontend in production mode
npm --prefix examples/example-frontend run start &
FRONT_PID=$!

# ensure child processes are killed on exit
cleanup() {
  echo "Stopping servers..."
  kill "$UVICORN_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
