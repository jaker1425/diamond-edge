"""
log5.py — Bill James Log5 Method for head-to-head win probability.

Given two teams' true winning percentages, estimates the probability
that team A beats team B in a specific matchup.

Formula: P(A beats B) = (WP_A - WP_A * WP_B) / (WP_A + WP_B - 2 * WP_A * WP_B)

Home field advantage is applied before the Log5 calculation by adjusting
the home team's win percentage upward by HOME_FIELD_BOOST.
"""

HOME_FIELD_BOOST = 0.040  # ~4% boost for home team win probability


def calculate(home_stats: dict, away_stats: dict) -> dict:
    """
    Calculates Log5 win probabilities for both teams.

    Uses actual W-L win percentages as input (season record).
    Returns full workings for display.
    """
    home_wp_raw = home_stats.get('win_pct', 0.500)
    away_wp_raw = away_stats.get('win_pct', 0.500)

    # Apply home field adjustment
    home_wp = min(home_wp_raw + HOME_FIELD_BOOST, 0.999)
    away_wp = max(away_wp_raw - HOME_FIELD_BOOST, 0.001)

    # Log5 formula
    home_win_prob = _log5(home_wp, away_wp)
    away_win_prob = 1.0 - home_win_prob

    return {
        'home_win_prob': round(home_win_prob, 4),
        'away_win_prob': round(away_win_prob, 4),
        'workings': {
            'formula': 'P(A beats B) = (WP_A - WP_A×WP_B) / (WP_A + WP_B - 2×WP_A×WP_B)',
            'home_field_boost': HOME_FIELD_BOOST,
            'home': {
                'win_pct_season': round(home_wp_raw, 4),
                'win_pct_adjusted': round(home_wp, 4),
                'wins': home_stats.get('wins', 40),
                'losses': home_stats.get('losses', 40),
            },
            'away': {
                'win_pct_season': round(away_wp_raw, 4),
                'win_pct_adjusted': round(away_wp, 4),
                'wins': away_stats.get('wins', 40),
                'losses': away_stats.get('losses', 40),
            },
            'numerator': round(home_wp - home_wp * away_wp, 6),
            'denominator': round(home_wp + away_wp - 2 * home_wp * away_wp, 6),
            'home_win_prob': round(home_win_prob, 4),
            'away_win_prob': round(away_win_prob, 4),
        }
    }


def _log5(wp_a: float, wp_b: float) -> float:
    """
    Core Log5 calculation.
    wp_a = adjusted win% of home team
    wp_b = adjusted win% of away team
    Returns P(A beats B).
    """
    wp_a = max(min(wp_a, 0.999), 0.001)
    wp_b = max(min(wp_b, 0.999), 0.001)

    numerator = wp_a - (wp_a * wp_b)
    denominator = wp_a + wp_b - (2 * wp_a * wp_b)

    if denominator == 0:
        return 0.5

    return numerator / denominator
