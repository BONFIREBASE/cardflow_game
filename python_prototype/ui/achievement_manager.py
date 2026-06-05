import os
import json
import time
from ui.paths import get_save_path
from ui.crypto_utils import encrypt_path, decrypt_path

ACHIEVEMENT_FILE = get_save_path("achievements.json")

ACHIEVEMENTS = [
    {"id": "first_match",  "title": "First Steps",      "desc": "Complete your first match",               "icon": "star",     "goal": 1,   "reward": 500,   "type": "match_played"},
    {"id": "first_win",    "title": "First Victory",    "desc": "Win your first game",                      "icon": "trophy",   "goal": 1,   "reward": 1000,  "type": "wins"},
    {"id": "wins_10",      "title": "Rising Star",      "desc": "Win 10 games",                             "icon": "star",     "goal": 10,  "reward": 3000,  "type": "wins"},
    {"id": "wins_50",      "title": "Seasoned Pro",     "desc": "Win 50 games",                             "icon": "star",     "goal": 50,  "reward": 8000,  "type": "wins"},
    {"id": "tongits_win",  "title": "Tong-its Master",  "desc": "Win by Tong-its",                          "icon": "target",   "goal": 1,   "reward": 2000,  "type": "tongits_wins"},
    {"id": "games_100",    "title": "Card Collector",   "desc": "Play 100 games",                           "icon": "medal2",   "goal": 100, "reward": 5000,  "type": "games_played"},
    {"id": "games_500",    "title": "Dedicated",        "desc": "Play 500 games",                           "icon": "medal2",   "goal": 500, "reward": 15000, "type": "games_played"},
    {"id": "streak_3",     "title": "Hot Streak",       "desc": "Win 3 games in a row",                     "icon": "exclamation", "goal": 3, "reward": 2000,  "type": "best_streak"},
    {"id": "streak_7",     "title": "Unstoppable",      "desc": "Win 7 games in a row",                     "icon": "exclamation", "goal": 7, "reward": 10000, "type": "best_streak"},
    {"id": "high_stakes",  "title": "High Roller",      "desc": "Win a match with bet of 1,000+ coins",      "icon": "trophy",   "goal": 1,   "reward": 5000,  "type": "high_stakes_wins"},
    {"id": "ranked_10",    "title": "Ranked Warrior",   "desc": "Win 10 Ranked matches",                    "icon": "target",   "goal": 10,  "reward": 10000, "type": "ranked_wins"},
    {"id": "level_30",     "title": "The Grinder",      "desc": "Reach Level 30",                           "icon": "star",     "goal": 30,  "reward": 5000,  "type": "level"},
    {"id": "level_75",     "title": "Veteran",          "desc": "Reach Level 75",                           "icon": "star",     "goal": 75,  "reward": 15000, "type": "level"},
    {"id": "rank_immortal","title": "Immortal",         "desc": "Reach Immortal rank",                      "icon": "trophy",   "goal": 1,   "reward": 25000, "type": "immortal_rank"},
    {"id": "fight_win",    "title": "Fight Champion",   "desc": "Win a Fight challenge",                    "icon": "target",   "goal": 1,   "reward": 3000,  "type": "fight_wins"},
    {"id": "comeback",     "title": "Phoenix Rising",   "desc": "Win a match after being burned",           "icon": "exclamation", "goal": 1, "reward": 4000,"type": "comeback_wins"},
    {"id": "coins_100k",   "title": "High Net Worth",   "desc": "Earn a total of 100,000 coins",             "icon": "trophy",   "goal": 100000,   "reward": 5000,  "type": "coins_earned"},
    {"id": "coins_1m",     "title": "Millionaire",      "desc": "Earn a total of 1,000,000 coins",           "icon": "trophy",   "goal": 1000000,  "reward": 50000, "type": "coins_earned"},
]

class AchievementManager:
    def __init__(self):
        self.progress = self._load()

    def _default_progress(self):
        return {
            "wins": 0,
            "games_played": 0,
            "tongits_wins": 0,
            "best_streak": 0,
            "current_streak": 0,
            "high_stakes_wins": 0,
            "ranked_wins": 0,
            "level": 1,
            "has_immortal_rank": False,
            "fight_wins": 0,
            "comeback_wins": 0,
            "coins_earned": 0,
            "claimed": [],
            "unlocked": []
        }

    def _load(self):
        if os.path.exists(ACHIEVEMENT_FILE):
            try:
                decrypt_path(ACHIEVEMENT_FILE)
                with open(ACHIEVEMENT_FILE, "r") as f:
                    data = json.load(f)
                encrypt_path(ACHIEVEMENT_FILE)
                prog = self._default_progress()
                prog.update(data)
                return prog
            except:
                return self._default_progress()
        return self._default_progress()

    def save(self):
        try:
            with open(ACHIEVEMENT_FILE, "w") as f:
                json.dump(self.progress, f, indent=2)
            encrypt_path(ACHIEVEMENT_FILE)
        except Exception as e:
            print(f"Error saving achievements: {e}")

    def get_unclaimed_count(self):
        count = 0
        for ach in ACHIEVEMENTS:
            if ach["id"] in self.progress["unlocked"] and ach["id"] not in self.progress["claimed"]:
                count += 1
        return count

    def check_and_unlock(self):
        anything_new = False
        for ach in ACHIEVEMENTS:
            if ach["id"] in self.progress["unlocked"]:
                continue
            if self._is_achieved(ach):
                self.progress["unlocked"].append(ach["id"])
                anything_new = True
        if anything_new:
            self.save()
        return anything_new

    def _is_achieved(self, ach):
        t = ach["type"]
        goal = ach["goal"]
        if t == "match_played":
            return self.progress["games_played"] >= goal
        elif t == "wins":
            return self.progress["wins"] >= goal
        elif t == "games_played":
            return self.progress["games_played"] >= goal
        elif t == "tongits_wins":
            return self.progress["tongits_wins"] >= goal
        elif t == "best_streak":
            return self.progress["best_streak"] >= goal
        elif t == "high_stakes_wins":
            return self.progress["high_stakes_wins"] >= goal
        elif t == "ranked_wins":
            return self.progress["ranked_wins"] >= goal
        elif t == "level":
            return self.progress["level"] >= goal
        elif t == "immortal_rank":
            return self.progress["has_immortal_rank"]
        elif t == "fight_wins":
            return self.progress["fight_wins"] >= goal
        elif t == "comeback_wins":
            return self.progress["comeback_wins"] >= goal
        elif t == "coins_earned":
            return self.progress["coins_earned"] >= goal
        return False

    def get_achievement_progress(self, ach_id):
        for ach in ACHIEVEMENTS:
            if ach["id"] == ach_id:
                t = ach["type"]
                goal = ach["goal"]
                if t == "match_played":
                    return min(self.progress["games_played"], goal), goal
                elif t == "wins":
                    return min(self.progress["wins"], goal), goal
                elif t == "games_played":
                    return min(self.progress["games_played"], goal), goal
                elif t == "tongits_wins":
                    return min(self.progress["tongits_wins"], goal), goal
                elif t == "best_streak":
                    return min(self.progress["best_streak"], goal), goal
                elif t == "high_stakes_wins":
                    return min(self.progress["high_stakes_wins"], goal), goal
                elif t == "ranked_wins":
                    return min(self.progress["ranked_wins"], goal), goal
                elif t == "level":
                    return min(self.progress["level"], goal), goal
                elif t == "immortal_rank":
                    return (1, 1) if self.progress["has_immortal_rank"] else (0, 1)
                elif t == "fight_wins":
                    return min(self.progress["fight_wins"], goal), goal
                elif t == "comeback_wins":
                    return min(self.progress["comeback_wins"], goal), goal
                elif t == "coins_earned":
                    return min(self.progress["coins_earned"], goal), goal
        return (0, 1)

    def claim(self, ach_id):
        if ach_id in self.progress["unlocked"] and ach_id not in self.progress["claimed"]:
            self.progress["claimed"].append(ach_id)
            self.save()
            for ach in ACHIEVEMENTS:
                if ach["id"] == ach_id:
                    return ach["reward"]
        return 0

    def update_stat(self, stat, value):
        if stat == "streak":
            self.progress["current_streak"] = value
            self.progress["best_streak"] = max(self.progress["best_streak"], value)
        else:
            if isinstance(self.progress.get(stat), int):
                self.progress[stat] += value

        if stat == "wins" or stat == "games_played":
            self.check_and_unlock()
