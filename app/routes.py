from flask import render_template, redirect, url_for, flash, request, abort, Blueprint, jsonify
from flask_login import login_user as loginUser, logout_user as logoutUser, current_user as currentUser, login_required as loginRequired
from app.models import dbSession, Yuzer, Statya, Category, Comment, Country, Mechanic, Unit, Technology, NationalFocus
from app.forms import RegistrForm, LoginForm, StatyaForm, CommentForm, CountryForm, MechanicForm, UnitForm, TechnologyForm, NationalFocusForm
import random
import os
from werkzeug.utils import secure_filename
from datetime import datetime

main = Blueprint('main', __name__)

# Настройки загрузки изображений
UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Загрузка изображений (для CKEditor) ----------
@main.route('/uploadImage', methods=['POST'])
@loginRequired
def uploadImage():
    if 'upload' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400
    file = request.files['upload']
    if file.filename == '':
        return jsonify({'error': 'Имя файла пустое'}), 400
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({'url': url})
    return jsonify({'error': 'Недопустимый формат'}), 400

# ---------- Главная ----------
def poluchitKategorii():
    sessia = dbSession()
    return [(cat.id, cat.nazvanie) for cat in sessia.query(Category).all()]

@main.route('/')
def index():
    sessia = dbSession()
    statyi = sessia.query(Statya).order_by(Statya.dataSozdaniya.desc()).limit(10).all()
    strany = sessia.query(Country).limit(5).all()
    mehaniki = sessia.query(Mechanic).limit(5).all()
    unity = sessia.query(Unit).limit(5).all()
    tehnologii = sessia.query(Technology).limit(5).all()
    fokusStrany = sessia.query(NationalFocus.stranaTeg.distinct()).limit(5).all()
    fokusStranyList = [teg[0] for teg in fokusStrany if teg[0]]
    return render_template('index.html', title='Главная', statyi=statyi, strany=strany,
                           mehaniki=mehaniki, unity=unity, tehnologii=tehnologii,
                           fokusStranyList=fokusStranyList)

# ---------- Аутентификация ----------
@main.route('/register', methods=['GET', 'POST'])
def register():
    if currentUser.is_authenticated:
        return redirect(url_for('main.index'))
    forma = RegistrForm()
    if forma.validate_on_submit():
        sessia = dbSession()
        noviyYuzer = Yuzer(name=forma.username.data, email=forma.email.data)
        noviyYuzer.setPassword(forma.password.data)
        sessia.add(noviyYuzer)
        sessia.commit()
        flash('Регистрация успешна! Теперь войдите.')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Регистрация', forma=forma)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if currentUser.is_authenticated:
        return redirect(url_for('main.index'))
    forma = LoginForm()
    if forma.validate_on_submit():
        sessia = dbSession()
        yuzer = sessia.query(Yuzer).filter(Yuzer.email == forma.email.data).first()
        if yuzer and yuzer.checkPassword(forma.password.data):
            loginUser(yuzer, remember=forma.rememberMe.data)
            nextPage = request.args.get('next')
            return redirect(nextPage) if nextPage else redirect(url_for('main.index'))
        else:
            flash('Неверный email или пароль')
    return render_template('login.html', title='Вход', forma=forma)

@main.route('/logout')
def logout():
    logoutUser()
    return redirect(url_for('main.index'))

# ---------- Статьи ----------
@main.route('/statya/<int:id>')
def statya(id):
    sessia = dbSession()
    statya = sessia.query(Statya).get(id)
    if not statya:
        abort(404)
    kommentarii = statya.kommentarii.order_by(Comment.dataSozdaniya.desc()).all()
    formaCommenta = CommentForm()
    return render_template('article.html', title=statya.zagolovok, statya=statya,
                           kommentarii=kommentarii, formaCommenta=formaCommenta)

@main.route('/statya/new', methods=['GET', 'POST'])
@loginRequired
def newStatya():
    forma = StatyaForm()
    forma.category.choices = poluchitKategorii()
    if forma.category.data is None:
        forma.category.data = []
    if forma.validate_on_submit():
        sessia = dbSession()
        content = request.form.get('soderzhanie', '')
        if not content.strip():
            flash('Содержание не может быть пустым')
            return render_template('editArticle.html', title='Новая статья', forma=forma,
                                   legend='Создать статью', soderzhanieRaw=content)
        novaya = Statya(zagolovok=forma.zagolovok.data, soderzhanie=content, avtorId=currentUser.id)
        vybraniyeKategorii = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        novaya.category = vybraniyeKategorii
        sessia.add(novaya)
        sessia.commit()
        flash('Статья создана')
        return redirect(url_for('main.statya', id=novaya.id))
    return render_template('editArticle.html', title='Новая статья', forma=forma,
                           legend='Создать статью', soderzhanieRaw='')

@main.route('/statya/<int:id>/edit', methods=['GET', 'POST'])
@loginRequired
def editStatya(id):
    sessia = dbSession()
    statya = sessia.query(Statya).get(id)
    if not statya:
        abort(404)
    if statya.avtorId != currentUser.id and not currentUser.is_admin:
        abort(403)
    forma = StatyaForm()
    forma.category.choices = poluchitKategorii()
    if request.method == 'GET':
        forma.zagolovok.data = statya.zagolovok
        forma.category.data = [cat.id for cat in statya.category]
    else:
        if forma.category.data is None:
            forma.category.data = []
    if forma.validate_on_submit():
        content = request.form.get('soderzhanie', '')
        if not content.strip():
            flash('Содержание не может быть пустым')
            return render_template('editArticle.html', title='Редактировать статью', forma=forma,
                                   legend='Редактировать статью', statya=statya, soderzhanieRaw=content)
        statya.zagolovok = forma.zagolovok.data
        statya.soderzhanie = content
        vybraniyeKategorii = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        statya.category = vybraniyeKategorii
        sessia.commit()
        flash('Статья обновлена')
        return redirect(url_for('main.statya', id=statya.id))
    soderzhanieRaw = statya.soderzhanie if request.method == 'GET' else request.form.get('soderzhanie', '')
    return render_template('editArticle.html', title='Редактировать статью', forma=forma,
                           legend='Редактировать статью', statya=statya, soderzhanieRaw=soderzhanieRaw)

@main.route('/statya/<int:id>/delete', methods=['POST'])
@loginRequired
def deleteStatya(id):
    sessia = dbSession()
    statya = sessia.query(Statya).get(id)
    if not statya:
        abort(404)
    if statya.avtorId != currentUser.id and not currentUser.is_admin:
        abort(403)
    sessia.delete(statya)
    sessia.commit()
    flash('Статья удалена')
    return redirect(url_for('main.index'))

# ---------- Комментарии ----------
@main.route('/statya/<int:id>/comment', methods=['POST'])
@loginRequired
def addComment(id):
    sessia = dbSession()
    statya = sessia.query(Statya).get(id)
    if not statya:
        abort(404)
    forma = CommentForm()
    if forma.validate_on_submit():
        comment = Comment(text=forma.text.data, avtorId=currentUser.id, statyaId=statya.id)
        sessia.add(comment)
        sessia.commit()
        flash('Комментарий добавлен')
    return redirect(url_for('main.statya', id=id))

@main.route('/comment/<int:commentId>/delete', methods=['POST'])
@loginRequired
def deleteComment(commentId):
    sessia = dbSession()
    comment = sessia.query(Comment).get(commentId)
    if not comment:
        abort(404)
    if comment.avtorId != currentUser.id and not currentUser.is_admin:
        abort(403)
    statyaId = comment.statyaId
    sessia.delete(comment)
    sessia.commit()
    flash('Комментарий удалён')
    return redirect(url_for('main.statya', id=statyaId))

# ---------- Страны ----------
@main.route('/countries')
def countriesList():
    categoryId = request.args.get('category', type=int)
    sessia = dbSession()
    if categoryId:
        cat = sessia.query(Category).get(categoryId)
        strany = cat.strany if cat else []
    else:
        strany = sessia.query(Country).order_by(Country.nazvanie).all()
    return render_template('countriesList.html', title='Страны', strany=strany)

@main.route('/country/<string:teg>')
def countryDetail(teg):
    sessia = dbSession()
    country = sessia.query(Country).filter(Country.teg == teg.upper()).first()
    if not country:
        abort(404)
    return render_template('countryDetail.html', title=country.nazvanie, country=country)

@main.route('/admin/country/new', methods=['GET', 'POST'])
@loginRequired
def newCountry():
    if not currentUser.is_admin:
        abort(403)
    forma = CountryForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        sessia = dbSession()
        novaya = Country(
            nazvanie=forma.nazvanie.data,
            teg=forma.teg.data.upper(),
            ideologiya=forma.ideologiya.data,
            istoricheskayaSpravka=forma.istoricheskayaSpravka.data,
            flagFileName=forma.flagFileName.data
        )
        vybraniyeKategorii = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        novaya.category = vybraniyeKategorii
        sessia.add(novaya)
        sessia.commit()
        flash('Страна добавлена')
        return redirect(url_for('main.countriesList'))
    return render_template('adminCountryForm.html', title='Добавить страну', forma=forma, legend='Создать страну')

@main.route('/admin/country/<int:id>/edit', methods=['GET', 'POST'])
@loginRequired
def editCountry(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    country = sessia.query(Country).get(id)
    if not country:
        abort(404)
    forma = CountryForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        country.nazvanie = forma.nazvanie.data
        country.teg = forma.teg.data.upper()
        country.ideologiya = forma.ideologiya.data
        country.istoricheskayaSpravka = forma.istoricheskayaSpravka.data
        country.flagFileName = forma.flagFileName.data
        country.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.commit()
        flash('Страна обновлена')
        return redirect(url_for('main.countryDetail', teg=country.teg))
    elif request.method == 'GET':
        forma.nazvanie.data = country.nazvanie
        forma.teg.data = country.teg
        forma.ideologiya.data = country.ideologiya
        forma.istoricheskayaSpravka.data = country.istoricheskayaSpravka
        forma.flagFileName.data = country.flagFileName
        forma.category.data = [cat.id for cat in country.category]
    return render_template('adminCountryForm.html', title='Редактировать страну', forma=forma, legend='Редактировать страну')

# ---------- Механики ----------
@main.route('/mechanics')
def mechanicsList():
    sessia = dbSession()
    mehaniki = sessia.query(Mechanic).order_by(Mechanic.nazvanie).all()
    return render_template('mechanicsList.html', title='Механики', mehaniki=mehaniki)

@main.route('/mechanic/<int:id>')
def mechanicDetail(id):
    sessia = dbSession()
    mechanic = sessia.query(Mechanic).get(id)
    if not mechanic:
        abort(404)
    return render_template('mechanicDetail.html', title=mechanic.nazvanie, mechanic=mechanic)

@main.route('/admin/mechanic/new', methods=['GET', 'POST'])
@loginRequired
def newMechanic():
    if not currentUser.is_admin:
        abort(403)
    forma = MechanicForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        sessia = dbSession()
        novaya = Mechanic(nazvanie=forma.nazvanie.data, opisanie=forma.opisanie.data)
        novaya.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.add(novaya)
        sessia.commit()
        flash('Механика добавлена')
        return redirect(url_for('main.mechanicDetail', id=novaya.id))
    return render_template('mechanicForm.html', title='Новая механика', forma=forma, legend='Создать механику')

@main.route('/admin/mechanic/<int:id>/edit', methods=['GET', 'POST'])
@loginRequired
def editMechanic(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    mechanic = sessia.query(Mechanic).get(id)
    if not mechanic:
        abort(404)
    forma = MechanicForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        mechanic.nazvanie = forma.nazvanie.data
        mechanic.opisanie = forma.opisanie.data
        mechanic.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.commit()
        flash('Механика обновлена')
        return redirect(url_for('main.mechanicDetail', id=mechanic.id))
    elif request.method == 'GET':
        forma.nazvanie.data = mechanic.nazvanie
        forma.opisanie.data = mechanic.opisanie
        forma.category.data = [cat.id for cat in mechanic.category]
    return render_template('mechanicForm.html', title='Редактировать механику', forma=forma, legend='Редактировать механику')

@main.route('/admin/mechanic/<int:id>/delete', methods=['POST'])
@loginRequired
def deleteMechanic(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    mechanic = sessia.query(Mechanic).get(id)
    if not mechanic:
        abort(404)
    sessia.delete(mechanic)
    sessia.commit()
    flash('Механика удалена')
    return redirect(url_for('main.mechanicsList'))

# ---------- Юниты ----------
@main.route('/units')
def unitsList():
    sessia = dbSession()
    unity = sessia.query(Unit).order_by(Unit.nazvanie).all()
    return render_template('unitsList.html', title='Юниты', unity=unity)

@main.route('/unit/<int:id>')
def unitDetail(id):
    sessia = dbSession()
    unit = sessia.query(Unit).get(id)
    if not unit:
        abort(404)
    return render_template('unitDetail.html', title=unit.nazvanie, unit=unit)

@main.route('/admin/unit/new', methods=['GET', 'POST'])
@loginRequired
def newUnit():
    if not currentUser.is_admin:
        abort(403)
    forma = UnitForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        sessia = dbSession()
        gg = Unit(nazvanie=forma.nazvanie.data, tip=forma.tip.data, ataka=forma.ataka.data,
                  zashita=forma.zashita.data, skorost=forma.skorost.data, opisanie=forma.opisanie.data)
        gg.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.add(gg)
        sessia.commit()
        flash('Юнит добавлен')
        return redirect(url_for('main.unitDetail', id=gg.id))
    return render_template('unitForm.html', title='Новый юнит', forma=forma, legend='Создать юнит')

@main.route('/admin/unit/<int:id>/edit', methods=['GET', 'POST'])
@loginRequired
def editUnit(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    unit = sessia.query(Unit).get(id)
    if not unit:
        abort(404)
    forma = UnitForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        unit.nazvanie = forma.nazvanie.data
        unit.tip = forma.tip.data
        unit.ataka = forma.ataka.data
        unit.zashita = forma.zashita.data
        unit.skorost = forma.skorost.data
        unit.opisanie = forma.opisanie.data
        unit.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.commit()
        flash('Юнит обновлён')
        return redirect(url_for('main.unitDetail', id=unit.id))
    elif request.method == 'GET':
        forma.nazvanie.data = unit.nazvanie
        forma.tip.data = unit.tip
        forma.ataka.data = unit.ataka
        forma.zashita.data = unit.zashita
        forma.skorost.data = unit.skorost
        forma.opisanie.data = unit.opisanie
        forma.category.data = [cat.id for cat in unit.category]
    return render_template('unitForm.html', title='Редактировать юнит', forma=forma, legend='Редактировать юнит')

@main.route('/admin/unit/<int:id>/delete', methods=['POST'])
@loginRequired
def deleteUnit(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    unit = sessia.query(Unit).get(id)
    if not unit:
        abort(404)
    sessia.delete(unit)
    sessia.commit()
    flash('Юнит удалён')
    return redirect(url_for('main.unitsList'))

# ---------- Технологии ----------
@main.route('/technologies')
def technologiesList():
    sessia = dbSession()
    tehnologii = sessia.query(Technology).order_by(Technology.nazvanie).all()
    return render_template('technologiesList.html', title='Технологии', tehnologii=tehnologii)

@main.route('/technology/<int:id>')
def technologyDetail(id):
    sessia = dbSession()
    tech = sessia.query(Technology).get(id)
    if not tech:
        abort(404)
    return render_template('technologyDetail.html', title=tech.nazvanie, tech=tech)

@main.route('/admin/technology/new', methods=['GET', 'POST'])
@loginRequired
def newTechnology():
    if not currentUser.is_admin:
        abort(403)
    forma = TechnologyForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        sessia = dbSession()
        ez = Technology(nazvanie=forma.nazvanie.data, opisanie=forma.opisanie.data, era=forma.era.data)
        ez.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.add(ez)
        sessia.commit()
        flash('Технология добавлена')
        return redirect(url_for('main.technologyDetail', id=ez.id))
    return render_template('technologyForm.html', title='Новая технология', forma=forma, legend='Создать технологию')

@main.route('/admin/technology/<int:id>/edit', methods=['GET', 'POST'])
@loginRequired
def editTechnology(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    tech = sessia.query(Technology).get(id)
    if not tech:
        abort(404)
    forma = TechnologyForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        tech.nazvanie = forma.nazvanie.data
        tech.opisanie = forma.opisanie.data
        tech.era = forma.era.data
        tech.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.commit()
        flash('Технология обновлена')
        return redirect(url_for('main.technologyDetail', id=tech.id))
    elif request.method == 'GET':
        forma.nazvanie.data = tech.nazvanie
        forma.opisanie.data = tech.opisanie
        forma.era.data = tech.era
        forma.category.data = [cat.id for cat in tech.category]
    return render_template('technologyForm.html', title='Редактировать технологию', forma=forma, legend='Редактировать технологию')

@main.route('/admin/technology/<int:id>/delete', methods=['POST'])
@loginRequired
def deleteTechnology(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    tech = sessia.query(Technology).get(id)
    if not tech:
        abort(404)
    sessia.delete(tech)
    sessia.commit()
    flash('Технология удалена')
    return redirect(url_for('main.technologiesList'))

# ---------- Фокусы ----------
@main.route('/focuses')
def focusesList():
    sessia = dbSession()
    tegi = sessia.query(NationalFocus.stranaTeg.distinct()).all()
    stranySFocusami = []
    for teg_tuple in tegi:
        teg_val = teg_tuple[0]
        if teg_val:
            country = sessia.query(Country).filter(Country.teg == teg_val).first()
            if country:
                stranySFocusami.append(country)
            else:
                stranySFocusami.append({'teg': teg_val, 'nazvanie': teg_val})
    return render_template('focusesList.html', title='Национальные фокусы', strany=stranySFocusami)

@main.route('/focuses/<string:teg>')
def focusesByCountry(teg):
    sessia = dbSession()
    fokusy = sessia.query(NationalFocus).filter(NationalFocus.stranaTeg == teg.upper()).all()
    country = sessia.query(Country).filter(Country.teg == teg.upper()).first()
    countryName = country.nazvanie if country else f'Страна {teg}'
    return render_template('countryFocuses.html', title=f'Фокусы {countryName}', fokusy=fokusy, teg=teg.upper(), countryName=countryName)

@main.route('/focus/<int:id>')
def focusDetail(id):
    sessia = dbSession()
    focus = sessia.query(NationalFocus).get(id)
    if not focus:
        abort(404)
    return render_template('focusDetail.html', title=focus.nazvanie, focus=focus)

@main.route('/admin/focus/new', methods=['GET', 'POST'])
@loginRequired
def newFocus():
    if not currentUser.is_admin:
        abort(403)
    forma = NationalFocusForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        sessia = dbSession()
        z = NationalFocus(nazvanie=forma.nazvanie.data, opisanie=forma.opisanie.data, stranaTeg=forma.stranaTeg.data.upper())
        z.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.add(z)
        sessia.commit()
        flash('Фокус добавлен')
        return redirect(url_for('main.focusDetail', id=z.id))
    return render_template('focusForm.html', title='Новый фокус', forma=forma, legend='Создать фокус')

@main.route('/admin/focus/<int:id>/edit', methods=['GET', 'POST'])
@loginRequired
def editFocus(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    focus = sessia.query(NationalFocus).get(id)
    if not focus:
        abort(404)
    forma = NationalFocusForm()
    forma.category.choices = poluchitKategorii()
    if forma.validate_on_submit():
        focus.nazvanie = forma.nazvanie.data
        focus.opisanie = forma.opisanie.data
        focus.stranaTeg = forma.stranaTeg.data.upper()
        focus.category = sessia.query(Category).filter(Category.id.in_(forma.category.data)).all()
        sessia.commit()
        flash('Фокус обновлён')
        return redirect(url_for('main.focusDetail', id=focus.id))
    elif request.method == 'GET':
        forma.nazvanie.data = focus.nazvanie
        forma.opisanie.data = focus.opisanie
        forma.stranaTeg.data = focus.stranaTeg
        forma.category.data = [cat.id for cat in focus.category]
    return render_template('focusForm.html', title='Редактировать фокус', forma=forma, legend='Редактировать фокус')

@main.route('/admin/focus/<int:id>/delete', methods=['POST'])
@loginRequired
def deleteFocus(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    focus = sessia.query(NationalFocus).get(id)
    if not focus:
        abort(404)
    sessia.delete(focus)
    sessia.commit()
    flash('Фокус удалён')
    return redirect(url_for('main.focusesList'))

# ---------- Случайная статья ----------
@main.route('/random')
def randomArticle():
    sessia = dbSession()
    count = sessia.query(Statya.id).count()
    if count == 0:
        flash('Пока нет статей.')
        return redirect(url_for('main.index'))
    randomOffset = random.randint(0, count-1)
    randomStatya = sessia.query(Statya).order_by(Statya.id).offset(randomOffset).first()
    return redirect(url_for('main.statya', id=randomStatya.id))

# ---------- Поиск ----------
@main.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    sessia = dbSession()
    pattern = f'%{query}%'
    statyi = sessia.query(Statya).filter(Statya.zagolovok.ilike(pattern)).all()
    strany = sessia.query(Country).filter(Country.nazvanie.ilike(pattern) | Country.teg.ilike(pattern)).all()
    mehaniki = sessia.query(Mechanic).filter(Mechanic.nazvanie.ilike(pattern)).all()
    unity = sessia.query(Unit).filter(Unit.nazvanie.ilike(pattern)).all()
    tehnologii = sessia.query(Technology).filter(Technology.nazvanie.ilike(pattern)).all()
    fokusy = sessia.query(NationalFocus).filter(NationalFocus.nazvanie.ilike(pattern)).all()
    kategorii = sessia.query(Category).filter(Category.nazvanie.ilike(pattern)).all()
    return render_template('searchResults.html', title=f'Поиск: {query}', query=query,
                           statyi=statyi, strany=strany, mehaniki=mehaniki,
                           unity=unity, tehnologii=tehnologii, fokusy=fokusy, kategorii=kategorii)

# ---------- Категории ----------
@main.route('/category/<int:id>')
def category(id):
    sessia = dbSession()
    cat = sessia.query(Category).get(id)
    if not cat:
        abort(404)
    statyi = sessia.query(Statya).filter(Statya.category.contains(cat)).all()
    strany = cat.strany if hasattr(cat, 'strany') else []
    mehaniki = cat.mechanics if hasattr(cat, 'mechanics') else []
    unity = cat.units if hasattr(cat, 'units') else []
    tehnologii = cat.technologies if hasattr(cat, 'technologies') else []
    fokusy = cat.focuses if hasattr(cat, 'focuses') else []
    return render_template('category.html', title=cat.nazvanie, category=cat,
                           statyi=statyi, strany=strany, mehaniki=mehaniki,
                           unity=unity, tehnologii=tehnologii, fokusy=fokusy)

@main.route('/admin/category/new', methods=['GET', 'POST'])
@loginRequired
def newCategory():
    if not currentUser.is_admin:
        abort(403)
    if request.method == 'POST':
        nazv = request.form.get('nazvanie')
        opis = request.form.get('opisanie')
        if nazv:
            sessia = dbSession()
            cat = Category(nazvanie=nazv, opisanie=opis)
            sessia.add(cat)
            sessia.commit()
            flash('Категория добавлена')
            return redirect(url_for('main.index'))
    return render_template('adminCategoryForm.html', title='Новая категория')

# ---------- Админ-панель ----------
@main.route('/admin')
@loginRequired
def adminPanel():
    if not currentUser.is_admin:
        abort(403)
    return render_template('adminPanel.html', title='Админ-панель')

@main.route('/admin/users')
@loginRequired
def adminUsers():
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    users = sessia.query(Yuzer).order_by(Yuzer.name).all()
    return render_template('adminUsers.html', title='Управление пользователями', users=users)

@main.route('/admin/users/<int:id>/toggleadmin')
@loginRequired
def toggleAdmin(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    yuzer = sessia.query(Yuzer).get(id)
    if yuzer:
        yuzer.isAdmin = not yuzer.isAdmin
        sessia.commit()
        flash(f'Права пользователя {yuzer.name} изменены')
    return redirect(url_for('main.adminUsers'))

@main.route('/admin/users/<int:id>/delete', methods=['POST'])
@loginRequired
def deleteUser(id):
    if not currentUser.is_admin:
        abort(403)
    sessia = dbSession()
    yuzer = sessia.query(Yuzer).get(id)
    if yuzer and yuzer.id != currentUser.id:
        sessia.delete(yuzer)
        sessia.commit()
        flash('Пользователь удалён')
    return redirect(url_for('main.adminUsers'))

# ---------- Обработчики ошибок ----------
@main.app_errorhandler(404)
def notFound(error):
    return render_template('404.html'), 404

@main.app_errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403