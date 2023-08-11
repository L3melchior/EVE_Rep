import requests
import os
import threading

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

def get_item_reprocessed_materials(item_id):
    response = requests.get(f'https://evemarketer.com/api/v1/types/{item_id}?language=ru&important_names=false').json()
    return response["reprocessed_materials"]

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

def get_price(type_id, use_system='30000142'):
    if type_id == int:
        type_id = str(type_id)
    headers = {
        'accept': 'application/json',
    }
    params = {
        'typeid': type_id,
        'usesystem': use_system,
    }
    response = requests.post('https://api.evemarketer.com/ec/marketstat/json', params=params, headers=headers).json()
    return response[0]





def list_elements_item_get(dict_response):
    global list_elements_item
    dict_element_item = {"id" : dict_response['id'], "name" : dict_response['name'], "sell_min" : get_price(type_id = dict_response['id'])['sell']['min'], "buy_max" : get_price(type_id = dict_response['id'])['buy']['max']}

    list_reprocess = []
    for materials_id in get_item_reprocessed_materials(dict_response['id']):
        dict_reprocess = {'material_id' : materials_id['material_type']['id'], 'material_name' : materials_id['material_type']['name'], 'material_count' : materials_id['quantity']}
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
        sell_item = get_price(type_id=reprocess['material_id'])['sell']['min'] * material_count
        buy_item = get_price(type_id=reprocess['material_id'])['buy']['max'] * material_count
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
    
    os.system("cls")
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
    for data in finally_elements:
        string = "This contains a word"
        if " Missile" in (" " + data['name']):
            data['item_sell_min'] = int(data['item_sell_min']) * 5000
        else:
            pass
        if int(data['reprocess_sell_min'] - data['item_sell_min']) > 0:
            profit = "\033[0;32mДА\033[0m"
            with open('ВЫГОДНО.txt', "w", encoding='utf-8') as f:
                f.write(data['name'] + str(" . Цена покупки предмета: ") + str(data['item_sell_min']) + str(" ISK. Цена продажи Репроцесса: ") + str(data['reprocess_buy_max']) + " ISK" + '\n')
        else:
            profit = "\033[0;31mНЕТ\033[0m"
        finally_data.append([data['name'], data['item_sell_min'], data['items_buy_max'], data['reprocess_sell_min'], data['reprocess_buy_max'], profit])
    
    time.sleep(1)
    os.system("cls")
    results = tabulate.tabulate(finally_data, tablefmt="grid")
    print(results)
    n = input("Для закрытия нажмите ENTER")

    