"""
poisson.py — Poisson regression model for MLB game outcomes.

Models each team's run scoring as a Poisson-distributed random variable.
Lambda (expected runs) is estimated by comparing team offense vs opponent pitching
against league averages.

Win probability is derived by computing P(team A score > team B score)
across the joint Poisson distribution.
"""

import numpy as np
from scipy import stats

# 2024 MLB league average runs per game
LEAGUE_AVG_RUNS_PER_GAME = 4.38
LEAGUE_AVG_ERA = 4.20

# Max runs to model (covers ~99.99% of all game outcomes)
MAX_RUNS = 20

# Home field run scoring boost
HOME_RUN_BOOST = 1.035  # ~3.5% more runs at home


def calculate(home_stats: dict, away_stats: dict) -> dict:
    """
    Calculates Poisson-based win probabilities.

    Estimates lambda for each team based on:
    - Team's offensive run rate (per game)
    - Opponent's defensive run rate (ERA-based)
    - Compared against league averages

    Returns full workings including lambda values and probability distribution.
    """
    home_gp = max(home_stats.get('games_played', 80), 1)
    away_gp = max(away_stats.get('games_played', 80), 1)

    # Offensive rates (runs scored per game)
    home_off_rate = home_stats.get('runs_scored', 350) / home_gp
    away_off_rate = away_stats.get('runs_scored', 350) / away_gp

    # Defensive rates (runs allowed per game)
    home_def_rate = home_stats.get('runs_allowed', 350) / home_gp
    away_def_rate = away_stats.get('runs_allowed', 350) / away_gp

    # Lambda for each team's run scoring:
    # team_offense * opponent_defense / league_average
    # This is the Dixon-Coles / attack-defense Poisson approach
    lambda_home = _estimate_lambda(
        attack=home_off_rate,
        defense=away_def_rate,
        league_avg=LEAGUE_AVG_RUNS_PER_GAME
    ) * HOME_RUN_BOOST

    lambda_away = _estimate_lambda(
        attack=away_off_rate,
        defense=home_def_rate,
        league_avg=LEAGUE_AVG_RUNS_PER_GAME
    )

    lambda_home = max(lambda_home, 0.5)
    lambda_away = max(lambda_away, 0.5)

    # Build Poisson probability mass functions
    home_pmf = np.array([stats.poisson.pmf(k, lambda_home) for k in range(MAX_RUNS + 1)])
    away_pmf = np.array([stats.poisson.pmf(k, lambda_away) for k in range(MAX_RUNS + 1)])

    # P(home wins) = sum over all (i, j) where i > j
    # P(tie) = sum over all (i, j) where i == j (assign 50/50)
    home_win_prob = 0.0
    away_win_prob = 0.0
    tie_prob = 0.0

    for home_runs in range(MAX_RUNS + 1):
        for away_runs in range(MAX_RUNS + 1):
            joint_prob = home_pmf[home_runs] * away_pmf[away_runs]
            if home_runs > away_runs:
                home_win_prob += joint_prob
            elif away_runs > home_runs:
                away_win_prob += joint_prob
            else:
                tie_prob += joint_prob

    # Split ties 50/50 (extra innings)
    home_win_prob += tie_prob * 0.5
    away_win_prob += tie_prob * 0.5

    # Build distribution data for chart (first 13 run values)
    distribution = {
        'labels': list(range(13)),
        'home_probs': [round(float(home_pmf[k]) * 100, 2) for k in range(13)],
        'away_probs': [round(float(away_pmf[k]) * 100, 2) for k in range(13)],
    }

    return {
        'home_win_prob': round(home_win_prob, 4),
        'away_win_prob': round(away_win_prob, 4),
        'workings': {
            'formula': 'λ = (team_RPG × opponent_RPG_allowed) / league_avg_RPG',
            'league_avg_rpg': LEAGUE_AVG_RUNS_PER_GAME,
            'home_run_boost': HOME_RUN_BOOST,
            'home': {
                'offensive_rpg': round(home_off_rate, 3),
                'opponent_defensive_rpg': round(away_def_rate, 3),
                'lambda': round(lambda_home, 4),
                'expected_runs': round(lambda_home, 2),
                'most_likely_score': int(np.argmax(home_pmf)),
            },
            'away': {
                'offensive_rpg': round(away_off_rate, 3),
                'opponent_defensive_rpg': round(home_def_rate, 3),
                'lambda': round(lambda_away, 4),
                'expected_runs': round(lambda_away, 2),
                'most_likely_score': int(np.argmax(away_pmf)),
            },
            'tie_probability': round(tie_prob, 4),
            'home_win_prob': round(home_win_prob, 4),
            'away_win_prob': round(away_win_prob, 4),
            'distribution': distribution,
        }
    }


def _estimate_lambda(attack: float, defense: float, league_avg: float) -> float:
    """
    Estimates expected runs using attack/defense strength ratios.
    attack  = team's runs scored per game
    defense = opponent's runs allowed per game
    """
    attack_strength = attack / league_avg
    defense_strength = defense / league_avg
    return attack_strength * defense_strength * league_avg
