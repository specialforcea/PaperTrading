# from urllib import response
import requests, json
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, APCA_API_BASE_URL

ACCOUNT_URL = f'{APCA_API_BASE_URL}/v2/account'
ORDERS_URL = f'{APCA_API_BASE_URL}/v2/orders'
POSITIONS_URL = f'{APCA_API_BASE_URL}/v2/positions'
PORTFOLIO_HISTORY_URL = f'{APCA_API_BASE_URL}/v2/account/portfolio/history'

HEADER = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

def get_account():

    r = requests.get(ACCOUNT_URL, headers=HEADER)
    return json.loads(r.content)

def get_orders(id=None):

    r = requests.get(f'{ORDERS_URL}/{id}',  headers=HEADER)
    return json.loads(r.content)

def get_all_orders(id=None):

    r = requests.get(f'{ORDERS_URL}', json={"status": "all"},  headers=HEADER)
    return json.loads(r.content)

def create_order(symbol, qty, side, type, time_in_force, limit_price=None, stop_price=None, trail_price=None, trail_percent=None):
    
    order_params = {
        "symbol": symbol,
        "qty": qty,
        "type": type,
        "side": side,
        "time_in_force": time_in_force
    }

    r = requests.post(ORDERS_URL, json=order_params, headers=HEADER)
    return json.loads(r.content)
    
def get_portfolio_history(period='5D',timeframe='1H'):

    portfolio_params = {
        "period": period,
        "timeframe": timeframe,
        "date_end": None,
        "extended_hours": False
    }
    r = requests.get(f'{PORTFOLIO_HISTORY_URL}', json=portfolio_params, headers=HEADER)
    return json.loads(r.content)    
# response = create_order('AAPL', 50, 'buy','market','gtc')

def cancel_order(id=None):

    r = requests.delete(f'{ORDERS_URL}/{id}', headers=HEADER)

    return r

def cancel_all_order():

    r = requests.delete(f'{ORDERS_URL}', headers=HEADER)

    return r

# orders = get_orders(id='1975d9b2-f188-40c8-913d-874dda2d7767')
# print(orders)
# response = cancel_order(id=orders[0]['id'])

def get_all_positions():

    r = requests.get(f'{POSITIONS_URL}', headers=HEADER)

    return json.loads(r.content)

# response = get_portfolio_history(period='3D', timeframe='15Min')
# response = get_all_orders()
# print(response)
if __name__ == 'main':
    # response = cancel_all_order()
    response = get_portfolio_history(period='10D')
    print(response)