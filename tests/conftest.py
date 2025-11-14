import pytest
import pandas as pd
from unittest.mock import MagicMock


@pytest.fixture
def sample_games():
    return pd.DataFrame({"GAME_DATE": ["2025-11-01", "2025-11-02"], "WL": ["W", "L"]})


@pytest.fixture
def mock_collector(monkeypatch, sample_games):
    # Patch teams.get_teams to a minimal list
    fake_teams = [{"full_name": "Toronto Raptors", "id": 1}, {"full_name": "Brooklyn Nets", "id": 2}]
    monkeypatch.setattr("src.data_collector.teams.get_teams", lambda: fake_teams)

    # Create a MagicMock instance to stand in for NBADataCollector
    MockCollector = MagicMock()
    inst = MockCollector.return_value
    inst.get_team_games.return_value = sample_games
    inst.get_team_efficiency.return_value = {"NET_RATING": 2.0, "OFF_RATING": 110.0, "DEF_RATING": 108.0, "PACE": 100.0}
    inst.get_recent_performance.return_value = 0.5

    # Also expose the class so tests can patch it
    monkeypatch.setattr("src.data_collector.NBADataCollector", MockCollector)
    return inst
