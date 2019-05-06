from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

# 数値種別
NUMBER_KIND_CHOICES = [
    ('N', '数値'),
    ('P', '時間'),
    ('T', '時刻'),
]

# 集計種別
SUMMARY_KIND = [
    ('S', '合計'),
    ('A', '平均'),
]

class User(AbstractUser):
    '''カスタムユーザー
    '''
    pass

class FreeInput(models.Model):
    '''自由入力：年・月・週・日の目標、振り返りの入力内容
    ・入力単位：Y/M/W/D
    ・入力種別：O(Objective)/R(Review)
    ・年：何年の記録か
    ・日番号：年・月・週・日の番号を入れる(週番号はisocalendar)
    ・フリーワード
    ・入力状況：入力済(1)/スキップ(2)…未入力はレコード無しで表現
    '''
    input_unit = models.CharField(
        max_length=1,
    )
    input_kind = models.CharField(
        max_length=1,
    )
    year = models.PositiveSmallIntegerField()
    day_index = models.PositiveSmallIntegerField()
    free_word = models.TextField(
        blank=True,
        null=True,
    )
    input_status = models.CharField(
        max_length=1,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

class NumberObjectiveMaster(models.Model):
    '''数値目標マスタ：数値目標のマスタ
    ・名称
    ・数値種別：数値(N:Number)、時間(P:Period)、時刻(T:Time)
    ・集計種別：合計(S)、平均(A)
    ・有効フラグ：最新で有効なもの：1、無効なもの：0
    ・ユーザーID
    '''
    name = models.CharField(
        max_length=100,
        verbose_name='名称'
    )
    number_kind = models.CharField(
        max_length=1,
        choices=NUMBER_KIND_CHOICES,
        verbose_name='数値種別',
    )
    summary_kind = models.CharField(
        max_length=1,
        choices=SUMMARY_KIND,
        verbose_name='集計種別',
    )
    valid_flag = models.CharField(
        max_length=1,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

class NumberObjective(models.Model):
    '''数値目標：週単位での数値目標の値を設定
    ・数値目標マスタID
    ・年
    ・週番号
    ・目標値：時間の場合は分単位で記録、時刻の場合は00:00基準で分を記録
    '''
    master_id = models.ForeignKey(
        NumberObjectiveMaster,
        on_delete=models.CASCADE,
    )
    year = models.PositiveSmallIntegerField()
    week_index = models.PositiveSmallIntegerField()
    objective_value = models.PositiveSmallIntegerField()

class NumberObjectiveOutput(models.Model):
    '''数値目標実績：日毎の数値目標実績を登録
    ・数値目標マスタID
    ・年
    ・週番号
    ・日付番号：日付の番号
    ・実績値：時間の場合は分単位で記録、時刻の場合は00:00基準で分を記録
    '''
    master_id = models.ForeignKey(
        NumberObjectiveMaster,
        on_delete=models.CASCADE,
    )
    year = models.PositiveSmallIntegerField()
    week_index = models.PositiveSmallIntegerField()
    date_index = models.PositiveSmallIntegerField()
    output_value = models.PositiveSmallIntegerField()
