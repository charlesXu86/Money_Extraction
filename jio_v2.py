# -*- coding: utf-8 -*-

'''
@Author  :   Xu

@Software:   PyCharm

@File    :   jio_v2.py

@Time    :   2019-05-30 11:06

@Desc    :   金额实体抽取核心处理类

'''

from enum import Enum, unique
import jieba
import re
import mon_log
import thulac

from mon_utils import filter_mon_value
from mon_utils import get_mon_no_property

# from nlp_model.inf_score

@unique
class Consts(Enum):
    BUFFER_SIZE = 100


propertyKs = ('.+金$', '.+款$', '.+费用?$', '.+险$', '.+税$', '利息', '首付', '.+价$', '价格', '.+费', '.+款', '优惠', '预算')  # 改
propertyKeys = ('.+金$', '.+款$', '.+费用?$', '.+险$', '.+税$', '.*损失$', '.+赔偿$', '.+利$', '首付', '.+价$', '价格')  # 改
adjust_src = ['借款本金', '贷款本金', '欠款本金', '拖运费', '透支款本金', '透支的本金']
adjust_dst = ['借款', '贷款', '欠款', '托运费', '透支款']
abandon_src = ['余款', '费用', '合计', '共计', '总计', '小计', '存款', '小利', '价值款']
abandon_vrb = ['扣除', '再扣除', '总计', '合计', '其中', '返还']
pay_vrb = ['偿还', '赔偿', '赔付', '支付']
pay_pattern = r'在?(.*险)(范围|限额)?.*(支付|偿还|赔偿|赔付).*\d元'
abandon_pattern = r'^(合计|总计|共计|去除|除去|扣除|再扣除).*(人民币)?\d*\.?\d\d?(美|日)?元'

num_bits = (3, 5, 7, 10, 12, 14)
spe_bits = (8, 15)
bit_bits = (2, 4, 6, 9, 11, 13)

thu1 = thulac.thulac(seg_only=True)

class MonNormalizer:
    def __init__(self):
        self.propertyKs = propertyKs
        self.propertyKeys = propertyKeys
        self.adjust_src = adjust_src
        self.adjust_dst = adjust_dst
        self.abandon_src = abandon_src
        self.abandon_vrb = abandon_vrb
        self.pay_vrb = pay_vrb
        self.pay_pattern = pay_pattern
        self.abandon_pattern = abandon_pattern

        self.num_bits = num_bits
        self.spe_bits = spe_bits
        self.bit_bits = bit_bits

    def repl_2dig(self, match_obj):
        result = ''
        max_bit = None
        for i in range(2, 20):
            if i in bit_bits:
                group_i = match_obj.group(i)
                if group_i is not None:
                    if max_bit is None:
                        max_bit = i
                        continue
                    if group_i == '零':
                        result += '0'
                else:
                    if max_bit is not None and i > max_bit:
                        result += '0'

            if i in num_bits:
                if match_obj.group(i) is not None:
                    result += match_obj.group(i)

            if i in spe_bits:
                if match_obj.group(i) is not None:
                    result += match_obj.group(i)
                    if max_bit is None:
                        max_bit = i
                elif max_bit is not None and i > max_bit:
                    result += '0'

        if match_obj.group(17) is not None:
            result += ('.' + match_obj.group(17))
            if match_obj.group(19) is not None:
                result += match_obj.group(19)
        elif match_obj.group(19) is not None:
            result += ('.0' + match_obj.group(19))
        return result + '元'


    def is_property(self, string):
        """
        判断一个字符串是否是款项类别
        :param string: 一个字符串
        :return:  如果string是以金/款/费/险结尾，或其他可能是款项类别的词语，就会返回True,否则False
        """
        for key in propertyKs:
            match = re.match(key, string)
            if match:
                return True
        return False


    def belong_property(self, string):
        for key in propertyKeys:
            match = re.match(key, string)
            if match:
                return True
        return False


    def is_abandon(self, string):
        for key in abandon_vrb:
            match = re.match(key, string)
            if match:
                return key
        return None


    def is_pay_vrb(self, string):
        for key in pay_vrb:
            search = re.search(key, string)
            if search:
                return True
        return False


    def get_properties_and_values(self, sentence):
        """
        从一个包含金额的句子中找到对应的款项类别
        :param sentence: 待处理的原句子
        :param intent: 该msg对应的意图
        :return: 从sentence中获取到的所有Property:Value的dict
        """
        quick_get_disabled = False
        pv_dict = {}


        # cut_words = jieba.lcut(sentence, cut_all=False)   # 结巴分词

        cut_words = thu1.cut(sentence, text=True).split(' ')

        # values = re.findall(r'(人民币)?([1-9]\d*\.\d*|0\.\d*[1-9]\d*|[1-9]\d*)(万?)(千?)(亿?)(美?日?元)', sentence)
        values = filter_mon_value(re.findall('([1-9]\d*\.\d*|0\.\d*[1-9]\d*|[1-9]\d*[万千亿]?)(美?日?元?)', sentence)) # 匹配出所有的包含有金额相关的数字



        last_index = 0
        for j in range(len(values)):
            for i in range(len(cut_words)):
                # value[j][1]是sentence中的第j个金额数字，通过下面这个比较，将得出“金额数字”在分词结果的下标(i)
                if cut_words[i] == values[j][0]:
                    v = values[j][0]
                    # v3 = values[j][3]
                    # v4 = values[j][4]

                    # if values[j][2] == '千':
                    #     v += '000'
                    # if values[j][2] == '万':
                    #     v = v + '万'
                    # if values[j][2] == '亿':
                    #     v += '00000000'
                    vrb_index = 0
                    pr_index_list = []
                    for k in range(1, i - last_index + 1):  # i是金额数字的下标
                        # 从金额数字前的那个词开始，到上一个金额数字的后一个词，
                        # 如果紧挨着的就是property,就立马认可，处理下一个金额数字
                        # 否则记录这些发现的property的下标
                        # 如果发现了要abandon的词，就中止对这个数字金额的处理，继续处理下一个
                        # 如果发现了赔付性动词，则记录这个动词的位置
                        word_index = i - k
                        seg = cut_words[word_index]
                        if self.is_property(seg):      # 如果在文本中拿到了金额的属性，则使用该属性，如果没有属性，则使用调用意图的结果作为属性
                            if k in range(5):
                                if not quick_get_disabled:
                                    pv_dict[seg] = v + '元'
                                    mon_log.p(seg)
                                    break
                            else:
                                pr_index_list.append(word_index)
                                continue
                        else:
                            pass

                        # if self.is_abandon(seg) and k in range(2):
                        #     break
                        if self.is_pay_vrb(seg):
                            vrb_index = word_index
                        if self.belong_property(seg):
                            if len(seg) < 3:
                                if word_index - 1 > last_index:
                                    mon_log.n(cut_words[word_index - 1] + seg)
                            if word_index not in pr_index_list:
                                pr_index_list.append(word_index)
                    # end for
                    length = len(pr_index_list)
                    last_index = i #改 添加了
                    if vrb_index > 0 and length > 1:
                        count = 0
                        while count < length and pr_index_list[count] > vrb_index:
                            count += 1
                        if count < length:
                            ind = pr_index_list[count]
                            p = cut_words[ind]
                            pv_dict[p] = v + '元'
                            mon_log.p(p)
                            break
                    if length > 0:
                        p = cut_words[pr_index_list[0]]
                        pv_dict[p] = v + '元'
                        mon_log.p(p)
                    break
        return pv_dict


    def wash_data(self, string):
        """
        去除干扰：数字之间的逗号、数字间的字母、替换汉字数字成阿拉伯数字、去掉括号的内容
        :return 对原字符串清洗后的字符串
        """
        string = re.sub('(（|\()[^（）]*(）|\))', '', string)  # 去除括号括起来的部分
        string = re.sub('【[^【】]*】', '', string)  # 去除圆角中括号括起来的部分
        string = re.sub('\[[^\[\]]*\]', '', string)  # 去除中括号括起来的部分
        string = re.sub('([1-9]\d*)，(?=\d)', '\\1', string)  # 去除数字之间的的逗号
        string = re.sub('(\d)(O|o|〇)(?=\d)', '\\g<1>0', string)  # 替换数字间写错的零成：0
        # 替换汉字数字成阿拉伯数字
        string = re.sub('一|Ⅰ|壹', '1', string)
        string = re.sub('二|Ⅱ|贰', '2', string)
        string = re.sub('三|Ⅲ|叄', '3', string)
        string = re.sub('四|Ⅳ|肆', '4', string)
        string = re.sub('五|Ⅴ|伍', '5', string)
        string = re.sub('六|Ⅵ|陆', '6', string)
        string = re.sub('七|Ⅶ|柒', '7', string)
        string = re.sub('八|Ⅷ|捌', '8', string)
        string = re.sub('九|Ⅸ|玖', '9', string)
        string = re.sub('零', '0', string)
        # 处理汉字数字的进制单位
        pattern = re.compile(
                r'(?<=[^\d\.])(((\d)[千仟])?((\d)[百佰]|零)?((\d)[十拾]|零)?(\d)?万)?((\d)[千仟]|零)?((\d)[百佰]|零)?((\d)[十拾]|零)?(\d)?元零?((\d|零)角|零)?(([1-9])分)?')
        string = re.sub(pattern, self.repl_2dig, string)
        return string


    def split_sentence(self, article):
        """
        切分出包含数字金额的句子,扣除
        :param article:
        :return: 将article切分，并过滤后的句子的list
        """
        raw_list = re.split('，|。|,|；', article)
        ripe_list = []
        for s in raw_list:
            search = re.search(r'(人民币)?([1-9]\d*\.\d*|0\.\d*[1-9]\d*|[1-9]\d*)(万?)(千?)(亿?)(美?日?元?)', s) #改
            if search:
                if re.search(abandon_pattern, s):
                    continue
                ripe_list.append(s)
        return ripe_list


    def adjust(self, p):
        p.replace('费费', '费')
        p.replace('款款', '款')
        p.replace('金金', '金')
        p.replace('险险', '险')
        p.replace('税税', '税')
        p = re.sub('1', '一', p)
        p = re.sub('2', '二', p)
        p = re.sub('3', '三', p)
        p = re.sub('4', '四', p)
        p = re.sub('5', '五', p)
        p = re.sub('6', '六', p)
        p = re.sub('7', '七', p)
        p = re.sub('8', '八', p)
        p = re.sub('9', '九', p)
        for i in range(len(adjust_src)):
            if re.search(adjust_src[i], p):
                p = adjust_dst[i]
                break
        for i in range(len(abandon_src)):
            if re.search(abandon_src[i], p):
                p = None
                break
        return p
