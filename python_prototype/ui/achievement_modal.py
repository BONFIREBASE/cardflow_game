import pygame
import math
import os
import time
from ui.ui_components import Colors, blur_surface
from ui.paths import get_resource_path
from ui.achievement_manager import AchievementManager, ACHIEVEMENTS

ICON_CACHE = {}

def get_ach_icon(icon_name, size=32):
    key = (icon_name, size)
    if key in ICON_CACHE:
        return ICON_CACHE[key]
    try:
        icon_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", f"{icon_name}.png"))
        img = pygame.image.load(icon_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (size, size))
        ICON_CACHE[key] = img
        return img
    except:
        ICON_CACHE[key] = None
        return None

class AchievementModal:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small

        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 750, 580)
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0
        self.scroll_y = 0
        self.max_scroll = 0

        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title

        self.close_btn_rect = pygame.Rect(0, 0, 30, 30)
        self.icon_close = None
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except:
            self.icon_close = None

        self.manager = AchievementManager()

        self.total_ach_count = len(ACHIEVEMENTS)
        self.unlocked_count = 0
        self.claimed_count = 0

    def open(self):
        self.active = True
        self._target_active = True
        self.alpha = 0
        self.time_alive = 0.0
        self._blurred_bg = None
        self.scroll_y = 0
        self.manager = AchievementManager()
        self.unlocked_count = len(self.manager.progress["unlocked"])
        self.claimed_count = len(self.manager.progress["claimed"])

        card_h = 110
        total_h = 80 + len(ACHIEVEMENTS) * (card_h + 12)
        self.max_scroll = max(0, total_h - self.rect.h + 40)

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

        title_surf = self.font_modal_title.render("ACHIEVEMENTS", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 20))
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, 65), (self.rect.w - 25, 65), 1)

        prog_text = self.font_small.render(f"{self.unlocked_count} / {self.total_ach_count} Unlocked", True, Colors.TEXT_MUTED)
        modal_surf.blit(prog_text, (self.rect.w // 2 - prog_text.get_width() // 2, 70))

        self.close_btn_rect.topright = (self.rect.w - 20, 20)
        rel_mouse = (pygame.mouse.get_pos()[0] - self.rect.x, pygame.mouse.get_pos()[1] - screen_y)
        close_hover = self.close_btn_rect.collidepoint(rel_mouse)
        close_color = (220, 50, 50) if close_hover else (180, 40, 40)
        pygame.draw.circle(modal_surf, close_color, self.close_btn_rect.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn_rect.centerx - 8, self.close_btn_rect.centery - 8))

        clip_rect = pygame.Rect(20, 85, self.rect.w - 40, self.rect.h - 105)
        modal_surf.set_clip(clip_rect)

        card_h = 110
        start_y = 95 - self.scroll_y
        gap = 12

        for i, ach in enumerate(ACHIEVEMENTS):
            cy = start_y + i * (card_h + gap)
            if cy + card_h < 85 or cy > self.rect.h:
                continue

            is_unlocked = ach["id"] in self.manager.progress["unlocked"]
            is_claimed = ach["id"] in self.manager.progress["claimed"]

            if is_claimed:
                bg_color = (25, 40, 30, 200)
                border_color = (60, 180, 80, 100)
            elif is_unlocked:
                bg_color = (40, 40, 25, 200)
                border_color = (255, 215, 50, 150)
            else:
                bg_color = (30, 30, 40, 180)
                border_color = (60, 60, 80, 100)

            pygame.draw.rect(modal_surf, bg_color, (40, cy, self.rect.w - 80, card_h), border_radius=16)
            pygame.draw.rect(modal_surf, border_color, (40, cy, self.rect.w - 80, card_h), width=1, border_radius=16)

            icon_img = get_ach_icon(ach["icon"])
            if icon_img and is_unlocked:
                modal_surf.blit(icon_img, (60, cy + (card_h - 32) // 2))
            elif icon_img:
                gray = pygame.Surface((32, 32), pygame.SRCALPHA)
                gray.fill((40, 40, 50, 200))
                modal_surf.blit(gray, (60, cy + (card_h - 32) // 2))

            title_color = Colors.TEXT_WHITE if is_unlocked else (120, 120, 130)
            title_txt = self.font_body.render(ach["title"], True, title_color)
            modal_surf.blit(title_txt, (105, cy + 12))

            desc_color = Colors.TEXT_MUTED if is_unlocked else (90, 90, 100)
            desc_txt = self.font_small.render(ach["desc"], True, desc_color)
            modal_surf.blit(desc_txt, (105, cy + 40))

            curr, goal = self.manager.get_achievement_progress(ach["id"])
            bar_w = self.rect.w - 300
            bar_h = 8
            bx = 105
            by = cy + 72
            pygame.draw.rect(modal_surf, (15, 20, 30), (bx, by, bar_w, bar_h), border_radius=bar_h // 2)

            if is_unlocked:
                fill_w = bar_w
                fill_color = (255, 215, 50) if not is_claimed else (60, 180, 80)
                pygame.draw.rect(modal_surf, fill_color, (bx, by, fill_w, bar_h), border_radius=bar_h // 2)
            else:
                progress = min(1.0, curr / goal) if goal > 0 else 0
                fill_w = int(bar_w * progress)
                if fill_w > 0:
                    pygame.draw.rect(modal_surf, (100, 100, 120), (bx, by, fill_w, bar_h), border_radius=bar_h // 2)

            prog_str = f"{curr}/{goal}" if not is_unlocked else "DONE"
            prog_txt = self.font_small.render(prog_str, True, Colors.TEXT_MUTED)
            modal_surf.blit(prog_txt, (bx + bar_w + 10, by - 2))

            if is_claimed:
                claimed_txt = self.font_small.render("CLAIMED", True, Colors.SAFE_GREEN)
                modal_surf.blit(claimed_txt, (self.rect.w - 130, cy + card_h // 2 - 8))
            elif is_unlocked:
                reward_str = f"+{ach['reward']:,}"
                rew_txt = self.font_small.render(reward_str, True, Colors.TEXT_GOLD)
                modal_surf.blit(rew_txt, (self.rect.w - 130, cy + card_h // 2 - 20))

                claim_btn = pygame.Rect(self.rect.w - 140, cy + card_h // 2 + 4, 80, 28)
                btn_hover = claim_btn.collidepoint(rel_mouse[0], rel_mouse[1] + self.scroll_y)
                btn_color = (255, 215, 50) if btn_hover else (200, 180, 40)
                pygame.draw.rect(modal_surf, btn_color, claim_btn, border_radius=14)
                btn_txt = self.font_small.render("CLAIM", True, (20, 15, 0))
                modal_surf.blit(btn_txt, (claim_btn.centerx - btn_txt.get_width() // 2, claim_btn.centery - btn_txt.get_height() // 2))
            else:
                rew_str = f"{ach['reward']:,} coins"
                rew_txt = self.font_small.render(rew_str, True, (80, 80, 95))
                modal_surf.blit(rew_txt, (self.rect.w - 130, cy + card_h // 2 - 8))

        modal_surf.set_clip(None)
        screen.blit(modal_surf, (self.rect.x, screen_y))

    def handle_click(self, event):
        if not self.active or not self._target_active:
            return None

        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - screen_y)

        if self.close_btn_rect.collidepoint(rel_pos):
            self.close()
            return {"type": "close"}

        if event.button == 1:
            card_h = 110
            gap = 12
            start_y = 95 - self.scroll_y

            for i, ach in enumerate(ACHIEVEMENTS):
                cy = start_y + i * (card_h + gap)
                if cy + card_h < 85 or cy > self.rect.h:
                    continue

                is_unlocked = ach["id"] in self.manager.progress["unlocked"]
                is_claimed = ach["id"] in self.manager.progress["claimed"]

                if is_unlocked and not is_claimed:
                    claim_btn = pygame.Rect(self.rect.w - 140, cy + card_h // 2 + 4, 80, 28)
                    if claim_btn.collidepoint(rel_pos[0], rel_pos[1]):
                        reward = self.manager.claim(ach["id"])
                        if reward > 0:
                            self.claimed_count = len(self.manager.progress["claimed"])
                            return {"type": "claim", "amount": reward, "ach_id": ach["id"]}

        if event.button == 4:
            self.scroll_y = max(0, self.scroll_y - 40)
        elif event.button == 5:
            self.scroll_y = min(self.max_scroll, self.scroll_y + 40)

        if self.rect.collidepoint(event.pos):
            return {"type": "blocked"}
        return None
