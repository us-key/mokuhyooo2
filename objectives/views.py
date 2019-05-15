import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from datetime import datetime,date,timedelta

from .forms import NumberObjectiveMasterForm
from .models import FreeInput,User,NumberObjectiveMaster, NumberObjective

# Create your views here.

class NumberObjectiveMasterListView(LoginRequiredMixin, ListView):
    '''数値目標一覧画面'''
    template_name = "numberobjectivemaster/list.html"
    model = NumberObjectiveMaster

    def get_queryset(self):
        return NumberObjectiveMaster.objects.filter(user=self.request.user)

class NumberObjectiveMasterCreateView(LoginRequiredMixin, CreateView):
    '''数値目標マスタ作成画面'''
    template_name = "numberobjectivemaster/create.html"
    form_class = NumberObjectiveMasterForm
    success_url = reverse_lazy('objectives:master_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.valid_flag = "1"
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

@login_required
def ajax_weekobj_create(request):
    '''ajaxで送信されたデータを元に週目標を登録する'''
    print("*****[#ajax_weekobj_create]start*****")
    data = json.loads(request.body)
    print(data)
    target_date = data["target_date"]
    if (target_date != ''):
        free_word = data["free_word"]
        year, month, date_index, week_tuple = get_date(target_date)
        print(free_word)
        if (free_word != ''):
            freeInput = FreeInput(
                input_unit = 'W',
                input_kind = 'O',
                year = week_tuple[0],
                day_index = week_tuple[1],
                free_word = free_word,
                input_status = 1,
                user = request.user,
            )
            freeInput.save()
        objectives = data["objectives"]
        print(objectives)
        for obj in objectives:
            numberObjective = NumberObjective(
                master_id = NumberObjectiveMaster.objects.get(id=int(obj["master_id"])),
                year = week_tuple[0],
                week_index = week_tuple[1],
                objective_value = int(obj["value"]),
            )
            numberObjective.save()
    return HttpResponse(target_date)


@login_required
def display_week_objective_form(request, datestr):
    '''週の目標設定画面表示'''
    start_date, end_date = get_week_start_and_end(datestr)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    numberObjectiveMaster = NumberObjectiveMaster.objects.filter(user=request.user, valid_flag="1")



    return render(request, 'objectives/week_objective_form.html', {
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'masters': numberObjectiveMaster,
    })

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

def get_week_start_and_end(target_date_str):
    '''対象日付を含む週の開始日・終了日(datetime)を返却する'''
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    week_tuple = target_date.isocalendar() #isocalendar:年,週番号,曜日番号
    # isocalendarは月曜=1、日曜=7
    start_date = target_date + timedelta(days=(1-week_tuple[2]))
    end_date = target_date + timedelta(days=7-week_tuple[2])
    return start_date, end_date