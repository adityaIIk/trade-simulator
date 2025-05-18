import logging
import time
import threading
import requests
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request
from sklearn.linear_model import LogisticRegression
from statsmodels.regression.quantile_regression import QuantReg
from collections import deque

# Configure logging
logging.basicConfig(
    filename='trade_simulator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# Global variables for orderbook and simulation state
orderbook = {'bids': [], 'asks': []}
simulation_results = {
    'slippage': 0.0,
    'fees': 0.0,
    'market_impact': 0.0,
    'net_cost': 0.0,
    'maker_taker': 0.0,
    'latency': 0.0
}
input_params = {
    'exchange': 'OKX',
    'asset': 'BTC-USDT-SWAP',
    'order_type': 'market',
    'quantity': 100.0,  # USD equivalent
    'volatility': 0.02,  # Default from market data
    'fee_tier': 'regular'  # regular or vip
}

# Performance metrics
latencies = deque(maxlen=1000)  # Store last 1000 latency measurements

# HTTP-based orderbook fetching
def fetch_orderbook():
    url = 'https://www.okx.com/api/v5/market/books?instId=BTC-USDT-SWAP&sz=20'
    while True:
        start_time = time.time()
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()['data'][0]
            orderbook['bids'] = [[float(price), float(size)] for price, size in data.get('bids', [])]
            orderbook['asks'] = [[float(price), float(size)] for price, size in data.get('asks', [])]
            compute_simulation()
            latency = (time.time() - start_time) * 1000  # ms
            latencies.append(latency)
            simulation_results['latency'] = latency
            logging.info(f"Processed orderbook fetch, latency: {latency:.2f}ms")
        except Exception as e:
            logging.error(f"Error fetching orderbook: {e}")
            orderbook['bids'] = []
            orderbook['asks'] = []
            simulation_results['slippage'] = 0.0
            simulation_results['market_impact'] = 0.0
            simulation_results['maker_taker'] = 0.0
        time.sleep(5)  # Fetch every 5 seconds

def compute_simulation():
    global simulation_results
    if not orderbook['bids'] or not orderbook['asks']:
        logging.warning("Empty orderbook, skipping simulation")
        return

    bids_df = pd.DataFrame(orderbook['bids'], columns=['price', 'size'])
    asks_df = pd.DataFrame(orderbook['asks'], columns=['price', 'size'])

    slippage = calculate_slippage(bids_df, asks_df)
    if slippage == float('inf'):
        return

    fees = calculate_fees()
    market_impact = calculate_market_impact(bids_df, asks_df)
    maker_taker = calculate_maker_taker(bids_df, asks_df)
    net_cost = slippage + fees + market_impact

    simulation_results.update({
        'slippage': slippage,
        'fees': fees,
        'market_impact': market_impact,
        'net_cost': net_cost,
        'maker_taker': maker_taker
    })

def calculate_slippage(bids_df, asks_df):
    try:
        quantity = input_params['quantity'] / asks_df['price'].iloc[0]
        remaining_qty = quantity
        total_cost = 0.0
        for _, row in asks_df.iterrows():
            if remaining_qty <= 0:
                break
            qty_filled = min(remaining_qty, row['size'])
            total_cost += qty_filled * row['price']
            remaining_qty -= qty_filled
        if remaining_qty > 0:
            logging.warning("Order quantity exceeds available liquidity")
            return float('inf')
        avg_price = total_cost / quantity
        mid_price = (bids_df['price'].iloc[0] + asks_df['price'].iloc[0]) / 2
        slippage = (avg_price - mid_price) / mid_price * 100
        return slippage
    except Exception as e:
        logging.error(f"Error calculating slippage: {e}")
        return 0.0

def calculate_fees():
    fees = {
        'regular': {'maker': 0.08, 'taker': 0.1},
        'vip': {'maker': 0.06, 'taker': 0.08}
    }
    fee_rate = fees[input_params['fee_tier']]['taker'] / 100
    return input_params['quantity'] * fee_rate

def calculate_market_impact(bids_df, asks_df):
    try:
        sigma = input_params['volatility']
        eta = 1e-6
        gamma = 1e-5
        quantity = input_params['quantity'] / asks_df['price'].iloc[0]
        avg_volume = asks_df['size'].sum()
        if avg_volume == 0:
            logging.warning("Zero volume in orderbook")
            return 0.0
        permanent_impact = eta * quantity
        temporary_impact = gamma * (quantity ** 2) / avg_volume
        total_impact = (permanent_impact + temporary_impact) * 100
        return total_impact
    except Exception as e:
        logging.error(f"Error calculating market impact: {e}")
        return 0.0

def calculate_maker_taker(bids_df, asks_df):
    try:
        spread = asks_df['price'].iloc[0] - bids_df['price'].iloc[0]
        quantity = input_params['quantity'] / asks_df['price'].iloc[0]
        X = np.array([[spread, quantity, input_params['volatility']]])
        model = LogisticRegression()
        model.fit(np.random.rand(100, 3), np.random.randint(0, 2, 100))
        maker_prob = model.predict_proba(X)[0][1]
        return maker_prob * 100
    except Exception as e:
        logging.error(f"Error calculating maker/taker: {e}")
        return 0.0

# Flask routes
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error rendering index: {e}")
        return "Internal Server Error", 500

@app.route('/api/results')
def get_results():
    try:
        return jsonify(simulation_results)
    except Exception as e:
        logging.error(f"Error in get_results: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/params', methods=['POST'])
def update_params():
    global input_params
    try:
        data = request.json
        input_params.update({
            'asset': data.get('asset', input_params['asset']),
            'quantity': float(data.get('quantity', input_params['quantity'])),
            'volatility': float(data.get('volatility', input_params['volatility'])),
            'fee_tier': data.get('fee_tier', input_params['fee_tier'])
        })
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error in update_params: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

# Start orderbook fetching in a background thread
def start_background_task():
    threading.Thread(target=fetch_orderbook, daemon=True).start()

if __name__ == '__main__':
    start_background_task()
    app.run(debug=False, host='0.0.0.0', port=5000)