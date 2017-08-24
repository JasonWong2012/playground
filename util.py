import threading
import time
import os
import requests
import tablib
from requests import RequestException
from retrying import retry

from constant import city_center_url_pattern, BAIDU_API_AK, TIMEOUT, STEP_NUM, UNIT_DISTANCE, HEADERS, THREAD_PROCESS_NUM


def get_city_center_lng_lat_by_city_name(city_name):
    city_url = city_center_url_pattern.format(city_name, BAIDU_API_AK)
    try:
        response = requests.get(city_url, timeout=TIMEOUT)
        response_dict = response.json()
        location = response_dict['result']['location']
        return location['lng'], location['lat']
    except:
        raise ConnectionError


def get_rect_list_by_lng_lat(lng, lat):
    # 经纬度+-1.2度范围
    rect_list = []
    for units_lng in range(STEP_NUM):
        dist_lng = units_lng * UNIT_DISTANCE
        for units_lat in range(STEP_NUM):
            dist_lat = units_lat * UNIT_DISTANCE
            rect_list.append(['%.6f' % (lng - dist_lng - UNIT_DISTANCE),
                              '%.6f' % (lat - dist_lat - UNIT_DISTANCE),
                              '%.6f' % (lng - dist_lng),
                              '%.6f' % (lat - dist_lat)])

            rect_list.append(['%.6f' % (lng + dist_lng),
                              '%.6f' % (lat - dist_lat - UNIT_DISTANCE),
                              '%.6f' % (lng + dist_lng + UNIT_DISTANCE),
                              '%.6f' % (lat - dist_lat)])

            rect_list.append(['%.6f' % (lng - dist_lng - UNIT_DISTANCE),
                              '%.6f' % (lat + dist_lat),
                              '%.6f' % (lng - dist_lng),
                              '%.6f' % (lat + dist_lat + UNIT_DISTANCE)])

            rect_list.append(['%.6f' % (lng + dist_lng),
                              '%.6f' % (lat + dist_lat),
                              '%.6f' % (lng + dist_lng + UNIT_DISTANCE),
                              '%.6f' % (lat + dist_lat + UNIT_DISTANCE)])
    return rect_list


@retry(stop_max_attempt_number=10)
def get_response_text_with_url(url):
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('链接错误')
        return None


def crawl_raw_data_by_thread_with_rect_list_func_and_city_name(func_name, city_name):
    lng, lat = get_city_center_lng_lat_by_city_name(city_name)
    rect_list = get_rect_list_by_lng_lat(lng, lat)
    len_of_sub_rect_list_for_thread = int(len(rect_list) / THREAD_PROCESS_NUM)
    process_list = []
    for i in range(THREAD_PROCESS_NUM):
        process = threading.Thread(target=func_name,
                                   args=(rect_list[i * len_of_sub_rect_list_for_thread: (i+1) * len_of_sub_rect_list_for_thread],
                                         city_name))
        process.start()
        process_list.append(process)
    for process in process_list:
        process.join()

def get_date():
    date = time.strftime("%Y_%m_%d", time.localtime())
    return date


def get_raw_data_file_path(city_name, source_name, data_type_label):
    date = get_date()
    path = "\\".join( [os.path.dirname(os.getcwd()), 'data', city_name, str(date)])
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = path + '\{}_{}_{}_{}.txt'.format(city_name, source_name, data_type_label, date)
    return file_path


def save_raw_data_in_tsv_file(file_path, data):
    formed_data = tablib.Dataset(data.values())
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(formed_data.tsv)
