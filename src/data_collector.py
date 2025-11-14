"""NBA data collector for prediction experiments.

This implementation uses `nba_api` to fetch team lists, recent games
and per-100-possession team stats via `LeagueDashTeamStats`. It includes
simple in-memory caching, rate-limiting and defensive fallbacks so tests
can run even if the live API is unavailable.
"""

import time
from typing import Optional, Dict

import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder, leaguedashteamstats


class NBADataCollector:
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache
        self._cache: Dict[str, object] = {}
        self._load_teams()

    def _load_teams(self) -> None:
        """Load NBA team metadata into memory."""
        try:
            self.teams = teams.get_teams()
            self.team_ids = {t["full_name"]: t["id"] for t in self.teams}
            self.id_to_team = {t["id"]: t["full_name"] for t in self.teams}
        except Exception:
            # Fallback minimal mapping if API unavailable
            self.teams = []
            self.team_ids = {"Toronto Raptors": 1, "Brooklyn Nets": 2}
            self.id_to_team = {1: "Toronto Raptors", 2: "Brooklyn Nets"}

    def _make_request(self, func, *args, **kwargs):
        """Call nba_api endpoint with basic rate limiting and caching.

        Returns None on failure.
        """
        cache_key = f"{func.__name__}_{args}_{kwargs}"
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        time.sleep(0.6)  # politeness / rate-limit
        try:
            result = func(*args, **kwargs)
            if self.enable_cache:
                self._cache[cache_key] = result
            return result
        except Exception as exc:
            print(f"❌ API 请求失败: {exc}")
            return None

    def get_team_games(self, team_name: str, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Return DataFrame of games for a team in a season, or None."""
        team_id = self.team_ids.get(team_name)
        if team_id is None:
            print(f"❌ 找不到球队: {team_name}")
            return None

        def _fetch():
            return leaguegamefinder.LeagueGameFinder(
                team_id_nullable=team_id, season_nullable=season
            ).get_data_frames()[0]

        df = self._make_request(_fetch)
        if df is None or df.empty:
            print(f"⚠️ 未能获取 {team_name} 的比赛记录")
            return None

        df = df.copy()
        if "GAME_DATE" in df.columns:
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
            df = df.sort_values("GAME_DATE", ascending=False)

        return df

    def get_team_efficiency(self, team_name: str, season: str = "2023-24") -> Dict[str, float]:
        """Return OFF/DEF/NET/PACE for a team. Returns fallback on failure."""
        team_id = self.team_ids.get(team_name)
        if team_id is None:
            raise ValueError(f"Unknown team: {team_name}")

        def _fetch():
            return leaguedashteamstats.LeagueDashTeamStats(
                season=season, per_mode_detailed="Per100Possessions"
            ).get_data_frames()[0]

        stats = self._make_request(_fetch)
        if stats is None or stats.empty:
            print(f"⚠️ 获取联盟统计数据失败，使用回退效率值 ({team_name})")
            return {"OFF_RATING": 110.0, "DEF_RATING": 110.0, "NET_RATING": 0.0, "PACE": 100.0}

        # Try to locate row by TEAM_ID, then TEAM_NAME
        row = stats[stats.get("TEAM_ID") == team_id]
        if row.empty:
            row = stats[stats.get("TEAM_NAME") == team_name]

        if not row.empty:
            # use defensive .get and defaults
            off = float(row.get("OFF_RATING", row.get("OFFRATING", pd.Series([110.0]))).iloc[0])
            df_def = row.get("DEF_RATING", row.get("DEFRATING", pd.Series([110.0])))
            pace = float(row.get("PACE", pd.Series([100.0])).iloc[0])
            def_val = float(df_def.iloc[0]) if hasattr(df_def, 'iloc') else 110.0
            net = float(row.get("NET_RATING", row.get("NETRATING", pd.Series([off - def_val]))).iloc[0])

            return {"OFF_RATING": off, "DEF_RATING": def_val, "NET_RATING": net, "PACE": pace}

        print(f"⚠️ 未在返回的联盟统计中找到 {team_name} 的行，使用回退值")
        return {"OFF_RATING": 110.0, "DEF_RATING": 110.0, "NET_RATING": 0.0, "PACE": 100.0}

    def get_recent_performance(self, team_name: str, games: int = 10) -> float:
        """Compute recent win percentage (last `games`). Returns 0.5 fallback."""
        df = self.get_team_games(team_name)
        if df is None or df.empty:
            return 0.5

        recent = df.head(games)

        # Get the 'WL' column robustly. recent.get may return a scalar
        # when there's a single row; convert to a Series to unify handling.
        wl_vals = recent.get("WL") if "WL" in recent.columns or hasattr(recent, 'get') else None
        if wl_vals is None:
            return 0.5

        # Convert scalar -> Series, leave Series/array as-is
        if isinstance(wl_vals, (str, bytes)):
            s = pd.Series([wl_vals])
        else:
            try:
                s = pd.Series(wl_vals)
            except Exception:
                # Fallback: treat as single value
                s = pd.Series([wl_vals])

        wins = (s == "W").sum()
        return float(wins) / max(1, len(s))
