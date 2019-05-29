from django import template

register = template.Library()

@register.filter
def create_obj_rev_msg(value):
    '''目標・振り返り作成のメッセージを作成する'''
    kind_dic = {"Y":"年","M":"月","W":"週"}
    or_dic = {"O":"目標","R":"振返り"}
    prev_this_dic = {"O":"今","R":"前"}
    return "%s%sの%sが未作成です。" % (prev_this_dic[value[1:]], kind_dic[value[:1]], or_dic[value[1:]])

def create_obj_rev_link(value):
    '''目標・振り返り作成のリンクを作成する'''
    pass