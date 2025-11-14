"""
Minimal NBA game analyzer for prediction experiments.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class NBAAnalyzer:
    def __init__(self, data_collector=None):
        from .data_collector import NBADataCollector
        self.collector = data_collector or NBADataCollector()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def extract_features(self, home_team, away_team):
        """Extract features for prediction."""
        home_data = self._get_team_data(home_team)
        away_data = self._get_team_data(away_team)

        if not home_data or not away_data:
            print("❌ 无法获取球队数据")
            return None

        features = [
            home_data['NET_RATING'] - away_data['NET_RATING'],
            home_data['OFF_RATING'] - away_data['DEF_RATING'],
            home_data['recent_win_pct'] - away_data['recent_win_pct'],
            0.04  # Home court advantage
        ]

        return np.array(features).reshape(1, -1)

    def _get_team_data(self, team_name):
        """Get team data for analysis."""
        efficiency = self.collector.get_team_efficiency(team_name)
        recent_win_pct = self.collector.get_recent_performance(team_name)

        if not efficiency:
            print(f"❌ 无法获取 {team_name} 的数据")
            return None
            
        return {
            'NET_RATING': efficiency.get('NET_RATING', 0.0),
            'OFF_RATING': efficiency.get('OFF_RATING', 110.0), 
            'DEF_RATING': efficiency.get('DEF_RATING', 110.0),
            'recent_win_pct': recent_win_pct
        }

    def train_model(self, historical_data):
        """Train the prediction model (placeholder)."""
        # This would require historical game data with features and outcomes
        # For minimal version, we'll use a simple heuristic approach
        self.is_trained = True

    def predict_game(self, home_team, away_team):
        """Predict game outcome."""
        print(f"🎯 预测比赛: {home_team} vs {away_team}")
        
        features = self.extract_features(home_team, away_team)
        if features is None:
            print("❌ 特征提取失败，使用默认预测")
            return {
                'home_team': home_team,
                'away_team': away_team, 
                'home_win_probability': 0.5,
                'away_win_probability': 0.5,
                'predicted_winner': "未知"
            }
        
        # Simple heuristic prediction (can be replaced with trained model)
        net_rating_diff = features[0, 0]
        home_win_prob = 0.5 + (net_rating_diff * 0.015) + 0.04
        
        home_win_prob = max(0.05, min(0.95, home_win_prob))
        
        predicted_winner = home_team if home_win_prob > 0.5 else away_team
        
        print(f"✅ 预测完成: {predicted_winner} 胜率 {home_win_prob:.1%}")
        
        return {
            'home_team': home_team,
            'away_team': away_team, 
            'home_win_probability': home_win_prob,
            'away_win_probability': 1 - home_win_prob,
            'predicted_winner': predicted_winner
        }

    def analyze_matchup(self, home_team, away_team):
        """Analyze team matchup."""
        prediction = self.predict_game(home_team, away_team)
        if not prediction:
            return None
        
        # Add basic analysis
        home_data = self._get_team_data(home_team)
        away_data = self._get_team_data(away_team)
        
        analysis = {
            'prediction': prediction,
            'efficiency_comparison': {
                'net_rating_diff': home_data['NET_RATING'] - away_data['NET_RATING'] if home_data and away_data else 0,
                'home_off_vs_away_def': home_data['OFF_RATING'] - away_data['DEF_RATING'] if home_data and away_data else 0
            },
            'recent_form': {
                'home_win_pct': home_data['recent_win_pct'] if home_data else 0.5,
                'away_win_pct': away_data['recent_win_pct'] if away_data else 0.5
            }
        }
        
        return analysis
