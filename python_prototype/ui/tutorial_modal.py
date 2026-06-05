import pygame
import math
import os
from ui.ui_components import Colors, blur_surface
from ui.paths import get_resource_path

STEPS = [
    {
        "title": "Welcome to Cardflow!",
        "body": [
            "Cardflow is a digital version of Tong-its,",
            "a popular Filipino card game.",
            "",
            "This quick tutorial will walk you through",
            "the basics so you can start playing.",
        ],
        "icon": None
    },
    {
        "title": "The Goal",
        "body": [
            "The goal is to be the first player to",
            "empty your hand by forming melds.",
            "",
            "Melds are either:",
            "  \u2022 SETS \u2014 3+ same rank (e.g. 7\u2660 7\u2665 7\u2666)",
            "  \u2022 RUNS \u2014 3+ consecutive same suit (e.g. 5\u2665 6\u2665 7\u2665)",
            "",
            "The fewer cards you have left, the better!",
        ],
        "icon": None
    },
    {
        "title": "Game Flow \u2014 Your Turn",
        "body": [
            "Each turn has 3 phases:",
            "",
            "1. DRAW \u2014 Draw from the closed deck or",
            "   take the top card from the discard pile.",
            "",
            "2. MELD \u2014 Drop valid melds face-up or add",
            "   cards to existing melds (Sapaw).",
            "",
            "3. DISCARD \u2014 Throw one card face-up to",
            "   end your turn.",
        ],
        "icon": None
    },
    {
        "title": "Special Actions",
        "body": [
            "\u2022 SAPAW \u2014 Add a card to an existing meld",
            "   on the table (yours or opponents').",
            "",
            "\u2022 FIGHT \u2014 Challenge when you think you have",
            "   fewer points than others. Lowest points wins!",
            "",
            "\u2022 BURN \u2014 If your hand points exceed the",
            "   discard value, you're burned (forced fold).",
        ],
        "icon": None
    },
    {
        "title": "Winning the Game",
        "body": [
            "A match ends when:",
            "",
            "\u2022 TONG-ITS \u2014 A player empties their hand.",
            "\u2022 FIGHT \u2014 The caller has the lowest points.",
            "\u2022 DRAW \u2014 The deck runs out; lowest points wins.",
            "",
            "Win coins, climb ranks, and unlock achievements!",
            "",
            "Good luck, and have fun!",
        ],
        "icon": None
    },
]

class TutorialModal:
    def __init__(self, font_title, font_body, font_small, font_btn=None):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        self.font_btn = font_btn if font_btn else font_small

        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 700, 520)
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0

        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title

        self.current_step = 0
        self.total_steps = len(STEPS)

        self.close_btn_rect = pygame.Rect(0, 0, 30, 30)
        self.icon_close = None
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except:
            self.icon_close = None

        self.prev_btn_rect = pygame.Rect(0, 0, 120, 40)
        self.next_btn_rect = pygame.Rect(0, 0, 120, 40)
        self.done_btn_rect = pygame.Rect(0, 0, 140, 44)
        self.callback = None

    def open(self, callback=None):
        self.active = True
        self._target_active = True
        self.alpha = 0
        self.time_alive = 0.0
        self._blurred_bg = None
        self.current_step = 0
        self.callback = callback

    def close(self):
        self._target_active = False

    def update(self, dt, mouse_pos):
        if not self.active:
            return
        self.time_alive += dt
        speed = 10.0
        if self._target_active:
            self.alpha = min(255, self.alpha + speed * 60 * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            if self.alpha <= 0:
                self.active = False

    def draw(self, screen, width, height):
        if not self.active:
            return

        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(screen.copy(), factor=6, tint=(10, 8, 20), tint_alpha=180)

        ease = min(self.alpha / 255.0, 1.0)
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            screen.blit(self._blurred_bg, (0, 0))
        elif blur_alpha > 0:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            screen.blit(temp, (0, 0))

        self.rect.center = (width // 2, height // 2)
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)

        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        for row in range(self.rect.h):
            t = row / self.rect.h
            r = int(15 + 15 * t)
            g = int(18 + 12 * t)
            b = int(35 + 20 * t)
            a = 245
            pygame.draw.line(modal_surf, (r, g, b, a), (0, row), (self.rect.w, row))

        mask = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, self.rect.w, self.rect.h), border_radius=28)
        modal_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.rect(modal_surf, (218, 175, 50, 120), (0, 0, self.rect.w, self.rect.h), width=2, border_radius=28)

        title_surf = self.font_modal_title.render(STEPS[self.current_step]["title"], True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 25))

        step_counter = self.font_small.render(f"Step {self.current_step + 1} of {self.total_steps}", True, Colors.TEXT_MUTED)
        modal_surf.blit(step_counter, (self.rect.w // 2 - step_counter.get_width() // 2, 70))

        for i in range(self.total_steps):
            dot_x = self.rect.w // 2 + (i - self.total_steps // 2) * 20
            dot_color = (255, 215, 50) if i == self.current_step else (60, 65, 80)
            pygame.draw.circle(modal_surf, dot_color, (dot_x, 95), 5)

        body = STEPS[self.current_step]["body"]
        line_y = 120
        for line in body:
            if line == "":
                line_y += 10
                continue
            color = Colors.TEXT_WHITE if not line.startswith("  ") else Colors.TEXT_GOLD
            txt = self.font_body.render(line, True, color)
            modal_surf.blit(txt, (55, line_y))
            line_y += 30

        close_color = (180, 40, 40)
        self.close_btn_rect.topright = (self.rect.w - 20, 15)
        pygame.draw.circle(modal_surf, close_color, self.close_btn_rect.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn_rect.centerx - 8, self.close_btn_rect.centery - 8))

        btn_y = self.rect.h - 60
        is_last = self.current_step == self.total_steps - 1

        if not is_last:
            n_x = self.rect.w // 2 + 10
            n_btn = self.next_btn_rect
            n_btn.topleft = (n_x, btn_y)
            pygame.draw.rect(modal_surf, (255, 215, 50), n_btn, border_radius=20)
            pygame.draw.rect(modal_surf, (200, 180, 40), n_btn, width=1, border_radius=20)
            n_txt = self.font_btn.render("NEXT", True, (20, 15, 0))
            modal_surf.blit(n_txt, (n_btn.centerx - n_txt.get_width() // 2, n_btn.centery - n_txt.get_height() // 2))

            p_x = self.rect.w // 2 - 130
            p_btn = self.prev_btn_rect
            p_btn.topleft = (p_x, btn_y)
            if self.current_step > 0:
                pygame.draw.rect(modal_surf, (60, 65, 80), p_btn, border_radius=20)
                pygame.draw.rect(modal_surf, (100, 105, 120), p_btn, width=1, border_radius=20)
                p_txt = self.font_btn.render("BACK", True, (220, 220, 230))
            else:
                pygame.draw.rect(modal_surf, (45, 45, 55), p_btn, border_radius=20)
                p_txt = self.font_btn.render("BACK", True, (80, 80, 90))
            modal_surf.blit(p_txt, (p_btn.centerx - p_txt.get_width() // 2, p_btn.centery - p_txt.get_height() // 2))
        else:
            d_x = self.rect.w // 2 - 70
            d_btn = self.done_btn_rect
            d_btn.topleft = (d_x, btn_y)
            pygame.draw.rect(modal_surf, (50, 180, 90), d_btn, border_radius=22)
            pygame.draw.rect(modal_surf, (80, 220, 120), d_btn, width=2, border_radius=22)
            d_txt = self.font_btn.render("LET'S GO!", True, (255, 255, 255))
            modal_surf.blit(d_txt, (d_btn.centerx - d_txt.get_width() // 2, d_btn.centery - d_txt.get_height() // 2))

            p2_x = self.rect.w // 2 - 220
            p2_btn = self.prev_btn_rect
            p2_btn.topleft = (p2_x, btn_y)
            pygame.draw.rect(modal_surf, (60, 65, 80), p2_btn, border_radius=20)
            pygame.draw.rect(modal_surf, (100, 105, 120), p2_btn, width=1, border_radius=20)
            p2_txt = self.font_btn.render("BACK", True, (220, 220, 230))
            modal_surf.blit(p2_txt, (p2_btn.centerx - p2_txt.get_width() // 2, p2_btn.centery - p2_txt.get_height() // 2))

        screen.blit(modal_surf, (self.rect.x, screen_y))

    def handle_click(self, event):
        if not self.active or not self._target_active:
            return None

        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - screen_y)

        if self.close_btn_rect.collidepoint(rel_pos):
            self.close()
            if self.callback:
                self.callback()
            return {"type": "close"}

        if event.button == 1:
            is_last = self.current_step == self.total_steps - 1

            if is_last:
                if self.done_btn_rect.collidepoint(rel_pos):
                    self.close()
                    if self.callback:
                        self.callback()
                    return {"type": "done"}
                if self.prev_btn_rect.collidepoint(rel_pos) and self.current_step > 0:
                    self.current_step -= 1
                    return {"type": "prev"}
            else:
                if self.next_btn_rect.collidepoint(rel_pos):
                    if self.current_step < self.total_steps - 1:
                        self.current_step += 1
                    return {"type": "next"}
                if self.prev_btn_rect.collidepoint(rel_pos) and self.current_step > 0:
                    self.current_step -= 1
                    return {"type": "prev"}

        if self.rect.collidepoint(event.pos):
            return {"type": "blocked"}
        return None
