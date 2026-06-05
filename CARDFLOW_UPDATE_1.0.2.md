# 🎴 Cardflow Update 1.0.2: The Achievement Patch

> **Version:** 1.0.2  
> **Status:** Live  
> **Region:** Philippines  

---

## 🏆 Major Feature: Achievement System

A full-featured **Achievement System** has been introduced, giving players 18 unique milestones to chase across every aspect of the game.

### How It Works
*   Achievements are **tracked automatically** as you play — wins, streaks, levels, and more.
*   Unlocked achievements can be **claimed for coin rewards** directly from the new Achievements modal.
*   All progress is **encrypted and persisted** locally using the existing HMAC-secured save system.

### All 18 Achievements

| Achievement | Goal | Reward |
| :--- | :--- | :--- |
| **First Steps** | Complete your first match | 500 |
| **First Victory** | Win your first game | 1,000 |
| **Rising Star** | Win 10 games | 3,000 |
| **Seasoned Pro** | Win 50 games | 8,000 |
| **Tong-its Master** | Win by Tong-its | 2,000 |
| **Card Collector** | Play 100 games | 5,000 |
| **Dedicated** | Play 500 games | 15,000 |
| **Hot Streak** | Win 3 games in a row | 2,000 |
| **Unstoppable** | Win 7 games in a row | 10,000 |
| **High Roller** | Win a 1,000+ coin bet match | 5,000 |
| **Ranked Warrior** | Win 10 Ranked matches | 10,000 |
| **The Grinder** | Reach Level 30 | 5,000 |
| **Veteran** | Reach Level 75 | 15,000 |
| **Immortal** | Reach Immortal rank | 25,000 |
| **Fight Champion** | Win a Fight challenge | 3,000 |
| **Phoenix Rising** | Win after being burned | 4,000 |
| **High Net Worth** | Earn 100,000 total coins | 5,000 |
| **Millionaire** | Earn 1,000,000 total coins | 50,000 |

---

## 🎨 UI & Lobby Enhancements

### New: Achievement Button in Lobby
*   A new **star-icon button** has been added to the lobby's bottom-right toolbar, next to the existing History and Quest buttons.
*   Features a **pulsing notification badge** that shows the number of unclaimed achievement rewards — drawing the player's attention when rewards are waiting.
*   Hover effects with icon color swap (white ↔ black) for a polished feel.

### Achievement Modal
*   Premium dark-themed scrollable modal with **gold accent borders** and the **Sekuya** title font.
*   Each achievement is displayed as a card showing:
    - Icon, title, and description
    - A **progress bar** with current / goal tracking
    - Reward amount and a **CLAIM button** (gold, animated) for unlocked achievements
    - Green "CLAIMED" badge for already-collected rewards
*   Smooth **bounce-in animation** on open, with blurred background overlay.
*   Mousewheel scrolling support.

### Lobby Keyboard Hints
*   A new subtle hint bar at the bottom center of the lobby: `ESC = Pause | ClickAvatar = Profile`.

---

## 📊 Profile & Stats Integration

### Profile Modal Update
*   The Profile Modal now displays an **ACHIEVEMENTS** stat card (e.g., `3/18`) alongside existing stats like Wins, Losses, Streak, and Level.
*   Modal height increased from 600px → 650px to accommodate the new row.

---

## ⚙️ Match Result Integration

### Post-Match Achievement Tracking
After every match, the system now automatically updates the following achievement stats:
*   `games_played` — incremented every match
*   `wins` — incremented on victory
*   `tongits_wins` — tracked on Tong-its victories
*   `high_stakes_wins` — tracked for bets ≥ 1,000 coins
*   `ranked_wins` — tracked for ranked victories
*   `comeback_wins` — tracked when winning after being burned
*   `fight_wins` — tracked for Fight-method victories
*   `coins_earned` — accumulated from match payouts
*   `streak` — current win streak synced from player stats
*   `level` — synced from updated profile
*   `has_immortal_rank` — flagged when Immortal rank is achieved

### Reward Claiming Flow
*   Claimed rewards are **instantly credited** to the player's coin balance.
*   A **floating coin notification** animates from center-screen to the coin counter in the lobby HUD.
*   A sound effect plays on claim for satisfying feedback.

---

## 🛠️ Technical Summary

| Area | Files Changed | Lines Added |
| :--- | :--- | :--- |
| Achievement Engine | `achievement_manager.py` [NEW] | 172 |
| Achievement UI | `achievement_modal.py` [NEW] | 268 |
| Lobby Integration | `lobby.py` | +55 |
| Main Game Loop | `main.py` | +47 |
| Match Result Hook | `match_result.py` | +25 |
| Profile Stats | `profile.py` | +10 |
| **Total** | **6 files** | **+565 lines** |

---

> [!IMPORTANT]
> This update is backward-compatible with v1.0.1 save data. Achievement progress will begin tracking from your existing profile stats (wins, level, rank) on first launch. No profile reset is required.
