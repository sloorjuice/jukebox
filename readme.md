ipconfig getifaddr en0
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000