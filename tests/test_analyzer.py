import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def test_analyzer_prediction_and_analysis(mock_collector):
    # mock_collector fixture ensures src.data_collector.NBADataCollector is patched
    from src.analyzer import NBAAnalyzer
    analyzer = NBAAnalyzer()

    prediction = analyzer.predict_game("Toronto Raptors", "Brooklyn Nets")
    assert prediction is not None and ('home_win_probability' in prediction and 0 <= prediction['home_win_probability'] <= 1)

    analysis = analyzer.analyze_matchup("Toronto Raptors", "Brooklyn Nets")
    assert analysis is not None and 'prediction' in analysis


if __name__ == "__main__":
    print("Run with pytest")
