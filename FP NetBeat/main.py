import pygame
import sys
import os
import socket
import threading
import json
import time
import scenes
from gameplay import GameplayManager

os.environ['SDL_VIDEO_ALLOW_BACKGROUNDING'] = '1'

SERVER_IP = '127.0.0.1'  
SERVER_PORT = 5025
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_network_id = "P1"
is_connected = False
current_latency = "0 ms"
net_game_start_trigger = False
opponent_disconnected_alert = False

rooms_list = ["ROOM_01", "ROOM_02", "ROOM_03"]
selected_room_idx = 0
network_states = {
    "P1": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""},
    "P2": {"score": 0, "state": "IDLE", "feedback": "", "chat": ""}
}

def network_receiver():
    """🔄 BACKGROUND THREAD RECEIVER: Mengambil data konstan dari server tanpa nge-lag"""
    global my_network_id, current_latency, net_game_start_trigger
    global songs_list, selected_song_idx, selected_diff_idx, network_states, opponent_disconnected_alert
    
    while True:
        try:
            data = client_socket.recv(2048)
            if not data:
                break
            message = json.loads(data.decode('utf-8'))
            
            if message["type"] == "INIT_PLAYER":
                my_network_id = message["player_id"]
                
            elif message["type"] == "PONG":
                diff = (time.time() - message["timestamp"]) * 1000
                current_latency = f"{int(diff)} ms"
                
            elif message["type"] == "ROOM_SYNC":
                if my_network_id == "P2":
                    if message["song"] in songs_list:
                        selected_song_idx = songs_list.index(message["song"])
                    if message["speed"] == 2.5: selected_diff_idx = 0
                    elif message["speed"] == 4.5: selected_diff_idx = 1
                    elif message["speed"] == 7.5: selected_diff_idx = 2

            elif message["type"] == "REALTIME_STATE":
                network_states = message["states"]
                
            elif message["type"] == "START_MATCH":
                net_game_start_trigger = True
                opponent_disconnected_alert = False
                
            elif message["type"] == "OPPONENT_DISCONNECTED":
                opponent_disconnected_alert = True
                net_game_start_trigger = False
        except:
            break
try:
    client_socket.connect((SERVER_IP, SERVER_PORT))
    is_connected = True
    threading.Thread(target=network_receiver, daemon=True).start()
except Exception as e:
    print(f"[⚠️ NETWORK ERROR] Gagal tersambung ke server. Mode offline aktif. {e}")

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("NetBeat - Online Multiplayer Edition")

f_title = pygame.font.SysFont("Courier", 60, bold=True)
f_large = pygame.font.SysFont("Courier", 45, bold=True)
f_medium = pygame.font.SysFont("Courier", 30, bold=True)
f_small = pygame.font.SysFont("Courier", 20, bold=True)
scenes.init_scene_fonts(f_title, f_large, f_medium, f_small)

def load_img(filename, size):
    path = os.path.join("Image", filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, size)

arrow_images = {
    "LEFT": load_img("arrow-left.png", (60, 60)), "RIGHT": load_img("arrow-right.png", (60, 60)),
    "UP": load_img("arrow-up.png", (60, 60)), "DOWN": load_img("arrow-down.png", (60, 60))
}
character_images = {
    "IDLE": load_img("man.png", (160, 260)), "DANCING": load_img("man dancing.png", (160, 260)), "MISS": load_img("man miss.png", (160, 260))
}

bg_utama = load_img("bgutama.png", (1280, 720))
room_backgrounds = {
    "ROOM_01": load_img("bg1.png", (1280, 720)),
    "ROOM_02": load_img("bg2.png", (1280, 720)),
    "ROOM_03": load_img("bg3.png", (1280, 720))
}

GREEN = (50, 205, 50)
songs_list = ["bidadari.mp3", "dropdead.mp3", "selfcontrol.mp3"]
selected_song_idx = 0

diff_list = ["EASY (Slow)", "MEDIUM (Normal)", "HARD (Fast!)"]
diff_speeds = [2.5, 4.5, 7.5]  
selected_diff_idx = 1          

current_scene = "MAIN_MENU"
player_name = "Aldi"
input_active = False
gameplay_manager = None
is_ready_lobby = False
ping_heartbeat_timer = 0

def play_menu_music():
    try:
        pygame.mixer.music.load(os.path.join("Song", "jingle_45.ogg"))
        pygame.mixer.music.set_volume(0.4) 
        pygame.mixer.music.play(-1)        
    except:
        pass

play_menu_music()
clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()
    if is_connected:
        ping_heartbeat_timer += 1
        if ping_heartbeat_timer >= 120:  
            ping_heartbeat_timer = 0
            try:
                client_socket.sendall(json.dumps({"type": "PING", "timestamp": time.time()}).encode('utf-8'))
            except:
                is_connected = False

    active_bg = room_backgrounds[rooms_list[selected_room_idx]]
    if current_scene == "MAIN_MENU":
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 490 <= mouse_pos[0] <= 790 and 300 <= mouse_pos[1] <= 340: input_active = True
                else: input_active = False
                if 490 <= mouse_pos[0] <= 790 and 400 <= mouse_pos[1] <= 450: current_scene = "CREATE_ROOM"
                if 490 <= mouse_pos[0] <= 790 and 480 <= mouse_pos[1] <= 530: running = False
            elif event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_BACKSPACE: player_name = player_name[:-1]
                elif event.key == pygame.K_RETURN: input_active = False
                else:
                    if len(player_name) < 12 and event.unicode.isalnum(): player_name += event.unicode
        scenes.draw_main_menu(screen, mouse_pos, player_name, input_active, bg_utama)

    elif current_scene == "CREATE_ROOM":
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(len(rooms_list)):
                    if 60 <= mouse_pos[0] <= 360 and (160 + i*55) <= mouse_pos[1] <= (205 + i*55):
                        selected_room_idx = i
                
                if my_network_id == "P1":
                    for i in range(len(songs_list)):
                        if 430 <= mouse_pos[0] <= 780 and (160 + i*55) <= mouse_pos[1] <= (205 + i*55):
                            selected_song_idx = i
                    for i in range(len(diff_list)):
                        if 850 <= mouse_pos[0] <= 1180 and (160 + i*55) <= mouse_pos[1] <= (205 + i*55):
                            selected_diff_idx = i
                    
                    if is_connected:
                        try:
                            client_socket.sendall(json.dumps({
                                "type": "ROOM_SETUP",
                                "room": rooms_list[selected_room_idx],
                                "song": songs_list[selected_song_idx],
                                "speed": diff_speeds[selected_diff_idx]
                            }).encode('utf-8'))
                        except:
                            pass
                            
                if 490 <= mouse_pos[0] <= 790 and 560 <= mouse_pos[1] <= 610: current_scene = "LOBBY"
                if 490 <= mouse_pos[0] <= 790 and 630 <= mouse_pos[1] <= 670: current_scene = "MAIN_MENU"
        scenes.draw_create_room_menu(screen, mouse_pos, songs_list, selected_song_idx, diff_list, selected_diff_idx, rooms_list, selected_room_idx, my_network_id, active_bg)
    elif current_scene == "LOBBY":
        if net_game_start_trigger:
            net_game_start_trigger = False
            chosen_speed = diff_speeds[selected_diff_idx]
            chosen_song = songs_list[selected_song_idx]
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.load(os.path.join("Song", chosen_song))
                pygame.mixer.music.set_volume(0.6)
                pygame.mixer.music.play(-1)
            except:
                pass
            gameplay_manager = GameplayManager(f_large, f_medium, f_small, arrow_images, character_images, chosen_speed, chosen_song, client_socket, is_connected, my_network_id, active_bg)
            current_scene = "GAMEPLAY"

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 490 <= mouse_pos[0] <= 790 and 580 <= mouse_pos[1] <= 630:
                    is_ready_lobby = not is_ready_lobby
                    if is_connected:
                        try:
                            client_socket.sendall(json.dumps({
                                "type": "PLAYER_READY",
                                "room": rooms_list[selected_room_idx],
                                "is_ready": is_ready_lobby
                            }).encode('utf-8'))
                        except:
                            pass
                    else:
                        net_game_start_trigger = True
                        
                if 1100 <= mouse_pos[0] <= 1220 and 30 <= mouse_pos[1] <= 65: current_scene = "CREATE_ROOM"
        
        scenes.draw_lobby(screen, mouse_pos, player_name, character_images["IDLE"], songs_list[selected_song_idx], diff_list[selected_diff_idx], is_ready_lobby, my_network_id, is_connected, rooms_list[selected_room_idx], active_bg)

    elif current_scene == "GAMEPLAY":
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            status = gameplay_manager.process_input(event)
            if status == "GO_TO_LOBBY":
                pygame.mixer.music.stop()
                play_menu_music()
                is_ready_lobby = False
                current_scene = "LOBBY"
        
        if current_scene == "GAMEPLAY":
            game_status = gameplay_manager.update()
            if game_status == "SONG_ENDED": pygame.mixer.music.stop()
            gameplay_manager.draw(screen, player_name, network_states)

    if is_connected:
        txt_ping_disp = f_small.render(f"Ping: {current_latency}", True, GREEN)
        screen.blit(txt_ping_disp, (1130, 25))

    pygame.display.flip()

client_socket.close()
pygame.quit()
sys.exit()
