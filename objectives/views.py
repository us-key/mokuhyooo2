from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from datetime import datetime,date,timedelta

from .models import FreeInput

# Create your views here.

@login_required
def display_index(request):
    today = date.today().strftime("%Y-%m-%d")
    # 今日日付でデータ取得
    freeObjective, freeReview = get_date_data(request, today)

    return render(request, 'objectives/index.html', {
        'display_date': today,
        'freeObjective': freeObjective,
        'freeReview': freeReview,
        })

@login_required
def display_date_data(request):
    # 指定された日付でデータ取得
    display_date = request.GET.get('display_date')
    freeObjective, freeReview = get_date_data(request, display_date)
    return render(request, 'objectives/index.html', {
        'display_date': display_date,
        'freeObjective': freeObjective,
        'freeReview': freeReview,
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
    year = display_date.split("-")[0]
    day_index = (datetime.strptime(display_date, '%Y-%m-%d')-datetime.strptime('{year}-01-01'.format(year=year), '%Y-%m-%d')).days + 1
    # 自由入力の取得
    freeObjective = FreeInput.objects.filter(
        input_unit='D',
        input_kind='O',
        year=year,
        day_index=day_index,
        user_id=request.user,
    )
    freeReview = FreeInput.objects.filter(
        input_unit='D',
        input_kind='R',
        year=year,
        day_index=day_index,
        user_id=request.user,
    )
    return freeObjective, freeReview
