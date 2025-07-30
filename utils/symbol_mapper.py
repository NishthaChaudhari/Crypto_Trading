class SymbolMapper:
    STANDARD_QUOTES = ['USD', 'USDT', 'USDC']
    
    @staticmethod
    def standardize_symbol(exchange_symbol: str) -> str:
        if exchange_symbol.startswith('1'):
            exchange_symbol = exchange_symbol[1:]
        if '-' in exchange_symbol:
            base, quote = exchange_symbol.split('-')
        elif '/' in exchange_symbol:
            base, quote = exchange_symbol.split('/')
        else:
            if exchange_symbol[-4:] in ['USDT', 'USDC']:
                base, quote = exchange_symbol[:-4], exchange_symbol[-4:]
            elif exchange_symbol[-3:] == 'USD':
                base, quote = exchange_symbol[:-3], 'USD'
            else:
                raise ValueError(f"Unknown symbol format: {exchange_symbol}")
        if quote in SymbolMapper.STANDARD_QUOTES:
            quote = 'USD'
        return f"{base.upper()}{quote.upper()}"
