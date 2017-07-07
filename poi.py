# coding=utf-8
import requests
import json
import threading

class PoiCrawler(object):
    ak = 'GEPiAH9zkDx5oy4K1Vj7Znw8zmbGhY0M'
    poi_base_url = 'https://api.map.baidu.com/place/v2/search?query={}&page_size=20&page_num={}&scope=2&coord_type=1&bounds={}&output=json&ak={}'
    city_center_url = 'https://api.map.baidu.com/geocoder/v2/?address={}&output=json&ak={}'
    # categories =['美食','酒店','购物','生活服务','丽人','旅游景点','休闲娱乐','运动健身','教育培训','文化传媒','医疗','汽车服务','交通设施','金融','房地产','公司企业','政府机构']
    categories = ['中餐厅$外国餐厅$小吃快餐店$蛋糕甜品店$咖啡厅$茶座$酒吧$酒店$超市','购物中心$便利店$家居建材$家电数码$集市$宿舍$园区$农林园艺$厂矿','商铺$生活服务$交通设施$金融$住宅区','丽人$休闲娱乐$旅游景点$运动健身$教育培训$文化传媒$医疗$政府机构$汽车服务$写字楼','公司']
    distance_unit = 0.01
    steps = 100
    rects = []
    pois = []
    poi_ids=[]
    location = {}
    city_name = ''
    timeout = 5
    process_number = 4

    def __init__(self, city_name,process_number):
        self.pois = [];
        self.city_name = city_name
        self.process_number = process_number

    def get_city_center(self):
        city_url = self.city_center_url.format(self.city_name, self.ak)
        r = requests.get(city_url, timeout=self.timeout)
        self.location = r.json()['result']['location']

    def get_rects_by_center(self):
        lng = self.location['lng']
        lat = self.location['lat']
        # 经纬度+-1.2度范围
        for units_lng in range(self.steps):
            dist_lng = units_lng * self.distance_unit
            for units_lat in range(self.steps):
                dist_lat = units_lat * self.distance_unit
                self.rects.append('{:.3f},{:.3f},{:.3f},{:.3f}'.format(lat - dist_lat - self.distance_unit,
                                                                       lng - dist_lng - self.distance_unit,
                                                                       lat - dist_lat, lng - dist_lng))
                self.rects.append(
                    '{:.3f},{:.3f},{:.3f},{:.3f}'.format(lat - dist_lat - self.distance_unit, lng + dist_lng,
                                                         lat - dist_lat, lng + dist_lng + self.distance_unit))
                self.rects.append(
                    '{:.3f},{:.3f},{:.3f},{:.3f}'.format(lat + dist_lat, lng - dist_lng - self.distance_unit,
                                                         lat + dist_lat + self.distance_unit, lng - dist_lng))
                self.rects.append('{:.3f},{:.3f},{:.3f},{:.3f}'.format(lat + dist_lat, lng + dist_lng,
                                                                       lat + dist_lat + self.distance_unit,
                                                                       lng + dist_lng + self.distance_unit))

    def get_poi_in_rect(self, rect):
        for category in self.categories:
            poi_url = self.poi_base_url.format(category, 0, rect, self.ak)
            print(category,rect)
            try:
                r = requests.get(poi_url, timeout=self.timeout).json()
                if r['results'] and r['total']:
                    self.save_pois(r['results'])
                    pages = round(r['total'] / 20) + 1
                    if pages > 1:
                        for page_num in range(1, pages):
                            other = requests.get(self.poi_base_url.format(category, page_num, rect, self.ak), timeout=self.timeout).json()
                            self.save_pois(other['results'])
            except:
                pass
    def save_pois(self, new_pois):
        # put it in list for now
        self.pois.extend(new_pois)

    def poi_to_string(self, poi):
        line = '\t'.join([poi['name'],
                          str(poi['location']['lat']),
                          str(poi['location']['lng']),
                          poi.get('address', ' '),
                          poi.get('telephone', ' '),
                          poi['uid']])
        if poi.get('detail_info'):
            tags = poi['detail_info'].get('tag', '其他;其他').split(';')
            line += '\t' + '\t'.join([tags[0],
                                      tags[1] if len(tags) > 1 else '其他',
                                      poi['detail_info'].get('price', ' '),
                                      poi['detail_info'].get('overall_rating', ' '),
                                      poi['detail_info'].get('service_rating', ' '),
                                      poi['detail_info'].get('environment_rating', ' ')])
        return line + '\n'

    def get_poi_in_rect_list(self,rect_list):
        for rect in rect_list:
            self.get_poi_in_rect(rect)
        print('total',len(self.pois))

    def get_all_pois(self):
        self.get_city_center()
        self.get_rects_by_center()
        len_rects = int(len(self.rects)/self.process_number)
        print('len',len_rects)
        process_list = []
        for i in range(self.process_number):
            process = threading.Thread(target=self.get_poi_in_rect_list, args=(self.rects[i*len_rects:(i+1)*len_rects],))
            process.start()
            process_list.append(process)
        for process in process_list:
            process.join()
        print('write',len(self.pois))
        self.write_pois_file()

    def write_pois_file(self):
        with open(self.city_name, 'a') as file:
            for poi in self.pois:
                if poi['uid'] not in self.poi_ids:
                    self.poi_ids.append(poi['uid'])
                    file.write(self.poi_to_string(poi))
            file.close()

if __name__ == '__main__':
    crawler = PoiCrawler('深圳',4)
    crawler.get_all_pois()
