import socket
import threading
import json
import time
import datetime

HOST = '127.0.0.1'
PORT = 5025

rooms = {
    "ROOM_01": {
        "players": {},       
        "states": {},        
        "ready": {},         
        "settings": {"song": "", "speed": 4}
    },
    "ROOM_02": {
        "players": {},       
        "states": {},        
        "ready": {},         
        "settings": {"song": "", "speed": 4}
    },
    "ROOM_03": {
        "players": {},       
        "states": {},        
        "ready": {},         
        "settings": {"song": "", "speed": 4}
    }
}

lock = threading.Lock()

def write_log(message):
    """📝 FITUR WAJIB: Logging Aktivitas Player"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open("server_network.log", "a") as f:
        f.write(log_msg + "\n")

def broadcast_to_room(room_id, data_dict):
    encoded_data = json.dumps(data_dict).encode('utf-8')
    with lock:
        for p_id, p_socket in rooms[room_id]["players"].items():
            try:
                p_socket.sendall(encoded_data)
            except:
                pass

def handle_client(client_socket, p_id, room_id):
    write_log(f"Player {p_id} terhubung ke {room_id}.")
    
    init_packet = {"type": "INIT_PLAYER", "player_id": p_id}
    client_socket.sendall(json.dumps(init_packet).encode('utf-8'))

    while True:
        try:
            data = client_socket.recv(2048)
            if not data:
                break
            
            message = json.loads(data.decode('utf-8'))
            
            if message["type"] == "PING":
                ping_response = {"type": "PONG", "timestamp": message["timestamp"]}
                client_socket.sendall(json.dumps(ping_response).encode('utf-8'))
                continue

            if message["type"] == "ROOM_SETUP":
                target_rm = message["room"]
                rooms[target_rm]["settings"]["song"] = message["song"]
                rooms[target_rm]["settings"]["speed"] = message["speed"]
                write_log(f"{target_rm} diperbarui: {message['song']} | Speed: {message['speed']}")
                
                broadcast_to_room(target_rm, {
                    "type": "ROOM_SYNC",
                    "song": message["song"],
                    "speed": message["speed"]
                })

            elif message["type"] == "PLAYER_READY":
                target_rm = message["room"]
                rooms[target_rm]["ready"][p_id] = message["is_ready"]
                write_log(f"[{target_rm}] Player {p_id} status Ready = {message['is_ready']}")
                
                if len(rooms[target_rm]["players"]) == 2 and all(rooms[target_rm]["ready"].values()):
                    write_log(f"Matchmaking selesai. {target_rm} memulai permainan!")
                    broadcast_to_room(target_rm, {"type": "START_MATCH"})

            elif message["type"] == "GAME_UPDATE":
                added_score = message["added_score"]
                if added_score > 1000:
                    write_log(f"[⚠️ CHEAT DETECTED] {p_id} mengirim paket skor tidak valid ({added_score})! Paket dibuang.")
                    continue
                
                rooms[room_id]["states"][p_id]["score"] += added_score
                rooms[room_id]["states"][p_id]["state"] = message["state"]
                rooms[room_id]["states"][p_id]["feedback"] = message["feedback"]
                if "chat" in message:
                    rooms[room_id]["states"][p_id]["chat"] = message["chat"]
                
                broadcast_to_room(room_id, {
                    "type": "REALTIME_STATE",
                    "states": rooms[room_id]["states"]
                })

        except Exception as e:
            break

    with lock:
        if p_id in rooms[room_id]["players"]: del rooms[room_id]["players"][p_id]
        if p_id in rooms[room_id]["states"]: del rooms[room_id]["states"][p_id]
        if p_id in rooms[room_id]["ready"]: del rooms[room_id]["ready"][p_id]
            
    client_socket.close()
    write_log(f"Player {p_id} terputus dari jaringan {room_id}. Slot dibersihkan.")
    broadcast_to_room(room_id, {"type": "OPPONENT_DISCONNECTED"})

def main_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(4)
    write_log(f"Dedicated Server NetBeat aktif di {HOST}:{PORT}. Menunggu matchmaking...")

    player_count = 1
    while True:
        conn, addr = server.accept()
        room_id = "ROOM_01"  
        p_id = f"P{player_count}"
        
        with lock:
            rooms[room_id]["players"][p_id] = conn
            rooms[room_id]["states"][p_id] = {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
            rooms[room_id]["ready"][p_id] = False

        thread = threading.Thread(target=handle_client, args=(conn, p_id, room_id))
        thread.daemon = True
        thread.start()
        player_count += 1

if __name__ == "__main__":
    main_server()