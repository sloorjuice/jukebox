# ...existing code...
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  IP=$(ipconfig getifaddr en0 2>/dev/null)
  if [ -z "$IP" ]; then
    IP=$(ipconfig getifaddr en1 2>/dev/null)
  fi
else
  # Linux
  IP=$(hostname -I | awk '{print $1}')
fi

echo "------------------------------------------------------"
echo "Frontend will be available at:"
echo "  http://localhost:3000"
if [ -n "$IP" ]; then
  echo "  http://$IP:3000"
fi
echo
echo "API server will be available at:"
echo "  http://localhost:8000"
if [ -n "$IP" ]; then
  echo "  http://$IP:8000"
fi
echo
echo "API interactive documentation will be available at:"
echo "  http://localhost:8000/docs"
if [ -n "$IP" ]; then
  echo "  http://$IP:8000/docs"
fi
echo "------------------------------------------------------"

# start backend in background
uvicorn src.api_server:app --reload --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# start frontend (run from examples/example-frontend) in background
npm --prefix examples/example-frontend run dev &
FRONT_PID=$!

# ensure child processes are killed on exit
cleanup() {
  echo "Stopping servers..."
  kill "$UVICORN_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
# ...existing code...