import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import NBADataCollector


def test_data_collector_loading():
    # teams.get_teams is patched in conftest; constructing collector should work
    collector = NBADataCollector()
    assert len(collector.team_ids) >= 1
    assert "Toronto Raptors" in collector.team_ids


def test_data_collector_methods(sample_games, mock_collector):
    # mock_collector fixture patches src.data_collector.NBADataCollector
    # so importing and constructing the class in other modules uses the mock
    from src.data_collector import NBADataCollector
    inst = NBADataCollector()

    games = inst.get_team_games("Toronto Raptors")
    assert games is not None

    efficiency = inst.get_team_efficiency("Toronto Raptors")
    assert efficiency is not None
    assert 'NET_RATING' in efficiency


if __name__ == "__main__":
    test_data_collector_loading()
    print("All data collector tests passed")
