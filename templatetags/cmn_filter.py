from django import template

register = template.Library()

@register.filter
def create_obj_rev_msg(key):
    '''目標・振り返り作成のメッセージを作成する'''
    kind_dic = {"Y":"年","M":"月","W":"週","D":"日"}
    or_dic = {"O":"目標","R":"振返り"}
    prev_this_dic = {"T":"今","P":"前"}
    return "%s%sの%sが未作成です。" % (prev_this_dic[key[:1]], kind_dic[key[1:2]], or_dic[key[2:]])

@register.filter
def create_obj_rev_link(key, target_date):
    '''目標・振り返り作成のリンクを作成する'''
    return "/objectives/objrev/%s/%s" % (key, target_date)

@register.filter
def get_checkbox(key):
    if key == "1":
        return "fas fa-check-square"
    else:
        return "far fa-square"
