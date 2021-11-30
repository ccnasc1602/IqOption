import sys
import json
from time import time
from datetime import datetime, timedelta
from colorama import init, Fore, Back
from iqoptionapi.stable_api import IQ_Option

# Busca dados de acesso no arquivo json
with open("settings.json") as json_file:
    settings = json.load(json_file)

init(autoreset=True)

API = IQ_Option(email=settings['login'], password=settings['password'])
API.connect()

if API.check_connect():
    print("Conectado com sucesso!")
else:
    print("Erro de conexão!")
    input("\n\n Pressione [ENTER] para sair.")
    sys.exit()

def catalog(par, days, perc_call, perc_put, timeframe):
    data = []
    data_testing = []
    sair = False
    _time = time()

    while sair == False:
        candles = API.get_candles(par, (timeframe * 60), 1000, _time)
        candles.reverse()

        for x in candles:
            if datetime.fromtimestamp(x['from']).strftime('%Y-%m-%d') not in data_testing:
                data_testing.append(datetime.fromtimestamp(x['from']).strftime('%Y-%m-%d'))
            
            if len(data_testing) <= days:
                x.update({
                    'cor': 'verde' if x['open'] < x['close'] else 'vermelho' if x['open'] > x['close'] else 'doji'
                })
                data.append(x)
            else:
                sair = True
                break
        
        _time = int(candles[-1]['from'] - 1)
    
    analysis = {}
    for candles in data:
        schedule = datetime.fromtimestamp(candles['from']).strftime('%H:%M')

        if schedule not in analysis:
            analysis.update({
                schedule: {
                    'verde': 0,
                    'vermelho': 0,
                    'doji': 0,
                    '%': 0,
                    'dir': ''
                }
            })
        
        analysis[schedule][candles['cor']] += 1
    
    try:
        total = analysis[schedule]['verde'] + analysis[schedule]['vermelho'] + analysis[schedule]['doji']
        media = analysis[schedule]['verde'] / total 
        analysis[schedule]['%'] = round(100 * media)
        print(total, analysis[schedule]['verde'], media)
        time.sleep(1)
    except:
        pass

    for schedule in analysis:
        if analysis[schedule]['%'] > 50:
            analysis[schedule]['dir'] = 'CALL'
        if analysis[schedule]['%'] < 50: 
            analysis[schedule]['dir'],analysis[schedule]['%'] = 'PUT ',(100 - analysis[schedule]['%'])

    return analysis

print('\n\n Qual timeframe deseja catalogar? ', end='')
timeframe = int(input())

print('\n Quantos dias para analisar? ', end='')
dias = int(input())

print('\n Qual a percentagem mínima? ', end='')
percent = int(input())

print('\n Quantos martingale? ', end='')
gales = input()

perc_call = abs(percent)
perc_put = abs(100 - percent)

P = API.get_all_open_time()
print('\n\n')
cataloguing = {}
for par in P['digital']:

    if P['digital'][par]['open'] == True:
        timer = int(time())

        print(Fore.GREEN + '*' + Fore.RESET + ' CATALOGANDO ' + par + '.. ', end='')
        
        cataloguing.update({
            par: catalog(par, dias, perc_call, perc_put, timeframe)
        })

        if gales.strip() != '':
            for schedule in sorted(cataloguing[par]):
                mg_time = schedule

                soma = {
                    'verde': cataloguing[par][schedule]['verde'],
                    'vermelho': cataloguing[par][schedule]['vermelho'],
                    'doji': cataloguing[par][schedule]['doji'],
                }

                for i in range(int(gales)):
                    i += 1
                    cataloguing[par][schedule].update({
                        'mg'+str(i): {'verde': 0, 'vermelho': 0, 'doji': 0, '%': 0}})
                    
                    now = datetime.now().strftime('%Y-%m-%d ')
                    mg_time = str(datetime.strptime(now + mg_time, '%Y-%m-%d %H:%M') + timedelta(minutes=timeframe))[11:-3]

                    if mg_time in cataloguing[par]:
                        
                        cataloguing[par][schedule]['mg'+str(i)]['verde'] += cataloguing[par][mg_time]['verde'] + soma['verde']
                        cataloguing[par][schedule]['mg'+str(i)]['vermelho'] += cataloguing[par][mg_time]['verde'] + soma['vermelho']
                        cataloguing[par][schedule]['mg'+str(i)]['doji'] += cataloguing[par][mg_time]['verde'] + soma['doji']

                        color = 'verde' if cataloguing[par][schedule]['dir'] == 'CALL' else 'vermelho'
                        somas = cataloguing[par][schedule]['mg' + str(i)]['verde'] + cataloguing[par][schedule]['mg' + str(i)]['vermelho'] + cataloguing[par][schedule]['mg' + str(i)]['doji']
                        cataloguing[par][schedule]['mg' + str(i)]['%'] = round(100 * cataloguing[par][schedule]['mg' + str(i)][color] / somas)

                        soma['verde'] += cataloguing[par][mg_time]['verde']
                        soma['vermelho'] += cataloguing[par][mg_time]['vermelho']
                        soma['doji'] += cataloguing[par][mg_time]['doji']
                    
                    else:
                        cataloguing[par][schedule]['mg'+str(i)]['%'] = 'N/A'

            print('finalizado em ' + str(int(time()) - timer) + ' segundos ')   

print('\n\n')

for par in cataloguing:
    for schedule in sorted(cataloguing[par]):
        ok = False
        msg = ''
        
        if cataloguing[par][schedule]['%'] >= percent:
            ok = True
        
        else:
            if gales.strip() != '':
                for i in range(int(gales)):
                    if cataloguing[par][schedule]['mg'+str(i+1)]['%'] >= percent:
                        ok = True
                        break
    
        if ok == True:
            msg = Fore.YELLOW + par + Fore.RESET + ' - ' + schedule + ' - ' + (Fore.GREEN if cataloguing[par][schedule]['dir'] == 'CALL' else Fore.RED) + cataloguing[par][schedule]['dir'] + Fore.RESET + ' - ' + str(cataloguing[par][schedule]['%']) + ' % - ' + Back.GREEN + Fore.BLACK + str(cataloguing[par][schedule]['verde']) + Back.RED + str(cataloguing[par][schedule]['vermelho']) + Back.RESET + Fore.RESET + str(cataloguing[par][schedule]['doji'])

            if gales.strip() != '':
                for i in range(int(gales)):
                    i += 1
                    if cataloguing[par][schedule]['mg'+str(i)]['%'] != 'N/A':
                        msg += ' | MG '
                        msg += str(i) + ' - ' + str(cataloguing[par][schedule]['mg'+str(i)]['%']) + '% - '
                        msg += Back.GREEN + Fore.BLACK + str(cataloguing[par][schedule]['mg'+str(i)]['verde'])
                        msg += Back.RED + str(cataloguing[par][schedule]['mg'+str(i)]['vermelho'])
                        msg += Back.RESET + Fore.RESET + str(cataloguing[par][schedule]['mg'+str(i)]['doji'])
                    else:
                        msg += ' | MG ' + str(i) + ' - ' + ' - N/A - N/A'
            
            print(msg)
            open('sinais_%s.txt' % (datetime.now().strftime('%Y-%m-%d %H:%M')), 'a').write(schedule + ';' + par + ';' + cataloguing[par][schedule]['dir'].strip()+'\n')