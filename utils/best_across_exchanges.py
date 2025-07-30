from connectors.exchange_connector import ExchangeConnector
from typing import List, Dict

def get_best_bid_ask_across_exchanges(exchanges: List[ExchangeConnector], symbol: str) -> Dict[str, float]:
    best_bid = float('-inf')
    best_ask = float('inf')
    for conn in exchanges:
        try:
            ba = conn.get_best_bid_ask(symbol)
            best_bid = max(best_bid, ba['bid'])
            best_ask = min(best_ask, ba['ask'])
        except Exception as e:
            print(f"Skipping {conn.exchange_name}: {str(e)}")
    if best_bid == float('-inf') or best_ask == float('inf'):
        raise ValueError("No valid bid/ask found")
    return {'bid': best_bid, 'ask': best_ask}
