# load_balancer.py
from flask import Flask, request, Response
import requests
import itertools

app = Flask(__name__)

# Daftar server backend
servers = ["http://localhost:8001", "http://localhost:8002", "http://localhost:8003"]
rr = itertools.cycle(servers)
room_map = {}  # room_id -> server_url

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    query = request.query_string.decode()
    room_id = request.args.get('room_id')

    # Logging request yang masuk
    print(f"\n[LB] Incoming request: /{path}?{query}")

    # Tentukan server tujuan
    if path == 'create_room' and room_id:
        server = next(rr)
        room_map[room_id] = server
        print(f"[LB] Assigned room '{room_id}' to {server}")
    elif room_id and room_id in room_map:
        server = room_map[room_id]
        print(f"[LB] Forwarding room '{room_id}' to {server}")
    else:
        print(f"[LB] Rejected request: unknown room_id '{room_id}'")
        return "room_id tidak valid atau belum dibuat", 400

    try:
        target_url = f"{server}/{path}?{query}"
        resp = requests.get(target_url)
        print(f"[LB] Forwarded to {target_url} -> status {resp.status_code}")
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get("Content-Type"))
    except Exception as e:
        print(f"[LB] Error forwarding to {server}: {e}")
        return f"Failed to forward request: {str(e)}", 502


if __name__ == '__main__':
    app.run(port=8080)