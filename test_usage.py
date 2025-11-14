# test_usage.py - NBA Predictor 測試
print("=== NBA Predictor 測試開始 ===")
import pandas as pd

try:
    # 導入模組
    from src.data_collector import NBADataCollector
    from src.analyzer import NBAAnalyzer
    print("✅ 模組導入成功")
    
    # 測試資料收集器
    collector = NBADataCollector()
    print("✅ 資料收集器建立成功")
    
    # 取得球隊列表（部分實作使用屬性 `teams`）
    if hasattr(collector, 'get_all_teams'):
        teams = collector.get_all_teams()
    else:
        teams = getattr(collector, 'teams', []) or []

    print(f"✅ 找到 {len(teams)} 支 NBA 球隊")

    # 顯示前3支球隊（若 teams 為 dict list，使用 'full_name'，否則列出原始值）
    for i in range(min(3, len(teams))):
        team = teams[i]
        if isinstance(team, dict) and 'full_name' in team:
            print(f"   {i+1}. {team['full_name']}")
        else:
            print(f"   {i+1}. {team}")
    
    # 測試取得效率資料
    print("正在取得多倫多暴龍隊資料...")
    efficiency = collector.get_team_efficiency("Toronto Raptors")
    if efficiency:
        print("✅ 效率資料取得成功:")
        print(f"   進攻效率: {efficiency.get('OFF_RATING', 'N/A')}")
        print(f"   防守效率: {efficiency.get('DEF_RATING', 'N/A')}")
        print(f"   淨效率: {efficiency.get('NET_RATING', 'N/A')}")
    else:
        print("⚠️ 未取得效率資料，可能為 API 或網路問題")
    
    # 測試分析器
    print("正在測試比賽分析...")
    analyzer = NBAAnalyzer()
    result = analyzer.predict_game("Toronto Raptors", "Brooklyn Nets")
    if result:
        print("✅ 預測分析成功:")
        print(f"   暴龍勝率: {result.get('home_win_probability', 'N/A')}")
        print(f"   籃網勝率: {result.get('away_win_probability', 'N/A')}")
        print(f"   預測勝方: {result.get('predicted_winner', 'N/A')}")
    else:
        print("⚠️ 分析器未回傳結果")

    # 新增多場比賽分析
    matchups = [
        ("Los Angeles Lakers", "Golden State Warriors"),
        ("Boston Celtics", "Miami Heat"),
        ("Phoenix Suns", "Dallas Mavericks")
    ]

    print("\n正在分析多組對戰...")
    for home, away in matchups:
        print(f"--- {home} vs {away} ---")
        try:
            analysis = analyzer.analyze_matchup(home, away)
            if analysis:
                print(f"  主隊勝率: {analysis.get('home_win_probability', 'N/A')}")
                print(f"  客隊勝率: {analysis.get('away_win_probability', 'N/A')}")
                print(f"  預測勝方: {analysis.get('predicted_winner', 'N/A')}")
            else:
                print("  ⚠️ 未取得分析結果")
        except Exception as e:
            print(f"  ❌ 分析 {home} vs {away} 時發生錯誤: {e}")
    
    # 添加近期表現趨勢（針對前 6 支球隊）
    teams_to_analyze = []
    for t in teams:
        if isinstance(t, dict) and 'full_name' in t:
            teams_to_analyze.append(t['full_name'])
        else:
            teams_to_analyze.append(str(t))

    print('\n📊 近期表現趨勢:')
    for team in teams_to_analyze[:6]:  # 只分析前6支球隊
        try:
            recent_performance = collector.get_recent_performance(team, games=10)
        except Exception:
            recent_performance = None
        try:
            efficiency = collector.get_team_efficiency(team)
        except Exception:
            efficiency = None

        if efficiency is not None and recent_performance is not None:
            net_rating = efficiency.get('NET_RATING', 0)
            if net_rating > 2:
                trend = "↑上升"
            elif net_rating < -2:
                trend = "↓下降"
            else:
                trend = "→平稳"
            print(f"{team:25}  近期胜率: {recent_performance:.1%} | 净效率: {net_rating:+.1f} {trend}")
        else:
            print(f"{team:25}  ⚠️ 无法取得近期数据或效率資料")

    # 對決矩陣分析：選取淨效率最高的前 4 支隊伍進行配對分析
    print("\n🥊 球隊對決勝率矩陣:")
    print('-' * 50)

    # 建立以 NET_RATING 排序的 DataFrame
    rows = []
    for t in teams_to_analyze:
        try:
            eff = collector.get_team_efficiency(t)
            net = eff.get('NET_RATING', 0) if eff else 0
        except Exception:
            net = 0
        rows.append({'Team': t, 'NET_RATING': net})

    df_sorted = pd.DataFrame(rows).sort_values('NET_RATING', ascending=False).reset_index(drop=True)
    print('Top teams by NET_RATING:')
    print(df_sorted.head(4).to_string(index=False))

    top_teams = df_sorted.head(4)['Team'].tolist()
    for i, team1 in enumerate(top_teams):
        for j, team2 in enumerate(top_teams):
            if i < j:
                try:
                    analysis = analyzer.analyze_matchup(team1, team2)
                    # 支援不同的回傳格式：若有 'prediction' 關鍵字則使用它，否則嘗試直接讀取
                    pred = None
                    if isinstance(analysis, dict):
                        pred = analysis.get('prediction') or analysis

                    if pred and isinstance(pred, dict):
                        winner = pred.get('predicted_winner', 'N/A')
                        home_prob = pred.get('home_win_probability')
                        if home_prob is not None:
                            print(f"{team1:20} 🆚 {team2:20} → {winner:20} ({home_prob:.1%})")
                        else:
                            print(f"{team1:20} 🆚 {team2:20} → {winner:20}")
                    else:
                        print(f"{team1:20} 🆚 {team2:20} → 無結構化預測")
                except Exception as e:
                    print(f"{team1} vs {team2} 分析錯誤: {e}")

    # 產生結構化的對決結果並儲存為 CSV（此步驟會再次呼叫 analyzer，僅用於建立報表）
    import os
    reports_dir = os.path.join(os.getcwd(), 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    match_rows = []
    for i, team1 in enumerate(top_teams):
        for j, team2 in enumerate(top_teams):
            if i < j:
                try:
                    analysis = analyzer.analyze_matchup(team1, team2)
                    pred = None
                    if isinstance(analysis, dict):
                        pred = analysis.get('prediction') or analysis

                    if isinstance(pred, dict):
                        match_rows.append({
                            'home': team1,
                            'away': team2,
                            'predicted_winner': pred.get('predicted_winner'),
                            'home_win_probability': pred.get('home_win_probability'),
                            'away_win_probability': pred.get('away_win_probability')
                        })
                    else:
                        match_rows.append({'home': team1, 'away': team2, 'predicted_winner': None})
                except Exception as e:
                    match_rows.append({'home': team1, 'away': team2, 'error': str(e)})

    try:
        df_match = pd.DataFrame(match_rows)
        matchup_csv = os.path.join(reports_dir, 'matchup_matrix.csv')
        df_match.to_csv(matchup_csv, index=False, encoding='utf-8-sig')
        print(f"📁 已將對決矩陣儲存為: {matchup_csv}")
    except Exception as e:
        print(f"⚠️ 儲存對決矩陣失敗: {e}")

    # 產生近期趨勢 CSV（前 6 支隊伍）
    recent_rows = []
    for team in teams_to_analyze[:6]:
        try:
            rp = collector.get_recent_performance(team, games=10)
        except Exception:
            rp = None
        try:
            eff = collector.get_team_efficiency(team)
            net = eff.get('NET_RATING') if eff else None
        except Exception:
            net = None
        recent_rows.append({'team': team, 'recent_win_rate': rp, 'net_rating': net})

    try:
        df_recent = pd.DataFrame(recent_rows)
        recent_csv = os.path.join(reports_dir, 'recent_trends.csv')
        df_recent.to_csv(recent_csv, index=False, encoding='utf-8-sig')
        print(f"📁 已將近期趨勢儲存為: {recent_csv}")
    except Exception as e:
        print(f"⚠️ 儲存近期趨勢失敗: {e}")

    print("🎉 所有測試完成")

except Exception as e:
    print(f"❌ 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
