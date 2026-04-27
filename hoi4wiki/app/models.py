import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session as scopedSession, sessionmaker
from flask_login import UserMixin
from werkzeug.security import generate_password_hash as generatePasswordHash, check_password_hash as checkPasswordHash

SqlAlchemyBase = declarative_base()

fabrika = sessionmaker()
dbSession = scopedSession(fabrika)

def globalInit(dbFile='sqlite:///hoi4wiki.db?checkSameThread=False'):
    engine = sa.create_engine(dbFile)
    fabrika.configure(bind=engine)
    SqlAlchemyBase.metadata.create_all(engine)
    zapolnitSeed(engine)

def zapolnitSeed(engine):
    """Стартовый набор данных, включая категории и связи."""
    from sqlalchemy.orm import Session
    sessia = Session(engine)
    try:
        # Категории
        if not sessia.query(Category).first():
            kategorii = {}
            cats = [
                Category(nazvanie='Страны', opisanie='Государства'),
                Category(nazvanie='Механики', opisanie='Игровые механики'),
                Category(nazvanie='Юниты', opisanie='Боевые единицы'),
                Category(nazvanie='Технологии', opisanie='Исследования'),
                Category(nazvanie='Национальные фокусы', opisanie='Фокусы стран'),
                Category(nazvanie='Советы', opisanie='Гайды и стратегии')
            ]
            for cat in cats:
                sessia.add(cat)
            sessia.flush()
            for cat in cats:
                kategorii[cat.nazvanie] = cat
        else:
            kategorii = {cat.nazvanie: cat for cat in sessia.query(Category).all()}

        # Страны
        if not sessia.query(Country).first():
            strany = [
                Country(nazvanie='Германский Рейх', teg='GER', ideologiya='Фашизм',
                        istoricheskayaSpravka='Мощная военная промышленность.',
                        flagFileName='ger.png'),
                Country(nazvanie='СССР', teg='SOV', ideologiya='Коммунизм',
                        istoricheskayaSpravka='Огромная армия и ресурсы.',
                        flagFileName='sov.png'),
                Country(nazvanie='США', teg='USA', ideologiya='Демократия',
                        istoricheskayaSpravka='Сильная экономика.',
                        flagFileName='usa.png'),
                Country(nazvanie='Великобритания', teg='ENG', ideologiya='Демократия',
                        istoricheskayaSpravka='Крупный флот.',
                        flagFileName='eng.png'),
                Country(nazvanie='Япония', teg='JAP', ideologiya='Фашизм',
                        istoricheskayaSpravka='Агрессивная политика.',
                        flagFileName='jap.png')
            ]
            catStrany = kategorii.get('Страны')
            for s in strany:
                if catStrany:
                    s.category.append(catStrany)
            sessia.add_all(strany)

        # Юниты
        if not sessia.query(Unit).first():
            unity = [
                Unit(nazvanie='Пехота', tip='Пехота', ataka=20, zashita=25, skorost=4,
                     opisanie='Основная пехота.'),
                Unit(nazvanie='Лёгкий танк', tip='Бронетехника', ataka=35, zashita=15, skorost=8,
                     opisanie='Быстрые танки.'),
                Unit(nazvanie='Артиллерия', tip='Поддержка', ataka=55, zashita=5, skorost=3,
                     opisanie='Огневая поддержка.')
            ]
            catUnits = kategorii.get('Юниты')
            for u in unity:
                if catUnits:
                    u.category.append(catUnits)
            sessia.add_all(unity)

        # Механики
        if not sessia.query(Mechanic).first():
            mehaniki = [
                Mechanic(nazvanie='Боевая система', opisanie='Сухопутные сражения.'),
                Mechanic(nazvanie='Производство', opisanie='Заводы и ресурсы.')
            ]
            catMech = kategorii.get('Механики')
            for m in mehaniki:
                if catMech:
                    m.category.append(catMech)
            sessia.add_all(mehaniki)

        # Технологии
        if not sessia.query(Technology).first():
            tehnologii = [
                Technology(nazvanie='Пехотное снаряжение I', opisanie='Базовое оружие.', era='1936'),
                Technology(nazvanie='Радар', opisanie='Обнаружение.', era='1936')
            ]
            catTech = kategorii.get('Технологии')
            for t in tehnologii:
                if catTech:
                    t.category.append(catTech)
            sessia.add_all(tehnologii)

        # Национальные фокусы
        if not sessia.query(NationalFocus).first():
            fokusy = [
                NationalFocus(nazvanie='Аншлюс', opisanie='Присоединение Австрии.', stranaTeg='GER'),
                NationalFocus(nazvanie='Массовая мобилизация', opisanie='Призыв.', stranaTeg='SOV')
            ]
            catFoc = kategorii.get('Национальные фокусы')
            for f in fokusy:
                if catFoc:
                    f.category.append(catFoc)
            sessia.add_all(fokusy)

        sessia.commit()
    except Exception as z:
        sessia.rollback()
        print(f"Seed error: {z}")
    finally:
        sessia.close()

# Промежуточные таблицы
statyaCategorySvyaz = sa.Table(
    'statyaCategorySvyaz', SqlAlchemyBase.metadata,
    sa.Column('statyaId', sa.Integer, sa.ForeignKey('statya.id')),
    sa.Column('categoryId', sa.Integer, sa.ForeignKey('category.id'))
)

mechanicCategorySvyaz = sa.Table(
    'mechanicCategorySvyaz', SqlAlchemyBase.metadata,
    sa.Column('mechanicId', sa.Integer, sa.ForeignKey('mechanic.id')),
    sa.Column('categoryId', sa.Integer, sa.ForeignKey('category.id'))
)

unitCategorySvyaz = sa.Table(
    'unitCategorySvyaz', SqlAlchemyBase.metadata,
    sa.Column('unitId', sa.Integer, sa.ForeignKey('unit.id')),
    sa.Column('categoryId', sa.Integer, sa.ForeignKey('category.id'))
)

techCategorySvyaz = sa.Table(
    'techCategorySvyaz', SqlAlchemyBase.metadata,
    sa.Column('techId', sa.Integer, sa.ForeignKey('technology.id')),
    sa.Column('categoryId', sa.Integer, sa.ForeignKey('category.id'))
)

focusCategorySvyaz = sa.Table(
    'focusCategorySvyaz', SqlAlchemyBase.metadata,
    sa.Column('focusId', sa.Integer, sa.ForeignKey('nationalfocus.id')),
    sa.Column('categoryId', sa.Integer, sa.ForeignKey('category.id'))
)

countryCategorySvyaz = sa.Table(
    'countryCategorySvyaz', SqlAlchemyBase.metadata,
    sa.Column('countryId', sa.Integer, sa.ForeignKey('country.id')),
    sa.Column('categoryId', sa.Integer, sa.ForeignKey('category.id'))
)

class Yuzer(SqlAlchemyBase, UserMixin):
    __tablename__ = 'yuzer'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(64), nullable=False, unique=True)
    email = sa.Column(sa.String(120), nullable=False, unique=True)
    passwordHash = sa.Column(sa.String(128), nullable=False)
    isAdmin = sa.Column(sa.Boolean, default=False)
    statyi = orm.relationship('Statya', backref='avtor', lazy='dynamic')
    kommentarii = orm.relationship('Comment', backref='avtor', lazy='dynamic')

    @property
    def is_admin(self):
        """Совместимость с Flask-Login и шаблонами"""
        return self.isAdmin

    def setPassword(self, password):
        self.passwordHash = generatePasswordHash(password)

    def checkPassword(self, password):
        return checkPasswordHash(self.passwordHash, password)

    def __repr__(self):
        return f'<Yuzer {self.name}>'

class Category(SqlAlchemyBase):
    __tablename__ = 'category'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nazvanie = sa.Column(sa.String(64), nullable=False, unique=True)
    opisanie = sa.Column(sa.Text)

    def __repr__(self):
        return f'<Category {self.nazvanie}>'

class Statya(SqlAlchemyBase):
    __tablename__ = 'statya'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    zagolovok = sa.Column(sa.String(128), nullable=False)
    soderzhanie = sa.Column(sa.Text, nullable=False)
    dataSozdaniya = sa.Column(sa.DateTime, default=sa.func.now())
    avtorId = sa.Column(sa.Integer, sa.ForeignKey('yuzer.id'))
    category = orm.relationship('Category', secondary=statyaCategorySvyaz, backref='statya')
    kommentarii = orm.relationship('Comment', backref='statya', lazy='dynamic')

    def __repr__(self):
        return f'<Statya {self.zagolovok}>'

class Comment(SqlAlchemyBase):
    __tablename__ = 'comment'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    text = sa.Column(sa.Text, nullable=False)
    dataSozdaniya = sa.Column(sa.DateTime, default=sa.func.now())
    avtorId = sa.Column(sa.Integer, sa.ForeignKey('yuzer.id'))
    statyaId = sa.Column(sa.Integer, sa.ForeignKey('statya.id'))

    def __repr__(self):
        return f'<Comment by {self.avtorId} on {self.statyaId}>'

class Country(SqlAlchemyBase):
    __tablename__ = 'country'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nazvanie = sa.Column(sa.String(100), nullable=False, unique=True)
    teg = sa.Column(sa.String(3), nullable=False, unique=True)
    ideologiya = sa.Column(sa.String(50))
    istoricheskayaSpravka = sa.Column(sa.Text)
    flagFileName = sa.Column(sa.String(100), default='default.png')
    category = orm.relationship('Category', secondary=countryCategorySvyaz, backref='strany')

    def __repr__(self):
        return f'<Country {self.teg}>'

class Mechanic(SqlAlchemyBase):
    __tablename__ = 'mechanic'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nazvanie = sa.Column(sa.String(120), nullable=False, unique=True)
    opisanie = sa.Column(sa.Text, nullable=False)
    category = orm.relationship('Category', secondary=mechanicCategorySvyaz, backref='mechanics')

    def __repr__(self):
        return f'<Mechanic {self.nazvanie}>'

class Unit(SqlAlchemyBase):
    __tablename__ = 'unit'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nazvanie = sa.Column(sa.String(100), nullable=False, unique=True)
    tip = sa.Column(sa.String(50))
    ataka = sa.Column(sa.Integer, default=0)
    zashita = sa.Column(sa.Integer, default=0)
    skorost = sa.Column(sa.Integer, default=0)
    opisanie = sa.Column(sa.Text)
    category = orm.relationship('Category', secondary=unitCategorySvyaz, backref='units')

    def __repr__(self):
        return f'<Unit {self.nazvanie}>'

class Technology(SqlAlchemyBase):
    __tablename__ = 'technology'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nazvanie = sa.Column(sa.String(120), nullable=False, unique=True)
    opisanie = sa.Column(sa.Text)
    era = sa.Column(sa.String(20))
    category = orm.relationship('Category', secondary=techCategorySvyaz, backref='technologies')

    def __repr__(self):
        return f'<Technology {self.nazvanie}>'

class NationalFocus(SqlAlchemyBase):
    __tablename__ = 'nationalfocus'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nazvanie = sa.Column(sa.String(120), nullable=False, unique=True)
    opisanie = sa.Column(sa.Text)
    stranaTeg = sa.Column(sa.String(3))
    category = orm.relationship('Category', secondary=focusCategorySvyaz, backref='focuses')

    def __repr__(self):
        return f'<NationalFocus {self.nazvanie}>'