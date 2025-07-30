# Blockhouse Crypto Work Trial Submission

## Setup Instructions
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`.
3. Set environment variables for API keys and AWS credentials.
4. Start Jupyter: `jupyter notebook`.
5. Open `crypto_work_trial.ipynb` and run cells in order.
6. For Task 5, update `s3_bucket` in the notebook to your S3 bucket name (e.g., `blockhouse-trial-yourname`).
7. Notes:
- Tasks 1, 4, and 5 use public data and don’t need API keys.
- Tasks 2 and 3 require trading-enabled API keys; use a testnet (e.g., Binance Futures Testnet) for safety.
- For Deribit, use symbols like 'BTC-PERPETUAL'.
- Task 5 requires AWS credentials and an S3 bucket.
- Check S3 for files in `order_books/YYYY-MM-DD/BTCUSDT/`.

## Open-Ended Challenge
### System Design & Scalability
**Critique**:
- **Rate Limits**: The code uses CCXT’s rate limiting, but fetching data every second (Task 5) could hit limits, especially with multiple exchanges. There’s no smart retry system.
- **Delays**: Calling APIs one-by-one for each exchange is slow, especially for Task 1’s best bid/ask across exchanges.
- **Crashes**: If the program stops during Task 5, unsaved data is lost.
- **Performance**: Calculating price impact for large trades with deep order books (500+ levels) can be slow.
- **Symbol Issues**: The symbol mapper doesn’t handle unusual pair formats well.

**Improvements for Production**:
- **Structure**: Build a web app with FastAPI to handle requests, use Celery to run tasks in the background, and deploy on Kubernetes to handle more users.
- **Faster Data**: Use WebSockets (CCXT’s `watch_` functions) to get live data instead of slow API calls.
- **Caching**: Store order books in Redis (a fast database) to avoid repeated API calls.
- **Reliability**: Run on multiple AWS servers; if one exchange fails, skip it automatically.
- **Monitoring**: Use tools like Prometheus to track performance and Grafana to show graphs of delays/errors.
- **Backtesting**: Use Airflow to schedule tests with stored data.

### Error Handling & Resilience
- **API Errors**: Retry failed API calls with a delay (e.g., wait longer each try). Separate temporary errors (like network issues) from permanent ones (like wrong keys).
- **Exchange Downtime**: Check if an exchange is down and skip it; use a backup data source like CoinGecko if all fail.
- **WebSocket Issues**: If using live data, reconnect automatically if the connection drops. Save the last data point to avoid gaps.
- **Consistency**: Before placing or cancelling orders, check their status to avoid mistakes. Regularly double-check positions with the exchange.
- **Testing**: Test the code with fake exchange responses to catch errors early.
