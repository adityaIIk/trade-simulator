# Trade Simulator 📈

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?logo=vercel)
![License](https://img.shields.io/badge/License-MIT-green)

Welcome to **Trade Simulator**, a sleek Flask-based web application that simulates trading costs for market orders on the OKX exchange, specifically for the BTC-USDT-SWAP pair. Fetch real-time orderbook data, compute slippage, fees, and market impact, and visualize results in a responsive UI—all hosted serverlessly on Vercel!

🌐 **Live Demo**: [trade-simulator-xyz.vercel.app](https://trade-simulator-xyz.vercel.app)  
📂 **GitHub**: [adityaIIk/trade-simulator](https://github.com/adityaIIk/trade-simulator)

---

## 🚀 Features

- **Real-Time Data**: Fetches live orderbook from OKX API for accurate simulations.
- **Trading Metrics**:
  - Slippage (%): Price deviation due to order size.
  - Fees (USD): Based on Regular (0.1%) or VIP (0.08%) taker rates.
  - Market Impact (%): Price effect of your order.
  - Net Cost (USD): Total cost (slippage + fees + impact).
  - Maker/Taker Proportion (%): Likelihood of maker vs. taker execution.
  - Latency (ms): API fetch time.
- **Interactive UI**: Input quantity, volatility, and fee tier; see live-updated outputs.
- **Responsive Design**: Mobile-friendly with side-by-side panels on desktop.
- **Error Handling**: Displays warnings for issues like insufficient liquidity.
- **Serverless Deployment**: Runs on Vercel with `gunicorn` for scalability.

---

## 📸 Screenshots

| Input Panel | Output Panel |
|-------------|--------------|
| ![Input Panel](screenshots/input_panel.png) | ![Output Panel](screenshots/output_panel.png) |

*Note*: Add screenshots to a `screenshots/` folder in your repo for the above links to work.

---

## 🛠️ Project Structure

```
trade_simulator/
├── api/
│   ├── app.py              # Backend Flask logic
│   └── templates/
│       └── index.html      # Frontend UI
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

- **`api/app.py`**: Fetches orderbook, computes metrics, serves API routes.
- **`api/templates/index.html`**: Responsive UI with inputs/outputs, styled with inline CSS, powered by JavaScript.
- **`requirements.txt`**: Lists `flask==3.0.3`, `requests==2.32.3`, `gunicorn==22.0.0`.
- **`vercel.json`**: Configures Vercel for serverless Python.

---

## 🔧 Setup

### Prerequisites
- Python 3.12.2
- Git
- Vercel CLI (`npm i -g vercel`)

### Local Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/adityaIIk/trade-simulator.git
   cd trade_simulator
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Locally**:
   ```bash
   cd api
   python app.py
   ```

5. **Access**:
   Open [http://localhost:5000](http://localhost:5000) in your browser.

### Vercel Deployment
1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy Trade Simulator"
   git push origin main
   ```

2. **Deploy via Vercel**:
   - Go to [vercel.com](https://vercel.com), sign in, and import `adityaIIk/trade-simulator`.
   - Configure:
     - **Framework Preset**: Other
     - **Root Directory**: `./`
     - **Install Command**: `pip install -r requirements.txt`
     - **Build Command**: (leave empty)
   - Click **Deploy**.

3. **Access**:
   Visit [trade-simulator-xyz.vercel.app](https://trade-simulator-xyz.vercel.app).

---

## 🎮 Usage

1. **Open the App**:
   - Local: [http://localhost:5000](http://localhost:5000)
   - Vercel: [trade-simulator-xyz.vercel.app](https://trade-simulator-xyz.vercel.app)

2. **Input Parameters**:
   - **Quantity**: Enter amount (default: 100 USD).
   - **Volatility**: Set market volatility (default: 0.02).
   - **Fee Tier**: Choose Regular (0.1%) or VIP (0.08%).
   - Fixed: OKX exchange, BTC-USDT-SWAP, Market order.

3. **View Outputs**:
   - Click **Update** to refresh metrics.
   - Outputs (Slippage, Fees, etc.) update every second.
   - Warnings appear for issues (e.g., “Order quantity exceeds available liquidity”).

4. **Experiment**:
   - Try high quantities (e.g., 10,000 USD) to trigger warnings.
   - Adjust volatility to see market impact changes.

---

## 🐛 Troubleshooting

- **Local Errors**:
  - Ensure dependencies: `pip install -r requirements.txt`.
  - Test OKX API: `curl https://www.okx.com/api/v5/market/books?instId=BTC-USDT-SWAP&sz=20`.
- **Vercel Errors**:
  - Check build logs in Vercel dashboard.
  - Verify `vercel.json` routes.
- **Outputs Stuck at 0.00**:
  - Increase JavaScript delay in `index.html`:
    ```javascript
    setTimeout(() => submitParams(defaultParams), 1000);
    ```

---

## 🤝 Contributing

Contributions are welcome! To contribute:
1. Fork the repo.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push: `git push origin feature/your-feature`.
5. Open a pull request.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Aditya**  
- GitHub: [adityaIIk](https://github.com/adityaIIk)  
- Email: (add your email if desired)

⭐️ If you find this project useful, give it a star on GitHub! 🚀