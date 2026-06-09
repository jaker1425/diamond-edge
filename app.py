"""
app.py — Flask entry point for the Baseball Betting Analysis Dashboard.
Run with: python app.py
Opens at: http://localhost:5000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify, request
from datetime import date
import json

from scraper.schedule import get_today_games
from scraper.bbref_scraper import get_team_stats
from models.aggregator import run_all_models
from analysis.edge import calculate_edge

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


def analyze_game(game: dict) -> dict:
    """Runs full analysis pipeline for a single game matchup."""
    home_abbr = game['home_abbr']
    away_abbr = game['away_abbr']

    # Fetch stats
    home_stats = get_team_stats(home_abbr)
    away_stats = get_team_stats(away_abbr)

    # Run all models
    prediction = run_all_models(home_stats, away_stats)

    # Calculate edge (no market lines yet — shows fair value)
    edge = calculate_edge(
        home_win_prob=prediction['home_win_prob'],
        away_win_prob=prediction['away_win_prob']
    )

    return {
        'game': game,
        'home_stats': home_stats,
        'away_stats': away_stats,
        'prediction': prediction,
        'edge': edge,
    }


@app.route('/')
def index():
    """Main dashboard — today's games with predictions."""
    games = get_today_games()
    analyses = []

    for game in games:
        try:
            result = analyze_game(game)
            analyses.append(result)
        except Exception as e:
            print(f"[app] Error analyzing {game['away_abbr']} @ {game['home_abbr']}: {e}")
            analyses.append({
                'game': game,
                'error': str(e),
                'home_stats': {},
                'away_stats': {},
                'prediction': None,
                'edge': None,
            })

    today = date.today().strftime('%A, %B %d, %Y')
    value_bets = sum(
        1 for a in analyses
        if a.get('edge') and (
            a['edge']['home']['is_value_bet'] or a['edge']['away']['is_value_bet']
        )
    )

    return render_template('index.html',
                           analyses=analyses,
                           today=today,
                           value_bets=value_bets)


@app.route('/game/<int:game_idx>')
def game_detail(game_idx):
    """Detailed mathematical breakdown for a single game."""
    games = get_today_games()

    if game_idx >= len(games):
        return "Game not found", 404

    game = games[game_idx]
    try:
        result = analyze_game(game)
    except Exception as e:
        return f"Error analyzing game: {e}", 500

    return render_template('game_detail.html', result=result, game_idx=game_idx)


@app.route('/api/game/<int:game_idx>')
def api_game(game_idx):
    """JSON endpoint for a single game's full analysis."""
    games = get_today_games()
    if game_idx >= len(games):
        return jsonify({'error': 'Game not found'}), 404

    game = games[game_idx]
    result = analyze_game(game)
    return jsonify(result)


@app.route('/refresh')
def refresh():
    """Force refresh all cached data."""
    games = get_today_games(force_refresh=True)
    return jsonify({'status': 'refreshed', 'games': len(games)})


if __name__ == '__main__':
    os.makedirs('cache', exist_ok=True)
    print("\n" + "="*55)
    print("  ⚾  Baseball Betting Analysis Dashboard")
    print("="*55)
    print(f"  Running at: http://localhost:5000")
    print(f"  Today:      {date.today().strftime('%B %d, %Y')}")
    print("  Press Ctrl+C to stop")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
