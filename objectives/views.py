from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.views.generic.edit import CreateView

from datetime import datetime,date,timedelta

from .forms import NumberObjectiveMasterForm
from .models import FreeInput,User

# Create your views here.

class NumberObjectiveMasterCreateView(LoginRequiredMixin, CreateView):
    template_name = "numberobjectivemaster/create.html"
    form_class = NumberObjectiveMasterForm
    success_url = '/objectives/master/create'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

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
    numberObjectives = []
    # 自由入力の取得
    dateFreeObjective = get_free_input('D', 'O', display_date, request.user).first()
    dateFreeReview = get_free_input('D', 'R', display_date, request.user).first()
    weekFreeObjective = get_free_input('W', 'O', display_date, request.user).first()
    return dateFreeObjective, dateFreeReview, weekFreeObjective

@login_required
def ajax_freeword_register(request):
    '''ajaxで送信されたパラメータを元にFreeInputを登録する。
    現状weekとdayのみ対応。month,yearは追って追加
    '''
    print("*****[#ajax_freeword_register]start*****")
    free_word = request.POST['free_word']
    id = request.POST['id']
    year, month, date_index, week_tuple = get_date(request.POST['input_date'])
    # 日番号：年・月・週・日
    day_index_dic = {'Y':year,'M':month,'W':week_tuple[1],'D':date_index}
    input_unit = request.POST['input_unit']
    input_kind = request.POST['input_kind']
    # 年：isocalendarは第１木曜の含まれる週を第１週とする週単位となるため、年が実際の年と異なる場合アリ
    register_year = week_tuple[0] if input_unit=='W' else year

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
        freeInput = FreeInput(
            input_unit = input_unit,
            input_kind = input_kind,
            year = register_year,
            day_index = day_index_dic[input_unit],
            free_word = free_word,
            input_status = 1,
            user = request.user,
        )
        freeInput.save()
        msg+="登録しました。"
    # TODO エラーハンドリング
    return HttpResponse(msg)

@login_required
def ajax_freeword_get(request):
    '''ajaxで送信されたパラメータを元にFreeInputを取得しJsonで返却する。
    '''
    print("*****[#ajax_freeword_get]start*****")
    input_unit = request.GET['input_unit']
    input_kind = request.GET['input_kind']
    user_id = request.GET['user']
    user = User.objects.get(id=user_id)
    freeInput = get_free_input(input_unit, input_kind, request.GET['input_date'], user)
    json = serializers.serialize('json', freeInput, ensure_ascii=False)
    return HttpResponse(json, content_type='application/json; charset=UTF-8')

def get_free_input(input_unit, input_kind, target_date_str, user):
    '''FreeInput取得のクエリを実行し結果を返却する'''
    year, month, date_index, week_tuple = get_date(target_date_str)
    # 日番号：年・月・週・日
    day_index_dic = {'Y':year,'M':month,'W':week_tuple[1],'D':date_index}
    # 年：isocalendarは第１木曜の含まれる週を第１週とする週単位となるため、年が実際の年と異なる場合アリ
    register_year = week_tuple[0] if input_unit=='W' else year
    return FreeInput.objects.filter(
        input_unit=input_unit,
        input_kind=input_kind,
        year=register_year,
        day_index=day_index_dic[input_unit],
        user=user,
    )

def get_date(target_date_str):
    '''対象日付の年、日付番号、isocalendarのtupleを返却する
    '''
    year = target_date_str.split("-")[0]
    month = target_date_str.split("-")[1]
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    date_index = (target_date - datetime.strptime('{year}-01-01'.format(year=year), '%Y-%m-%d')).days + 1
    week_tuple = target_date.isocalendar() #isocalendar:年,週番号,曜日番号
    return year, month, date_index, week_tuple
