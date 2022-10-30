import requests, json
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, APCA_API_BASE_URL

class alpaca_api():

    def __init__(self) -> None:
        
        self.ALPACA_API_KEY = ALPACA_API_KEY
        self.ALPACA_SECRET_KEY = ALPACA_SECRET_KEY
        self.APCA_API_BASE_URL = APCA_API_BASE_URL

        self.ACCOUNT_URL = f'{APCA_API_BASE_URL}/v2/account'
        self.ORDERS_URL = f'{APCA_API_BASE_URL}/v2/orders'
        self.POSITIONS_URL = f'{APCA_API_BASE_URL}/v2/positions'
        self.PORTFOLIO_HISTORY_URL = f'{APCA_API_BASE_URL}/v2/account/portfolio/history'

        self.HEADER = {
            'APCA-API-KEY-ID': ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
        }

        self.unfinished_order_status = {
            'partially_filled',
            'done_for_day',
            'pending_cancel',
            'pending_replace',
            'accepted',
            'pending_new',
            'accepted_for_bidding',
            'new'
        }


    def get_account(self):

        r = requests.get(self.ACCOUNT_URL, headers=self.HEADER)
        return json.loads(r.content)

    def get_open_orders(self):

        r = requests.get(f'{self.ORDERS_URL}', headers=self.HEADER)
        return json.loads(r.content)

    def get_order(self, id=None):

        r = requests.get(f'{self.ORDERS_URL}/{id}', headers=self.HEADER)
        return json.loads(r.content)

    def create_order(self, **kwargs):
    
        order_params = {
            "symbol": kwargs['symbol'],
            "qty": kwargs['qty'],
            "type": kwargs['type'],
            "side": kwargs['side'],
            "time_in_force": kwargs['time_in_force']
        }

        r = requests.post(self.ORDERS_URL, json=order_params, headers=self.HEADER)
        return json.loads(r.content)

    def cancel_order(self, id=None):

        r = requests.delete(f'{self.ORDERS_URL}/{id}', headers=self.HEADER)

        return r

    def close_all_positions(self):

        r = requests.delete(f'{self.POSITIONS_URL}', headers=self.HEADER)

        return r

    def close_position(self, symbol):

        r = requests.delete(f'{self.POSITIONS_URL}/{symbol}', headers=self.HEADER)

        return r
    
    def get_all_positions(self):

        r = requests.get(f'{self.POSITIONS_URL}', headers=self.HEADER)

        return json.loads(r.content)

    def get_portfolio_history(self, period='5D',timeframe='1H'):

        portfolio_params = {
            "period": period,
            "timeframe": timeframe,
            "date_end": None,
            "extended_hours": False
        }
        r = requests.get(f'{self.PORTFOLIO_HISTORY_URL}', json=portfolio_params, headers=self.HEADER)
        return json.loads(r.content)
        