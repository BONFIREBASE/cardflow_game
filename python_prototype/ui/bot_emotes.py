"""Bot emote system.

Makes the rule-based bots feel alive by reacting to their own moves with
little icon "speech bubbles". The bot AI does NOT make any decision based on
emotes -- this is a pure presentation layer:

    bot logic decides an action  ->  emits an action label here  ->
    this manager picks a context-aware icon and pops a bubble above the avatar.

Emote choice & frequency are driven by the bot's difficulty and how its move
went, so HARD/ELITE bots taunt more and reactions actually match the situation.
"""

import os
import math
import random

import pygame

from ui.paths import get_resource_path
from .animation import ease_out_back


# Semantic emote key -> icon filename (from assets/game_icons/PNG/White/2x)
_EMOTE_ICONS = {
    "think":      "question.png",
    "happy":      "trophy.png",
    "confident":  "medal1.png",
    "taunt":      "target.png",
    "frustrated": "warning.png",
    "sad":        "exclamation.png",
    "star":       "star.png",
}

# How chatty each difficulty is (base chance to emote on a routine move).
# "Big moment" actions (like calling a fight) ignore this and always show.
_TALKATIVENESS = {
    "EASY":      0.10,
    "MEDIUM":    0.20,
    "HARD":      0.34,
    "ELITE":     0.42,
    "LEGENDARY": 0.50,
}

# Per-bot cooldown so they don't spam bubbles every single tick.
_COOLDOWN = 2.8


class _Emote:
    """A single active bubble with pop-in / hold / fade-out animation."""

    def __init__(self, icon, lifetime=2.2):
        self.icon = icon
        self.t = 0.0
        self.lifetime = lifetime

    def update(self, dt):
        self.t += dt
        return self.t < self.lifetime


class EmoteManager:
    """Holds and renders the bots' reaction bubbles."""

    def __init__(self, icon_size=30):
        self.icon_size = icon_size
        self.icons = self._load_icons(icon_size)
        self.active = {}     # bot_idx -> _Emote
        self.cooldown = {}   # bot_idx -> seconds remaining before next routine emote

    def _load_icons(self, size):
        icons = {}
        base = get_resource_path(
            os.path.join("assets", "game_icons", "PNG", "White", "2x")
        )
        for key, fname in _EMOTE_ICONS.items():
            try:
                img = pygame.image.load(os.path.join(base, fname)).convert_alpha()
                icons[key] = pygame.transform.smoothscale(img, (size, size))
            except Exception:
                icons[key] = None
        return icons

    # ── lifecycle ────────────────────────────────────────────────────────────

    def clear(self):
        self.active.clear()
        self.cooldown.clear()

    def update(self, dt):
        for idx in list(self.cooldown.keys()):
            self.cooldown[idx] = max(0.0, self.cooldown[idx] - dt)
        for idx in list(self.active.keys()):
            if not self.active[idx].update(dt):
                del self.active[idx]

    # ── triggering ─────────────────────────────────────────────────────────--

    def _difficulty(self, player):
        d = getattr(player, "difficulty", "MEDIUM") or "MEDIUM"
        return d.upper()

    def _show(self, bot_idx, key, lifetime=2.2, set_cooldown=True):
        if key not in self.icons:
            return
        self.active[bot_idx] = _Emote(self.icons.get(key), lifetime)
        if set_cooldown:
            self.cooldown[bot_idx] = _COOLDOWN

    def react(self, bot_idx, action, player=None, engine=None):
        """Called by the bot executor right after a bot performs an action.

        action is one of:
            'draw_deck', 'draw_discard', 'meld', 'sapaw', 'fight', 'discard'
        """
        diff = self._difficulty(player) if player else "MEDIUM"

        # Calling a fight is always a dramatic moment -> always emote, taunt-heavy.
        if action == "fight":
            self._show(bot_idx, random.choice(["taunt", "confident", "star"]), lifetime=2.4)
            return

        # Routine moves are gated by talkativeness + cooldown.
        if self.cooldown.get(bot_idx, 0.0) > 0.0:
            return
        chance = _TALKATIVENESS.get(diff, 0.20)

        # Good things that happened on this move bias toward positive emotes and
        # are a bit more likely to be shown.
        if action == "meld":
            if random.random() < chance + 0.20:
                self._show(bot_idx, random.choice(["happy", "confident", "star"]))
        elif action == "sapaw":
            if random.random() < chance + 0.15:
                self._show(bot_idx, random.choice(["taunt", "confident"]))
        elif action == "draw_discard":
            # Grabbing from the discard pile usually means it helped their hand.
            if random.random() < chance + 0.05:
                self._show(bot_idx, random.choice(["confident", "happy"]))
        elif action == "draw_deck":
            if random.random() < chance:
                self._show(bot_idx, "think")
        elif action == "discard":
            # Was it forced to throw away a strong card? Read its hand strength.
            forced = self._hand_looks_weak(player, engine)
            if forced and random.random() < chance + 0.10:
                self._show(bot_idx, random.choice(["frustrated", "sad"]))
            elif random.random() < chance * 0.5:
                self._show(bot_idx, "think")

    def _hand_looks_weak(self, player, engine):
        """Rough read on whether the bot is in a bad spot (for frustrated emotes)."""
        if not player:
            return False
        try:
            # No melds dropped yet and still holding a full-ish hand late = weak.
            no_melds = len(getattr(player, "melds", [])) == 0
            many_cards = player.card_count() >= 9
            return no_melds and many_cards and random.random() < 0.5
        except Exception:
            return False

    # ── rendering ────────────────────────────────────────────────────────────

    def draw(self, surface, positions):
        """positions: {bot_idx: (anchor_cx, anchor_bottom_y)}.

        The bubble's tail points down to (anchor_cx, anchor_bottom_y), so pass
        the top-center of the bot panel.
        """
        for bot_idx, em in self.active.items():
            pos = positions.get(bot_idx)
            if not pos:
                continue
            self._draw_bubble(surface, pos[0], pos[1], em)

    def _draw_bubble(self, surface, anchor_cx, anchor_bottom_y, em):
        life_p = em.t / em.lifetime

        # Pop-in scale (first 0.18s) with a slight overshoot, fade-out at the end.
        if em.t < 0.18:
            scale = max(0.0, ease_out_back(em.t / 0.18))
        else:
            scale = 1.0
        if life_p > 0.80:
            alpha = int(255 * max(0.0, 1.0 - (life_p - 0.80) / 0.20))
        else:
            alpha = 255

        bob = math.sin(em.t * 4.0) * 3.0  # gentle hover

        pad = 10
        size = self.icon_size
        bw = size + pad * 2
        bh = size + pad * 2
        tail_h = 9

        bubble = pygame.Surface((bw, bh + tail_h), pygame.SRCALPHA)

        # Rounded bubble body
        pygame.draw.rect(bubble, (22, 26, 40, 235), (0, 0, bw, bh), border_radius=16)
        pygame.draw.rect(bubble, (255, 215, 110, 180), (0, 0, bw, bh), width=2, border_radius=16)
        # Little downward tail
        cx = bw // 2
        pygame.draw.polygon(
            bubble, (22, 26, 40, 235),
            [(cx - 8, bh - 2), (cx + 8, bh - 2), (cx, bh + tail_h)],
        )

        icon = em.icon
        if icon:
            bubble.blit(icon, (pad, pad))

        # Scale for the pop-in, then place so the tail tip sits on the anchor.
        full_w, full_h = bubble.get_size()
        sw = max(1, int(full_w * scale))
        sh = max(1, int(full_h * scale))
        scaled = pygame.transform.smoothscale(bubble, (sw, sh))
        if alpha < 255:
            scaled.set_alpha(alpha)

        draw_x = int(anchor_cx - sw / 2)
        draw_y = int(anchor_bottom_y - sh - 6 + bob)
        surface.blit(scaled, (draw_x, draw_y))
