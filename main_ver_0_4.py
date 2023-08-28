import requests
import os
import threading
import datetime
import pandas as pd
import datetime
dt = datetime.datetime.now()

locker = threading.Lock()

def formating_item_names(list_of_names):
    count = 0
    stroke = ''
    for i in list_of_names:
        if len(list_of_names) != 1:
            if count == 0:
                stroke = stroke + (f'"{i}"')
                count += 1
            else:
                stroke = stroke + (f', "{i}"')
        else:
            stroke = stroke + (f'"{i}"')
    return stroke

def get_item_id(item_name):
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    }
    params = {
        'datasource': 'tranquility',
        'language': 'ru',
    }
    data = f'[{item_name}]'
    response = requests.post('https://esi.evetech.net/latest/universe/ids/', params=params, headers=headers, data=data).json()
    return response['inventory_types']

def get_item_reprocessed_materials(item_id, item_name, janice_code):
    
    headers = {
        'accept': 'application/json',
        'X-ApiKey': f'{janice_code}',
        'Content-Type': 'text/plain',
    }
    params = {
    'market': '2',
    'designation': 'wtb',
    'pricing': 'split',
    'pricingVariant': 'immediate',
    'persist': 'true',
    'compactize': 'true',
    'pricePercentage': '1',
    }
    data = item_name

    response = requests.post('https://janice.e-351.com/api/rest/v2/appraisal', params=params, headers=headers, data=data).json()
    response['code']



    header = {
        "Referer": "https://janice.e-351.com/a/y400Z7/reprocess?se=1",
        "Content-Length": "311",
        "Origin": "https://janice.e-351.com",
    }

    postUrl='https://janice.e-351.com/api/rpc/v1?m=Appraisal.reprocess'
    a = '{"id":'+str(item_id)+',"method":"Appraisal.reprocess","params":{"code":"'+str(response['code'])+'","oreEfficiency":0.9063,"gasEfficiency":0.95,"scrapEfficiency":1}}'
    print(a)
    response = requests.post(postUrl, data=a, headers=header).json()
    return response['result']['items']


def input_str_item_name():
    contents = []
    line = None
    while line != "":
        try:
            line = input("")
            if line == "":
                pass
            else:
                line = line.split("*")[0]
        except EOFError:
            break
        contents.append(line)
    contents.pop()
    return contents

def get_price(type_id, janice_code):
    if type_id == int:
        type_id = str(type_id)
    headers = {
        'accept': 'application/json',
        'X-ApiKey': f'{janice_code}'
    }
    response = requests.get(f'https://janice.e-351.com/api/rest/v2/pricer/{type_id}?market=2', headers=headers).json()
    return response['immediatePrices']





def list_elements_item_get(dict_response):
    global list_elements_item
    dict_element_item = {"id" : dict_response['id'], "name" : dict_response['name'], "sell_min" : get_price(type_id = dict_response['id'], janice_code=janice_code)['sellPrice'], "buy_max" : get_price(type_id = dict_response['id'], janice_code=janice_code)['buyPrice']}

    list_reprocess = []
    for materials_id in get_item_reprocessed_materials(dict_response['id'], dict_response['name'], janice_code = janice_code):
        dict_reprocess = {'material_id' : materials_id['itemType']['eid'], 'material_name' : materials_id['itemType']['name'], 'material_count' : materials_id['amount']}
        list_reprocess.append(dict_reprocess)
        
    dict_element_item["reprocess"] = list_reprocess
    locker.acquire()
    list_elements_item.append(dict_element_item)
    locker.release()

def finally_elements_get(element_item):
    global finally_elements
    sell_min = 0
    buy_max = 0
    for reprocess in tqdm(element_item['reprocess'], ascii="░▒█"):
        time.sleep(0.1)
        #if int(reprocess['material_count']) != 1:
        material_count = reprocess['material_count'] * procent_per_reprocessing
        material_count = int(material_count)
        #else:
        #    pass
        sell_item = get_price(type_id=reprocess['material_id'], janice_code=janice_code)['sellPrice'] * material_count
        buy_item = get_price(type_id=reprocess['material_id'], janice_code=janice_code)['buyPrice'] * material_count
        sell_min = sell_min + sell_item
        buy_max = buy_max + buy_item

    finally_dict = {"name" : element_item['name'], "item_sell_min" : element_item['sell_min'], "items_buy_max" : element_item['buy_max'], "reprocess_sell_min" : sell_min, "reprocess_buy_max" : buy_max}
    locker.acquire()
    finally_elements.append(finally_dict)
    locker.release()





if __name__ == '__main__':
    import tabulate
    from tqdm import tqdm
    import threading
    import time

    janice_code = ''

    procent_per_reprocessing = int(input("Введите свой процент Репроцесинга, без знака процент: "))
    procent_per_reprocessing = procent_per_reprocessing / 100
    os.system("cls")
    print("Ваш коэффициент Репроцесинга: " + str(procent_per_reprocessing))
    print("Скопируйте названия предметов и вставьте их. После нажмите два раза ENTER.")
    print("")
    str_item_names = set(input_str_item_name())
    os.system("cls")
    formated_item_names = formating_item_names(list_of_names=str_item_names)
    items_id = get_item_id(item_name = formated_item_names)
    #print(items_id)
    #print("")
    #print("---------------------------------------------------------------------------")
    #print("")

    thr_list = []

    list_elements_item = []
    for dict_response in tqdm(items_id, ascii="░▒█"):
        #print("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
        #print(type(dict_response))
        #print(dict_response)
        #print("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
        ls = [dict_response]
        thr = threading.Thread(target=list_elements_item_get, args=(ls))
        thr_list.append(thr)
        time.sleep(0.3)
        thr.start()
    for i in thr_list:
        i.join()

    print(list_elements_item)
    
    #os.system("cls")
    print(f'Будет произведенно около {len(items_id)} оппераций.')
    finally_elements = []
    for element_item in list_elements_item:
        #print("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
        #print(type(element_item))
        #print(element_item)
        #print("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
        ls = [element_item]
        thr = threading.Thread(target=finally_elements_get, args=(ls))
        thr_list.append(thr)
        thr.start()
    for i in thr_list:
        i.join()
    
    
    finally_data = [['Имя', 'Цена продажи предмета', 'Цена покупки предмета', 'Цена продажи репроцесинга', 'Цена покупки репроцесинга', 'ВЫГОДА']]
    print_in_file = None
    list_name = []
    list_item_sell_min = []
    list_items_buy_max = []
    list_reprocess_sell_min = []
    list_reprocess_buy_max = []
    for data in finally_elements:
        string = "This contains a word"
        if " Missile" in (" " + data['name']):
            data['item_sell_min'] = int(data['item_sell_min']) * 5000
        else:
            pass
        if int(data['reprocess_sell_min'] - data['item_sell_min']) > 0:
            profit = "\033[0;32mДА\033[0m"
            print_in_file = str(print_in_file) + str(data['name'] + str(" . Цена покупки предмета: ") + str(data['item_sell_min']) + str(" ISK. Цена продажи Репроцесса: ") + str(data['reprocess_buy_max']) + " ISK" + '\n')
            list_name.append(data['name'])
            list_item_sell_min.append(data['item_sell_min'])
            list_items_buy_max.append(data['items_buy_max'])
            list_reprocess_sell_min.append(data['reprocess_sell_min'])
            list_reprocess_buy_max.append(data['reprocess_buy_max'])
        else:
            profit = "\033[0;31mНЕТ\033[0m"
        finally_data.append([data['name'], data['item_sell_min'], data['items_buy_max'], data['reprocess_sell_min'], data['reprocess_buy_max'], profit])
    
    with open('ВЫГОДНО.txt', "w", encoding='utf-8') as f:
        f.write(print_in_file)

    df = pd.DataFrame({'Имя' : list_name, 
                       'Цена продажи предмета' : list_item_sell_min,
                       'Цена покупки предмета' : list_items_buy_max,
                       'Цена продажи репроцесинга' : list_reprocess_sell_min,
                       'Цена покупки репроцесинга' : list_reprocess_buy_max,})
    
    file_name = "ВЫГОДА_" + str(dt.strftime('%Y-%m-%d'))
    df.to_excel("./"+str(file_name) + ".xlsx")

    time.sleep(1)
    os.system("cls")
    results = tabulate.tabulate(finally_data, tablefmt="grid")
    print(results)
    n = input("Для закрытия нажмите ENTER")
