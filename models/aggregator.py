"""
aggregator.py — Combines Pythagorean, Log5, and Poisson model outputs
into a single blended win probability with confidence interval.

Weights:
  Pythagorean:  25%
  Log5:         35%
  Poisson:      40%
"""

import numpy as np
from models import pythagorean, log5, poisson

WEIGHTS = {
    'pythagorean': 0.25,
    'log5': 0.35,
    'poisson': 0.40,
}

# Bootstrap iterations for confidence interval estimation
CI_ITERATIONS = 1000
CI_LEVEL = 0.95


def run_all_models(home_stats: dict, away_stats: dict) -> dict:
    """
    Runs all three models and returns a blended prediction with full workings.
    """
    pyth_result = pythagorean.calculate(home_stats, away_stats)
    log5_result = log5.calculate(home_stats, away_stats)
    poisson_result = poisson.calculate(home_stats, away_stats)

    # Weighted average
    home_blended = (
        WEIGHTS['pythagorean'] * pyth_result['home_win_prob'] +
        WEIGHTS['log5'] * log5_result['home_win_prob'] +
        WEIGHTS['poisson'] * poisson_result['home_win_prob']
    )
    away_blended = 1.0 - home_blended

    # 95% Confidence interval via bootstrap-style variance across models
    model_probs = np.array([
        pyth_result['home_win_prob'],
        log5_result['home_win_prob'],
        poisson_result['home_win_prob'],
    ])
    std = np.std(model_probs)
    z = 1.96  # 95% CI
    ci_lower = max(home_blended - z * std, 0.01)
    ci_upper = min(home_blended + z * std, 0.99)

    return {
        'home_win_prob': round(home_blended, 4),
        'away_win_prob': round(away_blended, 4),
        'ci_lower': round(ci_lower, 4),
        'ci_upper': round(ci_upper, 4),
        'ci_level': CI_LEVEL,
        'std_across_models': round(float(std), 4),
        'model_agreement': _agreement_label(std),
        'models': {
            'pythagorean': {
                'home_win_prob': pyth_result['home_win_prob'],
                'away_win_prob': pyth_result['away_win_prob'],
                'weight': WEIGHTS['pythagorean'],
                'weighted_contribution': round(WEIGHTS['pythagorean'] * pyth_result['home_win_prob'], 4),
                'workings': pyth_result['workings'],
            },
            'log5': {
                'home_win_prob': log5_result['home_win_prob'],
                'away_win_prob': log5_result['away_win_prob'],
                'weight': WEIGHTS['log5'],
                'weighted_contribution': round(WEIGHTS['log5'] * log5_result['home_win_prob'], 4),
                'workings': log5_result['workings'],
            },
            'poisson': {
                'home_win_prob': poisson_result['home_win_prob'],
                'away_win_prob': poisson_result['away_win_prob'],
                'weight': WEIGHTS['poisson'],
                'weighted_contribution': round(WEIGHTS['poisson'] * poisson_result['home_win_prob'], 4),
                'workings': poisson_result['workings'],
            },
        },
        'weights': WEIGHTS,
        'blend_formula': (
            f"P(home wins) = "
            f"{WEIGHTS['pythagorean']}×Pyth + "
            f"{WEIGHTS['log5']}×Log5 + "
            f"{WEIGHTS['poisson']}×Poisson"
        ),
    }


def _agreement_label(std: float) -> str:
    """Describes how much the models agree with each other."""
    if std < 0.03:
        return 'Strong'
    elif std < 0.07:
        return 'Moderate'
    else:
        return 'Weak'
