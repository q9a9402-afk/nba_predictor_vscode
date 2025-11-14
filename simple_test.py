print('開始測試...')
try:
    from src.data_collector import NBADataCollector
    print('導入成功！')
    collector = NBADataCollector()
    print('收集器建立成功！')
except Exception as e:
    print('錯誤:', e)
    import traceback
    traceback.print_exc()
