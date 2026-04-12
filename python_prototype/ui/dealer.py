import os
import random
import pygame
import math

class DealerManager:
    """Manages dealer state with smooth animated movement and minimalist breathing."""
    def __init__(self, assets_dir):
        self.dealer_idx = 0
        self.win_streak = 0
        self.chip_image = None
        
        # Animated properties
        self.pos = [0.0, 0.0]
        self.target_pos = [0.0, 0.0]
        self.rotation = 0.0
        self.is_first_draw = True
        
        self._load_assets(assets_dir)

    def _load_assets(self, assets_dir):
        path = os.path.join(assets_dir, "Casino", "Chips", "Dealer.png")
        try:
            raw = pygame.image.load(path).convert_alpha()
            self.chip_image = pygame.transform.smoothscale(raw, (42, 42))
        except Exception as e:
            print(f"Error loading dealer chip: {e}")
            self.chip_image = None

    def update(self, dt, target_x=None, target_y=None):
        """Smoothly moves the chip toward the target position and handles rotation."""
        if target_x is not None and target_y is not None:
            self.target_pos = [target_x, target_y]
            if self.is_first_draw:
                self.pos = [target_x, target_y]
                self.is_first_draw = False

        # Ease position toward target (Minimalist smooth glide)
        speed = 10.0
        self.pos[0] += (self.target_pos[0] - self.pos[0]) * speed * dt
        self.pos[1] += (self.target_pos[1] - self.pos[1]) * speed * dt

        # Update base rotation (very slow idle spin)
        self.rotation = (self.rotation + 45 * dt) % 360

    def randomize(self):
        self.dealer_idx = random.randint(0, 2)
        self.win_streak = 0
        return self.dealer_idx

    def rotate(self):
        self.dealer_idx = (self.dealer_idx + 1) % 3
        self.win_streak = 0
        return self.dealer_idx

    def get_idx(self):
        return self.dealer_idx

    def set_idx(self, idx):
        """Update dealer based on winner. Tracks consecutive wins."""
        if self.dealer_idx == idx:
            # Current dealer won again! Trigger "Hitter" animation
            self.win_streak += 1
        else:
            # Dealer changed. Reset streak to 0 (normal chip)
            self.dealer_idx = idx
            self.win_streak = 0 
        return self.dealer_idx

    def draw(self, surface):
        """Draw the dealer chip with a literal minimalist 'breathing' animation for hitters."""
        if not self.chip_image:
            return

        cx, cy = self.pos
        cw, ch = self.chip_image.get_size()
        ticks = pygame.time.get_ticks()
        
        # ── BREATHING LOGIC ──
        # Triggers only if the player has won at least once while being dealer
        is_hitter = (self.win_streak >= 1)
        
        if is_hitter:
            # Literal breathing: smooth scale pulse
            # Range: 1.0 to 1.3
            breath = (math.sin(ticks * 0.006) + 1.0) / 2.0 # 0.0 to 1.0
            scale = 1.0 + (0.30 * breath)
            
            s_w, s_h = int(cw * scale), int(ch * scale)
            curr_chip = pygame.transform.smoothscale(self.chip_image, (s_w, s_h))
            rw, rh = curr_chip.get_size()
            dx = cx - (rw - cw) // 2
            dy = cy - (rh - ch) // 2
        else:
            curr_chip = self.chip_image
            rw, rh = cw, ch
            dx, dy = cx, cy

        # 1. Minimalist Shadow (Static for stability)
        shadow_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 40), (rw//2, rh//2), rw//4)
        surface.blit(shadow_surf, (dx + 2, dy + 2))

        # 2. Base Chip (No rotation, no extra effects)
        surface.blit(curr_chip, (dx, dy))

    def get_deal_sequence(self):
        others = [(self.dealer_idx + 1) % 3, (self.dealer_idx + 2) % 3]
        round_order = others + [self.dealer_idx]
        sequence = []
        for _ in range(12):
            sequence.extend(round_order)
        sequence.append(self.dealer_idx)
        return sequence
