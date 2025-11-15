"""Single-match analyzer CLI
Usage example:
  .venv/Scripts/python.exe analyze_one.py --home "New York Knicks" --away "Miami Heat" --home-odds 1.53 --away-odds 4.5

Features:
- Prints market implied probabilities and normalized fair probabilities
- Fetches light context from `src.data_collector`
- Runs `NBAAnalyzer.analyze_matchup` and prints model output
- Optional outputs: write JSON/CSV summary
- Optional Kelly calculation and suggested bet size
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
    """Compute full Kelly fraction. Returns fraction of bankroll to stake."""
    if decimal_odds <= 1.0:
        return 0.0
    b = decimal_odds - 1.0
    q = 1.0 - p
    k = (b * p - q) / b
    return max(k, 0.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Single-match NBA analyzer comparing model vs market')
    p.add_argument('--home', default='New York Knicks')
    p.add_argument('--away', default='Miami Heat')
    p.add_argument('--home-odds', type=float, default=1.53)
    p.add_argument('--away-odds', type=float, default=4.50)
    p.add_argument('--home-spread', type=float, default=None)
    p.add_argument('--away-spread', type=float, default=None)
    p.add_argument('--home-water', type=float, default=None, help='Asian water / payout multiplier, e.g. 0.98')
    p.add_argument('--away-water', type=float, default=None)
    p.add_argument('--home-injuries', type=str, default='')
    p.add_argument('--away-injuries', type=str, default='')

    # outputs and betting options
    p.add_argument('--output-json', dest='output_json', type=str, default=None, help='Write analysis JSON to path')
    p.add_argument('--output-csv', dest='output_csv', type=str, default=None, help='Write CSV summary to path')
    p.add_argument('--bet-side', dest='bet_side', choices=['home', 'away', 'none'], default='none', help='Which side to compute Kelly for')
    p.add_argument('--bankroll', dest='bankroll', type=float, default=None, help='Bankroll size for suggested bet calculation')
    p.add_argument('--kelly-fraction', dest='kelly_fraction', type=float, default=1.0, help='Fraction of full Kelly to use (0-1)')

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

    print('\n=== Single-match analysis ===')
    print(f'Match: {home} (home) vs {away} (away)')
    print(f'Market odds (decimal): home={home_odds}, away={away_odds}')

    imp_home = implied_prob(home_odds)
    imp_away = implied_prob(away_odds)
    fair_h = fair_a = None
    if imp_home is not None and imp_away is not None:
        print(f'Market implied probs (raw): home={imp_home:.3f} ({imp_home:.1%}), away={imp_away:.3f} ({imp_away:.1%})')
        fair_h, fair_a = fair_probs_from_odds(home_odds, away_odds)
        if fair_h is not None:
            print(f'Fair market probs (normalized): home={fair_h:.3f} ({fair_h:.1%}), away={fair_a:.3f} ({fair_a:.1%})')
    else:
        print('Market implied probs: could not parse odds')

    # Lightweight context
    collector = NBADataCollector()
    analyzer = NBAAnalyzer()

    try:
        home_recent = collector.get_recent_performance(home)
    except Exception:
        home_recent = None
    try:
        away_recent = collector.get_recent_performance(away)
    except Exception:
        away_recent = None

    try:
        eff_home = collector.get_team_efficiency(home)
    except Exception:
        eff_home = None
    try:
        eff_away = collector.get_team_efficiency(away)
    except Exception:
        eff_away = None

    print('\nContext:')
    print(f'  {home}: recent_win_rate={home_recent}, NET_RATING={eff_home.get("NET_RATING") if eff_home else "N/A"}')
    print(f'  {away}: recent_win_rate={away_recent}, NET_RATING={eff_away.get("NET_RATING") if eff_away else "N/A"}')

    print('\nRunning model prediction...')
    try:
        analysis = analyzer.analyze_matchup(home, away)
    except Exception as e:
        print('Analyzer failed:', e)
        analysis = None

    print('\nRaw model output:')
    pprint(analysis)

    model_home_prob, model_away_prob = safe_get_prob(analysis)

    if model_home_prob is not None:
        mh = float(model_home_prob)
        print(f"\nModel home win probability: {mh:.3f} ({mh:.1%})")
        if imp_home is not None:
            edge_raw = mh - imp_home
            print(f"Edge vs market (raw implied): {edge_raw:.3f} ({edge_raw:.1%})")
        if fair_h is not None:
            edge_fair = mh - fair_h
            print(f"Edge vs fair market (normalized): {edge_fair:.3f} ({edge_fair:.1%})")
    else:
        print('\nModel did not return structured home probability')

    if model_home_prob is not None and fair_h is not None:
        mh = float(model_home_prob)
        edge = mh - fair_h
        if edge > 0.05:
            print('\nRecommendation: POSITIVE EDGE on HOME (consider bet)')
        elif edge < -0.05:
            print('\nRecommendation: MARKET FAVORS HOME MUCH MORE (avoid)')
        else:
            print('\nRecommendation: No clear value (edge small)')

    print('\n=== End analysis ===\n')

    # --- Additional outputs: JSON/CSV and Kelly suggestion ---
    result = {
        'home': home,
        'away': away,
        'market': {'home_odds': home_odds, 'away_odds': away_odds, 'imp_home': imp_home, 'imp_away': imp_away},
        'fair_market': {'home': fair_h, 'away': fair_a},
        'model': {'home_prob': model_home_prob, 'away_prob': model_away_prob},
        'context': {
            'home_recent': home_recent,
            'away_recent': away_recent,
            'eff_home': eff_home,
            'eff_away': eff_away,
        },
    }

    kelly = None
    suggested_bet = None
    if bet_side in ('home', 'away') and bankroll is not None:
        p = None
        odds = None
        if bet_side == 'home' and model_home_prob is not None:
            p = float(model_home_prob)
            odds = home_odds
        elif bet_side == 'away' and model_away_prob is not None:
            p = float(model_away_prob)
            odds = away_odds

        if p is not None and odds is not None:
            k = compute_kelly(p, odds)
            k_adj = k * float(kelly_fraction)
            kelly = k
            suggested_bet = k_adj * float(bankroll)
            result['kelly'] = {'full_kelly_frac': k, 'fraction_of_kelly_used': kelly_fraction, 'suggested_bet_size': suggested_bet, 'bankroll': bankroll, 'bet_side': bet_side}

    # write JSON if requested
    if out_json:
        try:
            with open(out_json, 'w', encoding='utf8') as fh:
                json.dump(result, fh, indent=2, default=str)
            print(f'Wrote JSON output to {out_json}')
        except Exception as e:
            print('Failed to write JSON:', e)

    # write CSV summary if requested (minimal rows)
    if out_csv:
        try:
            with open(out_csv, 'w', newline='', encoding='utf8') as fh:
                writer = csv.writer(fh)
                writer.writerow(['home', 'away', 'model_home_prob', 'model_away_prob', 'market_imp_home', 'market_imp_away', 'edge_vs_fair_home'])
                writer.writerow([home, away, model_home_prob, model_away_prob, imp_home, imp_away, (model_home_prob - fair_h) if (model_home_prob is not None and fair_h is not None) else None])
            print(f'Wrote CSV output to {out_csv}')
        except Exception as e:
            print('Failed to write CSV:', e)


if __name__ == '__main__':
    main()
"""Single-match analyzer CLI
Usage example:
  .venv/Scripts/python.exe analyze_one.py --home "New York Knicks" --away "Miami Heat" --home-odds 1.53 --away-odds 4.5

Features:
- Prints market implied probabilities and normalized fair probabilities
- Fetches light context from `src.data_collector`
- Runs `NBAAnalyzer.analyze_matchup` and prints model output
- Optional outputs: write JSON/CSV summary
- Optional Kelly calculation and suggested bet size
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
    """Compute full Kelly fraction. Returns fraction of bankroll to stake."""
    if decimal_odds <= 1.0:
        return 0.0
    b = decimal_odds - 1.0
    q = 1.0 - p
    k = (b * p - q) / b
    return max(k, 0.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Single-match NBA analyzer comparing model vs market')
    p.add_argument('--home', default='New York Knicks')
    p.add_argument('--away', default='Miami Heat')
    p.add_argument('--home-odds', type=float, default=1.53)
    p.add_argument('--away-odds', type=float, default=4.50)
    p.add_argument('--home-spread', type=float, default=None)
    p.add_argument('--away-spread', type=float, default=None)
    p.add_argument('--home-water', type=float, default=None, help='Asian water / payout multiplier, e.g. 0.98')
    p.add_argument('--away-water', type=float, default=None)
    p.add_argument('--home-injuries', type=str, default='')
    p.add_argument('--away-injuries', type=str, default='')

    # outputs and betting options
    p.add_argument('--output-json', dest='output_json', type=str, default=None, help='Write analysis JSON to path')
    p.add_argument('--output-csv', dest='output_csv', type=str, default=None, help='Write CSV summary to path')
    p.add_argument('--bet-side', dest='bet_side', choices=['home', 'away', 'none'], default='none', help='Which side to compute Kelly for')
    p.add_argument('--bankroll', dest='bankroll', type=float, default=None, help='Bankroll size for suggested bet calculation')
    p.add_argument('--kelly-fraction', dest='kelly_fraction', type=float, default=1.0, help='Fraction of full Kelly to use (0-1)')

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

    print('\n=== Single-match analysis ===')
    print(f'Match: {home} (home) vs {away} (away)')
    print(f'Market odds (decimal): home={home_odds}, away={away_odds}')

    imp_home = implied_prob(home_odds)
    imp_away = implied_prob(away_odds)
    fair_h = fair_a = None
    if imp_home is not None and imp_away is not None:
        print(f'Market implied probs (raw): home={imp_home:.3f} ({imp_home:.1%}), away={imp_away:.3f} ({imp_away:.1%})')
        fair_h, fair_a = fair_probs_from_odds(home_odds, away_odds)
        if fair_h is not None:
            print(f'Fair market probs (normalized): home={fair_h:.3f} ({fair_h:.1%}), away={fair_a:.3f} ({fair_a:.1%})')
    else:
        print('Market implied probs: could not parse odds')

    # Lightweight context
    collector = NBADataCollector()
    analyzer = NBAAnalyzer()

    try:
        home_recent = collector.get_recent_performance(home)
    except Exception:
        home_recent = None
    try:
        away_recent = collector.get_recent_performance(away)
    except Exception:
        away_recent = None

    try:
        eff_home = collector.get_team_efficiency(home)
    except Exception:
        eff_home = None
    try:
        eff_away = collector.get_team_efficiency(away)
    except Exception:
        eff_away = None

    print('\nContext:')
    print(f'  {home}: recent_win_rate={home_recent}, NET_RATING={eff_home.get("NET_RATING") if eff_home else "N/A"}')
    print(f'  {away}: recent_win_rate={away_recent}, NET_RATING={eff_away.get("NET_RATING") if eff_away else "N/A"}')

    print('\nRunning model prediction...')
    try:
        analysis = analyzer.analyze_matchup(home, away)
    except Exception as e:
        print('Analyzer failed:', e)
        analysis = None

    print('\nRaw model output:')
    pprint(analysis)

    model_home_prob, model_away_prob = safe_get_prob(analysis)

    if model_home_prob is not None:
        mh = float(model_home_prob)
        print(f"\nModel home win probability: {mh:.3f} ({mh:.1%})")
        if imp_home is not None:
            edge_raw = mh - imp_home
            print(f"Edge vs market (raw implied): {edge_raw:.3f} ({edge_raw:.1%})")
        if fair_h is not None:
            edge_fair = mh - fair_h
            print(f"Edge vs fair market (normalized): {edge_fair:.3f} ({edge_fair:.1%})")
    else:
        print('\nModel did not return structured home probability')

    if model_home_prob is not None and fair_h is not None:
        mh = float(model_home_prob)
        edge = mh - fair_h
        if edge > 0.05:
            print('\nRecommendation: POSITIVE EDGE on HOME (consider bet)')
        elif edge < -0.05:
            print('\nRecommendation: MARKET FAVORS HOME MUCH MORE (avoid)')
        else:
            print('\nRecommendation: No clear value (edge small)')

    print('\n=== End analysis ===\n')

    # --- Additional outputs: JSON/CSV and Kelly suggestion ---
    result = {
        'home': home,
        'away': away,
        'market': {'home_odds': home_odds, 'away_odds': away_odds, 'imp_home': imp_home, 'imp_away': imp_away},
        'fair_market': {'home': fair_h, 'away': fair_a},
        'model': {'home_prob': model_home_prob, 'away_prob': model_away_prob},
        'context': {
            'home_recent': home_recent,
            'away_recent': away_recent,
            'eff_home': eff_home,
            'eff_away': eff_away,
        },
    }

    kelly = None
    suggested_bet = None
    if bet_side in ('home', 'away') and bankroll is not None:
        p = None
        odds = None
        if bet_side == 'home' and model_home_prob is not None:
            p = float(model_home_prob)
            odds = home_odds
        elif bet_side == 'away' and model_away_prob is not None:
            p = float(model_away_prob)
            odds = away_odds

        if p is not None and odds is not None:
            k = compute_kelly(p, odds)
            k_adj = k * float(kelly_fraction)
            kelly = k
            suggested_bet = k_adj * float(bankroll)
            result['kelly'] = {'full_kelly_frac': k, 'fraction_of_kelly_used': kelly_fraction, 'suggested_bet_size': suggested_bet, 'bankroll': bankroll, 'bet_side': bet_side}

    # write JSON if requested
    if out_json:
        try:
            with open(out_json, 'w', encoding='utf8') as fh:
                json.dump(result, fh, indent=2, default=str)
            print(f'Wrote JSON output to {out_json}')
        except Exception as e:
            print('Failed to write JSON:', e)

    # write CSV summary if requested (minimal rows)
    if out_csv:
        try:
            with open(out_csv, 'w', newline='', encoding='utf8') as fh:
                writer = csv.writer(fh)
                writer.writerow(['home', 'away', 'model_home_prob', 'model_away_prob', 'market_imp_home', 'market_imp_away', 'edge_vs_fair_home'])
                writer.writerow([home, away, model_home_prob, model_away_prob, imp_home, imp_away, (model_home_prob - fair_h) if (model_home_prob is not None and fair_h is not None) else None])
            print(f'Wrote CSV output to {out_csv}')
        except Exception as e:
            print('Failed to write CSV:', e)


if __name__ == '__main__':
    main()
"""Single-match analyzer CLI
Usage example:
    .venv/Scripts/python.exe analyze_one.py \
        --home "New York Knicks" --away "Miami Heat" \
        --home-odds 1.53 --away-odds 4.5

This script prints market implied probabilities, optional fair (normalized) probs,
pulls light context from `src.data_collector`, runs `NBAAnalyzer.analyze_matchup`,
and reports model vs market edge with a simple recommendation.
"""
from pprint import pprint
import argparse
from typing import Optional, Tuple

from src.data_collector import NBADataCollector
from src.analyzer import NBAAnalyzer


def implied_prob(decimal_odds: Optional[float]) -> Optional[float]:
    if decimal_odds is None:

    kelly = None
    suggested_bet = None
    if bet_side in ('home', 'away') and bankroll is not None:
        if bet_side == 'home' and model_home_prob is not None:
            p = float(model_home_prob)
            odds = home_odds
        elif bet_side == 'away' and model_away_prob is not None:
            p = float(model_away_prob)
            odds = away_odds
        else:
            p = None
            odds = None

        if p is not None and odds is not None:
            k = compute_kelly(p, odds)
            k_adj = k * float(kelly_fraction)
            kelly = k
            suggested_bet = k_adj * float(bankroll)
            result['kelly'] = {'full_kelly_frac': k, 'fraction_of_kelly_used': kelly_fraction, 'suggested_bet_size': suggested_bet, 'bankroll': bankroll, 'bet_side': bet_side}

    # write JSON if requested
    if out_json:
        try:
            import json
            with open(out_json, 'w', encoding='utf8') as fh:
                json.dump(result, fh, indent=2, default=str)
            print(f'Wrote JSON output to {out_json}')
        except Exception as e:
            print('Failed to write JSON:', e)

    # write CSV summary if requested (minimal rows)
    if out_csv:
        try:
            import csv
            with open(out_csv, 'w', newline='', encoding='utf8') as fh:
                writer = csv.writer(fh)
                writer.writerow(['home', 'away', 'model_home_prob', 'model_away_prob', 'market_imp_home', 'market_imp_away', 'edge_vs_fair_home'])
                writer.writerow([home, away, model_home_prob, model_away_prob, imp_home, imp_away, (model_home_prob - fair_h) if (model_home_prob is not None and fair_h is not None) else None])
            print(f'Wrote CSV output to {out_csv}')
        except Exception as e:
            print('Failed to write CSV:', e)


if __name__ == '__main__':
    main()
"""Quick single-match analyzer
Usage: .venv/Scripts/python.exe analyze_one.py
Adjust `home`, `away`, and `home_odds`/`away_odds` as needed.
"""
from pprint import pprint

from src.data_collector import NBADataCollector
from src.analyzer import NBAAnalyzer


def implied_prob(decimal_odds):
    try:
        return 1.0 / float(decimal_odds)
    except Exception:
        return None


def safe_get_prob(analysis):
    """Try several possible shapes for analyzer output to extract home/away probs."""
    home = None
    away = None
    if analysis is None:
        return home, away
    if isinstance(analysis, dict):
        # common pattern: analysis['prediction'] -> dict with keys
        if 'prediction' in analysis and isinstance(analysis['prediction'], dict):
            p = analysis['prediction']
            home = p.get('home_win_probability') or p.get('home_prob') or p.get('home')
            away = p.get('away_win_probability') or p.get('away_prob') or p.get('away')
        else:
            home = analysis.get('home_win_probability') or analysis.get('home_prob') or analysis.get('home')
            away = analysis.get('away_win_probability') or analysis.get('away_prob') or analysis.get('away')
    return home, away


def main():
    # --- Edit these values as needed ---
    home = "New York Knicks"
    away = "Miami Heat"
    home_odds = 1.53  # decimal odds
    away_odds = 4.50  # decimal odds
    # -----------------------------------

    print("\n=== Single-match analysis ===")
    print(f"Match: {home} (home) vs {away} (away)")
    print(f"Market odds (decimal): home={home_odds}, away={away_odds}")

    imp_home = implied_prob(home_odds)
    imp_away = implied_prob(away_odds)
    if imp_home:
        print(f"Market implied probs: home={imp_home:.3f} ({imp_home:.1%}), away={imp_away:.3f} ({imp_away:.1%})")
    else:
        print("Market implied probs: could not parse odds")

    collector = NBADataCollector()
    analyzer = NBAAnalyzer()

    # Get recent performance / efficiency as context
    try:
        home_recent = collector.get_recent_performance(home)
    except Exception as e:
        home_recent = None
    try:
        away_recent = collector.get_recent_performance(away)
    except Exception:
        away_recent = None

    try:
        eff_home = collector.get_team_efficiency(home)
    except Exception:
        eff_home = None
    try:
        eff_away = collector.get_team_efficiency(away)
    except Exception:
        eff_away = None

    print('\nContext:')
    print(f"  {home}: recent_win_rate={home_recent}, NET_RATING={eff_home.get('NET_RATING') if eff_home else 'N/A'}")
    print(f"  {away}: recent_win_rate={away_recent}, NET_RATING={eff_away.get('NET_RATING') if eff_away else 'N/A'}")

    """Quick single-match analyzer with extra inputs (spread, water, injuries)
    Usage (example):
        .venv/Scripts/python.exe analyze_one.py
            --home "New York Knicks" --away "Miami Heat"
            --home-odds 1.53 --away-odds 4.5
            --home-spread -3.5 --away-spread 3.5 --home-water 0.98 --away-water 0.98
            --home-injuries "Randle: doubtful" --away-injuries "Butler: out"
    """

    from pprint import pprint
    import argparse
    from typing import Tuple, Optional

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
        """Convert market decimal odds into fair probabilities by removing overround.

        Returns (fair_home_prob, fair_away_prob).
        """
        ph = implied_prob(home_odds)
        pa = implied_prob(away_odds)
        if ph is None or pa is None:
            return None, None
        s = ph + pa
        if s <= 0:
            return None, None
        # normalize so they sum to 1 (remove vig)
        return ph / s, pa / s


    def safe_get_prob(analysis) -> Tuple[Optional[float], Optional[float]]:
        """Try several possible shapes for analyzer output to extract home/away probs."""
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


    def parse_args():
        p = argparse.ArgumentParser()
        p.add_argument('--home', default='New York Knicks')
        p.add_argument('--away', default='Miami Heat')
        p.add_argument('--home-odds', type=float, default=1.53)
        p.add_argument('--away-odds', type=float, default=4.50)
        p.add_argument('--home-spread', type=float, default=None)
        p.add_argument('--away-spread', type=float, default=None)
        p.add_argument('--home-water', type=float, default=None, help='Asian water / payout multiplier, e.g. 0.98')
        p.add_argument('--away-water', type=float, default=None)
        p.add_argument('--home-injuries', type=str, default='')
        p.add_argument('--away-injuries', type=str, default='')
        return p.parse_args()


    def main():
        args = parse_args()

        home = args.home
        away = args.away
        home_odds = args.home_odds
        away_odds = args.away_odds

        print('\n=== Single-match analysis (with extra inputs) ===')
        print(f'Match: {home} (home) vs {away} (away)')
        print(f'Market odds (decimal): home={home_odds}, away={away_odds}')
        if args.home_spread is not None:
            print(f'Parsed spreads: home {args.home_spread}, away {args.away_spread}')
        if args.home_water is not None:
            print(f'Asian water / payout multipliers: home {args.home_water}, away {args.away_water}')
        if args.home_injuries or args.away_injuries:
            print(f'Injuries / notes: home[{args.home_injuries}] away[{args.away_injuries}]')

        # Market implied probs (raw)
        imp_home = implied_prob(home_odds)
        imp_away = implied_prob(away_odds)
        fair_h = fair_a = None
        if imp_home is not None and imp_away is not None:
            print(f'Market implied probs (raw): home={imp_home:.3f} ({imp_home:.1%}), away={imp_away:.3f} ({imp_away:.1%})')
            fair_h, fair_a = fair_probs_from_odds(home_odds, away_odds)
            if fair_h is not None:
                print(f'Fair market probs (normalized, remove vig): home={fair_h:.3f} ({fair_h:.1%}), away={fair_a:.3f} ({fair_a:.1%})')
        else:
            print('Market implied probs: could not parse odds')

        # Context from collector
        collector = NBADataCollector()
        analyzer = NBAAnalyzer()

        try:
            home_recent = collector.get_recent_performance(home)
        except Exception:
            home_recent = None
        try:
            away_recent = collector.get_recent_performance(away)
        except Exception:
            away_recent = None

        try:
            eff_home = collector.get_team_efficiency(home)
        except Exception:
            eff_home = None
        try:
            eff_away = collector.get_team_efficiency(away)
        except Exception:
            eff_away = None

        print('\nContext:')
        print(f'  {home}: recent_win_rate={home_recent}, NET_RATING={eff_home.get("NET_RATING") if eff_home else "N/A"}')
        print(f'  {away}: recent_win_rate={away_recent}, NET_RATING={eff_away.get("NET_RATING") if eff_away else "N/A"}')

        # Run analyzer
        print('\nRunning model prediction...')
        try:
            analysis = analyzer.analyze_matchup(home, away)
        except Exception as e:
            print('Analyzer failed:', e)
            analysis = None

        print('\nRaw model output:')
        pprint(analysis)

        # Extract structured probs if available
        model_home_prob, model_away_prob = safe_get_prob(analysis)

        # Report model vs market and fair market
        if model_home_prob is not None:
            mh = float(model_home_prob)
            print(f"\nModel home win probability: {mh:.3f} ({mh:.1%})")
            if imp_home is not None:
                edge_raw = mh - imp_home
                print(f"Edge vs market (raw implied): {edge_raw:.3f} ({edge_raw:.1%})")
            if fair_h is not None:
                edge_fair = mh - fair_h
                print(f"Edge vs fair market (normalized): {edge_fair:.3f} ({edge_fair:.1%})")
        else:
            print('\nModel did not return structured home probability')

        # Recommendation using fair market (normalized) by default if available
        if model_home_prob is not None and fair_h is not None:
            mh = float(model_home_prob)
            edge = mh - fair_h
            if edge > 0.05:
                print('\nRecommendation: POSITIVE EDGE on HOME (consider bet)')
            elif edge < -0.05:
                print('\nRecommendation: MARKET FAVORS HOME MUCH MORE (avoid)')
            else:
                print('\nRecommendation: No clear value (edge small)')

        print('\n=== End analysis ===\n')


    if __name__ == '__main__':
        main()
