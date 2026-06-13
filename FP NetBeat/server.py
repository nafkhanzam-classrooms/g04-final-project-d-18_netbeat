import socket
import threading
import json
import time

# --- CONFIG BINDING SERVER ---
# Menggunakan '0.0.0.0' agar port terbuka untuk Localhost maupun SSH Tunneling
SERVER_IP = "0.0.0.0"  
SERVER_PORT = 5025

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Dedicated Server NetBeat (State-Driven) aktif di port {SERVER_PORT}...")

# Struktur Data Kamar Terpusat (Global Room Memory)
rooms_data = {
    "ROOM_01": {
        "config": {"song": "bidadari.mp3", "speed": 4.5},
        "players_ready": {"P1": False, "P2": False},
        "states": {
            "P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""},
            "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
        },
        "connections": {"P1": None, "P2": None}
    },
    "ROOM_02": {
        "config": {"song": "bidadari.mp3", "speed": 4.5},
        "players_ready": {"P1": False, "P2": False},
        "states": {
            "P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""},
            "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
        },
        "connections": {"P1": None, "P2": None}
    },
    "ROOM_03": {
        "config": {"song": "bidadari.mp3", "speed": 4.5},
        "players_ready": {"P1": False, "P2": False},
        "states": {
            "P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""},
            "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
        },
        "connections": {"P1": None, "P2": None}
    }
}

def broadcast_to_room(room_id, reply_message):
    """Memancarkan paket data ke semua player yang ada di dalam satu kamar"""
    payload = json.dumps(reply_message).encode('utf-8')
    for p_id, conn in rooms_data[room_id]["connections"].items():
        if conn:
            try:
                conn.sendall(payload)
            except:
                pass

def handle_client(conn, player_id, assigned_room):
    """Thread Mandiri untuk melayani siklus hidup satu Client game"""
    current_room = assigned_room
    print(f"[CONNECTED] Player {player_id} terhubung ke kamar {current_room}")
    
    # Berikan ID Jaringan Awal ke Client saat tersambung
    try:
        conn.sendall(json.dumps({"type": "INIT_PLAYER", "player_id": player_id}).encode('utf-8'))
    except:
        return

    while True:
        try:
            data = conn.recv(2048)
            if not data:
                break
                
            message = json.loads(data.decode('utf-8'))
            room = rooms_data[current_room]
            
            # 1. Logika Sinkronisasi Menu Lagu (Hanya P1/Host yang bisa mengubah)
            if message["type"] == "ROOM_SETUP" and player_id == "P1":
                room["config"]["song"] = message["song"]
                room["config"]["speed"] = message["speed"]
                reply = {"type": "ROOM_SYNC", "song": message["song"], "speed": message["speed"]}
                broadcast_to_room(current_room, reply)
                
            # 2. Logika Kesiapan Matchmaking (Ready Check)
            elif message["type"] == "PLAYER_READY":
                room["players_ready"][player_id] = message["is_ready"]
                # Jika kedua pemain sudah menekan tombol READY, trigger mulai pertandingan
                if room["players_ready"]["P1"] and room["players_ready"]["P2"]:
                    broadcast_to_room(current_room, {"type": "START_MATCH"})
            
            # 3. Logika Pertukaran Status Real-Time Game (Core Game Loop Sinkronisasi)
            elif message["type"] == "GAME_UPDATE":
                room["states"][player_id]["score"] = message["added_score"]
                room["states"][player_id]["state"] = message["state"]
                room["states"][player_id]["feedback"] = message["feedback"]
                room["states"][player_id]["chat"] = message["chat"]
                
                # Balas langsung dengan menyiarkan potret panggung dansa global terkini
                reply = {"type": "REALTIME_STATE", "states": room["states"]}
                broadcast_to_room(current_room, reply)
                
            # 4. Logika Mekanisme Detak Jantung Jaringan (PING-PONG)
            elif message["type"] == "PING":
                conn.sendall(json.dumps({"type": "PONG", "timestamp": message["timestamp"]}).encode('utf-8'))
                
        except:
            break

    # PENANGANAN EROR / CLIENT LOGOUT (Fault Tolerance)
    print(f"[DISCONNECTED] Player {player_id} keluar dari kamar {current_room}")
    rooms_data[current_room]["connections"][player_id] = None
    rooms_data[current_room]["players_ready"][player_id] = False
    rooms_data[current_room]["states"][player_id] = {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
    broadcast_to_room(current_room, {"type": "OPPONENT_DISCONNECTED"})
    conn.close()

# Loop Utama Matchmaking Alokasi Slot Kamar Otomatis
while True:
    conn, addr = server_socket.accept()
    allocated = False
    for r_name, r_content in rooms_data.items():
        if r_content["connections"]["P1"] is None:
            r_content["connections"]["P1"] = conn
            threading.Thread(target=handle_client, args=(conn, "P1", r_name), daemon=True).start()
            allocated = True
            break
        elif r_content["connections"]["P2"] is None:
            r_content["connections"]["P2"] = conn
            threading.Thread(target=handle_client, args=(conn, "P2", r_name), daemon=True).start()
            allocated = True
            break
            
    if not allocated:
        conn.sendall(json.dumps({"type": "SERVER_FULL"}).encode('utf-8'))
        conn.close()
