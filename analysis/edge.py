"""
edge.py — Calculates betting edge vs. market moneyline odds.

Converts our model's win probability to an implied moneyline,
then compares it to the market's implied probability to find edge.

Edge% = (our_probability - market_implied_probability) × 100

A positive edge means we think the team is more likely to win
than the market implies — a potential value bet.
"""

EDGE_THRESHOLD = 5.0  # Minimum edge % to flag as a value bet


def calculate_edge(home_win_prob: float, away_win_prob: float,
                   home_moneyline: int = None, away_moneyline: int = None) -> dict:
    """
    Calculates edge for both teams.

    If no market moneyline is provided, uses the model's own probabilities
    to generate a fair-value line (edge will be 0 in that case).

    Args:
        home_win_prob: Model's estimated home win probability (0-1)
        away_win_prob: Model's estimated away win probability (0-1)
        home_moneyline: Market moneyline for home team (e.g. -150, +130)
        away_moneyline: Market moneyline for away team

    Returns dict with edge calculations and BET/NO BET recommendations.
    """
    # Our model's implied moneylines
    our_home_ml = prob_to_moneyline(home_win_prob)
    our_away_ml = prob_to_moneyline(away_win_prob)

    # Market implied probabilities (use our line if no market line provided)
    if home_moneyline is not None:
        market_home_prob = moneyline_to_prob(home_moneyline)
        market_away_prob = moneyline_to_prob(
            away_moneyline) if away_moneyline else 1 - market_home_prob
        market_home_ml = home_moneyline
        market_away_ml = away_moneyline or prob_to_moneyline(market_away_prob)
    else:
        # No market line — use fair value (edge = 0, just show the math)
        market_home_prob = home_win_prob
        market_away_prob = away_win_prob
        market_home_ml = our_home_ml
        market_away_ml = our_away_ml

    # Remove vig from market probabilities (normalize so they sum to 1)
    total_market_prob = market_home_prob + market_away_prob
    market_home_prob_no_vig = market_home_prob / total_market_prob
    market_away_prob_no_vig = market_away_prob / total_market_prob

    # Edge calculations
    home_edge = (home_win_prob - market_home_prob_no_vig) * 100
    away_edge = (away_win_prob - market_away_prob_no_vig) * 100

    # Expected value per $100 bet
    home_ev = _expected_value(home_win_prob, market_home_ml)
    away_ev = _expected_value(away_win_prob, market_away_ml)

    return {
        'home': {
            'our_win_prob': round(home_win_prob, 4),
            'our_win_pct': round(home_win_prob * 100, 1),
            'our_implied_ml': our_home_ml,
            'market_ml': market_home_ml,
            'market_implied_prob': round(market_home_prob_no_vig, 4),
            'market_implied_pct': round(market_home_prob_no_vig * 100, 1),
            'edge_pct': round(home_edge, 2),
            'expected_value_per_100': round(home_ev, 2),
            'recommendation': _recommendation(home_edge),
            'is_value_bet': home_edge >= EDGE_THRESHOLD,
        },
        'away': {
            'our_win_prob': round(away_win_prob, 4),
            'our_win_pct': round(away_win_prob * 100, 1),
            'our_implied_ml': our_away_ml,
            'market_ml': market_away_ml,
            'market_implied_prob': round(market_away_prob_no_vig, 4),
            'market_implied_pct': round(market_away_prob_no_vig * 100, 1),
            'edge_pct': round(away_edge, 2),
            'expected_value_per_100': round(away_ev, 2),
            'recommendation': _recommendation(away_edge),
            'is_value_bet': away_edge >= EDGE_THRESHOLD,
        },
        'vig': round((total_market_prob - 1) * 100, 2) if home_moneyline else 0,
        'edge_threshold': EDGE_THRESHOLD,
        'workings': {
            'formula': 'Edge% = (our_prob - market_implied_prob) × 100',
            'ev_formula': 'EV per $100 = (our_prob × payout) - (1 - our_prob) × 100',
            'vig_explanation': 'Market odds de-vigged by normalizing sum of implied probs to 1.0',
            'home_edge_calc': f'{round(home_win_prob*100, 1)}% - {round(market_home_prob_no_vig*100, 1)}% = {round(home_edge, 2)}%',
            'away_edge_calc': f'{round(away_win_prob*100, 1)}% - {round(market_away_prob_no_vig*100, 1)}% = {round(away_edge, 2)}%',
        }
    }


def prob_to_moneyline(prob: float) -> int:
    """Converts win probability to American moneyline format."""
    prob = max(min(prob, 0.999), 0.001)
    if prob >= 0.5:
        ml = -round((prob / (1 - prob)) * 100)
    else:
        ml = round(((1 - prob) / prob) * 100)
    return int(ml)


def moneyline_to_prob(ml: int) -> float:
    """Converts American moneyline to implied probability (includes vig)."""
    if ml < 0:
        return abs(ml) / (abs(ml) + 100)
    else:
        return 100 / (ml + 100)


def _expected_value(our_prob: float, market_ml: int) -> float:
    """Expected value per $100 bet."""
    if market_ml < 0:
        payout = 100 / abs(market_ml) * 100  # profit on $100 bet
    else:
        payout = market_ml  # profit on $100 bet

    ev = (our_prob * payout) - ((1 - our_prob) * 100)
    return ev


def _recommendation(edge: float) -> str:
    if edge >= EDGE_THRESHOLD:
        return 'BET'
    elif edge >= 2.0:
        return 'LEAN'
    else:
        return 'PASS'
