from .models import Meld, TurnPhase
from itertools import combinations
import random


class RuleBasedAI:
    """
    Rule-based AI for Filipino Tong-its.

    Priority order:
    1. Draw (prefer deck; draw from discard only if it completes a meld)
    2. Drop all available melds to avoid being burned
    3. If drew from discard, MUST meld the drawn card first
    4. Sapaw onto table melds to reduce hand points
    5. Consider calling fight if hand points are low
    6. Discard the most strategic card
    """

    @staticmethod
    def take_turn(engine, player):
        """Execute a complete AI turn following Tong-its rules."""
        if engine.is_game_over:
            return

        # Special case: banker's/dealer's initial turn (13 cards, no draw)
        if engine.is_dealer_initial_discard:
            RuleBasedAI._do_banker_initial_turn(engine, player)
            return

        # ── Phase 0: INITIAL ACTIONS (Fight/Sapaw) ────────────────
        if RuleBasedAI._should_call_fight(engine, player):
            # Calculate a "confidence score" before calling
            if random.random() < 0.85: # 15% chance to hesitate/wait
                engine.call_fight(player)
                return

        # Sapaw pre-draw is allowed! Reducing hand points early helps with fight decisions later
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return

        # ── Phase 1: DRAW ─────────────────────────────────────────
        RuleBasedAI._do_draw(engine, player)
        if engine.is_game_over:
            return

        # ── Phase 2: FORCED MELD (if drew from discard) ───────────
        if player.forced_meld_card is not None:
            RuleBasedAI._do_forced_meld(engine, player)
            if engine.is_game_over:
                return

        # ── Phase 3: DROP OTHER MELDS ─────────────────────────────
        RuleBasedAI._do_melds(engine, player)
        if engine.is_game_over:
            return

        # ── Phase 4: SAPAW ──────────────────────────────────────
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return

       
    
        RuleBasedAI._do_discard(engine, player)

    # ─── Dealer Initial Discard ──────────────────────────────────────

    @staticmethod
    def _do_banker_initial_turn(engine, player):
        """Banker's first action: meld/sapaw then discard to start the pile."""
        # The banker already has 13 cards (effectively "drawn")
        
        # Phase 1: Try melds
        RuleBasedAI._do_melds(engine, player)
        if engine.is_game_over:
            return
            
        # Phase 2: Try sapaw (rare at start)
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return
            
        # Phase 3: Discard to end turn
        card = RuleBasedAI._choose_discard(engine, player)
        engine.dealer_initial_discard(card)

    # ─── Draw Logic ──────────────────────────────────────────────────

    @staticmethod
    def _do_draw(engine, player):
        """
        Decide whether to draw from closed pile or discard pile.
        Smart logic: Passing on a discard pickup if planning to Fight.
        """
        if engine.discard_pile:
            top_discard = engine.discard_pile[-1]
            if engine._can_meld_with_discard(player, top_discard):
                # STRATEGIC CHECK:
                # If we have very low points (< 10), we might want to FIGHT this turn.
                # Drawing from discard PREVENTS fighting. 
                # So if points are low, we skip the discard and draw from deck to fight.
                if player.calculate_points() <= 10 and engine.can_player_fight(player):
                    # Skip discard, drawing from deck allows CALLING FIGHT immediately after
                    pass 
                else:
                    success = engine.draw_from_discard(player)
                    if success:
                        return

        # Default: draw from closed pile
        engine.draw_from_deck(player)

    # ─── Forced Meld (after drawing from discard) ────────────────────

    @staticmethod
    def _do_forced_meld(engine, player):
        """Must meld the card drawn from the discard pile."""
        forced = player.forced_meld_card
        if forced is None:
            return

        # Find a meld containing the forced card
        for size in range(3, len(player.hand) + 1):
            for combo in combinations(player.hand, size):
                cards = list(combo)
                if forced in cards:
                    mtype = Meld.get_meld_type(cards)
                    if mtype:
                        engine.drop_meld(player, cards)
                        return

    # ─── Meld Detection & Dropping ───────────────────────────────────

    @staticmethod
    def _find_best_melds(player):
        """Find the best non-overlapping set of melds to drop."""
        all_melds = []
        hand = player.hand[:]

        for size in range(3, len(hand) + 1):
            for combo in combinations(hand, size):
                cards = list(combo)
                mtype = Meld.get_meld_type(cards)
                if mtype:
                    points = sum(c.value for c in cards)
                    all_melds.append((cards, mtype, points))

        all_melds.sort(key=lambda m: m[2], reverse=True)

        selected = []
        used_cards = set()
        for cards, mtype, points in all_melds:
            card_set = set(id(c) for c in cards)
            if not card_set & used_cards:
                selected.append((cards, mtype))
                used_cards |= card_set

        return selected

    @staticmethod
    def _do_melds(engine, player):
        """Drop all available melds."""
        melds_to_drop = RuleBasedAI._find_best_melds(player)
        for cards, mtype in melds_to_drop:
            if all(c in player.hand for c in cards):
                engine.drop_meld(player, cards)
                if engine.is_game_over:
                    return

    # ─── Sapaw Logic ─────────────────────────────────────────────────

    @staticmethod
    def _do_sapaw(engine, player):
        """Sapaw onto any available table meld to reduce hand points."""
        changed = True
        while changed:
            changed = False
            options = engine.get_sapaw_options(player)
            if not options:
                break

            # Prioritize sapaw-ing highest value cards
            options.sort(key=lambda o: o[0].value, reverse=True)
            for card, meld in options:
                if card in player.hand:
                    success = engine.sapaw(player, card, meld)
                    if success:
                        changed = True
                        if engine.is_game_over:
                            return

    # ─── Fight Decision ──────────────────────────────────────────────

    @staticmethod
    def _should_call_fight(engine, player):
        """
        Decide whether to call fight based on hand points, deck size, and opponent status.
        Uses a more aggressive 'Tong-its' playstyle.
        """
        if not engine.can_player_fight(player):
            return False

        points = player.calculate_points()
        deck_remaining = engine.deck.remaining()
        
        # 1. Immediate Win: extremely low points
        if points <= 5:
            return True
            
        # 2. Aggressive Late Game: If deck is running low
        if deck_remaining < 10 and points <= 15:
            return True

        # 3. Stratregic Mid-Game:
        # Check if we have significantly lower points than likely opponents
        avg_opponent_cards = sum(p.card_count() for p in engine.players if p != player) / 2
        
        # If we have very few cards (e.g. 3-4) and points are decent (e.g. < 10)
        if player.card_count() <= 5 and points <= 10:
            # If opponents have many cards (e.g. > 8), they likely have high points
            if avg_opponent_cards > player.card_count() + 3:
                return True

        # 4. Burned status check:
        # If someone is burned, our chances increase since they can't challenge
        burned_count = sum(1 for p in engine.players if p != player and p.is_burned)
        if burned_count >= 1 and points <= 12:
            return True

        return False

    @staticmethod
    def _should_respond_fight(engine, player, fight_context):
        """Decide whether to fight (challenge) or fold."""
        caller = fight_context['caller']
        points = player.calculate_points()
        
        # Never challenge if burned
        if player.is_burned:
            return 'fold'
            
        # Challenge if we have lower or equal points than we think the caller has
        # Heuristic: caller likely has < 15 points
        if points <= 5:
            return 'fight' # Extreme confidence
            
        if points > 20:
            return 'fold' # Extreme caution
            
        # Compare card counts as proxy for points
        if player.card_count() < caller.card_count():
            return 'fight'
            
        if player.card_count() == caller.card_count():
            # If same card count, it's a toss up, but favor fighting if points are decent
            return 'fight' if points <= 12 else 'fold'
            
        # If we have more cards, usually safer to fold unless points are very low
        return 'fight' if points <= 8 else 'fold'

    # ─── Discard Logic ───────────────────────────────────────────────

    @staticmethod
    def _do_discard(engine, player):
        """Discard the most strategic card."""
        if not player.hand:
            return
        card_to_discard = RuleBasedAI._choose_discard(engine, player)
        engine.discard_card(player, card_to_discard)

    @staticmethod
    def _choose_discard(engine, player):
        """
        Smart discard selection:
        - Penalizes cards that are 'connected' or part of potential melds.
        - Prioritizes high value cards if they are 'garbage'.
        - Checks for opponent sapaw safety.
        """
        hand = player.hand[:]
        if not hand: return None
        if len(hand) == 1: return hand[0]

        scores = {}
        for card in hand:
            # Baseline: higher value = better to discard
            score = card.value * 2 
            
            # 1. Penalty: Part of a full meld (Highest priority to keep)
            is_in_meld = False
            for combo in combinations(hand, 3):
                if card in combo and Meld.is_valid_meld(list(combo)):
                    is_in_meld = True
                    break
            if is_in_meld: score -= 100

            # 2. Penalty: Connectivity (Potential melds)
            # Check for pairs or near-runs
            connections = 0
            for other in hand:
                if card == other: continue
                # Same rank
                if card.rank == other.rank: connections += 20
                # Same suit, near rank
                if card.suit == other.suit:
                    from .models import RANK_ORDER
                    r1 = RANK_ORDER.index(card.rank)
                    r2 = RANK_ORDER.index(other.rank)
                    if abs(r1 - r2) == 1: connections += 15 # Consecutive
                    if abs(r1 - r2) == 2: connections += 10 # Gap of one

            score -= connections

            # 3. Penalty: Avoid giving opponents a sapaw
            for tmeld in engine.table_melds:
                if tmeld.owner != player and tmeld.can_sapaw(card):
                    score -= 30 # Heavy penalty: don't help others reduce points

            # 4. Bonus: Discarding dangerous high cards early
            if card.value == 10 and engine.deck.remaining() > 30:
                score += 5 # Get rid of Jacks/Queens/Kings early if not connected

            scores[id(card)] = (score, card)

        # Pick the highest score (the card we want to lose most)
        best_id = max(scores, key=lambda cid: scores[cid][0])
        return scores[best_id][1]
