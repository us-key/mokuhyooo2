import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.db.models import Max

from datetime import datetime,date,timedelta

from .forms import NumberObjectiveMasterForm
from .models import *

# Create your views here.

class NumberObjectiveMasterListView(LoginRequiredMixin, ListView):
    '''数値目標一覧画面'''
    template_name = "numberobjectivemaster/list.html"
    model = NumberObjectiveMaster

    def get_queryset(self):
        return NumberObjectiveMaster.objects.filter(user=self.request.user).order_by('order_index')

class NumberObjectiveMasterCreateView(LoginRequiredMixin, CreateView):
    '''数値目標マスタ作成画面'''
    template_name = "numberobjectivemaster/create.html"
    form_class = NumberObjectiveMasterForm
    success_url = reverse_lazy('objectives:master_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.valid_flag = "1"
        # ソート順は登録済みレコードのmax+1を登録する
        max = NumberObjectiveMaster.objects.filter(
            user=self.request.user,
            valid_flag="1",
            ).aggregate(Max("order_index"))
        form.instance.order_index = max["order_index__max"]+1
        return super().form_valid(form)

class NumberObjectiveMasterUpdateView(LoginRequiredMixin, UpdateView):
    '''数値目標マスタ更新画面'''
    model = NumberObjectiveMaster
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
        order by m.order_index
        ''' % (request.user.id, date_index, week_tuple[0], week_tuple[1])
    )
    print(list(numberObjective))
    # 自由入力の取得
    dateFreeObjective = get_free_input_date(year, date_index, "O", request.user).first()
    dateFreeReview = get_free_input_date(year, date_index, "R", request.user).first()
    weekFreeObjective = get_free_input_week(week_tuple[0], week_tuple[1], "O", request.user).first()
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
        'TYO': '1' if get_free_input_year(year, "O", request.user) else '0',
        'TMO': '1' if get_free_input_month(year, month, "O", request.user) else '0',
        'TYR': '1' if get_free_input_year(year, "R", request.user) else '0',
        'TMR': '1' if get_free_input_month(year, month, "R", request.user) else '0',
        'TWR': '1' if get_free_input_week(week_tuple[0], week_tuple[1], "R", request.user) else '0',
        # 使わない項目は0渡す
        'PYR': '0' if (get_free_input_year(pYear, "O", request.user)
                and not get_free_input_year(pYear, "R", request.user)) else '1',
        'PMR': '0' if (get_free_input_month(pMYear, pMonth, "O", request.user)
                and not get_free_input_month(pMYear, pMonth, "R", request.user)) else '1',
        'PWR': '0' if (get_free_input_week(pWWeek_tuple[0], pWWeek_tuple[1], "O", request.user)
                and not get_free_input_week(pWWeek_tuple[0], pWWeek_tuple[1], "R", request.user)) else '1',
        'PDR': '0' if (get_free_input_date(pDYear, pDDate_index, "O", request.user)
                and not get_free_input_date(pDYear, pDDate_index, "R", request.user)) else '1',
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
            # 新規作成
            if data["mode"] == "C":
                freeInput = FreeInput(
                    input_unit = 'W',
                    input_kind = 'O',
                    year = week_tuple[0],
                    day_index = week_tuple[1],
                    free_word = free_word,
                    input_status = 1,
                    user = request.user,
                )
            # 更新
            else:
                freeInput = get_free_input_week(week_tuple[0], week_tuple[1], "O", request.user).first()
                freeInput.free_word = free_word
            freeInput.save()
        objectives = data["objectives"]
        print(objectives)
        # 新規作成
        if data["mode"] == "C":
            for obj in objectives:
                numberObjective = NumberObjective(
                    master = NumberObjectiveMaster.objects.get(id=int(obj["master_id"])),
                    iso_year = week_tuple[0],
                    week_index = week_tuple[1],
                    objective_value = int(obj["value"]),
                )
                numberObjective.save()
        # 更新
        else:
            # 数値目標マスタを全件取得の上、登録値あり＆入力値あり：更新、登録値あり＆入力値なし：削除
            # 登録値なし＆入力値あり：登録、登録値なし＆入力値なし：なにもしない
            master = NumberObjectiveMaster.objects.filter(
                valid_flag = "1",
                user = request.user,
            )
            for m in master:
                # 数値目標登録値の有無確認
                numberObjective = NumberObjective.objects.filter(
                    master = m,
                    iso_year = week_tuple[0],
                    week_index = week_tuple[1],
                ).first()
                # 登録あり
                if numberObjective:
                    flg = False
                    for obj in objectives:
                        # 入力値あり:値更新
                        if m.id == int(obj["master_id"]):
                            numberObjective.objective_value = int(obj["value"])
                            numberObjective.save()
                            flg = True
                    # 入力値なし:削除
                    if not flg:
                        numberObjective.delete()
                # 登録なし
                else:
                    for obj in objectives:
                        # 入力値あり:値登録
                        if m.id == int(obj["master_id"]):
                            numberObjective = NumberObjective(
                                master = m,
                                iso_year = week_tuple[0],
                                week_index = week_tuple[1],
                                objective_value = int(obj["value"])
                            )
                            numberObjective.save()
                        # 入力値なし:何もしない
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
        # 週目標を全て取得し、入力値の有無で場合分け
        # 週目標あり＆入力値あり：登録or更新、週目標あり＆入力値なし：何もしないor削除
        
        # 週の数値目標を取得
        numObj = NumberObjective.objects.filter(
            master__user = request.user,
            iso_year = week_tuple[0],
            week_index = week_tuple[1],
        )
        for no in numObj:
            flg = False            
            for obj in outputs:
                # 週目標あり＆入力値あり
                if no.master.id == int(obj["master_id"]):
                    # TODO 登録と更新の場合分け
                    if obj["id"] != "":
                        # 更新
                        numberObjectiveOutput = NumberObjectiveOutput.objects.get(id=int(obj["id"]))
                        numberObjectiveOutput.output_value = int(obj["value"])
                        numberObjectiveOutput.save()
                    else:
                        master = NumberObjectiveMaster.objects.get(id=no.master.id)
                        # 登録
                        if master:
                            numberObjectiveOutput = NumberObjectiveOutput(
                                master = master,
                                year = year,
                                month = month,
                                iso_year = week_tuple[0],
                                week_index = week_tuple[1],
                                date_index = date_index,
                                day_of_week = week_tuple[2],
                                output_value = int(obj["value"]),
                            )
                            numberObjectiveOutput.save()
                    # フラグを立てる
                    flg = True
            if not flg:
                # 入力値なし：削除
                numObjOut = NumberObjectiveOutput.objects.filter(
                    master = no.master,
                    year = year,
                    month = month,
                    iso_year = week_tuple[0],
                    week_index = week_tuple[1],
                    date_index = date_index,
                ).first()
                if numObjOut:
                    numObjOut.delete()
    return JsonResponse({"target_date":target_date})

@login_required
def ajax_numobjmst_order_update(request):
    '''ajaxで送信されたデータを元にマスタのソート順を更新する'''
    print("*****[#ajax_numobjmst_order_update]start*****")
    data = json.loads(request.body)
    print(data)
    orders = data["data"]
    for k,v in orders.items():
        numobjmst = NumberObjectiveMaster.objects.get(id=int(k))
        numobjmst.order_index = int(v)
        numobjmst.save()
    return JsonResponse({"msg": "ソート順を更新しました。"})



@login_required
def display_week_objective_form(request, datestr):
    '''週の目標設定画面表示'''
    start_date, end_date = get_week_start_and_end(datestr)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    # 1週前の実績取得：7日前の日付を元に取得
    year, month, date_index, week_tuple = get_date(get_date_str_diff(datestr, -7))
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
        order by m.order_index
        ''' % (week_tuple[0], week_tuple[1], request.user.id)
    )

    return render(request, 'objectives/week_objective_form.html', {
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'masters': numObj,
        'mode': 'C',
    })

@login_required
def display_week_objective_form_edit(request, datestr):
    '''週の目標設定画面表示(編集)'''
    start_date, end_date = get_week_start_and_end(datestr)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # 1週前の実績取得：7日前の日付を元に取得
    # 設定済みの目標値取得
    year, month, date_index, week_tuple = get_date(datestr)
    pYear, pMonth, pDate_index, pWeek_tuple = get_date(get_date_str_diff(datestr, -7))
    numObj = NumberObjectiveMaster.objects.raw(
        '''
        select m.*, o.objective_value, o_sum.sumval, o_sum.cnt
        from objectives_numberobjectivemaster m
        left outer join objectives_numberobjective o
        on m.id = o.master_id
        and o.iso_year = %s
        and o.week_index = %s
        left outer join 
        (
            select master_id, iso_year, week_index, sum(output_value) sumval, count(*) cnt
            from objectives_numberobjectiveoutput
            group by master_id, iso_year, week_index
        ) o_sum
        on m.id = o_sum.master_id
        and o_sum.iso_year = %s
        and o_sum.week_index = %s
        where m.user_id = %s
        and   m.valid_flag = '1'
        order by m.order_index
        ''' % (week_tuple[0], week_tuple[1], pWeek_tuple[0], pWeek_tuple[1], request.user.id)
    )

    # 自由入力
    freeInput = get_free_input_week(week_tuple[0], week_tuple[1], "O", request.user).first()

    return render(request, 'objectives/week_objective_form.html', {
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'free_input': freeInput,
        'masters': numObj,
        'mode': 'U',
    })


@login_required
def display_objrev_form(request, key, target_date):
    '''key 1桁目:T/P(This/Prev)
           2桁目:Y/M/W/D(Year/Month/Week/Date)
           3桁目:O/R(Objective/Review)
       tartet_date 基準とする日付
    '''
    # 日：当日または前日のindexに飛ぶ
    if key[1:2] == "D":
        if key [:1] == "P":
            target_date = get_date_str_diff(target_date, -1)
        return display_date_data_from_view(request, target_date)
    
    # 返却値の初期化
    free_input_obj = {} # 目標自由入力
    free_input_rev = {} # 振り返り自由入力
    target_period_str = "" # 対象期間を表す文字列
    target_date_str = "" # 対象日付(登録時に使用)を表す文字列
    
    year, month, date_index, week_tuple = get_date(target_date)
    # 目標作成時：目標のみ、振り返り作成時：目標＋振り返り
    # 週
    if key[1:2] == "W":
        # 週の目標はdisplay_week_objective_form呼出
        if key[:1] == "P":
            target_date = get_date_str_diff(target_date, -7)
        if key[2:] == "O":
            return display_week_objective_form(request, target_date)
        elif key[2:] == "R":
            pYear, pMonth, pDate_index, pWeek_tuple = get_date(target_date)
            free_input_obj = get_free_input_week(pWeek_tuple[0], pWeek_tuple[1], "O", request.user).first()
            free_input_rev = get_free_input_week(pWeek_tuple[0], pWeek_tuple[1], "R", request.user).first()
        # 対象期間
        start_date, end_date = get_week_start_and_end(target_date)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        target_period_str = "%s ~ %s" % (start_date_str, end_date_str)
        target_date_str = start_date_str

    # 月
    elif key[1:2] == "M":
        if key[:1] == "P":
            (year, month) = (year, str(int(month) - 1)) if int(month) > 1 else (str(int(year) - 1), "12")
        free_input_obj = get_free_input_month(year, month, "O", request.user).first()
        if key[2:] == "R":
            free_input_rev = get_free_input_month(year, month, "R", request.user).first()
        # 対象期間
        target_period_str = "%s-%s" % (str(year), str(month).zfill(2))
        target_date_str = target_period_str
    # 年
    elif key[1:2] == "Y":
        if key[:1] == "P":
            year = str(int(year) - 1)
        free_input_obj = get_free_input_year(year, "O", request.user).first()
        if key[2:] == "R":
            free_input_rev = get_free_input_year(year, "R", request.user).first()
        # 対象期間
        target_period_str = "%s" % str(year)
        target_date_str = target_period_str

    # 振返りの場合、週・月・年で集計した定量目標の実績を表示する
    num_obj_rev = {}
    if key[2:] == "R":
        # 週
        # 目標名、目標値、合計値、件数
        get_numobj_summary(key[1:2], request.user, target_date)
        
        if key[1:2] == "W":
            num_obj_rev = NumberObjectiveMaster.objects.raw(
            '''
            select m.id, m.name, m.number_kind, m.summary_kind, o.objective_value, oo_sum.sumval, oo_sum.cnt
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

            where o.iso_year = %s
            and o.week_index = %s
            order by m.order_index
            ''' % (request.user.id, pWeek_tuple[0], pWeek_tuple[1],)
            )
        else:
            # 年・月の場合は目標値取得しない
            # TODO クエリを分解して共通部分と分かれる部分にする
            # num_obj_rev = NumberObjectiveMaster.objects.raw(
            sql_str = '''
                select m.id, m.name, m.number_kind, m.summary_kind, oo_sum.sumval, oo_sum.cnt
                from objectives_numberobjectivemaster m
                left outer join 
                '''
            sql_str2 = ""
            if key[1:2] == "Y":
                sql_str2 = '''
                (
                select master_id, year, sum(output_value) sumval, count(*) cnt
                from objectives_numberobjectiveoutput
                group by master_id, year
                ) oo_sum
                on m.id = oo_sum.master_id
                and oo_sum.year = %s
                where m.user_id = %s
                order by m.order_index
                ''' % (year, request.user.id)
            elif key[1:2] == "M":
                sql_str2 = '''
                (
                select master_id, year, month, sum(output_value) sumval, count(*) cnt
                from objectives_numberobjectiveoutput
                group by master_id, year, month
                ) oo_sum
                on m.id = oo_sum.master_id
                and oo_sum.year = %s
                and oo_sum.month = %s
                where m.user_id = %s
                order by m.order_index
                ''' % (year, month, request.user.id)
            num_obj_rev = NumberObjectiveMaster.objects.raw(sql_str + sql_str2)

    return render(request, 'objectives/objrev_form.html', {
        'input_unit': key[1:2],
        'input_kind': key[2:],
        'free_input_obj': free_input_obj,
        'free_input_rev': free_input_rev,
        'target_period_str': target_period_str,
        'target_date_str': target_date_str,
        'num_obj_rev': num_obj_rev,
    })

def get_numobj_summary(input_unit, user, target_date):
    '''振り返り画面で表示する数値目標実績集計値を取得する
       週：週目標に対して週の集計値、日ごとの実績を取得
       月：数値目標マスタに対して月の集計値、曜日ごとの実績を取得
       年：数値目標マスタに対して年の集計値、月ごとの実績を取得
       形式：
       {
            sum_header: ["集計","1月","2月",...],
            num_obj_rev:[
                {"id":1,"name":"xxx","number_kind":"N","summary_kind":"S", ※週の場合のみ目標値取得
                    "sum_dic_list":[
                        {"header":"集計","val":123,"cnt":10}, ※cntは平均値算出用 
                        {"header":"1月","val":10,"cnt":3},
                        ...
                    ]
                }
            ]
       }
    '''
    sum_header = get_sum_header(input_unit, target_date)
    ret_dic = {}
    num_obj_rev_list = []
    ret_dic.update({
        "sum_header": sum_header,
        "num_obj_rev": num_obj_rev_list,
    })
    year, month, date_index, week_tuple = get_date(target_date)
    if input_unit == "W":
        # 最初に集計レコード作成
        # 数値目標ごとの集計値
        num_obj_rev_qry = NumberObjectiveMaster.objects.raw(
        '''
        select m.id, m.name, m.number_kind, m.summary_kind, o.objective_value, oo_sum.sumval, oo_sum.cnt
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

        where o.iso_year = %s
        and o.week_index = %s
        order by m.order_index
        ''' % (user.id, week_tuple[0], week_tuple[1],)
        )
        for nor in num_obj_rev_qry:
            num_obj_rev_list.append({
                "id": nor.id,
                "name": nor.name,
                "number_kind": nor.number_kind,
                "summary_kind": nor.summary_kind,
                "objective_value": nor.objective_value,
                # 集計値リスト：総集計のみlistにセットしておく
                "sum_dic_list": [{
                    "header": "集計",
                    "val": nor.sumval,
                    "cnt": nor.cnt,
                }]
            })
        
        # 日付ごとのレコード作成
        # 週の開始日、終了日取得
        start_date, end_date = get_week_start_and_end(target_date)
        work_date = start_date
        while work_date <= end_date:
            work_date_str = work_date.strftime("%Y-%m-%d")
            year, month, date_index, week_tuple = get_date(work_date_str)
            # 日付ごとの実績を取る
            num_obj_out = NumberObjectiveOutput.objects.filter(
                year=year,
                date_index=date_index,
                master__user=user,
            )
            if num_obj_out:
                for noo in num_obj_out:
                    for nor in num_obj_rev_list:
                        # 一致するマスタのレコードに対して対象日付のレコードを追加する
                        if nor["id"] == noo.master.id:
                            nor["sum_dic_list"].append({
                                "header": work_date.strftime("%m/%d"),
                                "val": noo.output_value,
                                "cnt": 1,
                            })
            work_date = work_date + timedelta(days=1)
    elif input_unit == "M":
        # 集計レコード
        num_obj_rev_qry = NumberObjectiveMaster.objects.raw(
        '''
        select m.id, m.name, m.number_kind, m.summary_kind, oo_sum.sumval, oo_sum.cnt
        from objectives_numberobjectivemaster m
        left outer join 
        (
        select master_id, year, month, sum(output_value) sumval, count(*) cnt
        from objectives_numberobjectiveoutput
        group by master_id, year, month
        ) oo_sum
        on m.id = oo_sum.master_id
        and oo_sum.year = %s
        and oo_sum.month = %s
        where m.user_id = %s
        order by m.order_index
        ''' % (year, month, user.id)
        )
        for nor in num_obj_rev_qry:
            num_obj_rev_list.append({
                "id": nor.id,
                "name": nor.name,
                "number_kind": nor.number_kind,
                "summary_kind": nor.summary_kind,
                # 集計値リスト：総集計のみlistにセットしておく
                "sum_dic_list": [{
                    "header": "集計",
                    "val": nor.sumval,
                    "cnt": nor.cnt,
                }]
            })
        
        # 曜日ごとのレコード作成　
        numofweek_dic = {1:"月",2:"火",3:"水",4:"木",5:"金",6:"土",7:"日"}
        # 曜日ごとの実績の集計をとる
        num_obj_out = NumberObjectiveOutput.objects.raw(
        '''
        select m.id, oo_sum.day_of_week, oo_sum.sumval, oo_sum.cnt
        from objectives_numberobjectivemaster m
        left outer join
        (
            select master_id, day_of_week, sum(output_value) sumval, count(*) cnt
            from objectives_numberobjectiveoutput
            where year = %s
            and   month = %s
            group by master_id, day_of_week
        ) oo_sum
        on m.id = oo_sum.master_id
        where m.user_id = %s
        and   oo_sum.cnt > 0
        order by m.order_index, oo_sum.day_of_week
        ''' % (year, month, user.id)
        )
        if num_obj_out:
            for noo in num_obj_out:
                for nor in num_obj_rev_list:
                    # 一致するマスタのレコードに対して対象曜日のレコードを追加する
                    if nor["id"] == noo.id:
                        nor["sum_dic_list"].append({
                            "header": numofweek_dic[noo.day_of_week],
                            "val": noo.sumval,
                            "cnt": noo.cnt,
                        })
    elif input_unit == "Y":
        pass
    print("ret_dic: " + str(ret_dic))
    return ret_dic

def get_sum_header(input_unit, target_date): 
    ''' 単位ごとに一覧表示のヘッダをリスト形式で返却する
        例:["集計","1月","2月",...] '''
    ret_list = ["集計"]
    if input_unit == "W":
        start_date, end_date = get_week_start_and_end(target_date)
        work_date = start_date
        while work_date <= end_date:
            ret_list.append(work_date.strftime("%m/%d"))
            work_date = work_date + timedelta(days=1)
    elif input_unit == "M":
        ret_list.extend(["月","火","水","木","金","土","日"])
    elif input_unit == "Y":
        work_month = 1
        while work_month <= 12:
            ret_list.append("%s月" % work_month)
            work_month = work_month + 1
    return ret_list

        


def get_free_input_year(year, input_kind, user):
    return FreeInput.objects.filter(
        input_unit = "Y",
        input_kind = input_kind,
        year = year,
        day_index = year,
        user = user,
    )

def get_free_input_month(year, month, input_kind, user):
    return FreeInput.objects.filter(
        input_unit = "M",
        input_kind = input_kind,
        year = year,
        day_index = month,
        user = user,
    )

def get_free_input_week(isoyear, week_index, input_kind, user):
    return FreeInput.objects.filter(
        input_unit = "W",
        input_kind = input_kind,
        year = isoyear,
        day_index = week_index,
        user = user,
    )

def get_free_input_date(year, date_index, input_kind, user):
    return FreeInput.objects.filter(
        input_unit = "D",
        input_kind = input_kind,
        year = year,
        day_index = date_index,
        user = user,
    )

def get_free_input(input_unit, input_kind, year, month, date_index, week_tuple, user):
    '''FreeInput取得のクエリを実行し結果を返却する'''
    ret_dic = {
        "Y": get_free_input_year(year, input_kind, user),
        "M": get_free_input_month(year, month, input_kind, user),
        "W": get_free_input_week(week_tuple[0], week_tuple[1], input_kind, user),
        "D": get_free_input_date(year, date_index, input_kind, user),
    }
    return ret_dic[input_unit]

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