from json import JSONDecodeError
import pandas as pd
import json

from constant import BAIDU_POI_READY_DATA_HEADER_LIST
from crawler.crawler_enum import CrawlerSourceName, CrawlerDataLabel, CrawlerDataType
from util import get_file_path

def process_baidu_poi_raw_data(city_name):
    read_file_path = get_file_path(city_name,
                                   CrawlerDataType.RAW_DATA.value,
                                   CrawlerSourceName.BAIDU.value,
                                   CrawlerDataLabel.BAIDU_POI.value)
    raw_data = pd.read_table(read_file_path, error_bad_lines=False)
    ready_data = process_raw_data_to_ready(raw_data)
    return ready_data

def process_raw_data_to_ready(raw_data):
    raw_data['category'] = get_category_column_from_detail_info(raw_data['detail_info'])
    raw_data['type'] = get_type_column_from_detail_info(raw_data['detail_info'])
    raw_data['lat'] = get_lat_column_from_location(raw_data['location'])
    raw_data['lng'] = get_lng_column_from_location(raw_data['location'])
    ready_data = raw_data[BAIDU_POI_READY_DATA_HEADER_LIST]
    return ready_data

def get_category_column_from_detail_info(detail_info):
    category = list(map(transfer_detail_info_to_category, detail_info))
    return category

def get_type_column_from_detail_info(detail):
    type_name = list(map(transfer_detail_info_to_type, detail))
    return type_name

def get_lat_column_from_location(location):
    lat = list(map(transfer_lat_from_location, location))
    return lat

def get_lng_column_from_location(location):
    lng = list(map(transfer_lng_from_location, location))
    return lng

def transfer_lat_from_location(location):
    if type(location) == str:
        location_to_json_loads = location.replace("'", '"')
        try:
            location_dict = json.loads(location_to_json_loads)
            if 'lat' in location_dict.keys():
                return location_dict['lat']
        except JSONDecodeError:
            pass
    return ''

def transfer_lng_from_location(location):
    if type(location) == str:
        location_to_json_loads = location.replace("'", '"')
        try:
            location_dict = json.loads(location_to_json_loads)
            if 'lng' in location_dict.keys():
                return location_dict['lng']
        except JSONDecodeError:
            pass
    return ''

def transfer_detail_info_to_category(detail):
    if type(detail) == str:
        detail_to_json_loads = detail.replace("'", '"')
        try:
            detail_dict = json.loads(detail_to_json_loads)
            if 'tag' in detail_dict.keys():
                return detail_dict['tag']
        except JSONDecodeError:
            pass
    return ''

def transfer_detail_info_to_type(detail):
    if type(detail) == str:
        detail_to_json_loads = detail.replace("'", '"')
        try:
            detail_dict = json.loads(detail_to_json_loads)
            if 'type' in detail_dict.keys():
                return detail_dict['type']
        except JSONDecodeError:
            pass
    return ''