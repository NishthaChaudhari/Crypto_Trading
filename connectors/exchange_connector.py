import ccxt
import time
from typing import Dict, List, Optional, Any

class ExchangeConnector:
    SUPPORTED_EXCHANGES = ['bitmart', 'binance', 'deribit', 'kucoin', 'okx']
    
    def __init__(self, exchange_name: str, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        if exchange_name not in self.SUPPORTED_EXCHANGES:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        self.exchange_name = exchange_name
        config = {'enableRateLimit': True, 'timeout': 30000}
        if api_key and api_secret:
            config['apiKey'] = api_key
            config['secret'] = api_secret
        self.exchange = getattr(ccxt, exchange_name)(config)
        self._load_markets()

    def _load_markets(self):
        try:
            self.exchange.load_markets()
        except Exception as e:
            raise ConnectionError(f"Failed to load markets for {self.exchange_name}: {str(e)}")

    def get_best_bid_ask(self, symbol: str) -> Dict[str, float]:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {'bid': ticker['bid'], 'ask': ticker['ask']}
        except Exception as e:
            raise ValueError(f"Error fetching bid/ask for {symbol}: {str(e)}")

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, List[List[float]]]:
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=limit)
            return {'bids': order_book['bids'], 'asks': order_book['asks']}
        except Exception as e:
            raise ValueError(f"Error fetching order book for {symbol}: {str(e)}")

    def get_funding_rates(self, symbol: str) -> Dict[str, Any]:
        try:
            current = self.exchange.fetch_funding_rate(symbol)
            predicted = None
            if 'nextFundingRate' in current['info']:
                predicted = current['info']['nextFundingRate']
            return {'current': current['fundingRate'], 'predicted': predicted}
        except Exception as e:
            raise ValueError(f"Error fetching funding rates for {symbol}: {str(e)}")

    def get_historical_funding_rates(self, symbol: str, since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        try:
            return self.exchange.fetch_funding_rate_history(symbol, since=since, limit=limit)
        except Exception as e:
            raise ValueError(f"Error fetching historical funding rates: {str(e)}")

    def calculate_apr_from_funding_rate(self, funding_rate: float, payout_frequency_hours: int = 8) -> float:
        periods_per_year = (24 * 365) / payout_frequency_hours
        return funding_rate * periods_per_year * 100

    def calculate_price_impact(self, symbol: str, side: str, trade_volume: float) -> Dict[str, float]:
        order_book = self.get_order_book(symbol, limit=500)
        mid_price = (order_book['bids'][0][0] + order_book['asks'][0][0]) / 2 if order_book['bids'] and order_book['asks'] else 0
        if not mid_price:
            raise ValueError("Empty order book")
        
        cumulative_quote = 0
        total_base = 0
        weighted_sum = 0
        levels = order_book['asks'] if side == 'buy' else order_book['bids']
        
        for price, qty in levels:
            qty_quote = qty * price
            if cumulative_quote + qty_quote >= trade_volume:
                remaining_quote = trade_volume - cumulative_quote
                needed_base = remaining_quote / price
                total_base += needed_base
                weighted_sum += price * needed_base
                break
            else:
                total_base += qty
                weighted_sum += price * qty
                cumulative_quote += qty_quote
        
        if cumulative_quote < trade_volume:
            raise ValueError("Insufficient liquidity")
        
        average_price = weighted_sum / total_base if total_base > 0 else 0
        impact = ((average_price - mid_price) / mid_price) * 100 if mid_price > 0 else 0
        return {'average_price': average_price, 'impact': impact}

    def place_order(self, symbol: str, side: str, quantity: float, order_type: str, price: Optional[float] = None) -> str:
        try:
            if order_type.upper() == 'LIMIT':
                if price is None:
                    raise ValueError("Price required for LIMIT order")
                order = self.exchange.create_limit_order(symbol, side, quantity, price)
            elif order_type.upper() == 'MARKET':
                order = self.exchange.create_market_order(symbol, side, quantity)
            else:
                raise ValueError("Unsupported order type")
            return order['id']
        except Exception as e:
            raise ValueError(f"Error placing order: {str(e)}")

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        try:
            self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"Error cancelling order {order_id}: {str(e)}")
            return False

    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> str:
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order['status'].upper()
        except Exception as e:
            raise ValueError(f"Error fetching order status: {str(e)}")

    def get_position_from_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            if order['status'] != 'closed':
                raise ValueError("Order not filled")
            positions = self.exchange.fetch_positions([order['symbol']])
            pos = next((p for p in positions if p['symbol'] == order['symbol'] and p['side'] == order['side']), None)
            if not pos:
                raise ValueError("No position found")
            current_price = self.exchange.fetch_ticker(symbol)['last']
            net_pnl = pos['unrealizedPnl'] if 'unrealizedPnl' in pos else (current_price - pos['entryPrice']) * pos['contracts'] * (1 if pos['side'] == 'long' else -1)
            return {
                'connector_name': self.exchange_name,
                'pair_name': pos['symbol'],
                'entry_timestamp': pos['timestamp'],
                'entry_price': pos['entryPrice'],
                'quantity': pos['contracts'],
                'position_side': pos['side'],
                'NetPnL': net_pnl
            }
        except Exception as e:
            raise ValueError(f"Error fetching position: {str(e)}")
