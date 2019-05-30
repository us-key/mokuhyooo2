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
from .models import *

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
    dateFreeObjective, dateFreeReview, weekFreeObjective, numberObjective, objRevFlgList = get_date_data(request, today)

    return render(request, 'objectives/index.html', {
        'display_date': today,
        'dateFreeObjective': dateFreeObjective,
        'dateFreeReview': dateFreeReview,
        'weekFreeObjective': weekFreeObjective,
        'numberObjective': numberObjective,
        'objRevFlgList': objRevFlgList,
        })

@login_required
def display_date_data(request):
    # 指定された日付でデータ取得
    display_date = request.GET.get('target_date')
    return display_date_data_from_view(request, display_date)

def display_date_data_from_view(request, target_date):
    '''templateからではなくviewでtarget_date指定してindex表示する'''
    dateFreeObjective, dateFreeReview, weekFreeObjective, numberObjective, objRevFlgList = get_date_data(request, target_date)
    return render(request, 'objectives/index.html', {
        'display_date': target_date,
        'dateFreeObjective': dateFreeObjective,
        'dateFreeReview': dateFreeReview,
        'weekFreeObjective': weekFreeObjective,
        'numberObjective': numberObjective,
        'objRevFlgList': objRevFlgList,
        })

@login_required
def get_date_data(request, display_date):
    '''以下のデータを取得
    ・指定された日付の以下データ
    　・フリーワード(目標・振り返り)
    　・指定された日付の数値目標、実績値
    　⇒数値目標は指定された日付の週に目標として設定されたものを表示
    　・指定された日付の週のフリーワード(目標)
    　・年、月の目標設定有無
    　・前年、前月、前週の振り返り有無(目標が設定されている場合のみ)
    '''
    # 返却する値の初期化
    year, month, date_index, week_tuple = get_date(display_date)
    '''数量目標
    名称(マスタ)、集計種別(マスタ)、数値種別(マスタ)、
    目標値(数値目標)、実績集計値(実績：集計)、実績値(実績)、件数(実績：平均算出用)
    ⇒マスタと数値目標(年・週番号指定)を結合し、実績集計と当日の実績を
    　外部結合する
    '''
    numberObjective = NumberObjective.objects.raw(
        '''
        select oo.id, m.id masterid, m.name, m.number_kind, m.summary_kind, o.objective_value, oo_sum.sumval, oo.output_value, oo_sum.cnt
        from objectives_numberobjectivemaster m
        left join objectives_numberobjective o
        on m.id = o.master_id
        and m.user_id = %s
        left outer join 
        (
            select master_id, iso_year, week_index, sum(output_value) sumval, count(*) cnt
            from objectives_numberobjectiveoutput
            group by master_id, iso_year, week_index
        ) oo_sum
        on o.master_id = oo_sum.master_id
        and o.iso_year = oo_sum.iso_year
        and o.week_index = oo_sum.week_index

        left outer join objectives_numberobjectiveoutput oo
        on o.master_id = oo.master_id
        and o.iso_year = oo.iso_year
        and o.week_index = oo.week_index
        and oo.date_index = %s

        where o.iso_year = %s
        and o.week_index = %s
        ''' % (request.user.id, date_index, week_tuple[0], week_tuple[1])
    )
    print(list(numberObjective))
    # 自由入力の取得
    dateFreeObjective = get_free_input('D', 'O', year, month, date_index, week_tuple, request.user).first()
    dateFreeReview = get_free_input('D', 'R', year, month, date_index, week_tuple, request.user).first()
    weekFreeObjective = get_free_input('W', 'O', year, month, date_index, week_tuple, request.user).first()
    # 前年、前月取得
    pYear = str(int(year) - 1)
    (pMYear, pMonth) = (year, str(int(month) - 1)) if int(month) > 1 else (str(int(year) - 1), "12")
    # 前週の変数取得
    pWYear, pWMonth, pWDate_index, pWWeek_tuple = get_date(get_date_str_diff(display_date, -7))
    # 前日の変数取得
    pDYear, pDMonth, pDDate_index, pDWeek_tuple = get_date(get_date_str_diff(display_date, -1))

    # 年・月の目標設定有無(有：1、無：0)
    # 年・月・週・日の振り返り設定有無(目標設定有&振り返り設定無：0、それ以外：1)
    objRevFlgList = {
        'YO': '1' if get_free_input('Y','O', year, month, date_index, week_tuple, request.user) else '0',
        'MO': '1' if get_free_input('M','O', year, month, date_index, week_tuple, request.user) else '0',
        # 使わない項目は0渡す
        'YR': '0' if (get_free_input('Y','O', pYear, '0', '0', ['0','0','0'], request.user)
                and not get_free_input('Y','R', pYear, '0', '0', ['0','0','0'], request.user)) else '1',
        'MR': '0' if (get_free_input('M','O', pMYear, pMonth, '0', ['0','0','0'], request.user)
                and not get_free_input('M','R', pMYear, pMonth, '0', ['0','0','0'], request.user)) else '1',
        'WR': '0' if (get_free_input('W','O', '0', '0', '0', pWWeek_tuple, request.user)
                and not get_free_input('W','R', '0', '0', '0', pWWeek_tuple, request.user)) else '1',
        'DR': '0' if (get_free_input('D','O', pDYear, '0', pDDate_index, ['0','0','0'], request.user)
                and not get_free_input('D','R', pDYear, '0', pDDate_index, ['0','0','0'], request.user)) else '1',
    }
    return dateFreeObjective, dateFreeReview, weekFreeObjective, numberObjective, objRevFlgList

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
    year, month, date_index, week_tuple = get_date(request.GET['input_date'])
    freeInput = get_free_input(input_unit, input_kind, year, month, date_index, week_tuple, user)
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
                iso_year = week_tuple[0],
                week_index = week_tuple[1],
                objective_value = int(obj["value"]),
            )
            numberObjective.save()
    return JsonResponse({"target_date":target_date})

@login_required
def ajax_dateoutput_create(request):
    '''ajaxで送信されたデータを元に日の実績を登録する'''
    print("*****[#ajax_dateoutput_create]start*****")
    data = json.loads(request.body)
    print(data)
    target_date = data["target_date"]
    if (target_date != ''):
        year, month, date_index, week_tuple = get_date(target_date)
        outputs = data["outputs"]
        print(outputs)
        for obj in outputs:
            # TODO 登録と更新の場合分け
            if obj["id"] != "":
                # 更新
                numberObjectiveOutput = NumberObjectiveOutput.objects.get(id=int(obj["id"]))
                numberObjectiveOutput.output_value = int(obj["value"])
                numberObjectiveOutput.save()
            else:
                master = NumberObjectiveMaster.objects.get(id=int(obj["master_id"]))
                # TODO エラーハンドリング
                if master:
                    numberObjectiveOutput = NumberObjectiveOutput(
                        master = master,
                        iso_year = week_tuple[0],
                        week_index = week_tuple[1],
                        date_index = date_index,
                        output_value = int(obj["value"]),
                    )
                    numberObjectiveOutput.save()
    return JsonResponse({"target_date":target_date})

@login_required
def display_week_objective_form(request, datestr):
    '''週の目標設定画面表示'''
    start_date, end_date = get_week_start_and_end(datestr)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    # 1週前の実績取得：7日前の日付を元に取得
    year, month, date_index, week_tuple = get_date(get_date_str_diff(datestr, -7))
    #numberObjectiveMaster = NumberObjectiveMaster.objects.filter(user=request.user, valid_flag="1")
    numObj = NumberObjectiveMaster.objects.raw(
        '''
        select m.*, o_sum.sumval, o_sum.cnt
        from objectives_numberobjectivemaster m
        left outer join 
        (
            select master_id, iso_year, week_index, sum(output_value) sumval, count(*) cnt
            from objectives_numberobjectiveoutput o
            group by master_id, iso_year, week_index
        ) o_sum
        on m.id = o_sum.master_id
        and o_sum.iso_year = %s
        and o_sum.week_index = %s
        where m.user_id = %s
        and   m.valid_flag = '1'
        ''' % (week_tuple[0], week_tuple[1], request.user.id)
    )

    return render(request, 'objectives/week_objective_form.html', {
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'masters': numObj,
    })

@login_required
def display_objrev_form(request, key, target_date):
    if key[:1] == "D":
        target_date = get_date_str_diff(target_date, -1)
        return display_date_data_from_view(request, target_date)
    return render(request, 'objectives/objrev_form.html')


def get_free_input(input_unit, input_kind, year, month, date_index, week_tuple, user):
    '''FreeInput取得のクエリを実行し結果を返却する'''
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

def get_date_str_diff(target_date_str, diff):
    '''対象日付から一定の日付を加算or減算した日付の文字列を得る
    '''
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d') + timedelta(diff)
    return datetime.strftime(target_date, '%Y-%m-%d')

def get_week_start_and_end(target_date_str):
    '''対象日付を含む週の開始日・終了日(datetime)を返却する'''
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    week_tuple = target_date.isocalendar() #isocalendar:年,週番号,曜日番号
    # isocalendarは月曜=1、日曜=7
    start_date = target_date + timedelta(days=(1-week_tuple[2]))
    end_date = target_date + timedelta(days=7-week_tuple[2])
    return start_date, end_date