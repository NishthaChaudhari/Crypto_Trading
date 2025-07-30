import time
import boto3
import pandas as pd
import io
from datetime import datetime
from connectors.exchange_connector import ExchangeConnector

class OrderBookPipeline:
    def __init__(self, exchange_name: str, symbol: str, interval_seconds: int = 1, s3_bucket: str = 'your-bucket-name'):
        self.conn = ExchangeConnector(exchange_name)
        self.symbol = symbol
        self.interval = interval_seconds
        self.s3 = boto3.client('s3')
        self.bucket = s3_bucket
    
    def run(self, duration_minutes: int = 10):
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        while time.time() < end_time:
            try:
                timestamp = datetime.utcnow().isoformat()
                order_book = self.conn.get_order_book(self.symbol)
                bids_df = pd.DataFrame(order_book['bids'], columns=['price', 'quantity'])
                bids_df['side'] = 'bid'
                asks_df = pd.DataFrame(order_book['asks'], columns=['price', 'quantity'])
                asks_df['side'] = 'ask'
                df = pd.concat([bids_df, asks_df])
                df['timestamp'] = timestamp
                df['exchange'] = self.conn.exchange_name
                df['pair'] = self.symbol
                buffer = io.BytesIO()
                df.to_parquet(buffer, index=False)
                buffer.seek(0)
                date_str = datetime.utcnow().strftime('%Y-%m-%d')
                key = f"order_books/{date_str}/{self.symbol}/{timestamp}.parquet"
                self.s3.put_object(Bucket=self.bucket, Key=key, Body=buffer.getvalue())
                print(f"Saved snapshot at {timestamp}")
            except Exception as e:
                print(f"Error capturing/saving: {str(e)}")
            time.sleep(self.interval)
