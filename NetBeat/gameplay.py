import pygame
import random
import json

BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (20, 20, 20)
LIGHT_GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
CYAN = (0, 255, 255)

class GameplayManager:
    def __init__(self, f_large, f_medium, f_small, arrow_imgs, char_imgs, custom_speed, song_name, socket_conn=None, is_net=False, net_id="P1", bg_image=None):
        self.font_large = f_large
        self.font_medium = f_medium
        self.font_small = f_small
        self.arrow_images = arrow_imgs
        self.character_images = char_imgs
        self.song_name = song_name  
        self.bg_image = bg_image 
        
        self.socket_conn = socket_conn
        self.is_net = is_net
        self.my_net_id = net_id
        self.opp_net_id = "P2" if net_id == "P1" else "P1"
        
        self.score = 0
        self.feedback_text = ""
        self.feedback_color = WHITE
        self.feedback_timer = 0
        self.current_p1_state = "IDLE"
        self.character_state_timer = 0
        self.my_current_chat = ""
        self.chat_display_timer = 0
        self.chat_history = []       
        self.last_seen_opp_chat = "" 
        
        self.bar_x, self.bar_y, self.bar_width, self.bar_height = 80, 630, 1120, 30
        self.target_x, self.target_bar_width = 1080, 30
        self.beat_x = self.bar_x
        self.beat_speed = custom_speed 
        
        self.has_hit_space_this_round = False
        
        self.perfect_count = 0
        self.great_count = 0
        self.miss_count = 0
        
        self.NUM_ARROWS = 8
        self.arrows_pool = ["LEFT", "RIGHT", "UP", "DOWN"]
        self.current_arrows_goal = [random.choice(self.arrows_pool) for _ in range(self.NUM_ARROWS)]
        self.current_arrow_index = 0

        self.countdown_frames = 300  
        self.countdown_text = "READY"
        self.is_countdown_active = True
        
        self.is_game_finished = False
        if song_name == "bidadari.mp3":
            self.play_time_left = 279 * 60  
        elif song_name == "dropdead.mp3":
            self.play_time_left = 256 * 60  
        elif song_name == "selfcontrol.mp3":
            self.play_time_left = 291 * 60  
        else:
            self.play_time_left = 60 * 60   

    def add_to_chat_history(self, sender_id, text):
        """Menambahkan pesan baru ke riwayat log box kiri bawah"""
        chat_line = f"[{sender_id}]: {text}"
        if not self.chat_history or self.chat_history[-1] != chat_line:
            self.chat_history.append(chat_line)
            if len(self.chat_history) > 4:
                self.chat_history.pop(0)

    def send_score_update(self, added_score, state, feedback, chat_msg=""):
        if self.is_net and self.socket_conn:
            try:
                packet = {
                    "type": "GAME_UPDATE",
                    "added_score": added_score,
                    "state": state,
                    "feedback": feedback,
                    "chat": chat_msg
                }
                self.socket_conn.sendall(json.dumps(packet).encode('utf-8'))
            except:
                self.is_net = False

    def process_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "GO_TO_LOBBY"
            
            # Deteksi Tombol Quick Chat Hotkey
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3] and not self.is_game_finished:
                if event.key == pygame.K_1: msg = "GG!!"
                elif event.key == pygame.K_2: msg = "EZ LOL!!!"
                elif event.key == pygame.K_3: msg = "WKWK MISS TERUS KOCAK"
                
                self.my_current_chat = msg
                self.chat_display_timer = 120 
            
                self.add_to_chat_history("KAMU", msg)
                
                self.send_score_update(0, self.current_p1_state, self.feedback_text, self.my_current_chat)
                return "STAY"
            
            if self.is_countdown_active or self.is_game_finished:
                return "STAY"
                
            pressed_arrow = ""
            if event.key == pygame.K_LEFT: pressed_arrow = "LEFT"
            elif event.key == pygame.K_RIGHT: pressed_arrow = "RIGHT"
            elif event.key == pygame.K_UP: pressed_arrow = "UP"
            elif event.key == pygame.K_DOWN: pressed_arrow = "DOWN"
            
            if pressed_arrow and not self.has_hit_space_this_round:
                if self.current_arrow_index < len(self.current_arrows_goal):
                    if pressed_arrow == self.current_arrows_goal[self.current_arrow_index]:
                        self.current_arrow_index += 1
                    else:
                        self.current_arrow_index = 0
                        self.feedback_text = "SALAH INDIKATOR! ULANG!"
                        self.feedback_color = RED
                        self.feedback_timer = 15  
            
            elif event.key == pygame.K_SPACE and not self.has_hit_space_this_round:
                self.has_hit_space_this_round = True  
                if self.current_arrow_index == len(self.current_arrows_goal):
                    distance = abs(self.beat_x - self.target_x)
                    
                    if distance <= 45:
                        self.feedback_text = "!!! PERFECT !!!"
                        self.feedback_color = GOLD
                        self.score += 1000
                        self.perfect_count += 1
                        self.current_p1_state = "DANCING"
                        self.send_score_update(1000, "DANCING", "!!! PERFECT !!!", self.my_current_chat)
                    elif distance <= 85:
                        self.feedback_text = "GREAT"
                        self.feedback_color = GREEN
                        self.score += 500
                        self.great_count += 1
                        self.current_p1_state = "DANCING"
                        self.send_score_update(500, "DANCING", "GREAT", self.my_current_chat)
                    else:
                        self.feedback_text = "MISS"
                        self.feedback_color = RED
                        self.miss_count += 1
                        self.current_p1_state = "MISS"
                        self.send_score_update(0, "MISS", "MISS", self.my_current_chat)
                else:
                    self.feedback_text = "MISS (Belum Selesai!)"
                    self.feedback_color = RED
                    self.miss_count += 1
                    self.current_p1_state = "MISS"
                    self.send_score_update(0, "MISS", "MISS (Belum Selesai!)", self.my_current_chat)              
                self.feedback_timer = 30
                self.character_state_timer = 45
        return "STAY"

    def update(self):
        if self.is_game_finished:
            return "STAY"

        if self.chat_display_timer > 0:
            self.chat_display_timer -= 1
            if self.chat_display_timer == 0:
                self.my_current_chat = ""
                self.send_score_update(0, self.current_p1_state, self.feedback_text, "")

        if self.is_countdown_active:
            self.countdown_frames -= 1
            self.beat_x = self.bar_x  
            if self.countdown_frames > 240: self.countdown_text = "READY..."
            elif self.countdown_frames > 180: self.countdown_text = "3"
            elif self.countdown_frames > 120: self.countdown_text = "2"
            elif self.countdown_frames > 60: self.countdown_text = "1"
            elif self.countdown_frames > 0: self.countdown_text = "START!"
            else: self.is_countdown_active = False 
            return "STAY"

        self.play_time_left -= 1
        if self.play_time_left <= 0:
            self.is_game_finished = True
            self.current_p1_state = "IDLE"
            self.send_score_update(0, "IDLE", "FINISHED", "")
            return "SONG_ENDED" 

        self.beat_x += self.beat_speed
        if self.beat_x > (self.bar_x + self.bar_width):
            self.beat_x = self.bar_x  
            if not self.has_hit_space_this_round:
                self.feedback_text = "MISS (Waktu Habis!)"
                self.feedback_color = RED
                self.feedback_timer = 30
                self.miss_count += 1
                self.current_p1_state = "MISS"
                self.character_state_timer = 45
                self.send_score_update(0, "MISS", "MISS (Timeout)", self.my_current_chat)
            
            self.current_arrows_goal = [random.choice(self.arrows_pool) for _ in range(self.NUM_ARROWS)]
            self.current_arrow_index = 0
            self.has_hit_space_this_round = False  

        if self.feedback_timer > 0: self.feedback_timer -= 1
        else:
            if self.feedback_text == "SALAH INDIKATOR! ULANG!": self.feedback_text = ""

        if self.character_state_timer > 0: self.character_state_timer -= 1
        else: self.current_p1_state = "IDLE"
        return "STAY"

    def draw(self, screen, player_name, net_states_data=None):
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150)) 
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BLACK)
        
        seconds_left = max(0, self.play_time_left // 60)
        time_str = f"Time: {seconds_left // 60:02d}:{seconds_left % 60:02d}"

        screen.blit(self.font_small.render(f"[ARENA ONLINE] - USER: {player_name} ({self.my_net_id})", True, WHITE), (20, 20))
        screen.blit(self.font_medium.render(time_str, True, CYAN), (560, 15))
        screen.blit(self.font_small.render("[ESC] KELUAR ARENA", True, RED), (1050, 20))
        screen.blit(self.font_small.render("Quick Chat Hotkey: [1] GG!  [2] EZ!  [3] WKWK!", True, GOLD), (20, 50))
        
        pygame.draw.rect(screen, GRAY, (250, 150, 200, 300), border_radius=10)
        pygame.draw.rect(screen, GRAY, (830, 150, 200, 300), border_radius=10)
        
        opp_pose = "IDLE"
        opp_score = 0
        opp_feedback = ""
        opp_chat = ""
        
        if net_states_data and self.opp_net_id in net_states_data:
            opp_pose = net_states_data[self.opp_net_id]["state"]
            opp_score = net_states_data[self.opp_net_id]["score"]
            opp_feedback = net_states_data[self.opp_net_id]["feedback"]
            if "chat" in net_states_data[self.opp_net_id]:
                opp_chat = net_states_data[self.opp_net_id]["chat"]
                if opp_chat and opp_chat != self.last_seen_opp_chat:
                    self.add_to_chat_history("LAWAN", opp_chat)
                self.last_seen_opp_chat = opp_chat

        if self.my_net_id == "P1":
            screen.blit(self.character_images[self.current_p1_state], (270, 170))
            screen.blit(self.character_images[opp_pose], (850, 170))
            p1_chat_text = self.my_current_chat
            p2_chat_text = opp_chat
        else:
            screen.blit(self.character_images[opp_pose], (270, 170))
            screen.blit(self.character_images[self.current_p1_state], (850, 170))
            p1_chat_text = opp_chat
            p2_chat_text = self.my_current_chat
            

        if p1_chat_text:
            pygame.draw.rect(screen, CYAN, (210, 100, 280, 35), border_radius=8)
            txt_c1 = self.font_small.render(p1_chat_text, True, BLACK)
            screen.blit(txt_c1, txt_c1.get_rect(center=(250 + 100, 118)))
            
        if p2_chat_text:
            pygame.draw.rect(screen, CYAN, (790, 100, 280, 35), border_radius=8)
            txt_c2 = self.font_small.render(p2_chat_text, True, BLACK)
            screen.blit(txt_c2, txt_c2.get_rect(center=(830 + 100, 118)))
            
        p1_scr = self.score if self.my_net_id == "P1" else opp_score
        p2_scr = self.score if self.my_net_id == "P2" else opp_score
        screen.blit(self.font_small.render(f"P1 Score: {p1_scr}", True, WHITE), (250, 470))
        screen.blit(self.font_small.render(f"P2 Score: {p2_scr}", True, WHITE), (830, 470))
        
        if opp_feedback and not self.is_game_finished and not self.is_countdown_active:
            txt_opp_fb = self.font_small.render(opp_feedback, True, LIGHT_GRAY)
            fb_x = 830 if self.my_net_id == "P1" else 250
            screen.blit(txt_opp_fb, (fb_x, 500))
        if not self.is_game_finished:
            chat_box_surface = pygame.Surface((320, 130), pygame.SRCALPHA)
            chat_box_surface.fill((0, 0, 0, 120)) 
            pygame.draw.rect(chat_box_surface, LIGHT_GRAY, (0, 0, 320, 130), width=1, border_radius=5)
            screen.blit(chat_box_surface, (20, 475))
            for idx, log_text in enumerate(self.chat_history):
                text_color = CYAN if "[KAMU]" in log_text else GOLD
                txt_line = self.font_small.render(log_text, True, text_color)
                screen.blit(txt_line, (30, 485 + (idx * 26)))

        if self.is_countdown_active:
            txt_cd = self.font_large.render(self.countdown_text, True, GOLD)
            screen.blit(txt_cd, txt_cd.get_rect(center=(1280/2, 530)))
        elif self.feedback_text and not self.is_game_finished:
            txt_f = self.font_large.render(self.feedback_text, True, self.feedback_color)
            screen.blit(txt_f, txt_f.get_rect(center=(1280/2, 530)))
            
        for i, arrow_key in enumerate(self.current_arrows_goal):
            x_pos = 370 + (i * 68)
            y_pos = 555
            screen.blit(self.arrow_images[arrow_key], (x_pos, y_pos))
            if i < self.current_arrow_index and not self.is_game_finished:
                overlay = pygame.Surface((60, 60), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (x_pos, y_pos))
                
        pygame.draw.rect(screen, GRAY, (self.bar_x, self.bar_y, self.bar_width, self.bar_height), border_radius=5)
        pygame.draw.rect(screen, CYAN, (self.target_x - (self.target_bar_width // 2), self.bar_y - 6, self.target_bar_width, self.bar_height + 12), border_radius=5)
        pygame.draw.circle(screen, GOLD, (int(self.beat_x), self.bar_y + int(self.bar_height / 2)), 12)
        screen.blit(self.font_small.render("[SPACE ZONE]", True, CYAN), (self.target_x - 55, self.bar_y - 30))

        if self.is_game_finished:
            overlay_bg = pygame.Surface((600, 420))
            overlay_bg.fill(DARK_GRAY)
            pygame.draw.rect(overlay_bg, GOLD, (0, 0, 600, 420), width=4, border_radius=15)
            screen.blit(overlay_bg, (340, 120))
            
            txt_res_title = self.font_large.render("STAGE RESULT", True, GOLD)
            screen.blit(txt_res_title, txt_res_title.get_rect(center=(1280/2, 160)))
            
            pygame.draw.line(screen, LIGHT_GRAY, (380, 250), (900, 250), 2)
            pygame.draw.line(screen, LIGHT_GRAY, (380, 440), (900, 440), 2)
            
            screen.blit(self.font_medium.render("JUDUL PENILAIAN", True, CYAN), (390, 210))
            screen.blit(self.font_medium.render("JUMLAH KETUKAN", True, CYAN), (680, 210))
            
            screen.blit(self.font_small.render("PERFECT HIT", True, GOLD), (390, 270))
            screen.blit(self.font_medium.render(str(self.perfect_count), True, WHITE), (760, 265))
            
            screen.blit(self.font_small.render("GREAT HIT", True, GREEN), (390, 320))
            screen.blit(self.font_medium.render(str(self.great_count), True, WHITE), (760, 315))
            
            screen.blit(self.font_small.render("MISS / TIMEOUT", True, RED), (390, 370))
            screen.blit(self.font_medium.render(str(self.miss_count), True, WHITE), (760, 365))
            
            screen.blit(self.font_medium.render("TOTAL SKOR KAMU:", True, GOLD), (390, 465))
            screen.blit(self.font_large.render(f"{self.score}", True, GREEN), (680, 455))
            
            txt_esc_hint = self.font_small.render("[ Tekan ESC untuk kembali ke Lobby Room ]", True, LIGHT_GRAY)
            screen.blit(txt_esc_hint, txt_esc_hint.get_rect(center=(1280/2, 510)))