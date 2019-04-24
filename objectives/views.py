from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from datetime import datetime,date,timedelta

from .models import FreeInput

# Create your views here.

@login_required
def display_index(request):
    today = date.today().strftime("%Y-%m-%d")
    # 今日日付でデータ取得
    dateFreeObjective, dateFreeReview, weekFreeObjective = get_date_data(request, today)

    return render(request, 'objectives/index.html', {
        'display_date': today,
        'dateFreeObjective': dateFreeObjective,
        'dateFreeReview': dateFreeReview,
        'weekFreeObjective': weekFreeObjective,
        })

@login_required
def display_date_data(request):
    # 指定された日付でデータ取得
    display_date = request.GET.get('target_date')
    dateFreeObjective, dateFreeReview, weekFreeObjective = get_date_data(request, display_date)
    return render(request, 'objectives/index.html', {
        'display_date': display_date,
        'dateFreeObjective': dateFreeObjective,
        'dateFreeReview': dateFreeReview,
        'weekFreeObjective': weekFreeObjective,
        })

@login_required
def get_date_data(request, display_date):
    '''指定された日付のフリーワード(目標・振り返り)、数値目標を取得
    数値目標は指定された日付の週に目標として設定されたものを表示
    '''
    # 返却する値の初期化
    objective = ""
    review = ""
    numberObjectives = []
    # クエリに必要な変数の設定
    year, date_index, week_tuple = get_date(display_date)
    # 自由入力の取得
    dateFreeObjective = FreeInput.objects.filter(
        input_unit='D',
        input_kind='O',
        year=year,
        day_index=date_index,
        user_id=request.user,
    ).first()
    dateFreeReview = FreeInput.objects.filter(
        input_unit='D',
        input_kind='R',
        year=year,
        day_index=date_index,
        user_id=request.user,
    ).first()
    weekFreeObjective = FreeInput.objects.filter(
        input_unit='W',
        input_kind='O',
        year=week_tuple[0], #isocalendarは木曜が含まれる週単位のため、実際の年と異なる可能性があるため
        day_index=week_tuple[1],
        user_id=request.user,
    ).first()
    return dateFreeObjective, dateFreeReview, weekFreeObjective

@login_required
def ajax_freeword_register(request):
    '''ajaxで送信されたパラメータを元にFreeInputを登録する。
    現状weekとdayのみ対応。month,yearは追って追加
    '''
    print("*****[#ajax_freeword_register]start*****")
    free_word = request.POST['free_word']
    id = request.POST['id']
    year, date_index, week_tuple = get_date(request.POST['input_date'])
    input_unit = request.POST['input_unit']
    input_kind = request.POST['input_kind']

    msg_str_unit = {'Y':'年','M':'月','W':'週','D':'日'}
    msg_str_kind = {'O':'目標','R':'振返り'}
    msg=msg_str_unit[input_unit]+'の'+msg_str_kind[input_kind]+'を'
    if (id):
        print("update")
        freeInput = FreeInput.objects.get(id=id)
        freeInput.free_word = free_word
        freeInput.save()
        msg+="更新しました。"
    else:
        print("create")
        day_index = date_index if input_unit=='D' else week_tuple[1]
        freeInput = FreeInput(
            input_unit = input_unit,
            input_kind = input_kind,
            year = year,
            day_index = day_index,
            free_word = free_word,
            input_status = 1,
            user_id = request.user,
        )
        freeInput.save()
        msg+="登録しました。"
    # TODO エラーハンドリング
    return HttpResponse(msg)

def get_date(target_date_str):
    '''対象日付の年、日付番号、isocalendarのtupleを返却する
    '''
    year = target_date_str.split("-")[0]
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    date_index = (target_date - datetime.strptime('{year}-01-01'.format(year=year), '%Y-%m-%d')).days + 1
    week_tuple = target_date.isocalendar() #isocalendar:年,週番号,曜日番号
    return year, date_index, week_tuple