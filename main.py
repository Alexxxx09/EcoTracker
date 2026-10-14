from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'chiave_segreta_eco_tracker'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecotracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modello Tabella Utente
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

# Modello Tabella Risultati Test
class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(100), nullable=False)
    km_auto = db.Column(db.Float, nullable=False)
    dieta = db.Column(db.String(50), nullable=False)
    ore_riscaldamento = db.Column(db.Float, nullable=False)
    co2_totale = db.Column(db.Float, nullable=False)
    maggior_impatto = db.Column(db.String(50), nullable=False)

# Creazione delle tabelle al primo avvio
with app.app_context():
    db.create_all()

# 1. Pagina di Login (Rotta /)
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        form_login = request.form.get('email')
        form_password = request.form.get('password')

        users_db = User.query.all()
        for user in users_db:
            if form_login == user.email and form_password == user.password:
                session['user_email'] = user.email
                return redirect('/index')
        
        error = 'Email o password non corrette!'
        return render_template('login.html', error=error)
    
    return render_template('login.html')

# 2. Pagina di Registrazione (Rotta /reg)
@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Registrazione nuovo utente
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')
    else: 
        return render_template('registration.html')

# 3. Dashboard + Questionario + Risultati (Rotta /index)
@app.route('/index', methods=['GET', 'POST'])
def index():
    email = session.get('user_email')
    if not email:
        return redirect('/')

    risultato = None

    if request.method == 'POST':
        # Lettura dati dal questionario (ispirato a main1.py)
        km_auto = float(request.form.get('km_auto', 0))
        dieta = request.form.get('dieta')
        ore_riscaldamento = float(request.form.get('ore_riscaldamento', 0))

        # Calcolo Stima CO2 (kg/giorno)
        co2_trasporti = km_auto * 0.19

        dieta_map = {
            'molta_carne': 7.0,
            'moderata': 4.5,
            'vegetariana': 3.0,
            'vegana': 2.0
        }
        co2_cibo = dieta_map.get(dieta, 4.0)
        co2_casa = ore_riscaldamento * 0.8

        co2_totale = round(co2_trasporti + co2_cibo + co2_casa, 2)

        # Analisi maggior impatto
        impatto_dict = {
            'Trasporti (Auto)': co2_trasporti,
            'Alimentazione': co2_cibo,
            'Riscaldamento Casa': co2_casa
        }
        maggior_impatto = max(impatto_dict, key=impatto_dict.get)

        # Salvataggio nel Database
        nuovo_test = TestResult(
            user_email=email,
            km_auto=km_auto,
            dieta=dieta,
            ore_riscaldamento=ore_riscaldamento,
            co2_totale=co2_totale,
            maggior_impatto=maggior_impatto
        )
        db.session.add(nuovo_test)
        db.session.commit()

        risultato = {
            'totale': co2_totale,
            'trasporti': round(co2_trasporti, 2),
            'cibo': round(co2_cibo, 2),
            'casa': round(co2_casa, 2),
            'maggiore': maggior_impatto
        }

    # Carica la cronologia dei test passati dell'utente
    storico = TestResult.query.filter_by(user_email=email).all()

    return render_template('index.html', email=email, risultato=risultato, storico=storico)

# 4. Logout
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)