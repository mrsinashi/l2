from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def dispensarization_research(sex, age, client_id, d_start, d_end):
    """
    на входе: пол, возраст,
    выход: pk - исследований, справочника "DispensaryRouteSheet"
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ WITH
    t_field AS (
        SELECT directory_dispensaryroutesheet.research_id, directory_dispensaryroutesheet.sort_weight
        FROM directory_dispensaryroutesheet WHERE
        directory_dispensaryroutesheet.age_client = %(age_p)s
        and directory_dispensaryroutesheet.sex_client = %(sex_p)s
        ORDER BY directory_dispensaryroutesheet.sort_weight
    ),
    t_iss AS
        (SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id as napr,  
        directions_napravleniya.data_sozdaniya, 
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id 
        WHERE directions_napravleniya.client_id = %(client_p)s
         and directions_issledovaniya.research_id in (SELECT research_id FROM t_field) 
         and directions_issledovaniya.time_confirmation BETWEEN  %(start_p)s AND %(end_p)s
         ORDER BY directions_issledovaniya.time_confirmation DESC),
     t_research AS (SELECT directory_researches.id, directory_researches.title, 
                    directory_researches.short_title FROM directory_researches),
     t_disp AS 
        (SELECT DISTINCT ON (t_field.research_id) t_field.research_id as res_id, t_field.sort_weight as sort,
        client_id, napr, data_sozdaniya, t_iss.research_id, time_confirmation, date_confirm FROM t_field
        LEFT JOIN t_iss ON t_field.research_id = t_iss.research_id)
    
    SELECT res_id, sort, napr, time_confirmation, date_confirm, title, short_title 
    FROM t_disp
    LEFT JOIN t_research ON t_disp.res_id = t_research.id
    ORDER by sort
        """,
            params={'sex_p': sex, 'age_p': age, 'client_p': client_id, 'start_p': d_start, 'end_p': d_end, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def get_fraction_result(client_id, fraction_id, count=1):
    """
    на входе: id-фракции, id-карты,
    выход: последний результат исследования
    :return:
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id,   
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
        directions_result.value, directions_result.fraction_id
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
        LEFT JOIN directions_result
           ON directions_issledovaniya.id=directions_result.issledovaniye_id
        WHERE directions_napravleniya.client_id = %(client_p)s
         and directions_result.fraction_id = %(fraction_p)s
         and directions_issledovaniya.time_confirmation is not NULL
         ORDER BY directions_issledovaniya.time_confirmation DESC LIMIT %(count_p)s 
        """,
            params={'client_p': client_id, 'fraction_p': fraction_id, 'count_p': count, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def get_field_result(client_id, field_id, count=1):
    """
    на входе: id-поля, id-карты,
    выход: последний результат поля
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id,   
            directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s as time_confirmation,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            directions_paraclinicresult.value, directions_paraclinicresult.field_id
            FROM directions_issledovaniya
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN directions_paraclinicresult
            ON directions_issledovaniya.id=directions_paraclinicresult.issledovaniye_id
            WHERE directions_napravleniya.client_id = %(client_p)s
            and directions_paraclinicresult.field_id = %(field_id)s
            and directions_issledovaniya.time_confirmation is not NULL
            ORDER BY directions_issledovaniya.time_confirmation DESC LIMIT %(count_p)s
            """,
            params={'client_p': client_id, 'field_id': field_id, 'count_p': count, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def users_by_group(title_groups, hosp_id):

    with connection.cursor() as cursor:
        cursor.execute(
            """
        WITH 
          t_group AS (
          SELECT id as group_id FROM auth_group
          WHERE name = ANY(ARRAY[%(title_groups)s])),
            
        t_users_id AS(
          SELECT user_id FROM auth_user_groups
          WHERE group_id in (SELECT group_id from t_group)),
            
        t_podrazdeleniye AS (
          SELECT id as id, title as title_podr, short_title FROM podrazdeleniya_podrazdeleniya),
            
        t_users AS (
          SELECT users_doctorprofile.id as doc_id, fio, user_id, podrazdeleniye_id, title_podr, short_title, hospital_id
          FROM users_doctorprofile
          LEFT JOIN
          t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          WHERE user_id in (SELECT user_id FROM t_users_id) and hospital_id = %(hosp_id)s) 
    
        SELECT doc_id, fio, podrazdeleniye_id, title_podr, short_title FROM t_users
        ORDER BY podrazdeleniye_id                    
        """,
            params={'title_groups': title_groups, "hosp_id": hosp_id},
        )

        row = cursor.fetchall()
    return row


def users_all(hosp_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        WITH
        t_users_id AS (
          SELECT user_id FROM auth_user_groups),
            
        t_podrazdeleniye AS (
          SELECT id as id, title as title_podr, short_title FROM podrazdeleniya_podrazdeleniya),
            
        t_users AS (
          SELECT users_doctorprofile.id as doc_id, fio, user_id, podrazdeleniye_id, title_podr, short_title, hospital_id
          FROM users_doctorprofile
          LEFT JOIN
          t_podrazdeleniye ON users_doctorprofile.podrazdeleniye_id = t_podrazdeleniye.id
          WHERE user_id in (SELECT user_id FROM t_users_id) and hospital_id = %(hosp_id)s)            
        SELECT doc_id, fio, podrazdeleniye_id, title_podr, short_title FROM t_users
        ORDER BY podrazdeleniye_id                    
        """,
            params={"hosp_id": hosp_id},
        )

        row = cursor.fetchall()
    return row


def get_diagnoses(d_type="mkb10.4", diag_title="-1", diag_mkb="-1", limit=100):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT * FROM public.directions_diagnoses
            WHERE d_type=%(d_type)s 
            AND CASE
                WHEN %(diag_title)s != '-1' AND %(diag_mkb)s != '-1' THEN 
                  code ~* %(diag_mkb)s and title ~* %(diag_title)s
                WHEN %(diag_title)s != '-1' AND %(diag_mkb)s = '-1' THEN 
                  title ~* %(diag_title)s
                WHEN %(diag_title)s = '-1' AND %(diag_mkb)s != '-1' THEN 
                  code ~* %(diag_mkb)s
              END
            AND 
            nsi_id IS NOT NULL
            AND nsi_id != ''
        LIMIT %(limit)s
        """,
            params={"d_type": d_type, "diag_title": diag_title, "diag_mkb": diag_mkb, "limit": limit},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_resource_researches(resource_pks):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT scheduleresource_id, researches_id FROM doctor_schedule_scheduleresource_service
        WHERE scheduleresource_id in %(resource_pks)s 
        ORDER BY scheduleresource_id
        """,
            params={"resource_pks": resource_pks},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def serch_data_by_param(
    date_create_start,
    date_create_end,
    research_id,
    case_number,
    hosp,
    date_registred_start,
    date_registred_end,
    date_examination_start,
    date_examination_end,
    doc_confirm,
    date_recieve,
    date_get,
    final_text,
):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.value as field_value,
                directory_paraclinicinputfield.title as field_title,

                directions_issledovaniya.napravleniye_id as direction_number,
                directions_issledovaniya.medical_examination as date_service,
                users_doctorprofile.fio as doc_fio,

                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as patient_fio,

                hospitals_hospitals.title as hosp_title,
                hospitals_hospitals.okpo as hosp_okpo,
                hospitals_hospitals.okato as hosp_okato,

                to_char(clients_individual.birthday, 'DD.MM.YYYY') as patient_birthday,
                date_part('year', age(directions_issledovaniya.medical_examination, clients_individual.birthday))::int as patient_age,
                clients_individual.sex as patient_sex
                
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                LEFT JOIN users_doctorprofile ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
                WHERE 
                    directions_issledovaniya.research_id=%(research_id)s and directions_issledovaniya.time_confirmation IS NOT NULL 
                    and directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN (%(date_create_start)s AND %(date_create_end)s)
                AND CASE WHEN %(case_number)s > -1 THEN directions_napravleniya.additional_number = %(case_number)s 
                         WHEN %(case_number)s = -1 THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(hosp)s > -1 THEN directions_napravleniya.hospital_id = %(hosp)s
                         WHEN %(hosp)s = -1 THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(date_examination_start)s > -1 THEN 
                     directions_issledovaniya.medical_examination AT TIME ZONE %(tz)s BETWEEN %(date_examination_start)s AND %(date_examination_end)s
                     WHEN %(date_examination_start)s = -1 THEN directions_napravleniya.cancel is not Null
                END
                AND CASE WHEN %(doc_confirm)s > -1 THEN directions_issledovaniya.doc_confirmation_id = %(doc_confirm)s
                         WHEN %(doc_confirm)s = -1 THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(date_registred_start)s > -1 THEN directions_napravleniya.visit_date AT TIME ZONE %(tz)s BETWEEN %(date_registred_start)s AND %(date_registred_end)s
                         WHEN %(date_registred_start)s = -1 THEN directions_napravleniya.cancel is not Null 
                END
                AND CASE WHEN %(date_recieve)s > -1 THEN directory_paraclinicinputfield.title = 'Дата получения' and directions_paraclinicresult.value ~* %(date_recieve)s
                          WHEN %(date_recieve)s = -1 THEN directions_napravleniya.cancel is not Null
                END
                AND CASE WHEN %(date_get)s > -1 THEN directory_paraclinicinputfield.title = 'Дата забора' and directions_paraclinicresult.value ~* %(date_recieve)s
                         WHEN %(date_get)s = -1 THEN directions_napravleniya.cancel is not Null
                END
                AND CASE WHEN %(final_text)s != -1 THEN directions_paraclinicresult.value ~* %(final_text)s
                         WHEN %(final_text)s = -1 THEN directions_napravleniya.cancel is not Null 
                END
                order by directions_issledovaniya.napravleniye_id
            """,
            params={
                'date_create_start': date_create_start,
                'date_create_end': date_create_end,
                'research_id': research_id,
                'case_number': case_number,
                'hosp': hosp,
                'date_examination_start': date_examination_start,
                'date_examination_end': date_examination_end,
                'date_registred_start': date_registred_start,
                'date_registred_end': date_registred_end,
                'doc_confirm': doc_confirm,
                'date_recieve': date_recieve,
                'date_get': date_get,
                'final_text': final_text,
                'tz': TIME_ZONE,
            },
        )

        rows = namedtuplefetchall(cursor)
    return rows
