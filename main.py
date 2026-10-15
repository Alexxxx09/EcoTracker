from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

# Import aggiunti per i grafici
import base64
from io import BytesIO

import matplotlib
matplotlib.use('Agg')  # Backend senza finestra grafica per server web
import matplotlib.pyplot as plt
import seaborn as sns

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

# Funzione per il calcolo delle emissioni
def calcolo(km_auto, dieta, ore_riscaldamento):
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

    impatto_dict = {
        'Trasporti (Auto)': co2_trasporti,
        'Alimentazione': co2_cibo,
        'Riscaldamento Casa': co2_casa
    }
    maggior_impatto = max(impatto_dict, key=impatto_dict.get)

    return co2_totale, maggior_impatto, impatto_dict

# Funzione per generare il grafico a barre 
def grafico_a_barre(risultato):
    categorie = ['Trasporti (Auto)', 'Alimentazione', 'Riscaldamento Casa']
    valori = [risultato['trasporti'], risultato['cibo'], risultato['casa']]

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(x=categorie, y=valori, color="#7CCF7F", ax=ax)

    ax.set_title('Emissioni di CO₂ per categoria')
    ax.set_ylabel('')
    ax.set_xlabel('')
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100)
    plt.close(fig)
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# Rotte dell'applicazione
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


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')
    else: 
        return render_template('registration.html')


@app.route('/index', methods=['GET', 'POST'])
def index():
    email = session.get('user_email')
    if not email:
        return redirect('/')

    if request.method == 'GET':
        return render_template('index.html', email=email, errore=None)

    try:
        # Lettura dati dal questionario
        km_auto = float(request.form.get('km_auto', 0))
        dieta = request.form.get('dieta')
        ore_riscaldamento = float(request.form.get('ore_riscaldamento', 0))
    except (TypeError, ValueError):
        return render_template('index.html', email=email, error="Controlla i valori inseriti")

    # Utilizzo della funzione calcolo()
    co2_totale, maggior_impatto, impatto_dict = calcolo(km_auto, dieta, ore_riscaldamento)

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
        'trasporti': round(impatto_dict['Trasporti (Auto)'], 2),
        'cibo': round(impatto_dict['Alimentazione'], 2),
        'casa': round(impatto_dict['Riscaldamento Casa'], 2),
        'maggiore': maggior_impatto
    }

    # Generazione del grafico
    grafico = grafico_a_barre(risultato)

    # Reindirizzamento a result.html con i risultati e il grafico
    return render_template('result.html', email=email, risultato=risultato, grafico=grafico)


@app.route('/history')
def history():
    email = session.get('user_email')
    if not email:
        return redirect('/')
    
    storico = TestResult.query.filter_by(user_email=email).all()
    return render_template('history.html', email=email, storico=storico)


@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
