import json
import datetime
# from random import sample

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, current_user, login_required, logout_user

from agro_game import app, db
from agro_game.forms import RegistrationForm, SessionInitForm, LoginForm, FieldBuyForm, OperationForm, StuffForm, \
    SeedForm
from agro_game.models import User, Cultures
from agro_game.other_functions import *
from agro_game.operations_rules import *


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='AgroGame')


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    registration_date=datetime.datetime.now(),
                    )
        db.session.add(user)
        db.session.commit()
        flash('Пользователь создан!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    # if current_user.is_authenticated:
    #     return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            login_user(user, remember=form.remember.data)
            return redirect(url_for("session_menu"))
        else:
            flash("Пользователя с таким именем не существует", 'danger')
    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    return render_template('account.html')


@app.route('/initializing', methods=['POST', 'GET'])
@login_required
def initializing():
    form = SessionInitForm()
    user_id = current_user.get_id()
    session['error'] = None
    if form.validate_on_submit():
        time = form_time(form.session_start.data)
        db.session.execute(
            f"""
            INSERT INTO sessions (user_id, session_time ,session_start, money, productivity, difficulty, stage)
            values ({user_id}, "{time}", "{time}", {form.money.data}, "100", {form.difficulty.data}, "0");""")
        db.session.commit()
        return redirect(url_for('session_menu'))
    return render_template('initializing.html', form=form)


@app.route("/session_menu", methods=['POST', 'GET'])
@login_required
def session_menu():
    # ses = Session.query.filter_by(user_id=current_user.get_id()).all()
    ses = db.session.execute("SELECT * from sessions WHERE user_id = {};".format(current_user.get_id())).fetchall()
    db.session.commit()
    if is_sessions(db=db, user_id=current_user.get_id()) is None:
        flash('У вас нет сессий', 'danger')
        return redirect(url_for('initializing'))
    return render_template('session_menu.html', posts=ses)


@app.route("/session/<session_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_session(session_id):
    error = session.get('error')
    if error == 'Session_validation':
        message = "Некорректно инициализированная сессия"
        mark = "danger"
        session.get('error', None)
    else:
        message = "Ваша сессия была успешно удалена!"
        mark = "success"

    db.session.execute("DELETE from sessions WHERE id = {};".format(session_id))
    db.session.execute("DELETE from sessions_logs WHERE session_id = {}".format(session_id))
    db.session.commit()

    delete_inventory(db, session_id=session_id, user_id=current_user.get_id())

    flash(message, mark)
    return redirect(url_for('session_menu'))


# ---------------- Session_layout begin -----------------------

@app.route('/session_<session_id>/field_init', methods=['POST', 'GET'])
@login_required
def field_init(session_id):
    if session_to_user(db, id_user=current_user.get_id(), id_session=session_id) is False:
        flash('Ваши сессии вот!', 'danger')
        return redirect(url_for('session_menu'))

    session['id'] = session_id
    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session_id};").fetchone()
    if is_field(db, user_id=current_user.get_id(), ses_id=session_id):
        return redirect(url_for(('session_display'), session_id=session_id))

    form = FieldBuyForm()
    # form.target_culture.choices = [(g.id, g.culture_name) for g in Cultures.query.all()][1:]
    form.target_culture.choices = [(1, 'Яровая пшеница')]
    form.prev_culture.choices = [(6, "чистый пар")] + [(g.id, g.culture_name) for g in Cultures.query.all()][1:]
    if form.validate_on_submit():
        session['fields'] = form_fields(3, db=db,
                                        date=datetime.datetime.strptime(session_query.session_time, '%Y-%m-%d'))
        db.session.execute(
            f"""
            INSERT INTO users_fields (target_culture, purpose, prev_culture, user_id, session_id, productivity)
            values({form.target_culture.data}, '{form.purpose.data}', {form.prev_culture.data}, {current_user.get_id()}, {session_id}, '100');            
            """)
        db.session.commit()
        return redirect(url_for('field_map', session_id=session_id))
    return render_template('field_init.html', actual=session_query, form=form)


@app.route('/session_<session_id>/field_map', methods=['GET', 'POST'])
@login_required
def field_map(session_id):
    if session_to_user(db, id_user=current_user.get_id(), id_session=session_id) is False:
        flash('Ваши сессии вот!', 'danger')
        return redirect(url_for('session_menu'))

    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session_id};").fetchone()
    if request.method == 'POST':
        fields_data = json.loads(request.form.getlist('result')[0])
        if enough_money(db=db, session_id=session.get('id'), price=fields_data['price']):
            db.session.execute(
                f"""
                UPDATE users_fields
                SET area={fields_data['area']}, 
                temp_air={fields_data['temperature_air']},
                temp_soil={fields_data['temperature_soil']},
                pH={fields_data['pH']}, 
                price={fields_data['price']},
                humidity={fields_data['humidity']},
                watercapacity={fields_data['watercapacity']},
                N={fields_data['N']},
                P={fields_data['P']},
                K={fields_data['K']}
                WHERE user_id={current_user.get_id()} and session_id={session.get('id')};               
                """
            )
            refresh_score(db, old=session_query.money, price=fields_data['price'], ses_id=session.get('id'))
            db.session.commit()
            session.get('fields', None)
            return redirect(url_for('session_display', session_id=session_id))
        else:
            flash('Недостаточно средств', 'danger')
            return redirect(url_for('field_map', session_id=session_id))
    return render_template('field_map.html', actual=session_query, options=session.get('fields'))


@app.template_filter('rnd')
def rnd(num):
    if num is None:
        return num
    if not isinstance(num, float):
        num = float(str(num))
    return round(num, 2)


@app.route('/session_<session_id>/session_display', methods=['POST', 'GET'])
@login_required
def session_display(session_id):
    session['id'] = session_id
    if session_to_user(db, id_user=current_user.get_id(), id_session=session_id) is False:
        flash('Ваши сессии вот!', 'danger')
        return redirect(url_for('session_menu'))

    if session_validation(db, id_user=current_user.get_id(), id_session=session_id) is False:
        session['error'] = 'Session_validation'
        return redirect(url_for('delete_session', session_id=session_id))

    productivity = db.session.execute(
        f"SELECT productivity FROM users_fields WHERE user_id={current_user.get_id()} and session_id = {session_id};").fetchone()[
        0]

    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session_id};").fetchone()

    target = db.session.execute(
        f"SELECT target_culture FROM users_fields WHERE user_id={current_user.get_id()} and session_id = {session.get('id')};").fetchone()[0]

    operations = db.session.execute(
        f"""        
            SELECT * FROM actions where culture='{target}';
            """
    ).fetchall()

    stage = int(session_query.stage)
    if stage >= len(operations):
        return redirect(url_for('victory', session_id=session_id))

    if productivity == 0:
        return redirect(url_for('defeat', session_id=session_id))


    f_list = db.session.execute(
        f"SELECT * FROM users_fields WHERE user_id={current_user.get_id()} and session_id = {session_id};").fetchall()

    staff_form = StuffForm()
    seeds_form = SeedForm()

    names_for_desc = [name[0] for name in seeds_form.quality.choices]
    names_for_page = [name[1] for name in seeds_form.quality.choices]

    seeds_data = form_seeds_prices(number=4, names=names_for_page, names_for_descriptor=names_for_desc)
    seeds_form.prices = seeds_data.get('pricelist')
    descriptor = seeds_data.get('descriptor')

    if staff_form.validate_on_submit():
        db.session.execute(
            f"""
                INSERT INTO users_staff (qualification ,specialization, session_id, user_id)
                values ({staff_form.qualification.data}, '{staff_form.specialization.data}', {session.get('id')}, {current_user.get_id()});
                """
        )
        db.session.commit()
        return redirect(url_for('session_display', session_id=session_id))

    if seeds_form.validate_on_submit():
        random.seed(2)
        if enough_money(db=db, session_id=session.get('id'), price=descriptor.get(f"{seeds_form.quality.data}")):
            db.session.execute(
                f"""
                    INSERT INTO users_seeds (quality, price, session_id, user_id)
                     values ('{seeds_form.quality.data}', '{descriptor.get(f"{seeds_form.quality.data}")}', {session.get('id')}, {current_user.get_id()});
                """
            )
            refresh_score(db, old=session_query.money, price=descriptor.get(f"{seeds_form.quality.data}"),
                          ses_id=session.get('id'))
            db.session.commit()
            return redirect(url_for('session_display', session_id=session_id))
        else:
            flash('Недостаточно средств', 'danger')
            return redirect(url_for('field_map', session_id=session_id))

    # Sometimes session's id can be empty. Solution: refresh the page;
    if session.get('id') is None:
        return redirect(url_for('session_display', session_id=session_id))
    return render_template('session_display.html',
                           actual=session_query,
                           fields_list=f_list,
                           s_form=staff_form,
                           seeds_form=seeds_form,
                           stage=stage
                           )


@app.route("/session/sleep_<timecode>", methods=['POST', 'GET'])
@login_required
def sleep(timecode):
    TIMECODES = {
        0: timedelta(days=1),
        1: timedelta(days=2),
        2: timedelta(days=3),
        3: timedelta(days=5),
        4: timedelta(days=7),
        5: timedelta(days=14),
    }

    # current_time = Session.query.filter_by(user_id=current_user.get_id(), id=session.get('id')).first().session_time
    current_time = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone().session_time
    current_time = datetime.datetime.strptime(current_time, '%Y-%m-%d').date()
    refresh_time(db, current_time, dif=TIMECODES.get(int(timecode)), ses_id=session.get('id'))
    #
    # # New time
    time_after_refresh = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone().session_time
    time_after_refresh = datetime.datetime.strptime(time_after_refresh, '%Y-%m-%d').date()

    # New field parameters
    # field_data = db.session.execute(
    #     f"SELECT * FROM users_fields WHERE user_id={current_user.get_id()} and session_id = {session.get('id')};").fetchone()
    push_package(db=db,
                 table='users_fields',
                 id=session.get('id'),

                 temp_air=get_temp_by_day(average=get_temp(db=db,
                                                           date=time_after_refresh)),

                 temp_soil=get_temp(db=db, date=time_after_refresh, lgth=5),

                 humidity=get_humidity_by_day(average=get_humidity(db=db,
                                                                   date=time_after_refresh)),

                 # watercapacity=field_data.watercapacity - get_dif_watercapacity(temp=field_data.temp_air,
                 #                                                                time=float(
                 #                                                                    TIMECODES.get(int(timecode)).days
                 #                                                                )
                 #                                                                )
                 )

    return redirect(url_for('session_display', session_id=session.get('id')))


@app.route('/session/tab', methods=['POST', 'GET'])
@login_required
def tab():
    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone()
    total = round(
        sum([float(str(instance.get('рrice'))) for instance in session.get('machines').values()]),
        2)

    if request.method == 'POST':
        if enough_money(db=db, session_id=session.get('id'), price=total):
            techs = db.session.execute(
                f"""
                SELECT * FROM technics
                WHERE mark IN {tuple(session.get('marks'))}; 
                """
            ).fetchall()
            for tech in techs:
                db.session.execute(
                    f"""
                        INSERT INTO users_technics (session_id, mark, user_id,vid, tip, traction_class, price)
                        values ({session.get('id')}, "{tech[0]}", {current_user.get_id()}, "{tech[1]}", "{tech[2]}", "{tech[3]}", {tech[4]});
                    """
                )
            refresh_score(db=db, old=session_query.money, price=total, ses_id=session.get('id'))
            db.session.commit()
            return redirect(url_for('session_display', session_id=session.get('id')))
        else:
            flash('Недостаточно средств', 'danger')
            return redirect(url_for('session_display', session_id=session.get('id')))
    return render_template('tab.html', money=session_query, total=total)


@app.route('/session/operation', methods=['POST', 'GET'])
@login_required
def operation():
    target = db.session.execute(
        f"SELECT target_culture FROM users_fields WHERE user_id={current_user.get_id()} and session_id = {session.get('id')};").fetchone()[0]
    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone()

    oper_form = OperationForm()

    operations = db.session.execute(
        f"""        
        SELECT * FROM actions where culture='{target}';
        """
    ).fetchall()

    if target == 1:
        # 1 = Яровая пшеница
        from agro_game.rules_config import YP_rule, YP_duration
        rule = ProductivityRule(YP_rule, YP_duration, 'Яровая пшеница')
        rule.set_productivity(len(operations), (session_query.difficulty / 100))

    # Shuffling result
    # operations = sample(operations, len(operations))

    techs = db.session.execute(
        f"""        
        SELECT * FROM users_technics
        WHERE user_id={current_user.get_id()} and session_id={session.get('id')};
        """
    ).fetchall()

    staff = db.session.execute(
        f"""        
            SELECT * FROM users_staff
            WHERE user_id={current_user.get_id()} and session_id={session.get('id')};
            """
    ).fetchall()

    oper_form.machines.choices = [(g[0], g[1]) for g in techs]

    oper_form.operations.choices = [(g[0], g[1]) for g in operations]

    oper_form.staff.choices = [(g[0], g[2]) for g in staff]

    old_productivity = db.session.execute(
        f"SELECT productivity FROM users_fields WHERE user_id={current_user.get_id()} and session_id = {session.get('id')};").fetchone()[
        0]

    if request.method == "POST":
        current_time = db.session.execute(
            f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone().session_time
        current_time = datetime.datetime.strptime(current_time, '%Y-%m-%d').date()

        productivity = rule.apply_rule(current_time=current_time, operation_index=int(oper_form.operations.data))
        print('NEW_PRODUCTIVITY:', productivity)
        write_history(db=db,
                      user_id=current_user.get_id(),
                      session_id=session.get('id'),
                      operation_time=current_time,
                      target_culture=target,
                      operation=int(oper_form.operations.data),
                      old_productivity=old_productivity,
                      new_productivity=productivity)
        refresh_time(db=db, old=current_time,
                     dif=rule.durations.get(int(oper_form.operations.data)),
                     ses_id=session.get('id'))
        push_package(db=db,
                     table='users_fields',
                     id=session.get('id'),
                     productivity=productivity,
                     id_type='session_id'
                     )
        push_package(db=db,
                     table='sessions',
                     id=session.get('id'),
                     stage=session_query.stage+1)
        return redirect(url_for('session_display', session_id=session.get('id')))

    return render_template('Operation.html', actual=session_query, o_form=oper_form)


@app.route('/session/inventory', methods=['POST', 'GET'])
@login_required
def inventory():
    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone()

    techs = download_inventory(targets=['mark'], db=db, table='users_technics',
                               user=current_user.get_id(),
                               session=session.get("id"))

    staff = download_inventory(targets=['specialization'], db=db, table='users_staff',
                               user=current_user.get_id(),
                               session=session.get('id'))

    seeds = download_inventory(targets=['quality'], db=db, table='users_seeds',
                               user=current_user.get_id(),
                               session=session.get('id'))

    return render_template('inventory.html', actual=session_query, techs=techs, staff=staff, seeds=seeds)


@app.route("/session/market/tech", methods=['POST', 'GET'])
@login_required
def market_tech():
    session_query = db.session.execute(
        f"SELECT * FROM sessions WHERE user_id={current_user.get_id()} and id = {session.get('id')};").fetchone()
    values = []
    tips = download_tips(db)[1:]
    tech = [tech for tech in download_tech(db)]
    if request.method == 'POST':
        machines = request.form.getlist('buy')
        session['marks'] = machines
        if len(machines) != 0:
            values = download_tech(db, machines)
            session["machines"] = values
            return redirect(url_for('tab'))
    return render_template('market_tech.html', posts=(tips, tech), val=values, actual=session_query)


@app.route("/session_<session_id>/defeat", methods=['POST', 'GET'])
@login_required
def defeat(session_id):
    if session_to_user(db, id_user=current_user.get_id(), id_session=session_id) is False:
        session['error'] = 'Session_to_user'
        flash('Ваши сессии вот!', 'danger')
        return redirect(url_for('session_menu'))

    db.session.execute("DELETE from sessions WHERE id = {};".format(session_id))

    # ??? не джойнится: в таблицы культур неправильно сгенерированы id ???
    target = db.session.execute(
        f"""
        SELECT target_culture FROM users_fields 
        WHERE user_id={current_user.get_id()} and session_id = {session.get('id')};
        """).fetchone()[0]

    culture_name = db.session.execute(
        f"""
        SELECT cultures.culture_name from cultures
        WHERE cultures.id = '{target}'
        """).fetchone()[0]

    history = db.session.execute(
        """
        SELECT sessions_logs.operation_time, actions.action, old_productivity, new_productivity FROM sessions_logs
        INNER JOIN actions ON sessions_logs.operation_index=actions.id
        WHERE session_id = {} and user_id={};
        """.format(session.get('id'), current_user.get_id())).fetchall()

    point_of_defeat = len(history)

    if target == 1:
        # 1 - Яровая пшеница
        from agro_game.rules_config import YP_rule
        message = form_hint(db=db, culture=target, point_of_defeat=point_of_defeat, correct_points=YP_rule)
    else:
        message = "Internal Error"

    db.session.execute("DELETE from sessions_logs WHERE session_id = {}".format(session_id))
    db.session.commit()
    delete_inventory(db, session_id=session_id, user_id=current_user.get_id())
    return render_template('defeat.html', history=history, culture_name=culture_name, hint=message)


@app.route("/session_<session_id>/victory", methods=['POST', 'GET'])
@login_required
def victory(session_id):
    if session_to_user(db, id_user=current_user.get_id(), id_session=session_id) is False:
        session['error'] = 'Session_to_user'
        flash('Ваши сессии вот!', 'danger')
        return redirect(url_for('session_menu'))

    db.session.execute("DELETE from sessions WHERE id = {};".format(session_id))

    # ??? не джойнится: в таблицы культур неправильно сгенерированы id ???
    target = db.session.execute(
        f"""
        SELECT target_culture FROM users_fields 
        WHERE user_id={current_user.get_id()} and session_id = {session.get('id')};
        """).fetchone()[0]

    culture_name = db.session.execute(
        f"""
        SELECT cultures.culture_name from cultures
        WHERE cultures.id = '{target}'
        """).fetchone()[0]

    history = db.session.execute(
        """
        SELECT sessions_logs.operation_time, actions.action, old_productivity, new_productivity FROM sessions_logs
        INNER JOIN actions ON sessions_logs.operation_index=actions.id
        WHERE session_id = {} and user_id={};
        """.format(session.get('id'), current_user.get_id())).fetchall()

    db.session.execute("DELETE from sessions_logs WHERE session_id = {}".format(session_id))
    db.session.commit()
    delete_inventory(db, session_id=session_id, user_id=current_user.get_id())
    return render_template('victory.html', history=history, culture_name=culture_name)
