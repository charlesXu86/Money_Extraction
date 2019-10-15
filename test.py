# -*- coding: utf-8 -*-

'''
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   test.py
 
@Time    :   2019-10-15 14:12
 
@Desc    :
 
'''

from get_money import get_MON_entity

aaa = '我的购车预算是50万元'
# aaa = '买奥迪补助5000元'

mons = get_MON_entity(aaa)
print(mons)