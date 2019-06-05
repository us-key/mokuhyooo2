from django import template

register = template.Library()

@register.filter
def number_kind_choices(key):
    '''数値種別'''
    dic = {'N':'数値', 'P':'時間', 'T':'時刻',}
    return dic[key]

@register.filter
def summary_kind(key):
    '''集計種別'''
    dic = {'S':'合計', 'A':'平均',}
    return dic[key]

@register.filter
def input_unit(key):
    '''入力単位'''
    dic = {'Y':'年', 'M':'月', 'W':'週', 'D':'日',}
    return dic[key]

@register.filter
def input_kind(key):
    '''入力種別'''
    dic = {'O':'目標', 'R':'振返り',}
    return dic[key]

