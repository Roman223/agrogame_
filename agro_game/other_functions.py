import random
from datetime import timedelta, date
from itertools import chain


def form_time(datetime_):
    return date(datetime_.year, datetime_.month, datetime_.day)


def import_standart_set(db, user_id):
    machines = [('T-150K',),
                ('МТЗ-82',),
                ('ДТ-75М',),
                ('КАМАЗ',),
                ('СКД-6',),
                ("Мехток - ПЕКТУС",),
                ('ЛДГ-10',),
                ('ПЛП-6-35',),
                ('15БЗТС-1',),
                ('ПЭ-0,8',),
                ('МРГ-4',),
                ('18БЗТС-1',),
                ('Пу-3а',),
                ('3СЗТ - 3,56',),
                ('3КК-6',),
                ('ПР-200',),
                ('УПФ-1',),
                ]
    session_id = db.session.execute(
        """
        SELECT LAST_INSERT_ID();
        """
    ).fetchall()[0][0]
    for machine in machines:
        db.session.execute(
            f"""
                INSERT INTO users_technics (mark, technic_owner, session_id)
                values ('{machine[0]}', "{user_id}", "{session_id}");
                """
        )
    print('IMPORT SS WAS SUCCESSFUL!')


def is_sessions(db, user_id: int):
    k = db.session.execute(
        f"""
        SELECT * FROM sessions
        WHERE user_id = {user_id};
        """).fetchall()
    db.session.commit()
    if len(k) != 0:
        return True
    return None


def is_field(db, user_id: int, ses_id: int):
    k = db.session.execute(
        f"""
        SELECT * FROM users_fields
        WHERE user_id = {user_id} and session_id = {ses_id};
        """).fetchall()
    db.session.commit()
    if len(k) != 0:
        return True
    return None


def session_to_user(db, id_user: bool, id_session: bool) -> bool:
    """
    Принадлежит ли данная сессия пользователю?
    """
    k = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={id_user} and id = {id_session};").fetchall()
    if len(k) != 0:
        return True
    return False


def session_validation(db, id_user, id_session):
    """
    Правильно ли сгенерировалась сессия
    """
    k = db.session.execute(
        f"SELECT pH FROM users_fields WHERE user_id={id_user} and session_id = {id_session};").fetchone()[0]

    if isinstance(k, float):
        return True
    elif k is None:
        return False
    else:
        return -1


def download_tech(db, machines=None):
    """
    Prise -> рrise с русской р в начале, чтобы цена была в конце из-за автосоритровки словаря
    return:: jsonifiable dict
    """
    if machines is None:
        k = db.session.execute(
            """
            SELECT vid.vid, technics.mark, tip.tip, technics.traction_class, technics.price
            FROM technics
            JOIN tip ON technics.tip=tip.id
            JOIN vid ON technics.vid=vid.id;""").fetchall()
        db.session.commit()
        return k
    else:
        if len(machines) > 1:
            machines = tuple(machines)
        else:
            machines = f"('{machines[0]}')"
        k2 = db.session.execute(
            f"""
            SELECT technics.mark, vid.vid, tip.tip, technics.traction_class, technics.price
            FROM technics
            JOIN tip ON technics.tip=tip.id
            JOIN vid ON technics.vid=vid.id
            WHERE mark IN {machines};""").fetchall()

        m = {}
        index = 0
        for entry in k2:
            m[index] = {'index': index + 1,
                        'mark': k2[index][0],
                        'vid': k2[index][1],
                        'tip': k2[index][2],
                        'traction_class': k2[index][3],
                        'рrice': k2[index][4]
                        }
            index += 1

        db.session.commit()
        return m


def download_tips(db):
    k = db.session.execute(
        """
        SELECT * FROM tip;        
        """

    ).fetchall()
    tips = [tip[1] for tip in k]
    return tips


def get_temp_by_day(average):
    DERIVATION = 4
    temp = round(random.uniform(a=average - DERIVATION, b=average + DERIVATION), 2)
    return temp


def get_temp(date, db, lgth=1):
    if lgth == 1:
        month = date.month
        month_data = db.session.execute(
            f"""
            SELECT * FROM temperature_air
            WHERE month_number = '{month}';
            """
        ).fetchall()[0]
        month_data = [float(i) for i in month_data]
        db.session.commit()
        length_of_interval = abs(month_data[3] - month_data[1])

        # 10% derivation

        DISPERSION = .1

        length_of_derivation_interval = DISPERSION * length_of_interval

        temp = round(random.uniform(a=(month_data[2] - (length_of_derivation_interval / 2)),
                                    b=(month_data[2] + (length_of_derivation_interval / 2))),
                     2)

        return temp
    else:
        # else returns a list with temps before according format [5 days before, 4 days before, 3 before,..., cur_temp]
        # with length = lgth

        prev_temps = []

        for i in range(0, lgth):
            if i != 0:
                date -= timedelta(days=1)
            t = get_temp_by_day(average=get_temp(date=date, db=db))
            prev_temps.append(t)

        return round(sum(prev_temps) / len(prev_temps), 2)


def get_humidity(db, date):
    month = date.month
    month_data = db.session.execute(
        f"""
               SELECT humidity_air FROM humidity
               WHERE month_number = '{month}';
               """
    ).fetchall()[0][0]

    db.session.commit()
    return float(str(month_data))


def get_humidity_by_day(average):
    DERIVATION = 10
    humidity = round(random.uniform(a=average - DERIVATION, b=average + DERIVATION), 2)
    return humidity


def get_dif_watercapacity(temp, time: float):
    """
    Function returns a change of watercapacity

    time: int in days

    """
    if temp > 0:
        rate = temp / 10
        dif = rate * time
    else:
        dif = 0
    return dif


def form_fields(n_opt, db, date, target=None, purpose=None, prev_culture=None, money=None):
    """ Creating initial values of fields """

    # Количество дней до конкретной даты к усреднению для поиска температуры почвы
    INTERVAL_DAY_AVERAGE = 5

    r_d = {}
    for i in range(0, n_opt):
        temp_air = get_temp(db=db, date=date)
        temp_soil = get_temp(db=db, date=date, lgth=INTERVAL_DAY_AVERAGE)
        pH = round(random.uniform(4.7, 6.5), 1)
        area = round(random.uniform(100, 200), 1)
        N = round(random.uniform(40, 80), 1)
        K = round(random.uniform(110, 200), 1)
        P = round(random.uniform(90, 150), 1)
        price = round(random.uniform(1000000, 2000000), 2)
        humidity = get_humidity(db=db, date=date)
        watercapacity = 150
        get_inside = {"area": area,
                      "temperature_air": temp_air,
                      "temperature_soil": temp_soil,
                      "pH": pH,
                      "N": N,
                      "P": P,
                      "K": K,
                      "humidity": humidity,
                      "watercapacity": watercapacity,
                      "humus": "гумус",
                      "gran_sostav": "грунулометрический состав",
                      "price": price
                      }
        r_d[i] = get_inside
    return r_d


def enough_money(db, session_id, price):
    # Ask for current money score
    score = db.session.execute(
        f"""
        SELECT money FROM sessions
        WHERE id = {session_id};
        """
    ).fetchall()
    db.session.commit()

    score = score[0][0]

    if score >= price:
        return True

    return False


def refresh_score(db, old, price, ses_id):
    new = old - price
    db.session.execute(
        f"""
        UPDATE sessions
        SET money = {new}
        WHERE id = {ses_id};
        """
    )
    db.session.commit()


def refresh_time(db, old, dif, ses_id):
    new = old + dif
    db.session.execute(
        f"""
            UPDATE sessions
            SET session_time = "{new}"
            WHERE id = {ses_id};
            """
    )
    db.session.commit()


def push_package(db, id, table, id_type='id', **kwargs):
    for name, value in kwargs.items():
        db.session.execute(
            f"""
            UPDATE {table}
            SET {name} = {value}
            WHERE {id_type} = {id};
            """
        )
    db.session.commit()


def write_history(db, user_id, session_id,
              operation_time, target_culture, operation,
              old_productivity, new_productivity, *args, **kwarg):
    db.session.execute(
        f"""
        INSERT INTO sessions_logs (user_id, session_id, operation_time, target_culture, operation_index, old_productivity, new_productivity)
        VALUES ({user_id}, {session_id}, "{operation_time}", {target_culture}, {operation}, {old_productivity}, {new_productivity})
        """)
    db.session.commit()


def form_seeds_prices(number: int, names, desc: bool = True, names_for_descriptor=None):
    if desc:
        prices = [round(random.uniform(3000, 6000), 2) for i in range(0, number)]

        pricelist = dict(zip(names, prices))

        descriptor = dict(zip(names_for_descriptor, prices))

        return {"pricelist": pricelist, "descriptor": descriptor}


def download_inventory(targets: list, db, table, user, session):
    inv = {}
    for target in targets:
        pre = db.session.execute(
            f"""SELECT {target} FROM {table} WHERE user_id = {user} and session_id = {session};"""
        )
        upd = list(chain.from_iterable(pre))
        inv[target] = upd
    db.session.commit()

    return inv


def delete_inventory(db, session_id, user_id):
    TABLES = ['users_' + table for table in ['fields', 'seeds', 'staff', 'technics']]
    for table in TABLES:
        db.session.execute(
            f"""
                DELETE FROM {table}
                WHERE session_id={session_id} and user_id = {user_id};
             """
        )
    db.session.commit()


def form_hint(db, culture: int, point_of_defeat: int, correct_points: dict):
    operation_name = db.session.execute(
        f"""
        SELECT action from actions
        WHERE id = '{point_of_defeat-1}' and culture='{culture}';
        """).fetchone()[0]

    data = correct_points.get(point_of_defeat-1)

    month = str(date(1900, data[0], 1).strftime('%B'))

    first_border = month + ' ' + str(data[1])
    second_border = month + ' ' + str(data[2])

    return "Может быть, Вам стоит попробовать провести {} в следующем промежутке: {} - {}".format(operation_name,
                                                                                                 first_border,
                                                                                                 second_border)