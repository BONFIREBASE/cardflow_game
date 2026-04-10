# Mama's Go - Tong-its Implementation Plan

This document outlines the implementation plan for the "Mama's Go" Tong-its card game. The project will initially be developed as a Pure Python prototype using Pygame for local testing and logic refinement, with the ultimate goal of porting the core logic to Flutter for mobile release.

## Goal Description
Build the core mechanics of a 3-player "Tong-its" card game in Python using Pygame. The app will be strictly localized to landscape mode, utilize local assets for cards and fonts, and feature a pixel-art style background. The primary focus for this phase is locking down the core game logic, engine cycle, and rendering utilizing a dedicated Python environment.

> [!NOTE]
> Tong-its is a 3-player rummy-style card game where players draw and discard cards to form sets and runs, and minimize their unmatched cards.

## Proposed Changes

### Core Setup & Assets
1. **Python Initialization**
   - Initialize a new Python project in `c:\Users\Project\mama's_go\python_prototype\`.
   - Install dependencies: `pip install pygame`.
2. **Asset Organization**
   - Utilize existing `cards-assets` and map paths properly.
   - Utilize existing fonts (`Inter`, `JetBrains_Mono`, `Sora`).
   - Utilize the AI-generated `pixel_table_background.png`.
   - Assets can be symlinked or copied into a `python_prototype/assets/` folder to prevent cluttering the root directory.

### Game Logic Layer (`python_prototype/game/`)
1. **Models (`models.py`)**
   - `Card`: Suit, rank, value (for counting points).
   - `Deck`: Mechanics for shuffling and dealing.
   - `Player`: Hand, melds (lapag), points structure, player status (e.g., burned, secret melds).
   - `Meld`: Logic for validating sets (3+ same rank) and runs/straight flushes (3+ consecutive same suit).
2. **Game Engine (`engine.py`)**
   - **Initialization**: Deal 12 cards to the dealer (starts first) and 11 cards to the other 2 players. Place the rest into the Draw Pile. Flip one card to the Discard Pile.
   - **Turn Cycle**:
     - *Draw Phase*: Draw from the Draw Pile OR pick up the top Discard Pile card (if validating a meld).
     - *Meld Phase* (Optional): Drop valid melds ("lapag") or connect to other players' melds ("sapaw").
     - *Action Phase*: Declare "Fight" (if conditions met) or "Tong-its" (if hand is empty).
     - *Discard Phase*: Discard exactly one card to the Discard pile to end the turn.
   - **Win Conditions**:
     - *Tong-its*: Emptying the hand.
     - *Fight (Draw)*: Lowest points wins when someone calls a fight (Draw).
     - *Deck Empty*: Lowest points wins when the draw pile runs out.
   - **Burn Logic**: A player is "burned" (cannot win a fight) if they have not dropped any meld and a fight is called or deck runs out.
3. **AI Opponents (`ai_bot.py`)**
   - Implement a basic rule-based AI state machine:
     - Priority 1: Drop melds (Sets/Runs) if available to avoid being "Burned".
     - Priority 2: Attempt to "Sapaw" (connect) on existing melds.
     - Priority 3: Discard the highest value un-melded card.

### UI / Presentation Layer (`python_prototype/ui/`)
1. **Game Board Rendering (`main.py` / Pygame Loop)**
   - **Landscape Layout**: Pygame window locked at a standard landscape resolution (e.g., 1280x720). Render `pixel_table_background.png` appropriately scaled.
   - **Player Hands**: Interactive clickable bottom center for the main player, static back-of-cards top-left and top-right for opponent bots.
   - **Center Table**: Draw pile, discard pile face up, and bounding box areas for dropped melds.

## Verification Plan

### Core Logic Module Tests
- Standalone execution of `engine.py` without UI to verify card dealing, meld validation (sets/runs), and scoring logic (face cards = 10, Ace = 1, etc.).

### Manual UI Verification
- Run `main.py` locally and visually check Pygame layout constraints.
- Test player mouse interaction with cards (selecting, discarding, dropping melds).
- Observe complete game loops driven by the basic rule-based AI opponents.
