from django import template

register = template.Library()

@register.filter
def dividie(value, args):
    if value is None or args is None or value == 0 or args == 0:
        return 0
    else:
        return value // args

@register.filter
def percentie(value, args):
    if value is None or args is None or value == 0 or args == 0:
        return 0
    else:
        return dividie(value*100, args)

@register.filter
def num_to_time(value):
    if value is None or value == "":
        return ""
    # 時:分に変換
    return str(value // 60) + ":" + ("00" + str(value % 60))[-2:]