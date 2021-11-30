import time
import json
import logging
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option


def get_data():
    with open("signals.json", encoding='utf-8') as json_file:
        return json.load(json_file)


logging.disable(level=(logging.DEBUG))

user = {
    'username': 'ccnasc1602@gmail.com',
    'password': 'nasc1602'
}
IQ = IQ_Option(user['username'], user['password'])
check, reason = IQ.connect()
print(check, reason)

MODE = "PRACTICE"
IQ.change_balance(MODE)
interval = 5

while True:
    data = get_data()
    time_now = datetime.now().strftime('%H:%M')
    time.sleep(interval)
    if data.get(time_now):
        check, activeId = IQ.buy(
            data[time_now]['value'], 
            data[time_now]['asset'], 
            data[time_now]['signal'], 
            data[time_now]['duration'])
        if check:
            print("Entrada lançada às ", datetime.now().strftime('%H:%M'))
        else:
            print("Falha no lançamento...")
        #print(IQ.get_balances())
        time.sleep(60-interval)