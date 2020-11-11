import logging
import random

import simplejson as json
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

import directions.models as directions
from clients.models import Individual, Card
from directory.models import Researches, Fractions, ReleationsFT
from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.settings import AFTER_DATE
from laboratory.utils import current_time
from refprocessor.result_parser import ResultRight
from researches.models import Tubes
from slog.models import Log
from tfoms.integration import match_enp
from utils.data_verification import data_parse
from utils.dates import normalize_date, valid_date
from . import sql_if
from directions.models import Napravleniya


logger = logging.getLogger("IF")


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    if after_date == '0':
        after_date = AFTER_DATE
    next_n = int(request.GET.get("nextN", 1))
    type_researches = request.GET.get("research", '*')
    d_start = f'{after_date}'
    dirs = sql_if.direction_collect(d_start, type_researches, next_n)

    next_time = None
    naprs = []
    if dirs:
        for i in dirs:
            naprs.append(i[0])
            next_time = i[3]

    return Response({"next": naprs, "next_time": next_time, "n": next_n, "fromPk": from_pk, "afterDate": after_date})


@api_view()
def get_dir_amd(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_amd(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def get_dir_n3(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_n3(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def resend_dir_l2(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_l2(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def result_amd_send(request):
    result = json.loads(request.GET.get("result"))
    resp = {"ok": False}
    if result['error']:
        for i in result['error']:
            dir_pk = int(i.split(':')[0])
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, error_amd=True)
        resp = {"ok": True}
    if result['send']:
        for i in result['send']:
            data_amd = i.split(':')
            dir_pk = int(data_amd[0])
            amd_num = data_amd[1]
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, amd_number=amd_num, error_amd=False)
        resp = {"ok": True}

    return Response(resp)


@api_view()
def direction_data(request):
    pk = request.GET.get("pk")
    research_pks = request.GET.get("research", '*')
    direction = directions.Napravleniya.objects.get(pk=pk)
    card = direction.client
    individual = card.individual

    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=False)
    if research_pks != '*':
        iss = iss.filter(research__pk__in=research_pks.split(','))

    if not iss:
        return Response({"ok": False})

    iss_index = random.randrange(len(iss))

    return Response(
        {
            "ok": True,
            "pk": pk,
            "createdAt": direction.data_sozdaniya,
            "patient": {
                **card.get_data_individual(full_empty=True, only_json_serializable=True),
                "family": individual.family,
                "name": individual.name,
                "patronymic": individual.patronymic,
                "birthday": individual.birthday,
                "sex": individual.sex,
                "card": {"base": {"pk": card.base_id, "title": card.base.title, "short_title": card.base.short_title,}, "pk": card.pk, "number": card.number,},
            },
            "issledovaniya": [x.pk for x in iss],
            "timeConfirmation": iss[iss_index].time_confirmation,
            "docLogin": iss[iss_index].doc_confirmation.rmis_login if iss[iss_index].doc_confirmation else None,
            "docPassword": iss[iss_index].doc_confirmation.rmis_password if iss[iss_index].doc_confirmation else None,
            "department_oid": iss[iss_index].doc_confirmation.podrazdeleniye.oid if iss[iss_index].doc_confirmation else None,
            "finSourceTitle": direction.istochnik_f.title,
            "oldPk": direction.core_id,
            "isExternal": direction.is_external,
        }
    )


def format_time_if_is_not_none(t):
    if not t:
        return None
    return "{:%Y-%m-%d %H:%M}".format(t)


@api_view()
def issledovaniye_data(request):
    pk = request.GET.get("pk")
    ignore_sample = request.GET.get("ignoreSample") == 'true'
    i = directions.Issledovaniya.objects.get(pk=pk)

    sample = directions.TubesRegistration.objects.filter(issledovaniya=i, time_get__isnull=False).first()
    results = directions.Result.objects.filter(issledovaniye=i, fraction__fsli__isnull=False)

    if (not ignore_sample and not sample) or not results.exists():
        return Response({"ok": False})

    results_data = []

    for r in results:
        refs = r.calc_normal(only_ref=True, raw_ref=False)

        if isinstance(refs, ResultRight):
            if refs.mode == ResultRight.MODE_CONSTANT:
                refs = [refs.const_orig]
            else:
                refs = [str(refs.range.val_from.value), str(refs.range.val_to.value)]
                if refs[0] == '-inf':
                    refs = [f'до {refs[1]}']
                elif refs[1] == 'inf':
                    refs = [f'от {refs[0]}']
                elif refs[0] == refs[1]:
                    refs = [refs[0]]
        else:
            refs = [r.calc_normal(only_ref=True) or '']

        results_data.append(
            {
                "pk": r.pk,
                "fsli": r.fraction.get_fsli_code(),
                "value": r.value.replace(',', '.'),
                "units": r.get_units(),
                "ref": refs,
            }
        )

    time_confirmation = i.time_confirmation_local

    return Response(
        {
            "ok": True,
            "pk": pk,
            "sample": {"date": sample.time_get.date() if sample else i.time_confirmation.date()},
            "date": time_confirmation.date(),
            "dateTimeGet": format_time_if_is_not_none(sample.time_get_local) if sample else None,
            "dateTimeReceive": format_time_if_is_not_none(sample.time_recive_local) if sample else None,
            "dateTimeConfirm": format_time_if_is_not_none(time_confirmation),
            "docConfirm": i.doc_confirmation_fio,
            "results": results_data,
            "code": i.research.code,
            "comments": i.lab_comment,
        }
    )


@api_view()
def issledovaniye_data_multi(request):
    pks = request.GET["pks"].split(",")
    ignore_sample = request.GET.get("ignoreSample") == 'true'
    iss = (
        directions.Issledovaniya
        .objects
        .filter(pk__in=pks)
        .select_related('doc_confirmation', 'research')
        .prefetch_related(
            Prefetch(
                'result_set',
                queryset=(
                    directions.Result
                    .objects
                    .filter(fraction__fsli__isnull=False)
                    .select_related('fraction')
                )
            )
        )
        .prefetch_related(
            Prefetch(
                'tubes',
                queryset=(
                    directions.TubesRegistration
                    .objects.filter(time_get__isnull=False)
                )
            )
        )
    )

    result = []

    i: directions.Issledovaniya

    for i in iss:
        sample = i.tubes.all().first()

        if (not ignore_sample and not sample) or not i.result_set.all().exists():
            continue

        results_data = []

        for r in i.result_set.all():
            refs = r.calc_normal(only_ref=True, raw_ref=False)

            if isinstance(refs, ResultRight):
                if refs.mode == ResultRight.MODE_CONSTANT:
                    refs = [refs.const]
                else:
                    refs = [str(refs.range.val_from.value), str(refs.range.val_to.value)]
                    if refs[0] == '-inf':
                        refs = [f'до {refs[1]}']
                    elif refs[1] == 'inf':
                        refs = [f'от {refs[0]}']
                    elif refs[0] == refs[1]:
                        refs = [refs[0]]
            else:
                refs = [r.calc_normal(only_ref=True) or '']

            results_data.append(
                {
                    "pk": r.pk,
                    "fsli": r.fraction.get_fsli_code(),
                    "value": r.value.replace(',', '.'),
                    "units": r.get_units(),
                    "ref": refs,
                }
            )

        time_confirmation = i.time_confirmation_local

        result.append(
            {
                "pk": i.pk,
                "sample": {"date": sample.time_get.date() if sample else i.time_confirmation.date()},
                "date": time_confirmation.date(),
                "dateTimeGet": format_time_if_is_not_none(sample.time_get_local) if sample else None,
                "dateTimeReceive": format_time_if_is_not_none(sample.time_recive_local) if sample else None,
                "dateTimeConfirm": format_time_if_is_not_none(time_confirmation),
                "docConfirm": i.doc_confirmation_fio,
                "results": results_data,
                "code": i.research.code,
                "comments": i.lab_comment,
            }
        )
    return Response({
        "ok": len(result) > 0,
        "pks": pks,
        "results": result,
    })


@api_view(['GET'])
def make_log(request):
    key = request.GET.get("key")
    keys = request.GET.get("keys", key).split(",")
    t = int(request.GET.get("type"))
    body = {}

    if request.method == "POST":
        body = json.loads(request.body)

    pks_to_resend_n3_false = [x for x in keys if x] if t in (60000, 60001, 60002, 60003) else []
    pks_to_resend_l2_false = [x for x in keys if x] if t in (60004, 60005) else []

    with transaction.atomic():
        directions.Napravleniya.objects.filter(pk__in=pks_to_resend_n3_false).update(need_resend_n3=False)
        directions.Napravleniya.objects.filter(pk__in=pks_to_resend_l2_false).update(need_resend_l2=False)

        for k in pks_to_resend_n3_false:
            Log.log(key=k, type=t, body=json.dumps(body.get(k, {})))

        for k in pks_to_resend_l2_false:
            Log.log(key=k, type=t, body=json.dumps(body.get(k, {})))

    return Response({"ok": True})


@api_view(['POST'])
def check_enp(request):
    enp, bd = data_parse(request.body, {'enp': str, 'bd': str})

    enp = enp.replace(' ', '')

    tfoms_data = match_enp(enp)

    if tfoms_data:
        bdate = tfoms_data.get('birthdate', '').split(' ')[0]
        if normalize_date(bd) == normalize_date(bdate):
            return Response({"ok": True, 'patient_data': tfoms_data})

    return Response({"ok": False, 'message': 'Неверные данные или нет прикрепления к поликлинике'})


@api_view(['POST'])
def external_doc_call_create(request):
    data = json.loads(request.body)
    org_id = data.get('org_id')
    patient_data = data.get('patient_data')
    form = data.get('form')
    idp = patient_data.get('idp')
    enp = patient_data.get('enp')
    comment = form.get('comment')
    purpose = form.get('purpose')

    Individual.import_from_tfoms(patient_data)
    individuals = Individual.objects.filter(Q(tfoms_enp=enp or '###$fakeenp$###') | Q(tfoms_idp=idp or '###$fakeidp$###'))

    individual_obj = individuals.first()
    if not individual_obj:
        return JsonResponse({"ok": False, "number": None})

    card = Card.objects.filter(individual=individual_obj, base__internal_type=True).first()
    research = Researches.objects.filter(title='Обращение пациента').first()
    hospital = Hospitals.objects.filter(code_tfoms=org_id).first()

    if not card or not research or not hospital:
        return JsonResponse({"ok": False, "number": None})

    research_pk = research.pk

    doc_call = DoctorCall.doctor_call_save(
        {
            'card': card,
            'research': research_pk,
            'address': card.main_address,
            'district': -1,
            'date': current_time(),
            'comment': comment,
            'phone': form.get('phone'),
            'doc': -1,
            'purpose': int(purpose),
            'hospital': hospital.pk,
            'external': True,
        }
    )
    doc_call.external_num = f"{org_id}{doc_call.pk}"
    doc_call.save()

    return Response({"ok": True, "number": doc_call.pk})


@api_view(['POST'])
def set_core_id(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    core_id = data.get('coreId')
    n = directions.Napravleniya.objects.get(pk=pk)
    n.core_id = core_id
    n.save(update_fields=['core_id'])
    return Response({"ok": True})


class InvalidData(Exception):
    pass


@api_view(['POST'])
def external_research_create(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)

    old_pk = body.get("oldPk")
    org = body.get("org")
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not code_tfoms and not oid_org:
        return Response({"ok": False, 'message': 'Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid'})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid_org=oid_org).first()

    if not hospital:
        return Response({"ok": False, 'message': 'Организация не найдена'})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, 'message': 'Нет доступа в переданную организацию'})

    patient = body.get("patient", {})
    enp = patient.get("enp", '').replace(' ', '')

    if len(enp) != 16 or not enp.isdigit():
        return Response({"ok": False, 'message': 'Неверные данные полиса, должно быть 16 чисел'})

    individuals = Individual.objects.filter(tfoms_enp=enp)
    if not individuals.exists():
        individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title='Полис ОМС') | Q(document__document_type__title='ЕНП'))
    if not individuals.exists():
        tfoms_data = match_enp(enp)
        if not tfoms_data:
            return Response({"ok": False, 'message': 'Неверные данные полиса, в базе ТФОМС нет такого пациента'})
        Individual.import_from_tfoms(tfoms_data)
        individuals = Individual.objects.filter(tfoms_enp=enp)

    individual = individuals.first()
    if not individual:
        return Response({"ok": False, 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, 'message': 'Карта не найдена'})

    financing_source_title = body.get("financingSource", '')

    financing_source = (
        directions.IstochnikiFinansirovaniya
        .objects
        .filter(title__iexact=financing_source_title, base__internal_type=True)
        .first()
    )

    if not financing_source:
        return Response({"ok": False, 'message': 'Некорректный источник финансирования'})

    results = body.get("results")
    if not results or not isinstance(results, list):
        return Response({"ok": False, 'message': 'Некорректное значение results'})

    message = None

    try:
        with transaction.atomic():
            if old_pk and Napravleniya.objects.filter(pk=old_pk, hospital=hospital).exists():
                direction = Napravleniya.objects.get(pk=old_pk)
                direction.is_external = True
                direction.istochnik_f = financing_source
                direction.polis_who_give = card.polis.who_give if card.polis else None
                direction.polis_n = card.polis.number if card.polis else None
                direction.save()
                direction.issledovaniya_set.all().delete()
            else:
                direction = (
                    Napravleniya
                    .objects
                    .create(
                        client=card,
                        is_external=True,
                        istochnik_f=financing_source,
                        polis_who_give=card.polis.who_give if card.polis else None,
                        polis_n=card.polis.number if card.polis else None,
                        hospital=hospital,
                    )
                )

            for r in results:
                code_research = r.get("codeResearch", "unknown")
                research = Researches.objects.filter(code=code_research).first()
                if not research:
                    raise InvalidData(f'Исследование с кодом {code_research} не найдено')

                tests = r.get("tests")
                if not tests or not isinstance(tests, list):
                    raise InvalidData(f'Исследование {code_research} содержит некорректное поле tests')

                comments = str(r.get("comments", "") or "") or None

                time_confirmation = r.get("dateTimeConfirm")
                if not time_confirmation or not valid_date(time_confirmation):
                    raise InvalidData(f'{code_research}: содержит некорректное поле dateTimeConfirm. Оно должно быть заполнено и соответствовать шаблону YYYY-MM-DD HH:MM')

                time_get = str(r.get("dateTimeGet", "") or "") or None
                if time_get and not valid_date(time_confirmation):
                    raise InvalidData(f'{code_research}: содержит некорректное поле dateTimeGet. Оно должно быть пустым или соответствовать шаблону YYYY-MM-DD HH:MM')

                time_receive = str(r.get("dateTimeReceive", "") or "") or None
                if time_receive and not valid_date(time_confirmation):
                    raise InvalidData(f'{code_research}: содержит некорректное поле dateTimeReceive. Оно должно быть пустым или соответствовать шаблону YYYY-MM-DD HH:MM')

                doc_confirm = str(r.get("docConfirm", "") or "") or None

                iss = (
                    directions.Issledovaniya
                    .objects
                    .create(
                        napravleniye=direction,
                        research=research,
                        lab_comment=comments,
                        time_confirmation=time_confirmation,
                        time_save=timezone.now(),
                        doc_confirmation_string=doc_confirm or f'Врач {hospital.short_title or hospital.title}',
                    )
                )
                tube = Tubes.objects.filter(title='Универсальная пробирка').first()
                if not tube:
                    tube = Tubes.objects.create(
                        title='Универсальная пробирка',
                        color='#049372'
                    )

                ft = ReleationsFT.objects.filter(tube=tube).first()
                if not ft:
                    ft = ReleationsFT.objects.create(tube=tube)

                tr = iss.tubes.create(type=ft)
                tr.time_get = time_get
                tr.time_recive = time_receive
                tr.save(update_fields=['time_get', 'time_recive'])

                for t in tests:
                    fsli_code = t.get("idFsli", "unknown")
                    fraction = Fractions.objects.filter(fsli=fsli_code).first()
                    if not fraction:
                        raise InvalidData(f'В исследовании {code_research} не найден тест {fsli_code}')
                    value = str(t.get("valueString", "") or "")
                    units = str(t.get("units", "") or "")

                    reference_value = t.get("referenceValue") or None
                    reference_range = t.get("referenceRange") or None

                    if reference_value and not isinstance(reference_value, str):
                        raise InvalidData(f'{code_research} -> {fsli_code}: поле referenceValue должно быть строкой или null')
                    if reference_range and not isinstance(reference_range, dict):
                        raise InvalidData(f'{code_research} -> {fsli_code}: поле referenceRange должно быть объектом {{low, high}} или null')

                    if reference_range and ('low' not in reference_range or 'high' not in reference_range):
                        raise InvalidData(f'{code_research} -> {fsli_code}: поле referenceRange должно быть объектом с полями {{low, high}} или null')

                    ref_str = reference_value

                    if not ref_str and reference_range:
                        ref_str = f"{reference_range['low']} – {reference_range['high']}"

                    if ref_str:
                        ref_str = ref_str.replace("\"", "'")
                        ref_str = f'{{"Все": "{ref_str}"}}'

                    directions.Result(
                        issledovaniye=iss,
                        fraction=fraction,
                        value=value,
                        units=units,
                        ref_f=ref_str,
                        ref_m=ref_str,
                    ).save()
            try:
                Log.log(str(direction.pk), 90000, body=body)
            except Exception as e:
                logger.exception(e)
            return Response({"ok": True, 'id': str(direction.pk)})

    except InvalidData as e:
        message = str(e)
    except Exception as e:
        logger.exception(e)
        message = 'Серверная ошибка'

    return Response({"ok": False, 'message': message})
