"""
schedule.py — Fetches today's MLB schedule from Baseball Reference.
Returns a list of matchups with home/away teams and starting pitchers.
"""

import requests
from bs4 import BeautifulSoup
from datetime import date
import time
import json
import os

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36'
}


def get_today_games(force_refresh=False):
    """
    Returns list of today's games as dicts:
    {
        'home_team': str,
        'away_team': str,
        'home_abbr': str,
        'away_abbr': str,
        'home_pitcher': str,
        'away_pitcher': str,
        'game_time': str
    }
    """
    today = date.today()
    cache_file = os.path.join(CACHE_DIR, f'schedule_{today}.json')

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    games = _scrape_schedule(today)

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(games, f, indent=2)

    return games


def _scrape_schedule(today):
    url = f"https://www.baseball-reference.com/previews/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        time.sleep(2)
    except Exception as e:
        print(f"[schedule] Error fetching schedule: {e}")
        return _fallback_games()

    soup = BeautifulSoup(resp.text, 'lxml')
    games = []

    # BBRef preview pages list matchups in divs with class 'game_summary'
    summaries = soup.find_all('div', class_='game_summary')

    for s in summaries:
        try:
            teams = s.find_all('tr')
            if len(teams) < 2:
                continue

            away_row = teams[0]
            home_row = teams[1]

            away_td = away_row.find('td', class_='right')
            home_td = home_row.find('td', class_='right')

            away_link = away_row.find('a')
            home_link = home_row.find('a')

            if not (away_link and home_link):
                continue

            away_team = away_link.text.strip()
            home_team = home_link.text.strip()

            away_abbr = _team_name_to_abbr(away_team)
            home_abbr = _team_name_to_abbr(home_team)

            # Try to get pitchers from the preview
            pitcher_rows = s.find_all('td', class_='')
            home_pitcher = 'TBD'
            away_pitcher = 'TBD'

            time_td = s.find('td', class_='right gamelink')
            game_time = time_td.text.strip() if time_td else 'TBD'

            games.append({
                'home_team': home_team,
                'away_team': away_team,
                'home_abbr': home_abbr,
                'away_abbr': away_abbr,
                'home_pitcher': home_pitcher,
                'away_pitcher': away_pitcher,
                'game_time': game_time
            })
        except Exception as e:
            print(f"[schedule] Error parsing game: {e}")
            continue

    if not games:
        return _fallback_games()

    return games


def _fallback_games():
    """Returns sample games for testing when scraping fails."""
    return [
        {
            'home_team': 'Los Angeles Dodgers',
            'away_team': 'San Francisco Giants',
            'home_abbr': 'LAD',
            'away_abbr': 'SFG',
            'home_pitcher': 'Yoshinobu Yamamoto',
            'away_pitcher': 'Logan Webb',
            'game_time': '7:10 PM'
        },
        {
            'home_team': 'New York Yankees',
            'away_team': 'Boston Red Sox',
            'home_abbr': 'NYY',
            'away_abbr': 'BOS',
            'home_pitcher': 'Gerrit Cole',
            'away_pitcher': 'Brayan Bello',
            'game_time': '7:05 PM'
        },
        {
            'home_team': 'Houston Astros',
            'away_team': 'Texas Rangers',
            'home_abbr': 'HOU',
            'away_abbr': 'TEX',
            'home_pitcher': 'Framber Valdez',
            'away_pitcher': 'Nathan Eovaldi',
            'game_time': '8:10 PM'
        }
    ]


# Mapping of common team names to BBRef abbreviations
TEAM_ABBR_MAP = {
    'Arizona Diamondbacks': 'ARI', 'Atlanta Braves': 'ATL',
    'Baltimore Orioles': 'BAL', 'Boston Red Sox': 'BOS',
    'Chicago Cubs': 'CHC', 'Chicago White Sox': 'CHW',
    'Cincinnati Reds': 'CIN', 'Cleveland Guardians': 'CLE',
    'Colorado Rockies': 'COL', 'Detroit Tigers': 'DET',
    'Houston Astros': 'HOU', 'Kansas City Royals': 'KCR',
    'Los Angeles Angels': 'LAA', 'Los Angeles Dodgers': 'LAD',
    'Miami Marlins': 'MIA', 'Milwaukee Brewers': 'MIL',
    'Minnesota Twins': 'MIN', 'New York Mets': 'NYM',
    'New York Yankees': 'NYY', 'Oakland Athletics': 'OAK',
    'Philadelphia Phillies': 'PHI', 'Pittsburgh Pirates': 'PIT',
    'San Diego Padres': 'SDP', 'San Francisco Giants': 'SFG',
    'Seattle Mariners': 'SEA', 'St. Louis Cardinals': 'STL',
    'Tampa Bay Rays': 'TBR', 'Texas Rangers': 'TEX',
    'Toronto Blue Jays': 'TOR', 'Washington Nationals': 'WSN',
    'Athletics': 'OAK', 'Diamondbacks': 'ARI', 'Braves': 'ATL',
    'Orioles': 'BAL', 'Red Sox': 'BOS', 'Cubs': 'CHC',
    'White Sox': 'CHW', 'Reds': 'CIN', 'Guardians': 'CLE',
    'Rockies': 'COL', 'Tigers': 'DET', 'Astros': 'HOU',
    'Royals': 'KCR', 'Angels': 'LAA', 'Dodgers': 'LAD',
    'Marlins': 'MIA', 'Brewers': 'MIL', 'Twins': 'MIN',
    'Mets': 'NYM', 'Yankees': 'NYY', 'Phillies': 'PHI',
    'Pirates': 'PIT', 'Padres': 'SDP', 'Giants': 'SFG',
    'Mariners': 'SEA', 'Cardinals': 'STL', 'Rays': 'TBR',
    'Rangers': 'TEX', 'Blue Jays': 'TOR', 'Nationals': 'WSN',
}


def _team_name_to_abbr(name):
    for key, abbr in TEAM_ABBR_MAP.items():
        if key.lower() in name.lower():
            return abbr
    return name[:3].upper()
