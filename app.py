import sys
import subprocess
from pathlib import Path

import streamlit as st


PY = sys.executable
ROOT = Path(__file__).parent
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)


def run_command(cmd):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        return proc.returncode, proc.stdout + '\n' + proc.stderr
    except Exception as e:
        return 1, str(e)


st.title('NBA Predictor — 控制面板')

st.write('輕量面板：可執行測試、執行單場分析並匯出 JSON/CSV 報表。')

with st.expander('單場分析設定'):
    home = st.text_input('Home team', 'New York Knicks')
    away = st.text_input('Away team', 'Miami Heat')
    home_odds = st.number_input('Home decimal odds', value=1.53, format='%.2f')
    away_odds = st.number_input('Away decimal odds', value=4.50, format='%.2f')
    out_json = st.text_input('Output JSON path (relative)', 'reports/last_analysis.json')
    out_csv = st.text_input('Output CSV path (relative)', 'reports/last_analysis.csv')
    bet_side = st.selectbox('Kelly bet side', ['none', 'home', 'away'])
    bankroll = st.number_input('Bankroll (for Kelly)', value=1000.0)
    kelly_frac = st.slider('Kelly fraction', 0.0, 1.0, 0.5)

col1, col2 = st.columns(2)

if col1.button('Run single-match analysis'):
    cmd = [PY, 'analyze_cli.py', '--home', home, '--away', away, '--home-odds', str(home_odds), '--away-odds', str(away_odds)]
    if out_json:
        cmd += ['--output-json', out_json]
    if out_csv:
        cmd += ['--output-csv', out_csv]
    if bet_side in ('home', 'away'):
        cmd += ['--bet-side', bet_side, '--bankroll', str(bankroll), '--kelly-fraction', str(kelly_frac)]

    code, out = run_command(cmd)
    st.text_area('Analysis output', out, height=300)

if col2.button('Run tests (pytest)'):
    cmd = [PY, '-m', 'pytest', '-q']
    code, out = run_command(cmd)
    if code == 0:
        st.success('pytest passed')
    else:
        st.error('pytest failed')
    st.text_area('pytest output', out, height=300)

st.markdown('---')

st.header('Reports')
if (REPORTS / 'last_analysis.json').exists():
    st.write('Last analysis JSON:')
    try:
        with open(REPORTS / 'last_analysis.json', 'r', encoding='utf8') as fh:
            st.json(fh.read())
    except Exception:
        st.write('Could not display JSON (maybe invalid)')
else:
    st.write('No `reports/last_analysis.json` found yet.')

if (REPORTS / 'last_analysis.csv').exists():
    st.write('Last analysis CSV:')
    st.dataframe((REPORTS / 'last_analysis.csv').read_text())
else:
    st.write('No `reports/last_analysis.csv` found yet.')

st.markdown('---')

st.write('Run the app locally with:')
st.code(f"{PY} -m streamlit run app.py")
