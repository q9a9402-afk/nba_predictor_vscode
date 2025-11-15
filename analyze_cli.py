"""Clean CLI entry for analysis (new file).
This duplicates the intended functionality but avoids touching the broken `analyze_one.py`.
"""
from __future__ import annotations

import argparse
import csv
import json
from pprint import pprint
from typing import Optional, Tuple

from src.data_collector import NBADataCollector
from src.analyzer import NBAAnalyzer


def implied_prob(decimal_odds: Optional[float]) -> Optional[float]:
    if decimal_odds is None:
        return None
    try:
        return 1.0 / float(decimal_odds)
    except Exception:
        return None


def fair_probs_from_odds(home_odds: float, away_odds: float) -> Tuple[Optional[float], Optional[float]]:
    ph = implied_prob(home_odds)
    pa = implied_prob(away_odds)
    if ph is None or pa is None:
        return None, None
    s = ph + pa
    if s <= 0:
        return None, None
    return ph / s, pa / s


def safe_get_prob(analysis) -> Tuple[Optional[float], Optional[float]]:
    home = None
    away = None
    if analysis is None:
        return home, away
    if isinstance(analysis, dict):
        if 'prediction' in analysis and isinstance(analysis['prediction'], dict):
            p = analysis['prediction']
            home = p.get('home_win_probability') or p.get('home_prob') or p.get('home')
            away = p.get('away_win_probability') or p.get('away_prob') or p.get('away')
        else:
            home = analysis.get('home_win_probability') or analysis.get('home_prob') or analysis.get('home')
            away = analysis.get('away_win_probability') or analysis.get('away_prob') or analysis.get('away')
    try:
        if home is not None:
            home = float(home)
        if away is not None:
            away = float(away)
    except Exception:
        pass
    return home, away


def compute_kelly(p: float, decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        return 0.0
    b = decimal_odds - 1.0
    q = 1.0 - p
    k = (b * p - q) / b
    return max(k, 0.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--home', default='New York Knicks')
    p.add_argument('--away', default='Miami Heat')
    p.add_argument('--home-odds', type=float, default=1.53)
    p.add_argument('--away-odds', type=float, default=4.50)
    p.add_argument('--output-json', dest='output_json', type=str, default=None)
    p.add_argument('--output-csv', dest='output_csv', type=str, default=None)
    p.add_argument('--bet-side', dest='bet_side', choices=['home', 'away', 'none'], default='none')
    p.add_argument('--bankroll', dest='bankroll', type=float, default=None)
    p.add_argument('--kelly-fraction', dest='kelly_fraction', type=float, default=1.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    home = args.home
    away = args.away
    home_odds = args.home_odds
    away_odds = args.away_odds

    out_json = args.output_json
    out_csv = args.output_csv
    bet_side = args.bet_side
    bankroll = args.bankroll
    kelly_fraction = args.kelly_fraction

    print(f'Running analysis: {home} vs {away}')

    imp_home = implied_prob(home_odds)
    imp_away = implied_prob(away_odds)
    fair_h, fair_a = (None, None)
    if imp_home is not None and imp_away is not None:
        fair_h, fair_a = fair_probs_from_odds(home_odds, away_odds)

    collector = NBADataCollector()
    analyzer = NBAAnalyzer()
    try:
        analysis = analyzer.analyze_matchup(home, away)
    except Exception:
        analysis = None

    model_home_prob, model_away_prob = safe_get_prob(analysis)

    result = {
        'home': home,
        'away': away,
        'market': {'home_odds': home_odds, 'away_odds': away_odds, 'imp_home': imp_home, 'imp_away': imp_away},
        'fair_market': {'home': fair_h, 'away': fair_a},
        'model': {'home_prob': model_home_prob, 'away_prob': model_away_prob},
        'raw_analysis': analysis,
    }

    # optional Kelly
    if bet_side in ('home', 'away') and bankroll is not None:
        if bet_side == 'home' and model_home_prob is not None:
            p = float(model_home_prob); odds = home_odds
        elif bet_side == 'away' and model_away_prob is not None:
            p = float(model_away_prob); odds = away_odds
        else:
            p = None; odds = None
        if p is not None and odds is not None:
            k = compute_kelly(p, odds)
            k_adj = k * float(kelly_fraction)
            suggested = k_adj * float(bankroll)
            result['kelly'] = {'full_kelly': k, 'used_fraction': kelly_fraction, 'suggested_bet': suggested}

    if out_json:
        with open(out_json, 'w', encoding='utf8') as fh:
            json.dump(result, fh, indent=2, default=str)
        print('Wrote JSON to', out_json)

    if out_csv:
        with open(out_csv, 'w', newline='', encoding='utf8') as fh:
            w = csv.writer(fh)
            w.writerow(['home','away','model_home_prob','model_away_prob','imp_home','imp_away'])
            w.writerow([home, away, model_home_prob, model_away_prob, imp_home, imp_away])
        print('Wrote CSV to', out_csv)

    pprint(result)


if __name__ == '__main__':
    main()
