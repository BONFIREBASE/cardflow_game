import pygame
import math
from ui.ui_components import Colors, blur_surface, Button
from ui.animation import ease_out_back, ease_out_cubic
from ui.assets_mgr import get_sys_font

class IngameMenu:
    def __init__(self, font_title, font_body):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = get_sys_font("Arial", 18, bold=True)
        
        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 400, 450)
        self.close_btn = pygame.Rect(0, 0, 40, 40)
        
        self.alpha = 0
        self._blurred_bg = None
        self.time_acc = 0.0
        
        # View state: 'main' or 'settings'
        self.view = 'main'
        self.flip_progress = 1.0 # 1.0 = fully visible, 0.0 = edge-on
        self._is_flipping = False
        self._next_view = 'main'
        
        # Settings State
        self.bgm_volume = 0.3
        self.sfx_volume = 0.7
        self.is_muted = False
        
        # Buttons - Main View
        bw, bh = 240, 50
        self.btn_resume = Button(0, 0, bw, bh, "Resume", font_body, color=(20, 160, 50), hover_color=(30, 220, 80))
        self.btn_settings = Button(0, 0, bw, bh, "Settings", font_body, color=(60, 60, 90), hover_color=(80, 80, 120))
        self.btn_quit = Button(0, 0, bw, bh, "Quit to Lobby", font_body, color=(160, 30, 30), hover_color=(220, 40, 40))
        
        # Buttons - Settings View
        self.btn_back = Button(0, 0, 120, 40, "Back", self.font_small, color=(100, 100, 120), hover_color=(130, 130, 150))
        self.btn_mute = Button(0, 0, 180, 45, "Mute All: OFF", self.font_small, color=(60, 60, 80), hover_color=(80, 80, 100))
        
        self.main_buttons = [self.btn_resume, self.btn_settings, self.btn_quit]
        self.settings_buttons = [self.btn_back, self.btn_mute]
        
        self.button_scales = {btn: 1.0 for btn in (self.main_buttons + self.settings_buttons)}
        
        # Volume Slider Rects (Local to modal)
        self.bgm_slider_rect = pygame.Rect(0, 0, 200, 10)
        self.sfx_slider_rect = pygame.Rect(0, 0, 200, 10)
        
    def toggle(self):
        if not self._target_active:
            self.active = True
            self._target_active = True
            self.alpha = 0
            self.view = 'main'
            self.flip_progress = 1.0
            self._is_flipping = False
            self._blurred_bg = None
        else:
            self._target_active = False
            
    def on_resize(self, width, height):
        self.rect.center = (width // 2, height // 2)
        self._blurred_bg = None
        self._reposition_elements()
        
    def _reposition_elements(self):
        cx, cy = self.rect.centerx, self.rect.centery
        
        # Main View
        self.btn_resume.rect.center = (cx, cy - 40)
        self.btn_settings.rect.center = (cx, cy + 30)
        self.btn_quit.rect.center = (cx, cy + 100)
        
        # Settings View
        self.bgm_slider_rect.center = (cx, cy - 60)
        self.sfx_slider_rect.center = (cx, cy + 20)
        self.btn_mute.rect.center = (cx, cy + 90)
        self.btn_back.rect.bottomright = (self.rect.right - 25, self.rect.bottom - 25)

    def update(self, dt):
        self.time_acc += dt
        speed = 10.0
        if self._target_active:
            self.alpha = min(255, self.alpha + speed * 60 * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            if self.alpha <= 0:
                self.active = False

        # Flip Animation
        if self._is_flipping:
            self.flip_progress -= 12 * dt
            if self.flip_progress <= 0:
                self.flip_progress = 0
                self.view = self._next_view
                self._is_flipping = False
        elif self.flip_progress < 1.0:
            self.flip_progress = min(1.0, self.flip_progress + 12 * dt)

        if self.active:
            mouse_pos = pygame.mouse.get_pos()
            current_btns = self.main_buttons if self.view == 'main' else self.settings_buttons
            for btn in current_btns:
                btn.update(mouse_pos, dt)
                target_scale = 1.08 if btn.is_hovered else 1.0
                self.button_scales[btn] += (target_scale - self.button_scales[btn]) * 15 * dt
                
            if self.view == 'settings' and pygame.mouse.get_pressed()[0]:
                self._handle_sliders(mouse_pos)

    def _handle_sliders(self, mouse_pos):
        # Local to world
        if self.bgm_slider_rect.inflate(0, 30).collidepoint(mouse_pos):
            val = (mouse_pos[0] - self.bgm_slider_rect.left) / self.bgm_slider_rect.width
            self.bgm_volume = max(0.0, min(1.0, val))
        elif self.sfx_slider_rect.inflate(0, 30).collidepoint(mouse_pos):
            val = (mouse_pos[0] - self.sfx_slider_rect.left) / self.sfx_slider_rect.width
            self.sfx_volume = max(0.0, min(1.0, val))

    def draw(self, screen, width, height):
        if not self.active: return
        
        # 1. Backdrop
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(screen.copy(), factor=6, tint=(8, 12, 25), tint_alpha=190)

        ease = min(self.alpha / 255.0, 1.0)
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            screen.blit(self._blurred_bg, (0, 0))
        else:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            screen.blit(temp, (0, 0))

        # Modal Scale & Flip
        modal_scale = ease_out_back(ease)
        final_flip = self.flip_progress
        
        self.rect.center = (width // 2, height // 2)
        self._reposition_elements()
        
        # 2. Glassmorphic Modal
        # We calculate the current drawing width based on flip
        draw_w = int(self.rect.w * modal_scale * final_flip)
        draw_h = int(self.rect.h * modal_scale)
        
        if draw_w > 0 and draw_h > 0:
            modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            
            # Glow
            glow_size = 15
            glow_surf = pygame.Surface((self.rect.w + glow_size*2, self.rect.h + glow_size*2), pygame.SRCALPHA)
            glow_alpha = int(40 * ease)
            pygame.draw.rect(glow_surf, (255, 215, 100, glow_alpha), (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=35)
            
            # Scaling Glow
            gs_w = int(glow_surf.get_width() * modal_scale * final_flip)
            gs_h = int(glow_surf.get_height() * modal_scale)
            if gs_w > 0 and gs_h > 0:
                glow_scaled = pygame.transform.smoothscale(glow_surf, (gs_w, gs_h))
                screen.blit(glow_scaled, (width//2 - gs_w//2, height//2 - gs_h//2))

            # Body
            pygame.draw.rect(modal_surf, (20, 25, 45, 240), (0, 0, self.rect.w, self.rect.h), border_radius=30)
            
            # Border
            border_pulse = int(180 + 75 * math.sin(self.time_acc * 3))
            pygame.draw.rect(modal_surf, (255, 215, 0, border_pulse), (0, 0, self.rect.w, self.rect.h), width=3, border_radius=30)
            
            # Content
            if self.view == 'main':
                title_str = "SYSTEM MENU"
            else:
                title_str = "SOUND SETTINGS"
                
            title_surf = self.font_title.render(title_str, True, Colors.TEXT_GOLD)
            modal_surf.blit(title_surf, (self.rect.width//2 - title_surf.get_width()//2, 25))
            
            if self.view == 'settings':
                # Draw Sliders
                self._draw_slider(modal_surf, self.bgm_slider_rect.move(-self.rect.x, -self.rect.y), "BGM Volume", self.bgm_volume)
                self._draw_slider(modal_surf, self.sfx_slider_rect.move(-self.rect.x, -self.rect.y), "SFX Volume", self.sfx_volume)

            # Final Blit with Flip Scaling
            final_modal = pygame.transform.smoothscale(modal_surf, (draw_w, draw_h))
            screen.blit(final_modal, (width//2 - draw_w//2, height//2 - draw_h//2))

        # 3. UI Elements (only when mostly visible and not edge-on)
        if ease > 0.7 and final_flip > 0.5:
            # Close Button
            self.close_btn.center = (self.rect.right - 25, self.rect.top + 25)
            pygame.draw.circle(screen, (220, 40, 40), self.close_btn.center, 22)
            pygame.draw.circle(screen, (255, 255, 255), self.close_btn.center, 22, width=2)
            cross = get_sys_font("Arial", 20, bold=True).render("X", True, (255, 255, 255))
            screen.blit(cross, (self.close_btn.centerx - cross.get_width()//2, self.close_btn.centery - cross.get_height()//2))

            # Buttons
            current_btns = self.main_buttons if self.view == 'main' else self.settings_buttons
            for btn in current_btns:
                s = self.button_scales[btn]
                orig_rect = btn.rect.copy()
                btn.rect.size = (int(orig_rect.w * s), int(orig_rect.h * s))
                btn.rect.center = orig_rect.center
                btn.draw(screen)
                btn.rect = orig_rect

    def _draw_slider(self, surf, rect, label, value):
        # Label
        lbl = self.font_small.render(label, True, (200, 200, 220))
        surf.blit(lbl, (rect.x, rect.y - 25))
        
        # Track
        pygame.draw.rect(surf, (40, 45, 60), rect, border_radius=5)
        
        # Fill
        fill_w = int(rect.w * value)
        if fill_w > 0:
            pygame.draw.rect(surf, Colors.TEXT_GOLD, (rect.x, rect.y, fill_w, rect.h), border_radius=5)
            
        # Knob
        kx = rect.x + fill_w
        pygame.draw.circle(surf, (255, 255, 255), (kx, rect.centery), 10)
        pygame.draw.circle(surf, Colors.TEXT_GOLD, (kx, rect.centery), 10, width=2)
        
        # Percentage
        pct = self.font_small.render(f"{int(value * 100)}%", True, Colors.TEXT_GOLD)
        surf.blit(pct, (rect.right + 10, rect.y - 5))

    def handle_event(self, event, width, height):
        if not self.active or self.alpha < 150 or self._is_flipping: return None
        
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and event.button == 1:
            if self.close_btn.collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.toggle()
                    return "resume"
                return None # Ignore UP for this simple rect
                
        if self.view == 'main':
            if self.btn_resume.is_clicked(event):
                self.toggle()
                return "resume"
            if self.btn_settings.is_clicked(event):
                self._is_flipping = True
                self._next_view = 'settings'
                return "click"
            if self.btn_quit.is_clicked(event):
                self.toggle()
                return "quit"
        else:
            if self.btn_back.is_clicked(event):
                self._is_flipping = True
                self._next_view = 'main'
                return "click"
            if self.btn_mute.is_clicked(event):
                self.is_muted = not self.is_muted
                self.btn_mute.text = f"Mute All: {'ON' if self.is_muted else 'OFF'}"
                self.btn_mute.color = (160, 30, 30) if self.is_muted else (60, 60, 80)
                return "volume_change"
            
            # Slider interaction handled in update via mouse_pressed
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    return "volume_change"
            
        return None
