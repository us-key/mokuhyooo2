from django import template

register = template.Library()

@register.filter
def dividie(value, args):
    if value is None or args is None or value == 0 or args == 0:
        return 0
    else:
        return value // args

@register.filter
def num_to_time(value):
    if value is None:
        return ""
    # 時:分に変換
    return str(value // 60) + ":" + str(value % 60)