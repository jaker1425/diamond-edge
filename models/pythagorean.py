"""
pythagorean.py — Bill James Pythagorean Expectation model.

Estimates a team's true winning percentage based on runs scored vs allowed.
Uses the refined exponent of 1.83 (Pythagenpat) for improved accuracy.

Formula: Win% = RS^1.83 / (RS^1.83 + RA^1.83)
"""

import math


EXPONENT = 1.83  # Bill James refined exponent
HOME_FIELD_ADJUSTMENT = 0.020  # ~54% home win rate league-wide


def calculate(home_stats: dict, away_stats: dict) -> dict:
    """
    Calculates Pythagorean win probabilities for both teams.

    Returns a dict with full workings for display:
    {
        'home_win_prob': float,
        'away_win_prob': float,
        'home_pyth_pct': float,
        'away_pyth_pct': float,
        'workings': dict  # all intermediate values for display
    }
    """
    home_rs = home_stats.get('runs_scored', 350)
    home_ra = home_stats.get('runs_allowed', 350)
    away_rs = away_stats.get('runs_scored', 350)
    away_ra = away_stats.get('runs_allowed', 350)

    # Games played (normalize to per-game rates if needed)
    home_gp = max(home_stats.get('games_played', 80), 1)
    away_gp = max(away_stats.get('games_played', 80), 1)

    # Per-game rates
    home_rpg = home_rs / home_gp
    home_rapg = home_ra / home_gp
    away_rpg = away_rs / away_gp
    away_rapg = away_ra / away_gp

    # Pythagorean win percentages
    home_pyth = _pythagorean(home_rpg, home_rapg)
    away_pyth = _pythagorean(away_rpg, away_rapg)

    # Apply home field adjustment
    home_pyth_adj = min(home_pyth + HOME_FIELD_ADJUSTMENT, 0.999)
    away_pyth_adj = max(away_pyth - HOME_FIELD_ADJUSTMENT, 0.001)

    # Normalize so they don't have to sum to 1 (each is independent estimate)
    total = home_pyth_adj + away_pyth_adj
    home_win_prob = home_pyth_adj / total
    away_win_prob = away_pyth_adj / total

    return {
        'home_win_prob': round(home_win_prob, 4),
        'away_win_prob': round(away_win_prob, 4),
        'home_pyth_pct': round(home_pyth, 4),
        'away_pyth_pct': round(away_pyth, 4),
        'workings': {
            'exponent': EXPONENT,
            'home_field_adjustment': HOME_FIELD_ADJUSTMENT,
            'home': {
                'runs_scored_total': home_rs,
                'runs_allowed_total': home_ra,
                'games_played': home_gp,
                'runs_scored_per_game': round(home_rpg, 3),
                'runs_allowed_per_game': round(home_rapg, 3),
                'rs_exp': round(home_rpg ** EXPONENT, 4),
                'ra_exp': round(home_rapg ** EXPONENT, 4),
                'pyth_pct_raw': round(home_pyth, 4),
                'pyth_pct_adjusted': round(home_pyth_adj, 4),
            },
            'away': {
                'runs_scored_total': away_rs,
                'runs_allowed_total': away_ra,
                'games_played': away_gp,
                'runs_scored_per_game': round(away_rpg, 3),
                'runs_allowed_per_game': round(away_rapg, 3),
                'rs_exp': round(away_rpg ** EXPONENT, 4),
                'ra_exp': round(away_rapg ** EXPONENT, 4),
                'pyth_pct_raw': round(away_pyth, 4),
                'pyth_pct_adjusted': round(away_pyth_adj, 4),
            },
            'formula': f'Win% = RS^{EXPONENT} / (RS^{EXPONENT} + RA^{EXPONENT})',
        }
    }


def _pythagorean(rs_per_game: float, ra_per_game: float) -> float:
    """Core Pythagorean formula."""
    rs = max(rs_per_game, 0.01)
    ra = max(ra_per_game, 0.01)
    rs_exp = rs ** EXPONENT
    ra_exp = ra ** EXPONENT
    return rs_exp / (rs_exp + ra_exp)
