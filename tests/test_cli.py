import json
from pathlib import Path

import analyze_cli


class DummyCollector:
    def get_recent_performance(self, t):
        return 0.5

    def get_team_efficiency(self, t):
        return {'NET_RATING': 0.0}


class DummyAnalyzer:
    def analyze_matchup(self, h, a):
        return {'prediction': {'home_team': h, 'away_team': a, 'home_win_probability': 0.6, 'away_win_probability': 0.4, 'predicted_winner': h}}


def test_cli_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(analyze_cli, 'NBADataCollector', lambda: DummyCollector())
    monkeypatch.setattr(analyze_cli, 'NBAAnalyzer', lambda: DummyAnalyzer())
    out = tmp_path / 'out.json'
    monkeypatch.setattr('sys.argv', ['prog', '--home', 'A', '--away', 'B', '--home-odds', '2.0', '--away-odds', '3.0', '--output-json', str(out), '--bet-side', 'home', '--bankroll', '1000', '--kelly-fraction', '0.5'])
    analyze_cli.main()
    assert out.exists()
    j = json.loads(out.read_text())
    assert j['model']['home_prob'] == 0.6
