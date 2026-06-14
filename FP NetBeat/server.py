import socket
import threading
import json
import time

SERVER_IP = "0.0.0.0"  
SERVER_PORT = 5025

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Dedicated Server NetBeat (Dynamic Room Matchmaking) aktif...")

rooms_data = {
    "ROOM_01": {
        "config": {"song": "bidadari.mp3", "speed": 4.5},
        "players_ready": {"P1": False, "P2": False},
        "states": {"P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}, "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}},
        "connections": {"P1": None, "P2": None}
    },
    "ROOM_02": {
        "config": {"song": "bidadari.mp3", "speed": 4.5},
        "players_ready": {"P1": False, "P2": False},
        "states": {"P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}, "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}},
        "connections": {"P1": None, "P2": None}
    },
    "ROOM_03": {
        "config": {"song": "bidadari.mp3", "speed": 4.5},
        "players_ready": {"P1": False, "P2": False},
        "states": {"P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}, "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}},
        "connections": {"P1": None, "P2": None}
    }
}

def broadcast_to_room(room_id, reply_message):
    """Memancarkan paket data eksklusif hanya kepada player di dalam kamar yang sama"""
    raw_string = json.dumps(reply_message)
    payload_bytes = raw_string.encode('utf-8')
    size_in_bytes = len(payload_bytes)
    
    if reply_message.get("type") == "REALTIME_STATE":
        try:
            with open("server_network.log", "a") as log_file:
                log_time = time.strftime('%Y-%m-%d %H:%M:%S')
                log_file.write(f"[{log_time}] BROADCAST OUTBOUND -> ROOM: {room_id} | TYPE: REALTIME_STATE | SIZE: {size_in_bytes} Bytes\n")
        except:
            pass

    for p_id, conn in rooms_data[room_id]["connections"].items():
        if conn:
            try:
                conn.sendall(payload_bytes)
            except:
                pass

def handle_client(conn, initial_player_id, initial_room):
    """Thread Mandiri untuk melayani siklus hidup satu Client game secara dinamis"""
    player_id = initial_player_id
    current_room = initial_room
    
    timestamp_connect = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp_connect}] [CONNECTED] Client terhubung. Alokasi Awal: {player_id} di {current_room}")
    
    try:
        conn.sendall(json.dumps({"type": "INIT_PLAYER", "player_id": player_id}).encode('utf-8'))
    except:
        return

    while True:
        try:
            data = conn.recv(2048)
            if not data:
                break
                
            size_in_bytes = len(data)
            message = json.loads(data.decode('utf-8'))
            
            if message["type"] == "ROOM_SETUP":
                target_room = message["room"]
                if target_room != current_room:

                    rooms_data[current_room]["connections"][player_id] = None
                    rooms_data[current_room]["players_ready"][player_id] = False
                    rooms_data[current_room]["states"][player_id] = {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
                    broadcast_to_room(current_room, {"type": "OPPONENT_DISCONNECTED"})
                    current_room = target_room
                    if rooms_data[current_room]["connections"]["P1"] is None:
                        player_id = "P1"
                    else:
                        player_id = "P2"
                        
                    rooms_data[current_room]["connections"][player_id] = conn
                    conn.sendall(json.dumps({"type": "INIT_PLAYER", "player_id": player_id}).encode('utf-8'))
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [ROOM_TRANSFER] Player bermigrasi menjadi {player_id} di {current_room}")

                
                if player_id == "P1":
                    rooms_data[current_room]["config"]["song"] = message["song"]
                    rooms_data[current_room]["config"]["speed"] = message["speed"]
                    reply = {"type": "ROOM_SYNC", "song": message["song"], "speed": message["speed"]}
                    broadcast_to_room(current_room, reply)
            
           
            elif message["type"] == "PLAYER_READY":
                rooms_data[current_room]["players_ready"][player_id] = message["is_ready"]
                room = rooms_data[current_room]
                if room["connections"]["P1"] and room["connections"]["P2"]:
                    if room["players_ready"]["P1"] and room["players_ready"]["P2"]:
                        broadcast_to_room(current_room, {"type": "START_MATCH"})
            elif message["type"] == "GAME_UPDATE":
                rooms_data[current_room]["states"][player_id]["score"] = message["added_score"]
                rooms_data[current_room]["states"][player_id]["state"] = message["state"]
                rooms_data[current_room]["states"][player_id]["feedback"] = message["feedback"]
                rooms_data[current_room]["states"][player_id]["chat"] = message["chat"]
                
                reply = {"type": "REALTIME_STATE", "states": rooms_data[current_room]["states"]}
                broadcast_to_room(current_room, reply)
                
                try:
                    with open("server_network.log", "a") as log_file:
                        log_time = time.strftime('%Y-%m-%d %H:%M:%S')
                        log_file.write(f"[{log_time}] PACKET INBOUND <- ROOM: {current_room} | PLAYER: {player_id} | TYPE: GAME_UPDATE | SIZE: {size_in_bytes} Bytes\n")
                except:
                    pass
            elif message["type"] == "PING":
                current_time = time.time()
                rtt_estimation = (current_time - message["timestamp"]) * 1000
                conn.sendall(json.dumps({"type": "PONG", "timestamp": message["timestamp"]}).encode('utf-8'))
                
                try:
                    with open("server_network.log", "a") as log_file:
                        log_time = time.strftime('%Y-%m-%d %H:%M:%S')
                        log_file.write(f"[{log_time}] ROOM: {current_room} | PLAYER: {player_id} | STATUS: PING-PONG SUCCESS | EST_LATENCY: {int(rtt_estimation)} ms\n")
                except:
                    pass
                
        except:
            break
    timestamp_disconnect = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp_disconnect}] [DISCONNECTED] Player {player_id} keluar dari kamar {current_room}")
    
    try:
        with open("server_network.log", "a") as log_file:
            log_file.write(f"[{timestamp_disconnect}] ROOM: {current_room} | PLAYER: {player_id} | STATUS: CONNECTION CLOSED FORCIBLY\n")
    except:
        pass

    rooms_data[current_room]["connections"][player_id] = None
    rooms_data[current_room]["players_ready"][player_id] = False
    rooms_data[current_room]["states"][player_id] = {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
    broadcast_to_room(current_room, {"type": "OPPONENT_DISCONNECTED"})
    conn.close()
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
