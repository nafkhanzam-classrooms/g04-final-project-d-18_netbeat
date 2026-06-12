import pygame
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (25, 25, 25)
LIGHT_GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
CYAN = (0, 255, 255)

def init_scene_fonts(f_title, f_large, f_medium, f_small):
    global font_title, font_large, font_medium, font_small
    font_title, font_large, font_medium, font_small = f_title, f_large, f_medium, f_small

def draw_main_menu(screen, mouse_pos, player_name, input_active, bg_image):
    screen.blit(bg_image, (0, 0))
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))  
    screen.blit(overlay, (0, 0))

    # Murni Menggunakan Nama NetBeat Saja
    txt_logo = font_title.render("NetBeat", True, GOLD)
    screen.blit(txt_logo, txt_logo.get_rect(center=(1280/2, 150)))
    
    txt_label = font_small.render("MASUKKAN NAMA KAMU:", True, LIGHT_GRAY)
    screen.blit(txt_label, (490, 270))
    
    box_color = CYAN if input_active else GRAY
    pygame.draw.rect(screen, box_color, (490, 300, 300, 40), border_radius=5)
    txt_name_display = font_medium.render(player_name + ("|" if input_active else ""), True, WHITE)
    screen.blit(txt_name_display, (500, 305))
    
    btn_room_hover = 490 <= mouse_pos[0] <= 790 and 400 <= mouse_pos[1] <= 450
    pygame.draw.rect(screen, GREEN if btn_room_hover else GRAY, (490, 400, 300, 50), border_radius=10)
    txt_btn1 = font_medium.render("CREATE / JOIN ROOM", True, BLACK if btn_room_hover else WHITE)
    screen.blit(txt_btn1, txt_btn1.get_rect(center=(1280/2, 425)))
    
    btn_exit_hover = 490 <= mouse_pos[0] <= 790 and 480 <= mouse_pos[1] <= 530
    pygame.draw.rect(screen, RED if btn_exit_hover else GRAY, (490, 480, 300, 50), border_radius=10)
    txt_btn2 = font_medium.render("KELUAR GAME", True, BLACK if btn_exit_hover else WHITE)
    screen.blit(txt_btn2, txt_btn2.get_rect(center=(1280/2, 505)))

def draw_create_room_menu(screen, mouse_pos, songs, selected_song_idx, difficulties, selected_diff_idx, available_rooms, selected_room_idx, my_net_id, bg_image):
    screen.blit(bg_image, (0, 0))
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))  
    screen.blit(overlay, (0, 0))

    txt_heading = font_large.render("[ ROOM & STAGE CONFIGURATION ]", True, CYAN)
    screen.blit(txt_heading, (40, 30))
    
    screen.blit(font_medium.render("PILIH ROOM KAMAR:", True, WHITE), (60, 110))
    for i, rm_name in enumerate(available_rooms):
        is_selected = (i == selected_room_idx)
        btn_hover = 60 <= mouse_pos[0] <= 360 and (160 + i*55) <= mouse_pos[1] <= (205 + i*55)
        btn_color = CYAN if is_selected else (LIGHT_GRAY if btn_hover else GRAY)
        
        pygame.draw.rect(screen, btn_color, (60, 160 + i*55, 300, 45), border_radius=5)
        txt_rm = font_small.render(rm_name, True, BLACK if (is_selected or btn_hover) else WHITE)
        screen.blit(txt_rm, (80, 172 + i*55))

    screen.blit(font_medium.render("PILIH LAGU:", True, WHITE), (430, 110))
    for i, song in enumerate(songs):
        is_selected = (i == selected_song_idx)
        btn_hover = 430 <= mouse_pos[0] <= 780 and (160 + i*55) <= mouse_pos[1] <= (205 + i*55)
        btn_color = GOLD if is_selected else (DARK_GRAY if my_net_id == "P2" else (LIGHT_GRAY if btn_hover else GRAY))
            
        pygame.draw.rect(screen, btn_color, (430, 160 + i*55, 350, 45), border_radius=5)
        txt_song = font_small.render(song, True, BLACK if (is_selected or (btn_hover and my_net_id == "P1")) else WHITE)
        screen.blit(txt_song, (450, 172 + i*55))

    screen.blit(font_medium.render("KESULITAN:", True, WHITE), (850, 110))
    for i, diff in enumerate(difficulties):
        is_selected = (i == selected_diff_idx)
        btn_hover = 850 <= mouse_pos[0] <= 1180 and (160 + i*55) <= mouse_pos[1] <= (205 + i*55)
        
        diff_colors = [GREEN, GOLD, RED]
        btn_color = diff_colors[i] if is_selected else (DARK_GRAY if my_net_id == "P2" else (LIGHT_GRAY if btn_hover else GRAY))
            
        pygame.draw.rect(screen, btn_color, (850, 160 + i*55, 330, 45), border_radius=5)
        txt_diff = font_small.render(diff, True, BLACK if (is_selected or (btn_hover and my_net_id == "P1")) else WHITE)
        screen.blit(txt_diff, (870, 172 + i*55))

    role_str = "HAK AKSES: HOST (Bisa Atur Lagu/Diff)" if my_net_id == "P1" else "HAK AKSES: GUEST (Ikut Setelan Host)"
    screen.blit(font_small.render(role_str, True, GREEN if my_net_id == "P1" else GOLD), (430, 420))

    btn_confirm_hover = 490 <= mouse_pos[0] <= 790 and 560 <= mouse_pos[1] <= 610
    pygame.draw.rect(screen, CYAN if btn_confirm_hover else GRAY, (490, 560, 300, 50), border_radius=10)
    txt_confirm = font_medium.render("MASUK LOBBY ROOM", True, BLACK if btn_confirm_hover else WHITE)
    screen.blit(txt_confirm, txt_confirm.get_rect(center=(1280/2, 585)))
    
    btn_back_hover = 490 <= mouse_pos[0] <= 790 and 630 <= mouse_pos[1] <= 670
    pygame.draw.rect(screen, RED if btn_back_hover else GRAY, (490, 630, 300, 40), border_radius=8)
    txt_back = font_small.render("KEMBALI KE MENU", True, WHITE)
    screen.blit(txt_back, txt_back.get_rect(center=(1280/2, 650)))

def draw_lobby(screen, mouse_pos, player_name, idle_char_img, song_name, difficulty_name, is_ready_lobby, my_net_id, is_connected, current_room_name, bg_image):
    screen.blit(bg_image, (0, 0))
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  
    screen.blit(overlay, (0, 0))

    txt_lobby_title = font_large.render(f"[ LOBBY {current_room_name} ]", True, CYAN)
    screen.blit(txt_lobby_title, (40, 30))
    
    txt_info = font_small.render(f"Track: {song_name} | Speed: {difficulty_name}", True, GOLD)
    screen.blit(txt_info, (40, 90))
    
    btn_back_hover = 1100 <= mouse_pos[0] <= 1220 and 30 <= mouse_pos[1] <= 65
    pygame.draw.rect(screen, RED if btn_back_hover else GRAY, (1100, 30, 120, 35), border_radius=5)
    txt_back = font_small.render("KEMBALI", True, WHITE)
    screen.blit(txt_back, (1120, 38))
    
    pygame.draw.rect(screen, DARK_GRAY, (150, 150, 400, 380), border_radius=15)
    pygame.draw.rect(screen, DARK_GRAY, (730, 150, 400, 380), border_radius=15)
    
    screen.blit(idle_char_img, (270, 200))
    pygame.draw.rect(screen, CYAN if my_net_id == "P1" else GRAY, (180, 480, 340, 35), border_radius=5)
    p1_label = f"P1: {player_name} [HOST]" if my_net_id == "P1" else "P1: Musuh [HOST]"
    screen.blit(font_small.render(p1_label, True, BLACK if my_net_id == "P1" else WHITE), (200, 488))
    
    if is_connected:
        screen.blit(idle_char_img, (850, 200))
        pygame.draw.rect(screen, CYAN if my_net_id == "P2" else GRAY, (760, 480, 340, 35), border_radius=5)
        p2_label = f"P2: {player_name} [GUEST]" if my_net_id == "P2" else "P2: Player 2 Terhubung"
        screen.blit(font_small.render(p2_label, True, BLACK if my_net_id == "P2" else WHITE), (780, 488))
    else:
        screen.blit(font_medium.render("[ SLOT KOSONG ]", True, LIGHT_GRAY), (810, 300))
        screen.blit(font_small.render("(Offline Mode)", True, LIGHT_GRAY), (845, 340))
    
    btn_start_hover = 490 <= mouse_pos[0] <= 790 and 580 <= mouse_pos[1] <= 630
    pygame.draw.rect(screen, GREEN if is_ready_lobby else (GOLD if btn_start_hover else GRAY), (490, 580, 300, 50), border_radius=10)
    
    status_str = "READY / START GAME" if not is_ready_lobby else "WAITING OPPONENT..."
    txt_btn_start = font_medium.render(status_str, True, BLACK if (is_ready_lobby or btn_start_hover) else WHITE)
    screen.blit(txt_btn_start, txt_btn_start.get_rect(center=(1280/2, 605)))