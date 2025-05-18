import logging
import time
import threading
import requests
from flask import Flask, render_template, jsonify, request
from collections import deque
import math
import os

# Configure logging
logging.basicConfig(
    filename='trade_simulator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Flask
app = Flask(__name__, template_folder='templates', static_folder='static')

# Global variables
orderbook = {'bids': [], 'asks': []}
simulation_results = {
    'slippage': 0.0,
    'fees': 0.0,
    'market_impact': 0.0,
    'net_cost': 0.0,
    'maker_taker': 0.0,
    'latency': 0.0,
    'warning': ''
}
input_params = {
    'exchange': 'OKX',
    'asset': 'BTC-USDT-SWAP',
    'order_type': 'market',
    'quantity': 100.0,
    'volatility': 0.02,
    'fee_tier': 'regular'
}
latencies = deque(maxlen=1000)

# Fetch orderbook
def fetch_orderbook():
    url = 'https://www.okx.com/api/v5/market/books?instId=BTC-USDT-SWAP&sz=20'
    while True:
        start_time = time.time()
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()['data'][0]
            bids = []
            asks = []
            for entry in data.get('bids', []):
                if len(entry) >= 2:
                    bids.append([float(entry[0]), float(entry[1])])
                else:
                    logging.warning(f"Invalid bid entry: {entry}")
            for entry in data.get('asks', []):
                if len(entry) >= 2:
                    asks.append([float(entry[0]), float(entry[1])])
                else:
                    logging.warning(f"Invalid ask entry: {entry}")
            orderbook['bids'] = bids
            orderbook['asks'] = asks
            logging.info(f"Fetched orderbook: {len(bids)} bids, {len(asks)} asks")
            compute_simulation()
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            simulation_results['latency'] = latency
            logging.info(f"Processed orderbook fetch, latency: {latency:.2f}ms")
        except Exception as e:
            logging.error(f"Error fetching orderbook: {e}")
            orderbook['bids'] = []
            orderbook['asks'] = []
            simulation_results.update({
                'slippage': 0.0,
                'fees': 0.0,
                'market_impact': 0.0,
                'net_cost': 0.0,
                'maker_taker': 0.0,
                'latency': 0.0,
                'warning': 'Failed to fetch orderbook'
            })
        time.sleep(10)

def compute_simulation():
    global simulation_results
    simulation_results['warning'] = ''
    if not orderbook['bids'] or not orderbook['asks']:
        logging.warning("Empty orderbook, skipping simulation")
        simulation_results['warning'] = 'No orderbook data'
        return

    bids = orderbook['bids']
    asks = orderbook['asks']

    # Always compute fees and other metrics
    fees = calculate_fees()
    market_impact = calculate_market_impact(bids, asks)
    maker_taker = calculate_maker_taker(bids, asks)

    # Compute slippage, handle errors
    slippage = calculate_slippage(bids, asks)
    if slippage == float('inf'):
        simulation_results['warning'] = 'Order quantity exceeds available liquidity'
        simulation_results.update({
            'slippage': 0.0,
            'fees': fees,
            'market_impact': market_impact,
            'net_cost': fees + market_impact,
            'maker_taker': maker_taker
        })
        return

    net_cost = slippage + fees + market_impact
    simulation_results.update({
        'slippage': slippage,
        'fees': fees,
        'market_impact': market_impact,
        'net_cost': net_cost,
        'maker_taker': maker_taker
    })

def calculate_slippage(bids, asks):
    try:
        ask_price = asks[0][0]
        if ask_price <= 0:
            logging.error("Invalid ask price: zero or negative")
            return 0.0
        quantity = input_params['quantity'] / ask_price
        remaining_qty = quantity
        total_cost = 0.0
        total_volume = sum(size for _, size in asks)
        if quantity > total_volume:
            logging.warning("Order quantity exceeds available liquidity")
            return float('inf')
        for price, size in asks:
            if remaining_qty <= 0:
                break
            qty_filled = min(remaining_qty, size)
            total_cost += qty_filled * price
            remaining_qty -= qty_filled
        if remaining_qty > 0:
            logging.warning("Order quantity exceeds available liquidity")
            return float('inf')
        avg_price = total_cost / quantity
        mid_price = (bids[0][0] + asks[0][0]) / 2
        if mid_price <= 0:
            logging.error("Invalid mid price: zero or negative")
            return 0.0
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

def calculate_market_impact(bids, asks):
    try:
        sigma = input_params['volatility']
        eta = 1e-6
        gamma = 1e-5
        ask_price = asks[0][0]
        if ask_price <= 0:
            logging.error("Invalid ask price for market impact")
            return 0.0
        quantity = input_params['quantity'] / ask_price
        avg_volume = sum(size for _, size in asks)
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

def calculate_maker_taker(bids, asks):
    try:
        spread = asks[0][0] - bids[0][0]
        ask_price = asks[0][0]
        if ask_price <= 0:
            logging.error("Invalid ask price for maker/taker")
            return 0.0
        quantity = input_params['quantity'] / ask_price
        maker_prob = 1 / (1 + math.exp(-(spread / input_params['volatility'])))
        return maker_prob * 100
    except Exception as e:
        logging.error(f"Error calculating maker/taker: {e}")
        return 0.0

# Flask routes
@app.route('/')
def index():
    try:
        template_path = os.path.join(app.root_path, app.template_folder, 'index.html')
        logging.info(f"Attempting to render index.html at {template_path}")
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error rendering index: {e}")
        return "Internal Server Error", 500

@app.route('/api/results')
def get_results():
    try:
        logging.info("Serving /api/results")
        return jsonify(simulation_results)
    except Exception as e:
        logging.error(f"Error in get_results: {e}")
        return jsonify({'error': str(e)}), 500

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
        compute_simulation()  # Recompute immediately after param update
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error in update_params: {e}")
        return jsonify({'error': str(e)}), 500

# Start background task
def start_background_task():
    threading.Thread(target=fetch_orderbook, daemon=True).start()

if __name__ == '__main__':
    start_background_task()
    app.run(debug=False, host='0.0.0.0', port=5000)