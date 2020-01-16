import datetime
import locale
import os.path
import re
import sys
from copy import deepcopy
from io import BytesIO

import simplejson as json
from anytree import Node, RenderTree
from reportlab.lib import colors
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Indenter, Frame, KeepInFrame
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from appconf.manager import SettingManager
from directions.models import Issledovaniya, Napravleniya, ParaclinicResult
from directory.models import Fractions
from laboratory import utils
from laboratory.settings import FONTS_FOLDER
from utils import tree_directions
from . import forms_func
from api.stationar.stationar_func import hosp_get_hosp_direction, hosp_get_data_direction
from api.stationar.sql_func import get_result_value_iss
from api.sql_func import get_fraction_result
from utils.dates import normalize_date


def form_01(request_data):
    """
    Ведомость статталонов по амбулаторным приемам. Входные параметры врач, дата.
    Выходные: форма
    """

    doc_confirm = request_data['user'].doctorprofile
    req_date = request_data['date']
    str_date = json.loads(req_date)
    date_confirm = datetime.datetime.strptime(str_date, "%d.%m.%Y")
    doc_results = forms_func.get_doc_results(doc_confirm, date_confirm)
    data_talon = forms_func.get_finaldata_talon(doc_results)

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=12 * mm,
                            rightMargin=5 * mm, topMargin=25 * mm,
                            bottomMargin=28 * mm, allowSplitting=1,
                            title="Форма {}".format("Ведомость по статталонам"))

    styleSheet = getSampleStyleSheet()
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 9
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.fontSize = 11
    styleBold.alignment = TA_LEFT
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 9
    styleCenter.leading = 10
    styleCenter.spaceAfter = 0 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 14
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []
    objs.append(Spacer(1, 1 * mm))

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.firstLineIndent = 0
    styleT.fontSize = 9
    param = request_data.get('param', '0') == '1'

    if param:
        title = 'Ведомость статистических талонов по услугам пациентов'
        opinion = [
            [Paragraph('№ п.п.', styleT), Paragraph('ФИО пациента, дата рождени', styleT),
             Paragraph('Дата осмотра, &nbsp №', styleT),
             Paragraph('№ карты', styleT), Paragraph('Данные полиса', styleT),
             Paragraph('Код услуги', styleT),
             Paragraph('Наименование услуги', styleT), ]
        ]
    else:
        title = 'Ведомость статистических талонов по посещениям пациентов'
        opinion = [
            [Paragraph('№ п.п.', styleT), Paragraph('ФИО пациента, дата рождения ', styleT), Paragraph('Дата осмотра, &nbsp №', styleT),
             Paragraph('№ карты', styleT), Paragraph('Данные полиса', styleT), Paragraph('Цель посещения (код)', styleT),
             Paragraph('Первичный прием', styleT), Paragraph('Диагноз МКБ', styleT), Paragraph('Впервые', styleT),
             Paragraph('Результат обращения (код)', styleT), Paragraph('Исход (код)', styleT),
             Paragraph('Д-учет<br/>Стоит', styleT),
             Paragraph('Д-учет<br/>Взят', styleT), Paragraph('Д-учет<br/>Снят', styleT),
             Paragraph('Причина снятия', styleT),
             Paragraph('Онко<br/> подозрение', styleT), ]
        ]

    new_page = False
    list_g = []

    if param:
        talon = data_talon[1]
    else:
        talon = data_talon[0]

    for k, v in talon.items():
        if len(talon.get(k)) == 0:
            continue
        if new_page:
            objs.append(PageBreak())
        objs.append(Paragraph('Источник финансирования - {}'.format(str(k).upper()), styleBold))
        objs.append(Spacer(1, 1.5 * mm))
        t_opinion = opinion.copy()
        for u, s in v.items():
            list_t = [Paragraph(str(u), styleT)]
            for t, q in s.items():
                list_t.append(Paragraph(str(q).replace("\n", "<br/>"), styleT))
            list_g.append(list_t)
        t_opinion.extend(list_g)

        if param:
            tbl = Table(t_opinion,
                        colWidths=(10 * mm, 60 * mm, 19 * mm, 15 * mm, 75 * mm, 30 * mm, 70 * mm,))
        else:
            tbl = Table(t_opinion,
                        colWidths=(10 * mm, 30 * mm, 19 * mm, 15 * mm, 46 * mm, 20 * mm, 10 * mm, 13 * mm, 11 * mm,
                                   20 * mm, 20 * mm, 14 * mm, 14 * mm, 14 * mm, 17 * mm, 13 * mm))

        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))

        objs.append(tbl)
        new_page = True
        list_g = []

    styleTatr = deepcopy(style)
    styleTatr.alignment = TA_LEFT
    styleTatr.firstLineIndent = 0
    styleTatr.fontSize = 11

    opinion = [
        [Paragraph('ФИО врача:', styleTatr), Paragraph('{}'.format(doc_confirm.fio), styleTatr),
         Paragraph('{}'.format(date_confirm.strftime('%d.%m.%Y')), styleTatr)],
        [Paragraph('Специальность:', styleTatr), Paragraph('{}'.format(doc_confirm.specialities), styleTatr),
         Paragraph('', styleTatr)],
    ]

    def later_pages(canvas, document):
        canvas.saveState()
        # вывести Название и данные врача
        width, height = landscape(A4)
        canvas.setFont('PTAstraSerifBold', 14)
        canvas.drawString(99 * mm, 200 * mm, '{}'.format(title))

        tbl = Table(opinion, colWidths=(35 * mm, 220 * mm, 25 * mm), rowHeights=(5 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        tbl.wrapOn(canvas, width, height)
        tbl.drawOn(canvas, 30, 530)
        canvas.restoreState()

    doc.build(objs, onFirstPage=later_pages, onLaterPages=later_pages, )

    pdf = buffer.getvalue()

    buffer.close()
    return pdf


################################################################################################################
def form_02(request_data):
    """
    Отдельный статталон по отдельному амбулаторному приему.
    Краткая форма - результата проткола. Учитываются те поля, к-рые имеют признак "для статталона"
    -------------------------------
    Вход: Направление.
    Выходные: форма

    в файле .....\Lib\site-packages\anytree\render.py
        class ContStyle(AbstractStyle):
        необходимое мотод super сделать так:(изменить символы)
                super(ContStyle, self).__init__(u'\u2063   ',
                                        u'\u2063   ',
                                        u'\u2063   ')
    """

    # получить направления
    ind_dir = json.loads(request_data["napr_id"])

    hospital_name = SettingManager.get("org_title")
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=18 * mm,
                            rightMargin=5 * mm, topMargin=6 * mm,
                            bottomMargin=6 * mm, allowSplitting=1,
                            title="Форма {}".format("Статталон пациента"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10
    style.leading = 12
    style.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 10
    styleCenter.spaceAfter = 1 * mm

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'
    styleCenterBold.borderColor = black

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    for dir in ind_dir:
        obj_dir = Napravleniya.objects.get(pk=dir)
        ind_card = obj_dir.client
        patient_data = ind_card.get_data_individual()

        if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
            patient_data['serial'] = patient_data['bc_serial']
            patient_data['num'] = patient_data['bc_num']
        else:
            patient_data['serial'] = patient_data['passport_serial']
            patient_data['num'] = patient_data['passport_num']

        card_num_obj = patient_data['card_num'].split(' ')
        p_card_num = card_num_obj[0]
        if len(card_num_obj) == 2:
            p_card_type = '(' + str(card_num_obj[1]) + ')'
        else:
            p_card_type = ''

        space_symbol = '&nbsp;'

        # Добавить сведения о пациента
        content_title = [
            Indenter(left=0 * mm),
            Spacer(1, 1 * mm),
            Paragraph('{}'.format(hospital_name), styleCenterBold),
            Spacer(1, 2 * mm),
            Paragraph('<u>Статистический талон пациента</u>', styleCenter),
            Paragraph('{}<font size=10>Карта № </font><font fontname="PTAstraSerifBold" size=10>{}</font><font size=10> из {}</font>'.format(
                3 * space_symbol, p_card_num, p_card_type), styleCenter),
            Spacer(1, 2 * mm),
            Paragraph('<font size=11>Данные пациента:</font>', styleBold),
            Paragraph("1. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(
                patient_data['fio']), style),
            Paragraph(
                '2. Пол: {} {} 3. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']),
                style),
            Paragraph('4. Место регистрации: {}'.format(patient_data['main_address']), style),
            Paragraph('5. Полис ОМС: серия {} №: {} {}'
                      '6. СНИЛС: {}'.format(patient_data['oms']['polis_serial'], patient_data['oms']['polis_num'],
                                            13 * space_symbol, patient_data['snils']), style),
            Paragraph('7. Наименование страховой медицинской организации: {}'.format(patient_data['oms']['polis_issued']),
                      style),
        ]

        objs.extend(content_title)

        # добавить данные об услуге
        objs.append(Spacer(1, 3 * mm))
        objs.append(Paragraph('<font size=11>Данные об услуге:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))

        obj_iss = Issledovaniya.objects.filter(napravleniye=obj_dir, parent_id=None).first()
        date_proto = utils.strfdatetime(obj_iss.time_confirmation, "%d.%m.%Y")

        opinion = [
            [Paragraph('Основная услуга', styleT), Paragraph(
                '<font fontname="PTAstraSerifBold">{}</font> <font face="Symbola">\u2013</font> {}'.format(
                    obj_iss.research.code, obj_iss.research.title), styleT)],
            [Paragraph('Направление №', styleT), Paragraph('{}'.format(dir), styleT)],
            [Paragraph('Дата протокола', styleT), Paragraph('{}'.format(date_proto), styleT)],
        ]

        # Найти и добавить поля у к-рых флаг "for_talon". Отсортировано по 'order' (группа, поле)
        field_iss = ParaclinicResult.objects.filter(issledovaniye=obj_iss, field__for_talon=True, ).order_by(
            'field__group__order', 'field__order')

        for f in field_iss:
            v = f.value.replace("\n", "<br/>")
            if f.field.field_type == 1:
                vv = v.split('-')
                if len(vv) == 3:
                    v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
            list_f = [[Paragraph(f.field.get_title(), styleT), Paragraph(v, styleT)]]
            opinion.extend(list_f)

        tbl = Table(opinion, colWidths=(60 * mm, 123 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))

        objs.append(tbl)

        # Заключительные положения
        objs.append(Spacer(1, 4 * mm))
        objs.append(Paragraph('<font size=11>Заключительные положения:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))
        empty = '-'
        purpose = empty if not obj_iss.purpose else obj_iss.purpose
        outcome_illness = empty if not obj_iss.outcome_illness else obj_iss.outcome_illness
        result_reception = empty if not obj_iss.result_reception else obj_iss.result_reception
        diagnos = empty if not obj_iss.diagnos else obj_iss.diagnos

        opinion = [
            [Paragraph('Цель посещения', styleT), Paragraph('{}'.format(purpose), styleT)],
            [Paragraph('Исход заболевания', styleT), Paragraph('{}'.format(outcome_illness), styleT)],
            [Paragraph('Результат обращения', styleT), Paragraph('{}'.format(result_reception), styleT)],
            [Paragraph('Основной диагноз', styleT), Paragraph('{}'.format(diagnos), styleT)],
        ]

        tbl = Table(opinion, colWidths=(60 * mm, 123 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        objs.append(tbl)

        # Добавить Дополнительные услуги
        add_research = Issledovaniya.objects.filter(parent_id__napravleniye=obj_dir)
        if add_research:
            objs.append(Spacer(1, 3 * mm))
            objs.append(Paragraph('<font size=11>Дополнительные услуги:</font>', styleBold))
            objs.append(Spacer(1, 1 * mm))
            for i in add_research:
                objs.append(Paragraph('{} <font face="Symbola">\u2013</font> {}'.format(i.research.code, i.research.title), style))

        objs.append(Spacer(1, 5 * mm))
        objs.append(
            HRFlowable(width=185 * mm, thickness=0.7 * mm, spaceAfter=1.3 * mm, spaceBefore=0.5 * mm, color=colors.black, hAlign=TA_LEFT))
        objs.append(Paragraph('<font size=11>Лечащий врач:</font>', styleBold))
        objs.append(Spacer(1, 1 * mm))

        personal_code = ''
        doc_fio = ''
        if obj_iss.doc_confirmation:
            personal_code = empty if not obj_iss.doc_confirmation.personal_code else obj_iss.doc_confirmation.personal_code
            doc_fio = obj_iss.doc_confirmation.get_fio()

        objs.append(Paragraph('{} /_____________________/ {} Код врача: {} '.format(doc_fio,
                                                                                    42 * space_symbol, personal_code), style))

        objs.append(Spacer(1, 5 * mm))

        # Получить структуру Направлений если, направление в Дереве не важно в корне в середине или в начале
        root_dir = tree_directions.root_direction(dir)
        num_iss = (root_dir[-1][-2])
        tree_dir = tree_directions.tree_direction(num_iss)
        final_tree = {}
        pattern = re.compile('<font face=\"Symbola\" size=10>\u2713</font>')

        node_dir = Node("Структура направлений")
        for j in tree_dir:
            if len(j[9]) > 47:
                research = j[9][:47] + '...'
            else:
                research = j[9]
            diagnos = '  --' + j[-2] if j[-2] else ""
            temp_s = f"{j[0]} - {research}. Создано {j[1]} в {j[2]} {diagnos}"
            if dir == j[0]:
                temp_s = f"{temp_s} -- <font face=\"Symbola\" size=10>\u2713</font>"
            if not j[3]:
                final_tree[j[5]] = Node(temp_s, parent=node_dir)
            else:
                final_tree[j[5]] = Node(temp_s, parent=final_tree.get(j[3]))

        counter = 0
        opinion = []
        for row in RenderTree(node_dir):
            counter += 1
            result = pattern.search(row.node.name)
            current_style = styleBold if result else styleT
            count_space = len(row.pre) // 2 * 2
            para = [Paragraph('{}{}'.format(space_symbol * count_space, row.node.name), current_style)]
            opinion.append(para)

        tbl = Table(opinion, colWidths=(190 * mm))
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        objs.append(tbl)

        objs.append(PageBreak())

    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


##########################################################################################################################

def form_03(request_data):
    """
    Статистическая форма 066/у Приложение № 5 к приказу Минздрава России от 30 декабря 2002 г. № 413
    """
    num_dir = request_data["dir_pk"]
    direction_obj = Napravleniya.objects.get(pk=num_dir)
    hosp_nums_obj = hosp_get_hosp_direction(num_dir)
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=25 * mm,
                            rightMargin=5 * mm, topMargin=6 * mm,
                            bottomMargin=4 * mm, allowSplitting=1,
                            title="Форма {}".format("003/у"))
    width, height = portrait(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
    styleCenter.spaceAfter = 1 * mm
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'
    styleCenterBold.borderColor = black
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    print_district = ''
    if SettingManager.get("district", default='True', default_type='b'):
        if ind_card.district is not None:
            print_district = 'Уч: {}'.format(ind_card.district.title)

    opinion = [
        [Paragraph('<font size=11>{}<br/>Адрес: {}<br/>ОГРН: {} <br/><u>{}</u> </font>'.format(
            hospital_name, hospital_address, hospital_kod_ogrn, print_district), styleT),
            Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: 31348613<br/>'
                      'Медицинская документация<br/>форма № 003/у</font>', styleT)],
    ]

    tbl = Table(opinion, 2 * [90 * mm])
    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
        ('LEFTPADDING', (1, 0), (-1, -1), 80),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    objs.append(tbl)
    space_symbol = '&nbsp;'
    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    p_phone = ''
    if patient_data['phone']:
        p_phone = 'тел. ' + ", ".join(patient_data['phone'])

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]

    # взять самое последнее направленеие из hosp_dirs
    hosp_last_num = hosp_nums_obj[-1].get('direction')
    ############################################################################################################
    # Получение данных из выписки
    # Взять услугу типа выписка. Из полей "Дата выписки" - взять дату. Из поля "Время выписки" взять время
    hosp_extract = hosp_get_data_direction(hosp_last_num, site_type=7, type_service='None', level=2)
    hosp_extract_iss, extract_research_id = None, None
    if hosp_extract:
        hosp_extract_iss = hosp_extract[0].get('iss')
        extract_research_id = hosp_extract[0].get('research_id')
    titles_field = ['Время выписки', 'Дата выписки', 'Основной диагноз (описание)',
                    'Осложнение основного диагноза (описание)', 'Сопутствующий диагноз (описание)'
                    ]
    list_values = None
    if titles_field and hosp_extract:
        list_values = get_result_value_iss(hosp_extract_iss, extract_research_id, titles_field)
    date_value, time_value = '', ''
    final_diagnos, other_diagnos, near_diagnos = '', '', ''

    if list_values:
        for i in list_values:
            if i[3] == 'Дата выписки':
                date_value = i[2]
            if i[3] == 'Время выписки':
                time_value = i[2]
            if i[3] == 'Основной диагноз (описание)':
                final_diagnos = i[2]
            if i[3] == 'Осложнение основного диагноза (описание)':
                other_diagnos = i[2]
            if i[3] == 'Сопутствующий диагноз (описание)':
                near_diagnos = i[2]

        if date_value:
            vv = date_value.split('-')
            if len(vv) == 3:
                date_value = "{}.{}.{}".format(vv[2], vv[1], vv[0])

    # Получить отделение - из названия услуги изи самого главного направления
    hosp_depart = hosp_nums_obj[0].get('research_title')

    ############################################################################################################
    # Получить данные из первичного приема (самого первого hosp-направления)
    hosp_first_num = hosp_nums_obj[0].get('direction')
    hosp_primary_receptions = hosp_get_data_direction(hosp_first_num, site_type=0, type_service='None', level=2)
    hosp_primary_iss, primary_research_id = None, None
    if hosp_primary_receptions:
        hosp_primary_iss = hosp_primary_receptions[0].get('iss')
        primary_research_id = hosp_primary_receptions[0].get('research_id')

    titles_field = ['Дата поступления', 'Время поступления', 'Виды транспортировки',
                    'Побочное действие лекарств (непереносимость)', 'Кем направлен больной',
                    'Вид госпитализации',
                    'Время через, которое доставлен после начала заболевания, получения травмы',
                    'Диагноз направившего учреждения', 'Диагноз при поступлении']
    if titles_field and hosp_primary_receptions:
        list_values = get_result_value_iss(hosp_primary_iss, primary_research_id, titles_field)

    date_entered_value, time_entered_value, type_transport, medicament_allergy = '', '', '', ''
    who_directed, plan_hospital, extra_hospital, type_hospital = '', '', '', ''
    time_start_ill, diagnos_who_directed, diagnos_entered = '', '', ''

    if list_values:
        for i in list_values:
            if i[3] == 'Дата поступления':
                date_entered_value = i[2]
                continue
            if i[3] == 'Время поступления':
                time_entered_value = i[2]
                continue
            if i[3] == 'Виды транспортировки':
                type_transport = i[2]
                continue
            if i[3] == 'Побочное действие лекарств (непереносимость)':
                medicament_allergy = i[2]
                continue
            if i[3] == 'Кем направлен больной':
                who_directed = i[2]
                continue
            if i[3] == 'Вид госпитализации':
                type_hospital = i[2]
            if type_hospital == 'Экстренная':
                time_start_ill_obj = get_result_value_iss(hosp_primary_iss, primary_research_id, ['Время через, которое доставлен после начала заболевания, получения травмы'])
                if time_start_ill_obj:
                    time_start_ill = time_start_ill_obj[0][2]
                extra_hospital = "Да"
                plan_hospital = "Нет"
            else:
                plan_hospital = "Да"
                extra_hospital = "Нет"
                time_start_ill = ''
            if i[3] == 'Диагноз направившего учреждения':
                diagnos_who_directed = i[2]
                continue
            if i[3] == 'Диагноз при поступлении':
                diagnos_entered = i[2]
                continue

        if date_entered_value:
            vv = date_entered_value.split('-')
            if len(vv) == 3:
                date_entered_value = "{}.{}.{}".format(vv[2], vv[1], vv[0])

    ###########################################################################################################

    fcaction_avo_id = Fractions.objects.filter(title='Групповая принадлежность крови по системе АВО').first()
    fcaction_rezus_id = Fractions.objects.filter(title='Резус').first()
    group_blood_avo = get_fraction_result(ind_card.pk, fcaction_avo_id.pk, count=1)
    group_blood_avo_value = ''
    if group_blood_avo:
        group_blood_avo_value = group_blood_avo[0][5]
    group_blood_rezus = get_fraction_result(ind_card.pk, fcaction_rezus_id.pk, count=1)
    group_rezus_value = ''
    if group_blood_rezus:
        group_rezus_value = group_blood_rezus[0][5].replace('<br/>', ' ')
    ###########################################################################################################
    # получение данных клинического диагноза
    hosp_day_entries = hosp_get_data_direction(hosp_first_num, site_type=1, type_service='None', level=-1)
    day_entries_iss = []
    day_entries_research_id = None
    if hosp_day_entries:
        for i in hosp_day_entries:
            # найти дневники совместно с заведующим
            if i.get('research_title').find('заведующ') != -1:
                day_entries_iss.append(i.get('iss'))
                if not day_entries_research_id:
                    day_entries_research_id = i.get('research_id')

    titles_field = ['Диагноз клинический', 'Дата установления диагноза']
    list_values = []
    if titles_field and day_entries_iss:
        for i in day_entries_iss:
            list_values.append(get_result_value_iss(i, day_entries_research_id, titles_field))
    s = ''
    if list_values:
        for i in list_values:
            if (i[1][3]).find('Дата установления диагноза') != -1:
                date_diag = i[1][2]
                if date_diag:
                    vv = date_diag.split('-')
                    if len(vv) == 3:
                        date_diag = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                        s = s + i[0][2] + '; дата:' + date_diag + '<br/>'
            elif (i[0][3]).find('Дата установления диагноза') != -1:
                date_diag = i[0][2]
                if date_diag:
                    vv = date_diag.split('-')
                    if len(vv) == 3:
                        date_diag = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                        s = s + i[1][2] + '; дата:' + str(date_diag) + '<br/>'

    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 8 * mm),
        Paragraph(
            '<font fontname="PTAstraSerifBold" size=13>СТАТИСТИЧЕСКАЯ КАРТА ВЫБЫВШЕГО ИЗ СТАЦИОНАРА<br/> '
            'круглосуточного пребывания, дневного стационара при больничном<br/> учреждении, дневного стационара при'
            ' амбулаторно-поликлиническом<br/> учреждении, стационара на дому</font>'.format(
                p_card_num, hosp_nums), styleCenter),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),
        Spacer(1, 2 * mm),

        Paragraph('Дата и время поступления: {} - {}'.format(date_entered_value, time_entered_value), style),
        Spacer(1, 2 * mm),

        Paragraph('Дата и время выписки: {} - {}'.format(date_value, time_value), style),
        Spacer(1, 2 * mm),
        Paragraph('Отделение: {}'.format(hosp_depart), style),
        Spacer(1, 2 * mm),
        Paragraph('Палата №: {}'.format('_________________________'), style),
        Spacer(1, 2 * mm),
        Paragraph('Переведен в отделение: {}'.format('______________'), style),
        Spacer(1, 2 * mm),
        Paragraph('Проведено койко-дней: {}'.format('______________________________________________'), style),
        Spacer(1, 2 * mm),
        Paragraph('Виды транспортировки(на каталке, на кресле, может идти): {}'.format(type_transport), style),
        Spacer(1, 2 * mm),
        Paragraph('Группа крови: {}. Резус-принадлежность: {}'.format(group_blood_avo_value, group_rezus_value), style),
        Spacer(1, 2 * mm),
        Paragraph('Побочное действие лекарств(непереносимость):', style),
        Spacer(1, 12 * mm),
        Paragraph("1. Фамилия, имя, отчество:&nbsp;  <font size=11.7 fontname ='PTAstraSerifBold'> {} </font> ".format(patient_data['fio']), style),
        Spacer(1, 2 * mm),
        Paragraph(
            '2. Пол: {} {} 3. Дата рождения: {}'.format(patient_data['sex'], 3 * space_symbol, patient_data['born']),
            style),
        Spacer(1, 2 * mm),
        Paragraph('4. Постоянное место жительства: город, село: {}'.format(patient_data['main_address']), style),
        Paragraph('{}'.format(p_phone), style),
        Spacer(1, 2 * mm),
        Paragraph('5. Место работы, профессия или должность', style),
        Spacer(1, 2 * mm),
        Paragraph('6. Кем направлен больной: {}'.format(who_directed), style),
        Spacer(1, 2 * mm),
        Paragraph('7. Доставлен в стационар по экстренным показаниям: {}'.format(extra_hospital), style),
        Spacer(1, 1 * mm),
        Paragraph(' через: {} часов после начала заболевания, получения травмы; '.format(time_start_ill), style),
        Spacer(1, 1 * mm),
        Paragraph(' госпитализирован в плановом порядке (подчеркнуть) {}.'.format(plan_hospital), style),
        Spacer(1, 3 * mm),
        Paragraph('8. Диагноз направившего учреждения:', style),
        Spacer(1, 8 * mm),
        Paragraph('9. Диагноз при поступлении:', style),
        Spacer(1, 10 * mm),
        Paragraph('10. Диагноз клинический:', style),
        PageBreak()]

    second_page = [
        Spacer(1, 2 * mm),
        Paragraph('11. Диагноз заключительный клинический:', style),
        Spacer(1, 0.5 * mm),
        Paragraph('а) основной:', style),
        Spacer(1, 45 * mm),
        Paragraph('б) осложнение основного:', style),
        Spacer(1, 18 * mm),
        Paragraph('в) сопутствующий:', style),
        Spacer(1, 19 * mm),
        Paragraph('12. Госпитализирован в данном году по поводу данного заболевания: впервые, повторно (подчеркнуть),'
                  'всего  - ___раз.:{}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('13. Хирургические операции, методы обезболивания и послеоперационные осложнения:', style),
        Spacer(1, 40 * mm),
        Paragraph('14. Другие виды лечения:___________________________________________'.format('Из '), style),
        Spacer(1, 0.2 * mm),
        Paragraph('для больных злокачественными новообразованиями.', style),
        Spacer(1, 0.2 * mm),
        Paragraph(' 1.Специальное лечение: хирургическое(дистанционная гамматерапия, рентгенотерапия, быстрые '
                  'электроны, контактная и дистанционная гамматерапия, контактная гамматерапия и глубокая '
                  'рентгенотерапия); комбинированное(хирургическое и гамматерапия, хирургическое и рентгено - '
                  'терапия, хирургическое и сочетанное лучевое); химиопрепаратами, гормональными препаратами.', style),
        Spacer(1, 1 * mm),
        Paragraph('2. Паллиативное', style),
        Spacer(1, 0.2 * mm),
        Paragraph('3. Симптоматическое лечение.', style),
        Spacer(1, 0.2 * mm),
        Paragraph('15. Отметка о выдаче листка нетрудоспособности: {}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('16. Исход заболевания: {}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('17.  Трудоспособность восстановлена полностью, снижена, временно утрачена, стойко утрачена в связи '
                  'с данным заболеванием, с другими причинами(подчеркнуть): {}'.format(''), style),
        Spacer(1, 1 * mm),
        Paragraph('18. Для поступивших на экспертизу - заключение:___________________', style),
        Spacer(1, 1 * mm),
        Paragraph('___________________________________________________________________', style),
        Spacer(1, 1 * mm),
        Paragraph('19. Особые отметки', style)
    ]

    objs.extend(title_page)
    objs.extend(second_page)

    def first_pages(canvas, document):
        canvas.saveState()
        # Побочное действие лекарств(непереносимость) координаты
        medicament_text = [Paragraph('{}'.format(medicament_allergy), styleJustified)]
        medicament_frame = Frame(27 * mm, 163 * mm, 175 * mm, 12 * mm, leftPadding=0, bottomPadding=0,
                                 rightPadding=0, topPadding=0, showBoundary=0)
        medicament_inframe = KeepInFrame(175 * mm, 12 * mm, medicament_text, hAlign='LEFT', vAlign='TOP', )
        medicament_frame.addFromList([medicament_inframe], canvas)

        # Диагноз направившего учреждения координаты
        diagnos_directed_text = [Paragraph('{}'.format(diagnos_who_directed), styleJustified)]
        diagnos_directed_frame = Frame(27 * mm, 81 * mm, 175 * mm, 10 * mm, leftPadding=0, bottomPadding=0,
                                       rightPadding=0, topPadding=0, showBoundary=0)
        diagnos_directed_inframe = KeepInFrame(175 * mm, 10 * mm, diagnos_directed_text, hAlign='LEFT', vAlign='TOP', )
        diagnos_directed_frame.addFromList([diagnos_directed_inframe], canvas)

        # Диагноз при поступлении координаты
        diagnos_entered_text = [Paragraph('{}'.format(diagnos_entered), styleJustified)]
        diagnos_entered_frame = Frame(27 * mm, 67 * mm, 175 * mm, 10 * mm, leftPadding=0, bottomPadding=0,
                                      rightPadding=0, topPadding=0, showBoundary=0)
        diagnos_entered_inframe = KeepInFrame(175 * mm, 10 * mm, diagnos_entered_text, hAlign='LEFT',
                                              vAlign='TOP', )
        diagnos_entered_frame.addFromList([diagnos_entered_inframe], canvas)

        # клинический диагноз координаты
        diagnos_text = [Paragraph('{}'.format(s * 1), styleJustified)]
        diagnos_frame = Frame(27 * mm, 5 * mm, 175 * mm, 55 * mm, leftPadding=0, bottomPadding=0,
                              rightPadding=0, topPadding=0, showBoundary=0)
        diagnos_inframe = KeepInFrame(175 * mm, 55 * mm, diagnos_text)
        diagnos_frame.addFromList([diagnos_inframe], canvas)
        canvas.restoreState()

    # Получить все услуги из категории операции
    styleTO = deepcopy(style)
    styleTO.alignment = TA_LEFT
    styleTO.firstLineIndent = 0
    styleTO.fontSize = 9.5
    styleTO.leading = 10
    styleTO.spaceAfter = 0.2 * mm

    # Таблица для операции
    opinion_oper = [
        [Paragraph('№', styleTO),
         Paragraph('Название операции', styleTO),
         Paragraph('Дата, &nbsp час', styleTO),
         Paragraph('Метод обезболивания', styleTO),
         Paragraph('Осложнения', styleTO),
         Paragraph('Оперировал', styleTO),
         ]
    ]

    hosp_operation = hosp_get_data_direction(num_dir, site_type=3, type_service='None', level=-1)
    operation_iss = []
    operation_research_id = None
    if hosp_operation:
        for i in hosp_operation:
            # найти протоколы по типу операции
            if i.get('research_title').lower().find('операци') != -1:
                operation_iss.append(i.get('iss'))
                if not operation_research_id:
                    operation_research_id = i.get('research_id')

    titles_field = ['Название операции', 'Дата проведения',
                    'Время начала', 'Время окончания', 'Метод обезболивания', 'Осложнения']
    list_values = []
    if titles_field and operation_research_id and hosp_operation:
        for i in operation_iss:
            list_values.append(get_result_value_iss(i, operation_research_id, titles_field))

        operation_result = []
        x = 0
        operation_template = [''] * len(titles_field)
        for fields_operation in list_values:
            date_time = {}
            date_time['date'], date_time['time_start'], date_time['time_end'] = '', '', ''
            field = None
            iss_obj = Issledovaniya.objects.filter(pk=fields_operation[0][1]).first()
            if not iss_obj.doc_confirmation:
                continue
            x += 1
            for field in fields_operation:
                if field[3] == 'Название операции':
                    operation_template[1] = Paragraph(field[2], styleTO)
                    continue
                if field[3] == 'Дата проведения':
                    date_time['date'] = normalize_date(field[2])
                    continue
                if field[3] == 'Время начала':
                    date_time['time_start'] = field[2]
                    continue
                if field[3] == 'Время окончания':
                    date_time['time_end'] = field[2]
                    continue
                if field[3] == 'Метод обезболивания':
                    operation_template[3] = Paragraph(field[2], styleTO)
                    continue
                if field[3] == 'Осложнения':
                    operation_template[4] = Paragraph(field[2], styleTO)
                    continue
            operation_template[0] = Paragraph(str(x), styleTO)
            operation_template[2] = Paragraph(date_time.get('date') + '<br/>' + date_time.get('time_start') + '-' +
                                              date_time.get('time_end'), styleTO)
            doc_fio = iss_obj.doc_confirmation.get_fio()
            operation_template[5] = Paragraph(doc_fio, styleTO)
            operation_result.append(operation_template.copy())
        opinion_oper.extend(operation_result)

    t_opinion_oper = opinion_oper.copy()
    tbl_o = Table(t_opinion_oper,
                  colWidths=(7 * mm, 62 * mm, 25 * mm, 30 * mm, 15 * mm, 45 * mm,))
    tbl_o.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.1 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    def later_pages(canvas, document):
        canvas.saveState()
        # Заключительные диагнозы
        # Основной заключительный диагноз
        final_diagnos_text = [Paragraph('{}'.format(final_diagnos), styleJustified)]
        final_diagnos_frame = Frame(27 * mm, 230 * mm, 175 * mm, 45 * mm, leftPadding=0, bottomPadding=0,
                                    rightPadding=0, topPadding=0, showBoundary=0)
        final_diagnos_inframe = KeepInFrame(175 * mm, 50 * mm, final_diagnos_text, hAlign='LEFT', vAlign='TOP', )
        final_diagnos_frame.addFromList([final_diagnos_inframe], canvas)

        # Осложнения основного заключительного диагноза
        other_diagnos_text = [Paragraph('{}'.format(other_diagnos), styleJustified)]
        other_diagnos_frame = Frame(27 * mm, 205 * mm, 175 * mm, 20 * mm, leftPadding=0, bottomPadding=0,
                                    rightPadding=0, topPadding=0, showBoundary=0)
        other_diagnos_inframe = KeepInFrame(175 * mm, 20 * mm, other_diagnos_text, hAlign='LEFT', vAlign='TOP', )
        other_diagnos_frame.addFromList([other_diagnos_inframe], canvas)

        # Сопутствующие основного заключительного диагноза
        near_diagnos_text = [Paragraph('{}'.format(near_diagnos), styleJustified)]
        near_diagnos_frame = Frame(27 * mm, 181 * mm, 175 * mm, 20 * mm, leftPadding=0, bottomPadding=0,
                                   rightPadding=0, topPadding=0, showBoundary=0)
        near_diagnos_inframe = KeepInFrame(175 * mm, 20 * mm, near_diagnos_text, vAlign='TOP')
        near_diagnos_frame.addFromList([near_diagnos_inframe], canvas)

        # Таблица операции
        operation_text = [tbl_o]
        operation_frame = Frame(27 * mm, 123 * mm, 175 * mm, 40 * mm, leftPadding=0, bottomPadding=0,
                                rightPadding=0, topPadding=0, showBoundary=0)
        operation_inframe = KeepInFrame(175 * mm, 40 * mm, operation_text, hAlign='CENTRE', vAlign='TOP', fakeWidth=False)
        operation_frame.addFromList([operation_inframe], canvas)
        canvas.restoreState()

    doc.build(objs, onFirstPage=first_pages, onLaterPages=later_pages)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
