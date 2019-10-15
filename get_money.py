# -*- coding: utf-8 -*-

'''
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   get_money.py
 
@Time    :   2019-05-30 11:06
 
@Desc    :  获取文本中的金额实体
 
'''

import jio
from functools import reduce

def get_MON_entity(text):
    '''

    :param text:
    :return:
    '''
    M = []
    MON = []
    tr = jio.wash_data(text)
    sent = jio.split_sentence(tr)
    for sentence in sent:
        money = jio.get_properties_and_values(sentence)
        M.append(money)
        for i in range(len(M)):
            if M[i]:
                MON.append(M[i])
    dup = lambda x, y: x if y in x else x + [y]  # 去重
    MON = reduce(dup, [[], ] + MON)
    return MON

