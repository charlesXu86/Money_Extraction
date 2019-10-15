# -*- coding: utf-8 -*-

'''
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   main.py
 
@Time    :   2019-07-10 16:38
 
@Desc    :
 
'''


from jio import JIO
import mon_log

try:
    jio = JIO('data/1万篇训练数据集.csv', 'result.csv')
    jio.write_result()
finally:
    mon_log.commit()