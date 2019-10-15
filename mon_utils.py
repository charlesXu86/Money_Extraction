# -*- coding: utf-8 -*-

'''
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   mon_utils.py
 
@Time    :   2019-07-16 14:51
 
@Desc    :
 
'''

import thulac
import re


def join_digit(l):
    '''
    拼接分词结果中的数字
    :param l:  传过来的list
    :return:
    '''
    digit_list = []
    for i, ll in enumerate(l):

        if int(l[i]):
            digit_list.append(l[i])

    ss = [i for i in l if l[i].isdigit]
    print(ss)
    return ss

def func_text2price(self,text0,text_fenci_all): # 车价
    res_car_price = []
    price_finditer = re.finditer(r'(人民币)?(\d+\.?\d*)(万?)(美?元?)(公里)?',text0)
    price_values_index_valid = [x + [1 if '公里' not in x[0] and ('万' in x[0] or ('.' not in x[0] and x[0][0] != '0' and 5<=len(x[0])<=7 and x[0][-2:] == '00')) else 0] for x in [[k.group(),k.start()] for k in price_finditer]]
    price_values = [x[0] for x in price_values_index_valid if x[2] == 1]
    price_index = [x[1] for x in price_values_index_valid if x[2] == 1]
    if price_values != []:
        res_sell_word = [x for x in text_fenci_all if re.match('.+价|价格|首付',x)]
        if res_sell_word != []:
            res_sell_word_index = [x.start() for x in re.finditer('|'.join(res_sell_word), text0)]
            for i in range(len(res_sell_word_index)):
                temp = [x-res_sell_word_index[i] for x in price_index]
                if [x for x in temp if x > 0]!=[]:
                    temp_min = min([x for x in temp if x>0])
                    if 0<temp_min<=7:
                        res_car_price.append(':'.join([res_sell_word[i],price_values[temp.index(temp_min)]]))
        if res_car_price == []:
            res_car_price.append(price_values[-1])
    return res_car_price


# sent = '车款大概三千来块钱吧'
# thu1 = thulac.thulac(seg_only=True)
# text = thu1.cut(sent, text=True).split(' ')
# text = text.split(' ')
# print(text)

# print(HanLP.segment('你好，欢迎在Python中调用HanLP的API'))


def get_mon_no_property(data):
    '''

    :param data:  list
    :return:
    '''
    mon_res = []
    for i in range(len(data)):
        if '万' in data[i][0]:
            mon_res.append(data[i][0])
    return mon_res

def filter_mon_value(data):
    '''
    过滤掉value比较小的值
    :param data:
    :return:
    '''
    for i in range(len(data)-1, -1, -1):
        if data[i][0].isdigit():
            if int(data[i][0]) < 1000 or int(data[i][0]) > 5000000:
                data.remove(data[i])
    return data


sentence = '你好哦，北京50福瑞英菲尼迪4万的您，是在网上咨询过说三千吗？'
values = re.findall('([1-9]\d*\.\d*|0\.\d*[1-9]\d*|[1-9]\d*[万千亿]?)(美?日?元?)', sentence)
# values = re.findall('([1-9]\d*\.\d*|0\.\d*[1-9]\d*|[1-9]\d*[万千]?)(美?日?元?)', sentence)
# price_values_index_valid = [x + [1 if '公里' not in x[0] and (
#             '万' in x[0] or ('.' not in x[0] and x[0][0] != '0' and 5 <= len(x[0]) <= 7 and x[0][-2:] == '00')) else 0]
#                             for x in [[k.group(), k.start()] for k in values]]

# get_mon_no_property(values)
filter_mon_value(values)
# print(price_values_index_valid)



