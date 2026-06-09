"""
bbref_scraper.py — Scrapes team and pitcher stats from Baseball Reference.
Caches results daily to avoid rate limiting.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
from datetime import date

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
BASE_URL = 'https://www.baseball-reference.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36'
}

# Current season
SEASON = date.today().year


def get_team_stats(abbr, force_refresh=False):
    """
    Returns a dict of team stats for the given abbreviation.
    Pulls from cache if available, otherwise scrapes BBRef.
    """
    today = date.today()
    cache_file = os.path.join(CACHE_DIR, f'team_{abbr}_{today}.json')

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    stats = _scrape_team_stats(abbr)

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(stats, f, indent=2)

    return stats


def _scrape_team_stats(abbr):
    """Scrapes season stats for a team from their BBRef page."""
    url = f"{BASE_URL}/teams/{abbr}/{SEASON}.shtml"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        time.sleep(2)
    except Exception as e:
        print(f"[scraper] Failed to fetch {abbr}: {e}")
        return _fallback_team_stats(abbr)

    soup = BeautifulSoup(resp.text, 'lxml')
    stats = {'abbr': abbr}

    # --- Batting stats ---
    try:
        batting_table = soup.find('table', id='team_batting')
        if batting_table:
            rows = batting_table.find('tfoot').find_all('tr')
            for row in rows:
                cells = {td.get('data-stat'): td.text.strip()
                         for td in row.find_all(['td', 'th'])}
                if cells:
                    stats['runs_scored'] = _safe_float(cells.get('R', 0))
                    stats['batting_avg'] = _safe_float(cells.get('BA', 0))
                    stats['obp'] = _safe_float(cells.get('OBP', 0))
                    stats['slg'] = _safe_float(cells.get('SLG', 0))
                    stats['ops'] = _safe_float(cells.get('OPS', 0))
                    stats['home_runs'] = _safe_float(cells.get('HR', 0))
                    break
    except Exception as e:
        print(f"[scraper] Batting parse error for {abbr}: {e}")

    # --- Pitching stats ---
    try:
        pitching_table = soup.find('table', id='team_pitching')
        if pitching_table:
            rows = pitching_table.find('tfoot').find_all('tr')
            for row in rows:
                cells = {td.get('data-stat'): td.text.strip()
                         for td in row.find_all(['td', 'th'])}
                if cells:
                    stats['era'] = _safe_float(cells.get('earned_run_avg', 4.50))
                    stats['whip'] = _safe_float(cells.get('whip', 1.30))
                    stats['runs_allowed'] = _safe_float(cells.get('R', 0))
                    stats['k9'] = _safe_float(cells.get('strikeouts_per_nine', 8.0))
                    stats['bb9'] = _safe_float(cells.get('bases_on_balls_per_nine', 3.0))
                    break
    except Exception as e:
        print(f"[scraper] Pitching parse error for {abbr}: {e}")

    # --- Win/Loss record ---
    try:
        record = _get_team_record(soup)
        stats.update(record)
    except Exception as e:
        print(f"[scraper] Record parse error for {abbr}: {e}")

    # Fill in any missing fields with league averages
    stats = _fill_defaults(stats, abbr)
    return stats


def _get_team_record(soup):
    """Extracts W-L record and home/away splits."""
    record = {}
    try:
        # Team record from the meta div
        meta = soup.find('div', id='meta')
        if meta:
            p_tags = meta.find_all('p')
            for p in p_tags:
                text = p.text
                if 'Record:' in text or 'W-L' in text:
                    parts = text.split(':')[-1].strip().split('-')
                    if len(parts) >= 2:
                        record['wins'] = int(parts[0].strip().split()[0])
                        record['losses'] = int(parts[1].strip().split()[0])
    except Exception:
        record['wins'] = 40
        record['losses'] = 40

    record.setdefault('wins', 40)
    record.setdefault('losses', 40)

    games_played = record['wins'] + record['losses']
    record['win_pct'] = round(record['wins'] / max(games_played, 1), 4)
    record['games_played'] = games_played

    return record


def _fill_defaults(stats, abbr):
    """Fill missing stats with league-average defaults."""
    defaults = {
        'abbr': abbr,
        'runs_scored': 350,
        'runs_allowed': 350,
        'batting_avg': 0.248,
        'obp': 0.318,
        'slg': 0.408,
        'ops': 0.726,
        'home_runs': 80,
        'era': 4.20,
        'whip': 1.28,
        'k9': 8.5,
        'bb9': 3.1,
        'wins': 40,
        'losses': 40,
        'win_pct': 0.500,
        'games_played': 80,
    }
    for key, val in defaults.items():
        stats.setdefault(key, val)
    return stats


def _fallback_team_stats(abbr):
    """Returns league-average stats when scraping fails."""
    print(f"[scraper] Using fallback stats for {abbr}")
    return _fill_defaults({'abbr': abbr}, abbr)


def get_all_team_stats(force_refresh=False):
    """
    Scrapes the MLB standings page to get runs scored/allowed
    for all 30 teams in one shot — more efficient than 30 individual requests.
    """
    today = date.today()
    cache_file = os.path.join(CACHE_DIR, f'all_teams_{today}.json')

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    url = f"{BASE_URL}/leagues/majors/{SEASON}-standings.shtml"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        time.sleep(2)
    except Exception as e:
        print(f"[scraper] Failed to fetch standings: {e}")
        return {}

    soup = BeautifulSoup(resp.text, 'lxml')
    all_stats = {}

    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            try:
                team_link = row.find('a')
                if not team_link:
                    continue
                team_name = team_link.text.strip()
                from scraper.schedule import _team_name_to_abbr
                abbr = _team_name_to_abbr(team_name)
                cell_data = {td.get('data-stat'): td.text.strip() for td in cells}
                if 'R' in cell_data and 'RA' in cell_data:
                    all_stats[abbr] = {
                        'abbr': abbr,
                        'runs_scored': _safe_float(cell_data.get('R', 350)),
                        'runs_allowed': _safe_float(cell_data.get('RA', 350)),
                        'wins': _safe_float(cell_data.get('W', 40)),
                        'losses': _safe_float(cell_data.get('L', 40)),
                    }
            except Exception:
                continue

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(all_stats, f, indent=2)

    return all_stats


def _safe_float(val, default=0.0):
    try:
        return float(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return default
