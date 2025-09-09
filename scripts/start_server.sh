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

uvicorn src.api_server:app --reload --host 0.0.0.0 --port 8000