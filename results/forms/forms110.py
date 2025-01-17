import datetime
from hospitals.models import Hospitals
from reportlab.platypus import Paragraph, Spacer, Table, FrameBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import black
from results.forms.flowable import FrameDataCol
from results.prepare_data import fields_result_only_title_fields
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None):
    """
    Карта обратившегося за антирабической помощью (бывш 045/у)
    """

    hospital: Hospitals = direction.hospital
    hospital_name = hospital.safe_short_title
    hospital_address = hospital.safe_address
    patient_data = direction.client.get_data_individual()

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.alignment = TA_JUSTIFY
    style.leading = 16

    style_header = deepcopy(style)
    style_header.fontName = "PTAstraSerifBold"
    style_header.fontSize = 14
    style_header.alignment = TA_CENTER

    style_right = deepcopy(style)
    style_right.alignment = TA_RIGHT

    style_center_bold = deepcopy(style)
    style_center_bold.alignment = TA_CENTER
    style_center_bold.fontName = "PTAstraSerifBold"

    style_center = deepcopy(style_center_bold)
    style_center.fontName = "PTAstraSerifReg"

    style_left_bold = deepcopy(style_center_bold)
    style_left_bold.alignment = TA_LEFT

    protocol_data = title_fields(iss)

    date_zero = datetime.datetime.strptime(protocol_data["Дата осмотра"], "%d.%m.%Y")
    normal_date_zero = ".".join(str(date_zero).split()[0].split('-')[::-1])
    date_three = date_zero + datetime.timedelta(days=3)
    date_three = ".".join(str(date_three).split()[0].split('-')[::-1])
    date_seven = date_zero + datetime.timedelta(days=7)
    date_seven = ".".join(str(date_seven).split()[0].split('-')[::-1])
    date_fourteen = date_zero + datetime.timedelta(days=14)
    date_fourteen = ".".join(str(date_fourteen).split()[0].split('-')[::-1])
    date_thirty = date_zero + datetime.timedelta(days=30)
    date_thirty = ".".join(str(date_thirty).split()[0].split('-')[::-1])
    date_ninety = date_zero + datetime.timedelta(days=90)
    date_ninety = ".".join(str(date_ninety).split()[0].split('-')[::-1])

    underline = '_______________'
    bold_open = '<font face="PTAstraSerifBold">'
    bold_close = '</font>'
    space = 5 * mm
    text = []
    params_columns = []
    text.append(Paragraph(f'{bold_open}17. Осложнения во время проведения прививок:{bold_close} {protocol_data["17. Осложнения во время проведения прививок"]}', style))
    text.append(
        Paragraph(
            f'{bold_open}18. Курс прививок полностью закончен, отменен, так как животное оказалось здоровым, прерван самостоятельно и пр. <br/> '
            f'(подчеркнуть или вписать){bold_close}_______________________________________',
            style,
        )
    )
    text.append(Paragraph(f'{bold_open}19. Какие меры приняты к продолжению прививок:{bold_close} {protocol_data["19. Какие приняты меры к продолжению прерванных прививок"]}', style))
    text.append(Paragraph(f'{bold_open}20. Примечание:{bold_close} {protocol_data["20. Примечание"]}', style))
    text.append(Spacer(1, space))
    text.append(Paragraph('Беседа о профилактике бешенства проведена', style_header))
    text.append(Spacer(1, space))
    text.append(Paragraph(f'Подпись законного представителя{underline}', style_right))
    text.append(Spacer(1, space))
    text.append(Paragraph(f'С правилами поведения во время прививок ознакомлен{underline}', style_right))
    text.append(Spacer(1, space))
    text.append(Paragraph(f'Подпись врача{underline}', style_right))
    text.append(Spacer(1, space))
    text.append(Paragraph('Инструкция', style_header))
    text.append(Spacer(1, space))
    text.append(Paragraph('к заполнению карты обратившегося за антирабической помощью', style_center_bold))
    text.append(Spacer(1, space))
    text.append(
        Paragraph(
            '1. На каждого обратившегося за антирабической помощью в лечебно профилактическое учреждение карта заполняется в двух экземплярах. По окончанию курса прививок '
            '(срок наблюдения за животным) один экземпляр карты посылается в районную (городскую) санитарно-эпидемиологическую станцию (санэпидотдел больницы, в район '
            'деятельности которой расположено данное лечебно-профилактическое учреждение). На обратившихся за антирабической помощью в антирабическое отделение '
            'санитарно-эпидемиологической станции карта заполняется в одном экземпляре, которой остается в данном учреждении.',
            style,
        )
    )
    text.append(Paragraph('2. На основании разработки данных карт заполняется соответствующий раздел отчетной формы №36', style))

    params_columns.append({"x": -4.5 * mm, "y": -170 * mm, "width": 135.5 * mm, "height": 185 * mm, "text": text, "showBoundary": 0})

    text = []
    opinion = [
        [
            Paragraph(f'Кабинет неотложной травматологии и ортопедии <br/> {hospital_name} <br/> {hospital_address}', style_left_bold),
            Paragraph(f'КАРТА №{direction.pk}', style_center_bold),
        ],
    ]
    tbl = Table(opinion, colWidths=[50 * mm, 86 * mm], hAlign='LEFT')
    table_style = [('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('RIGHTPADDING', (1, 0), (1, 0), 50 * mm)]
    tbl.setStyle(table_style)
    text.append(tbl)
    text.append(Spacer(1, 3 * mm))
    text.append(Paragraph('Обратившегося за антирабической помощью', style_header))
    text.append(Spacer(1, space))
    text.append(Paragraph(f'{bold_open}Дата осмотра:{bold_close} {protocol_data["Дата осмотра"]}', style_right))
    text.append(Spacer(1, space))
    text.append(Paragraph(f'{bold_open}1. Фамилия, имя, отчество:{bold_close} {patient_data["fio"]}', style))
    text.append(Paragraph(f'{bold_open}2. Возраст:{bold_close} {patient_data["age"]}', style))
    text.append(Paragraph(f'{bold_open}3. Домашний адрес, телефон:{bold_close} {patient_data["fact_address"]}, {" ".join(patient_data["phone"])}', style))
    text.append(Paragraph(f'{bold_open}4. Школа, д/сад - класс, группа:{bold_close} {patient_data["work_place"]}', style))
    text.append(Paragraph(f'{bold_open}5. Дата укуса, оцарапания, ослюнения:{bold_close} {protocol_data["5. Дата укуса, оцарапания, ослюнения"]}', style))
    text.append(
        Paragraph(
            f'{bold_open}6. В какое лечебное учреждение обращался по поводу укуса и когда:{bold_close} '
            f'{protocol_data["6. В какое лечебное учреждение обращался по поводу укуса и когда"]}',
            style,
        )
    )
    text.append(Paragraph(f'{bold_open}7. Описание повреждения и его локализация:{bold_close} {protocol_data["7. Описание повреждения и его локализация"]}', style))
    text.append(
        Paragraph(f'{bold_open}8. Сведения об укусившем, оцарапшем, ослюнившем животном:{bold_close} {protocol_data["8. Сведения об укусившем, оцарапавшем, ослюнившем животном"]}', style)
    )
    text.append(Paragraph(f'{bold_open}9. Обстоятельства укуса, оцарапания, ослюнения:{bold_close} {protocol_data["9. Обстоятельства укуса, оцарапания, ослюнения"]}', style))
    text.append(Paragraph(f'{bold_open}10. Бешенство животного установлено ветврачом клинически, лабораторно <br/> (подчеркнуть или вписать){bold_close}{underline}', style))
    text.append(Paragraph(f'{bold_open}11.Животное:{bold_close} {protocol_data["11. Животное"]}', style))
    text.append(Paragraph(f'{bold_open}12. Анамнез обратившегося:{bold_close}', style))
    text.append(Paragraph(f'{bold_open}a) заболевание нервной системы:{bold_close} {protocol_data["а) заболевание нервной системы"]}', style))
    text.append(Paragraph(f'{bold_open}б) употребляет ли спиртные напитки, как часто:{bold_close} {protocol_data["б) употребляет ли спиртные напитки, как часто"]}', style))
    text.append(
        Paragraph(
            f'{bold_open}в) получал ли в прошлом антирабические прививки, когда, сколько:{bold_close} ' f'{protocol_data["в) получал ли в прошлом антирабические прививки, когда, сколько"]}',
            style,
        )
    )
    text.append(Paragraph(f'{bold_open}г) прочие сведения:{bold_close} {protocol_data["г) прочие сведения"]}', style))

    params_columns.append({"x": 145.5 * mm, "y": -170 * mm, "width": 135.5 * mm, "height": 185 * mm, "text": text, "showBoundary": 0})
    fwb.append(FrameDataCol(params_columns=params_columns))
    fwb.append(FrameBreak())
    fwb.append(Spacer(1, space))

    params_columns = []
    text = []
    text.append(Paragraph(f'{bold_open}13. Назначение прививки:{bold_close} {protocol_data["13. Назначение прививки"]}', style))
    text.append(Paragraph(f'{bold_open}14. Назначенный режим:{bold_close} {protocol_data["14. Назначенный режим"]}', style))
    text.append(
        Paragraph(f'{bold_open}15. Введение антирабического гаммаглобулина: Дата, серия:{bold_close} {protocol_data["15. Введение антирабического гаммаглобулина: дата, серия"]}', style)
    )
    text.append(Paragraph(f'{bold_open}16. Реакция на внутрикожную пробу: {bold_close}', style))
    text.append(Paragraph(f'{bold_open}покраснение:{bold_close} {protocol_data["покраснение"]}', style))
    text.append(Paragraph(f'{bold_open}отёк:{bold_close} {protocol_data["отек"]}', style))
    text.append(Paragraph(f'{bold_open}Десенсибилизация:{bold_close} {protocol_data["Десенсибилизация"]}', style))
    text.append(Paragraph(f'{bold_open}Суточная доза:{bold_close} {protocol_data["Суточная доза"]}', style))
    opinion = [
        [
            Paragraph(f'{bold_open}Повторные введения:{bold_close}', style),
            Paragraph('Дата', style),
            Paragraph('', style),
            Paragraph('Доза', style),
            Paragraph('', style),
            Paragraph('Серия', style),
            Paragraph('', style),
        ],
        [Paragraph('', style), Paragraph('Дата', style), Paragraph('', style), Paragraph('Доза', style), Paragraph('', style), Paragraph('Серия', style), Paragraph('', style)],
    ]
    tbl = Table(opinion, colWidths=[45 * mm, 9 * mm, 15 * mm, 9 * mm, 15 * mm, 11.5 * mm, 15 * mm], hAlign='LEFT')
    table_style = [
        ('SPAN', (0, 0), (0, -1)),
        ('VALIGN', (0, 0), (0, -1), 'TOP'),
        ('RIGHTPADDING', (1, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (2, 0), (2, 1), 0.5, black),
        ('LINEBELOW', (4, 0), (4, 1), 0.5, black),
        ('LINEBELOW', (6, 0), (6, 1), 0.5, black),
    ]
    tbl.setStyle(table_style)
    text.append(tbl)
    text.append(Spacer(1, space))
    opinion = [
        [
            Paragraph('Номер', style_center_bold),
            Paragraph('Дата', style_center_bold),
            Paragraph('Доза вакцины', style_center_bold),
            Paragraph('№ Серия <br/> вакцины', style_center_bold),
            Paragraph('Подпись', style_center_bold),
        ],
        [
            Paragraph('1 (0 день)', style_center),
            Paragraph(f'{normal_date_zero}', style_center),
            Paragraph('1.0', style_center),
        ],
        [
            Paragraph('2 (3 день)', style_center),
            Paragraph(f'{date_three}', style_center),
            Paragraph('1.0', style_center),
        ],
        [
            Paragraph('3 (7 день)', style_center),
            Paragraph(f'{date_seven}', style_center),
            Paragraph('1.0', style_center),
        ],
        [
            Paragraph('4 (14 день)', style_center),
            Paragraph(f'{date_fourteen}', style_center),
            Paragraph('1.0', style_center),
        ],
        [
            Paragraph('5 (30 день)', style_center),
            Paragraph(f'{date_thirty}', style_center),
            Paragraph('1.0', style_center),
        ],
        [
            Paragraph('6 (90 день)', style_center),
            Paragraph(f'{date_ninety}', style_center),
            Paragraph('1.0', style_center),
        ],
    ]

    tbl = Table(opinion)
    table_style = [
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('VALIGN', (0, 0), (-1, 0), 'TOP'),
        ('VALIGN', (0, 1), (0, -1), 'CENTER'),
    ]
    tbl.setStyle(table_style)
    text.append(tbl)
    text.append(Spacer(1, space))
    text.append(Paragraph(f'{bold_open}Привит по возрасту{bold_close}', style))
    text.append(Spacer(1, space))
    text.append(Paragraph(f'{bold_open}Подпись{underline}{bold_close}', style))
    params_columns.append({"x": -4.5 * mm, "y": -170 * mm, "width": 135.5 * mm, "height": 185 * mm, "text": text, "showBoundary": 0})
    fwb.append(FrameDataCol(params_columns=params_columns))

    fwb.append(FrameBreak())
    fwb.append(Spacer(1, space))

    text = []
    params_columns = []

    text.append(Paragraph(f'{patient_data["fio"]}', style))
    text.append(Paragraph(f'{bold_open}Часы приема:{bold_close} <br/> {protocol_data["Часы приема"]}', style))
    text.append(Paragraph('Даты прививок', style_header))
    text.append(Spacer(1, space))
    text.append(tbl)
    text.append(Spacer(1, space))
    params_columns.append({"x": -4.5 * mm, "y": -170 * mm, "width": 135.5 * mm, "height": 185 * mm, "text": text, "showBoundary": 0})
    fwb.append(FrameDataCol(params_columns=params_columns))

    return fwb


def title_fields(iss):
    title_fields = [
        "Дата осмотра",
        "5. Дата укуса, оцарапания, ослюнения",
        "6. В какое лечебное учреждение обращался по поводу укуса и когда",
        "7. Описание повреждения и его локализация",
        "8. Сведения об укусившем, оцарапавшем, ослюнившем животном",
        "9. Обстоятельства укуса, оцарапания, ослюнения",
        "11. Животное",
        "а) заболевание нервной системы",
        "б) употребляет ли спиртные напитки, как часто",
        "в) получал ли в прошлом антирабические прививки, когда, сколько",
        "г) прочие сведения",
        "13. Назначение прививки",
        "14. Назначенный режим",
        "15. Введение антирабического гаммаглобулина: дата, серия",
        "покраснение",
        "отек",
        "Десенсибилизация",
        "Суточная доза",
        "Повторные введения",
        "17. Осложнения во время проведения прививок",
        "19. Какие приняты меры к продолжению прерванных прививок",
        "20. Примечание",
        "Часы приема",
    ]

    result = fields_result_only_title_fields(iss, title_fields, False)
    data = {i['title']: i['value'] for i in result}

    for t in title_fields:
        if not data.get(t, None):
            data[t] = ""

    return data
