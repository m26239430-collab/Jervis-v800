ki # ==============================================================================
# JERVIS V800 - MASTER UNIVERSAL QUANTITATIVE & SMC TRADING ENGINE
# Features: Auto-Library Installer, Explicit Extended OOP Logic,
# Smart Money Concepts (Order Blocks, FVG, Sweeps), 4-Timeframe Matrix (5M/15M/1H/4H),
# Separate 5M & 15M Engines, Random Forest ML, Real-time Backtest, DB & Telegram,
# Trading Session Filter (London/NY), Dynamic Trailing Stop & Break-Even Engine.
# ==============================================================================

import sys
import subprocess
from datetime import datetime, timezone

# --- 1. FIXED AUTO-INSTALLATION PIPELINE (No Loop Bug) ---
LIB_MAP = {
    'yfinance': 'yfinance',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'matplotlib': 'matplotlib',
    'scikit-learn': 'sklearn',
    'requests': 'requests',
    'IPython': 'IPython'
}

for pkg, module in LIB_MAP.items():
    try:
        __import__(module)
    except ImportError:
        print(f"📦 Auto-Installing missing library: '{pkg}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

print("✅ ALL LIBRARIES OK! Starting JERVIS V800 Engine...")

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import requests
import io
import sqlite3
import logging
import warnings
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from IPython.display import display, clear_output

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# --- GLOBAL CONFIGURATION PARAMETERS ---
SYMBOL = "EURUSD=X"
REFRESH_SECONDS = 600      # 10 Minutes Cycle
ACCOUNT_BALANCE = 10000.0  # $10,000 Trading Account
BASE_RISK_PERCENT = 1.0    # 1% Risk per trade
TARGET_RR_RATIO = 2.5      # Dynamic Risk-Reward Ratio (1:2.5)
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
# --- 2. SQLITE DATABASE PERSISTENCE ENGINE ---
class JervisV800Database:
    def __init__(self, db_name="jervis_v800_master.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                price REAL,
                signal_5m TEXT,
                signal_15m TEXT,
                master_signal TEXT,
                win_rate REAL,
                ml_confidence REAL,
                liquidity_condition TEXT,
                fvg_status TEXT,
                active_session TEXT,
                trailing_sl REAL,
                break_even_active INTEGER
            )
        ''')
        self.conn.commit()

    def insert_log(self, timestamp, symbol, price, sig_5m, sig_15m, master_sig, win_rate, ml_conf, liq_cond, fvg_stat, session, trailing_sl, be_active):
        self.cursor.execute('''
            INSERT INTO system_logs (timestamp, symbol, price, signal_5m, signal_15m, master_signal, win_rate, ml_confidence, liquidity_condition, fvg_status, active_session, trailing_sl, break_even_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, symbol, price, sig_5m, sig_15m, master_sig, win_rate, ml_conf, liq_cond, fvg_stat, session, trailing_sl, be_active))
        self.conn.commit()


# --- 3. TELEGRAM DISPATCHER & ALERT SYSTEM ---
class TelegramAlertEngine:
    @staticmethod
    def send_notification(message, figure_object=None):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return
        try:
            if figure_object is not None:
                buffer = io.BytesIO()
                figure_object.savefig(buffer, format='png', bbox_inches='tight', facecolor='black')
                buffer.seek(0)
                endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                files_payload = {'photo': buffer}
                data_payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message}
                requests.post(endpoint, data=data_payload, files=files_payload, timeout=12)
            else:
                endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                data_payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
                requests.post(endpoint, data=data_payload, timeout=12)
        except Exception as error:
            logging.error(f"Telegram Dispatcher Error: {error}")


# --- 4. TRADING SESSION & HIGH-IMPACT NEWS FILTER ENGINE ---
class MarketSessionEngine:
    @staticmethod
    def get_active_session():
        current_utc_hour = datetime.now(timezone.utc).hour
        current_weekday = datetime.now(timezone.utc).weekday()
        
        if current_weekday >= 5:
            return "MARKET_CLOSED_WEEKEND", False

        active_sessions = []
        if 8 <= current_utc_hour < 16:
            active_sessions.append("LONDON")
        if 13 <= current_utc_hour < 21:
            active_sessions.append("NEW_YORK")
        if 0 <= current_utc_hour < 8:
            active_sessions.append("ASIA")
            
        session_str = " + ".join(active_sessions) if active_sessions else "OFF_HOURS"
        is_prime_volume = ("LONDON" in active_sessions) or ("NEW_YORK" in active_sessions)
        
        return session_str, is_prime_volume


# --- 5. DYNAMIC TRAILING STOP & BREAK-EVEN ENGINE ---
class DynamicTrailingEngine:
    @staticmethod
    def compute_trailing_and_breakeven(entry_price, current_price, initial_sl, atr_value, trade_type):
        risk_distance = abs(entry_price - initial_sl)
        current_profit = (current_price - entry_price) if trade_type == "BUY" else (entry_price - current_price)
        
        break_even_active = 0
        updated_sl = initial_sl
        
        if current_profit >= (risk_distance * 1.5):
            break_even_active = 1
            updated_sl = entry_price
            
        if trade_type == "BUY":
            trail_sl = current_price - (atr_value * 1.2)
            updated_sl = max(updated_sl, trail_sl)
        elif trade_type == "SELL":
            trail_sl = current_price + (atr_value * 1.2)
            updated_sl = min(updated_sl, trail_sl)
            
        return updated_sl, break_even_active


# --- 6. MULTI-TIMEFRAME DATA PIPELINE & NEWS ENGINE ---
class DataPipelineManager:
    @staticmethod
    def fetch_live_sentiment(symbol_string):
        try:
            ticker_obj = yf.Ticker(symbol_string)
            news_feed = ticker_obj.news
            if not news_feed:
                return "Neutral Market Environment", 0
            
            bullish_keywords = ['high', 'gain', 'bull', 'growth', 'rise', 'positive', 'strong', 'up', 'surge', 'rally', 'beat']
            bearish_keywords = ['low', 'loss', 'bear', 'fall', 'drop', 'negative', 'weak', 'down', 'plunge', 'slump', 'miss']
            
            sentiment_index = 0
            primary_headline = news_feed[0].get('title', 'Market Updating')
            
            for news_item in news_feed[:10]:
                headline_text = news_item.get('title', '').lower()
                for word in bullish_keywords:
                    if word in headline_text:
                        sentiment_index += 1
                for word in bearish_keywords:
                    if word in headline_text:
                        sentiment_index -= 1
                        
            return primary_headline[:55] + "...", sentiment_index
        except Exception:
            return "News Processing Active", 0

    @staticmethod
    def download_multi_tf_datasets():
        df_5m = yf.download(SYMBOL, period="5d", interval="5m", progress=False)
        df_15m = yf.download(SYMBOL, period="10d", interval="15m", progress=False)
        df_1h = yf.download(SYMBOL, period="30d", interval="1h", progress=False)
        df_4h = yf.download(SYMBOL, period="60d", interval="1h", progress=False)
        
        for dataframe in [df_5m, df_15m, df_1h, df_4h]:
            if isinstance(dataframe.columns, pd.MultiIndex):
                dataframe.columns = dataframe.columns.get_level_values(0)
            dataframe.columns = [str(col).strip() for col in dataframe.columns]
                
        return df_5m.dropna(), df_15m.dropna(), df_1h.dropna(), df_4h.dropna()


# --- 7. INSTITUTIONAL & SMART MONEY CONCEPTS (SMC) ENGINE ---
class SmartMoneyQuantEngine:
    @staticmethod
    def calculate_full_technical_stack(df):
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        wma_10 = df['Close'].rolling(10).apply(lambda x: np.dot(x, np.arange(1, 11)) / np.sum(np.arange(1, 11)), raw=True)
        wma_20 = df['Close'].rolling(20).apply(lambda x: np.dot(x, np.arange(1, 21)) / np.sum(np.arange(1, 21)), raw=True)
        hma_diff = (2 * wma_10) - wma_20
        df['HMA20'] = hma_diff.rolling(4).apply(lambda x: np.dot(x, np.arange(1, 5)) / np.sum(np.arange(1, 5)), raw=True)

        price_diff = df['Close'].diff()
        gain = (price_diff.where(price_diff > 0, 0)).rolling(14).mean()
        loss = (-price_diff.where(price_diff < 0, 0)).rolling(14).mean()
        relative_strength = gain / (loss + 1e-8)
        df['RSI'] = 100 - (100 / (1 + relative_strength))
        
        min_rsi = df['RSI'].rolling(14).min()
        max_rsi = df['RSI'].rolling(14).max()
        df['StochRSI'] = (df['RSI'] - min_rsi) / (max_rsi - min_rsi + 1e-8) * 100

        df['MACD'] = df['EMA12'] - df['EMA26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        df['BB_MID'] = df['Close'].rolling(20).mean()
        df['BB_STD'] = df['Close'].rolling(20).std()
        df['BB_UP'] = df['BB_MID'] + (2 * df['BB_STD'])
        df['BB_LOW'] = df['BB_MID'] - (2 * df['BB_STD'])
        df['BB_Bandwidth'] = (df['BB_UP'] - df['BB_LOW']) / df['BB_MID']

        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        volume_sum = df['Volume'].cumsum()
        
        if volume_sum.iloc[-1] == 0 or df['Volume'].sum() == 0:
            df['VWAP'] = df['EMA200']
        else:
            df['VWAP'] = (typical_price * df['Volume']).cumsum() / (volume_sum + 1e-8)
            df['VWAP'] = df['VWAP'].fillna(df['EMA200'])

        df['TR'] = pd.concat([df['High'] - df['Low'], abs(df['High'] - df['Close'].shift(1)), abs(df['Low'] - df['Close'].shift(1))], axis=1).max(axis=1)
        df['ATR'] = df['TR'].rolling(14).mean()

        mf_multiplier = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-8)
        df['CMF'] = (mf_multiplier * df['Volume']).rolling(20).sum() / (df['Volume'].rolling(20).sum() + 1e-8)

        df['Bullish_FVG'] = df['Low'] > df['High'].shift(2)
        df['Bearish_FVG'] = df['High'] < df['Low'].shift(2)

        df['Rolling_High_30'] = df['High'].rolling(30).max()
        df['Rolling_Low_30'] = df['Low'].rolling(30).min()
        df['Bullish_Sweep'] = (df['Low'] < df['Rolling_Low_30'].shift(1)) & (df['Close'] > df['Rolling_Low_30'].shift(1))
        df['Bearish_Sweep'] = (df['High'] > df['Rolling_High_30'].shift(1)) & (df['Close'] < df['Rolling_High_30'].shift(1))

        return df.dropna()

    @staticmethod
    def execute_vectorized_backtest(df):
        backtest_df = df.copy()
        backtest_df['Buy_Condition'] = (backtest_df['EMA9'] > backtest_df['EMA21']) & (backtest_df['Close'] > backtest_df['EMA50']) & (backtest_df['RSI'] > 50) & (backtest_df['MACD'] > backtest_df['MACD_Signal'])
        backtest_df['Sell_Condition'] = (backtest_df['EMA9'] < backtest_df['EMA21']) & (backtest_df['Close'] < backtest_df['EMA50']) & (backtest_df['RSI'] < 50) & (backtest_df['MACD'] < backtest_df['MACD_Signal'])
        
        backtest_df['Trade_Position'] = 0
        backtest_df.loc[backtest_df['Buy_Condition'], 'Trade_Position'] = 1
        backtest_df.loc[backtest_df['Sell_Condition'], 'Trade_Position'] = -1
        
        backtest_df['Strategy_Returns'] = backtest_df['Close'].pct_change() * backtest_df['Trade_Position'].shift(1)
        executed_trades = backtest_df[backtest_df['Trade_Position'].diff() != 0]
        
        winning_count = len(backtest_df[backtest_df['Strategy_Returns'] > 0])
        losing_count = len(backtest_df[backtest_df['Strategy_Returns'] < 0])
        
        calculated_winrate = (winning_count / (winning_count + losing_count + 1e-8)) * 100
        gross_profit = backtest_df[backtest_df['Strategy_Returns'] > 0]['Strategy_Returns'].sum()
        gross_loss = abs(backtest_df[backtest_df['Strategy_Returns'] < 0]['Strategy_Returns'].sum())
        profit_factor = gross_profit / (gross_loss + 1e-8)
        total_accumulated_return = backtest_df['Strategy_Returns'].sum() * 100
        
        return len(executed_trades), round(calculated_winrate, 1), round(profit_factor, 2), round(total_accumulated_return, 2)


# --- 8. ADVANCED RANDOM FOREST MACHINE LEARNING ENGINE ---
class AdvancedMachineLearningEngine:
    @staticmethod
    def train_and_forecast(df):
        feature_columns = ['EMA9', 'EMA21', 'EMA50', 'EMA200', 'RSI', 'StochRSI', 'MACD', 'BB_Bandwidth', 'ATR', 'CMF', 'HMA20', 'VWAP']
        clean_dataset = df[feature_columns + ['Close', 'Open', 'High', 'Low']].copy().dropna()
        
        clean_dataset['Target_Direction'] = np.where(clean_dataset['Close'].shift(-1) > clean_dataset['Close'], 1, -1)
        clean_dataset['Target_Return'] = clean_dataset['Close'].shift(-1) - clean_dataset['Close']
        
        training_samples = clean_dataset.iloc[:-1]
        latest_feature_row = clean_dataset[feature_columns].iloc[[-1]]
        
        feature_scaler = StandardScaler()
        scaled_training_features = feature_scaler.fit_transform(training_samples[feature_columns])
        scaled_latest_row = feature_scaler.transform(latest_feature_row)
        
        classifier_model = RandomForestClassifier(n_estimators=120, max_depth=8, random_state=42)
        classifier_model.fit(scaled_training_features, training_samples['Target_Direction'])
        direction_prediction = classifier_model.predict(scaled_latest_row)[0]
        prediction_probabilities = classifier_model.predict_proba(scaled_latest_row)[0]
        
        regressor_model = RandomForestRegressor(n_estimators=120, max_depth=8, random_state=42)
        regressor_model.fit(scaled_training_features, training_samples['Target_Return'])
        return_prediction = regressor_model.predict(scaled_latest_row)[0]
        
        current_market_price = df['Close'].iloc[-1]
        forecasted_trajectory = [current_market_price + (return_prediction * (0.85 ** i)) for i in range(5)]
        model_confidence = np.max(prediction_probabilities) * 100
        
        return forecasted_trajectory, direction_prediction, model_confidence


# --- 9. INDEPENDENT DUAL-TIMEFRAME EVALUATION ENGINE ---
class DualTimeframeAnalysisEngine:
    @staticmethod
    def evaluate_5m_timeframe(df_5m):
        c5 = df_5m['Close'].iloc[-1]
        ema9 = df_5m['EMA9'].iloc[-1]
        ema21 = df_5m['EMA21'].iloc[-1]
        ema50 = df_5m['EMA50'].iloc[-1]
        rsi = df_5m['RSI'].iloc[-1]
        
        bullish = (ema9 > ema21) and (c5 > ema50) and (rsi > 50)
        bearish = (ema9 < ema21) and (c5 < ema50) and (rsi < 50)
        
        if df_5m['Bullish_Sweep'].iloc[-1] or df_5m['Bullish_FVG'].iloc[-1]:
            bullish = True
        if df_5m['Bearish_Sweep'].iloc[-1] or df_5m['Bearish_FVG'].iloc[-1]:
            bearish = True
            
        return "BUY 🟢" if bullish else ("SELL 🔴" if bearish else "WAIT ⚪")

    @staticmethod
    def evaluate_15m_timeframe(df_15m):
        c15 = df_15m['Close'].iloc[-1]
        ema9 = df_15m['EMA9'].iloc[-1]
        ema21 = df_15m['EMA21'].iloc[-1]
        ema50 = df_15m['EMA50'].iloc[-1]
        rsi = df_15m['RSI'].iloc[-1]
        
        bullish = (ema9 > ema21) and (c15 > ema50) and (rsi > 50)
        bearish = (ema9 < ema21) and (c15 < ema50) and (rsi < 50)
        
        return "BUY 🟢" if bullish else ("SELL 🔴" if bearish else "WAIT ⚪")

    @staticmethod
    def check_macro_timeframes(df_1h, df_4h):
        macro_bull = (df_1h['Close'].iloc[-1] > df_1h['EMA50'].iloc[-1]) and (df_4h['Close'].iloc[-1] > df_4h['EMA50'].iloc[-1])
        macro_bear = (df_1h['Close'].iloc[-1] < df_1h['EMA50'].iloc[-1]) and (df_4h['Close'].iloc[-1] < df_4h['EMA50'].iloc[-1])
        return macro_bull, macro_bear


# --- 10. MAIN SYSTEM ORCHESTRATION LOOP ---
database_instance = JervisV800Database()
execution_cycle = 1

while True:
    try:
        session_str, is_prime_volume = MarketSessionEngine.get_active_session()
        if "MARKET_CLOSED" in session_str:
            logging.info("💤 Weekend detected. Market is closed. Resting for 1 hour...")
            time.sleep(3600)
            continue

        df_5m_raw, df_15m_raw, df_1h_raw, df_4h_raw = DataPipelineManager.download_multi_tf_datasets()
        
        df_5m = SmartMoneyQuantEngine.calculate_full_technical_stack(df_5m_raw.copy())
        df_15m = SmartMoneyQuantEngine.calculate_full_technical_stack(df_15m_raw.copy())
        df_1h = SmartMoneyQuantEngine.calculate_full_technical_stack(df_1h_raw.copy())
        df_4h = SmartMoneyQuantEngine.calculate_full_technical_stack(df_4h_raw.copy())
        
        news_headline, news_score = DataPipelineManager.fetch_live_sentiment(SYMBOL)
        total_trades, winrate_pct, profit_factor, total_return = SmartMoneyQuantEngine.execute_vectorized_backtest(df_5m)
        
        forecast_prices, ml_direction, ml_confidence = AdvancedMachineLearningEngine.train_and_forecast(df_5m)
        
        CURRENT_PRICE = df_5m['Close'].iloc[-1]
        signal_5m = DualTimeframeAnalysisEngine.evaluate_5m_timeframe(df_5m)
        signal_15m = DualTimeframeAnalysisEngine.evaluate_15m_timeframe(df_15m)
        macro_bullish, macro_bearish = DualTimeframeAnalysisEngine.check_macro_timeframes(df_1h, df_4h)
        
        current_atr = df_5m['ATR'].iloc[-1]
        sl_buy_level = CURRENT_PRICE - (current_atr * 1.5)
        tp_buy_level = CURRENT_PRICE + (current_atr * (1.5 * TARGET_RR_RATIO))
        sl_sell_level = CURRENT_PRICE + (current_atr * 1.5)
        tp_sell_level = CURRENT_PRICE - (current_atr * (1.5 * TARGET_RR_RATIO))
        
        trailing_sl_buy, be_active_buy = DynamicTrailingEngine.compute_trailing_and_breakeven(CURRENT_PRICE, CURRENT_PRICE, sl_buy_level, current_atr, "BUY")
        trailing_sl_sell, be_active_sell = DynamicTrailingEngine.compute_trailing_and_breakeven(CURRENT_PRICE, CURRENT_PRICE, sl_sell_level, current_atr, "SELL")
        
        risk_capital = ACCOUNT_BALANCE * (BASE_RISK_PERCENT / 100.0)
        lot_size_buy = max(round((risk_capital / abs(CURRENT_PRICE - sl_buy_level)) / 100000.0, 2), 0.01)
        lot_size_sell = max(round((risk_capital / abs(CURRENT_PRICE - sl_sell_level)) / 100000.0, 2), 0.01)
        
        if "BUY" in signal_5m and "BUY" in signal_15m and ml_direction == 1 and macro_bullish and winrate_pct >= 45 and is_prime_volume:
            MASTER_ALERT = f"🚨 MASTER BUY SIGNAL 🟢 @ {CURRENT_PRICE:.5f} | SL: {sl_buy_level:.5f} | TP: {tp_buy_level:.5f} | LOTS: {lot_size_buy} | SESSION: {session_str}"
            chart_color = 'lime'
            is_trade_active = True
            master_sig_type = "BUY"
            active_trailing_sl = trailing_sl_buy
            be_status = be_active_buy
        elif "SELL" in signal_5m and "SELL" in signal_15m and ml_direction == -1 and macro_bearish and winrate_pct >= 45 and is_prime_volume:
            MASTER_ALERT = f"🚨 MASTER SELL SIGNAL 🔴 @ {CURRENT_PRICE:.5f} | SL: {sl_sell_level:.5f} | TP: {tp_sell_level:.5f} | LOTS: {lot_size_sell} | SESSION: {session_str}"
            chart_color = 'red'
            is_trade_active = True
            master_sig_type = "SELL"
            active_trailing_sl = trailing_sl_sell
            be_status = be_active_sell
        else:
            MASTER_ALERT = f"🚨 STATUS: WAIT ⚪ | 5M [{signal_5m}] | 15M [{signal_15m}] | Session: {session_str}"
            chart_color = 'gray'
            is_trade_active = False
            master_sig_type = "WAIT"
            active_trailing_sl = 0.0
            be_status = 0
            
        liquidity_cond_str = "BULLISH SWEEP" if df_5m['Bullish_Sweep'].iloc[-1] else ("BEARISH SWEEP" if df_5m['Bearish_Sweep'].iloc[-1] else "NORMAL")
        fvg_stat_str = "BULL FVG" if df_5m['Bullish_FVG'].iloc[-1] else ("BEAR FVG" if df_5m['Bearish_FVG'].iloc[-1] else "NONE")
        
        database_instance.insert_log(
            datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            SYMBOL, CURRENT_PRICE, signal_5m, signal_15m, master_sig_type,
            winrate_pct, ml_confidence, liquidity_cond_str, fvg_stat_str,
            session_str, active_trailing_sl, be_status
        )
        
        # --- 11. SYNCHRONIZED MULTI-PANEL CHARTS RENDERING ---
        clear_output(wait=True)
        print(f"==================================================")
        print(f"--- Executing Master Cycle {execution_cycle} ---")
        print(f"==================================================")
        print(MASTER_ALERT)
        print(f"📊 BACKTEST PERFORMANCE: WinRate={winrate_pct}% | ProfitFactor={profit_factor} | Total Return={total_return}%")
        
        last_5m_candles = df_5m.tail(90)
        
        fig = plt.figure(figsize=(14, 10), facecolor='black')
        
        ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2, rowspan=2)
        ax1.set_facecolor('#050505')
        ax1.plot(last_5m_candles.index, last_5m_candles['Close'], color='white', lw=1.5, label='Close Price')
        ax1.plot(last_5m_candles.index, last_5m_candles['EMA9'], color='#00ff88', lw=1, label='EMA9')
        ax1.plot(last_5m_candles.index, last_5m_candles['EMA21'], color='#ffaa00', lw=1, label='EMA21')
        ax1.plot(last_5m_candles.index, last_5m_candles['VWAP'], color='cyan', lw=1, ls='--', label='VWAP')
        
        forecast_x_axis = pd.date_range(start=last_5m_candles.index[-1], periods=6, freq='5min')[1:]
        ax1.plot(forecast_x_axis, forecast_prices, color=chart_color, ls='--', marker='o', ms=6, lw=2, label='ML Forecast Trajectory')
        ax1.set_title(f'{SYMBOL} V800 Master Terminal | Cycle {execution_cycle} | {MASTER_ALERT}', color='white', fontsize=9, fontweight='bold')
        ax1.tick_params(colors='white')
        ax1.legend(fontsize=7, facecolor='black', labelcolor='white', loc='upper left')
        
        ax2 = plt.subplot2grid((3, 2), (2, 0))
        ax2.set_facecolor('#050505')
        ax2.plot(last_5m_candles.index, last_5m_candles['RSI'], color='#ff1493', label='RSI 14')
        ax2.axhline(70, color='red', ls='--', alpha=0.5)
        ax2.axhline(30, color='green', ls='--', alpha=0.5)
        ax2.set_title('RSI Momentum Indicator', color='white', fontsize=8)
        ax2.tick_params(colors='white')
        
        ax3 = plt.subplot2grid((3, 2), (2, 1))
        ax3.set_facecolor('#050505')
        ax3.plot(last_5m_candles.index, last_5m_candles['MACD'], color='cyan', label='MACD')
        ax3.plot(last_5m_candles.index, last_5m_candles['MACD_Signal'], color='orange', label='Signal')
        ax3.set_title('MACD Trend Oscillator', color='white', fontsize=8)
        ax3.tick_params(colors='white')
        
        plt.tight_layout()
        display(fig)
        plt.close('all')
        
        if is_trade_active:
            telegram_text = (
                f"🤖 JERVIS V800 MASTER ALERT 🤖\n\n"
                f"{MASTER_ALERT}\n\n"
                f"🏛 Active Session: {session_str}\n"
                f"⏱ 5M Signal: {signal_5m}\n"
                f"⏱ 15M Signal: {signal_15m}\n"
                f"💧 Liquidity: {liquidity_cond_str}\n"
                f"📊 Backtest WinRate: {winrate_pct}%\n"
                f"🧠 ML Confidence: {ml_confidence:.1f}%\n"
                f"📰 Headlines: {news_headline}"
            )
            TelegramAlertEngine.send_notification(telegram_text, fig)
            
        print(f"Cycle {execution_cycle} complete. Sleeping for {REFRESH_SECONDS} seconds...")
        execution_cycle += 1
        time.sleep(REFRESH_SECONDS)
        
    except Exception as system_exception:
        logging.error(f"Captured Exception: {system_exception}")
        time.sleep(10)
