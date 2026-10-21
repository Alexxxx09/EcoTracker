from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

# Import per la gestione dei grafici
import base64
from io import BytesIO

import matplotlib
matplotlib.use('Agg')  
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
    uso_plastica = db.Column(db.String(50), nullable=False)
    minuti_doccia = db.Column(db.Float, nullable=False)
    co2_totale = db.Column(db.Float, nullable=False)
    maggior_impatto = db.Column(db.String(50), nullable=False)

# Creazione delle tabelle al primo avvio
with app.app_context():
    db.create_all()

# Funzione per il calcolo delle emissioni
def calcolo(km_auto, dieta, ore_riscaldamento, uso_plastica, minuti_doccia):
    co2_trasporti = km_auto * 0.19

    dieta_map = {
        'molta_carne': 7.0,
        'moderata': 4.5,
        'vegetariana': 3.0,
        'vegana': 2.0
    }
    co2_cibo = dieta_map.get(dieta, 4.0)
    co2_casa = ore_riscaldamento * 0.8

    # Calcolo per l'uso della plastica (~0.25 kg CO2 al giorno per uso prevalente di monouso)
    co2_plastica = 0.25 if uso_plastica == 'monouso' else 0.02

    # Calcolo per l'acqua calda della doccia (~0.05 kg CO2 per minuto)
    co2_doccia = minuti_doccia * 0.05

    co2_totale = round(co2_trasporti + co2_cibo + co2_casa + co2_plastica + co2_doccia, 2)

    impatto_dict = {
        'Trasporti (Auto)': co2_trasporti,
        'Alimentazione': co2_cibo,
        'Riscaldamento Casa': co2_casa,
        'Consumo Plastica': co2_plastica,
        'Doccia e Acqua Calda': co2_doccia
    }
    maggior_impatto = max(impatto_dict, key=impatto_dict.get)

    return co2_totale, maggior_impatto, impatto_dict

# Funzione 1: Grafico a barre
def grafico_a_barre(risultato):
    categorie = ['Trasporti', 'Cibo', 'Riscaldamento', 'Plastica', 'Doccia']
    valori = [
        risultato['trasporti'], 
        risultato['cibo'], 
        risultato['casa'], 
        risultato['plastica'], 
        risultato['doccia']
    ]

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=categorie, y=valori, palette="Greens_d", ax=ax)

    ax.set_title('Emissioni per Categoria (kg CO₂)', fontsize=12, fontweight='bold')
    ax.set_ylabel('kg CO₂')
    ax.set_xlabel('')
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100)
    plt.close(fig)
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# Funzione 2: Grafico a torta
def grafico_a_torta(risultato):
    categorie = ['Trasporti', 'Cibo', 'Riscaldamento', 'Plastica', 'Doccia']
    valori = [
        risultato['trasporti'], 
        risultato['cibo'], 
        risultato['casa'], 
        risultato['plastica'], 
        risultato['doccia']
    ]

    valori_filtrati = []
    categorie_filtrate = []
    for v, c in zip(valori, categorie):
        if v > 0:
            valori_filtrati.append(v)
            categorie_filtrate.append(c)

    fig, ax = plt.subplots(figsize=(6, 4))
    colori = sns.color_palette("YlGn", len(valori_filtrati))
    
    ax.pie(valori_filtrati, labels=categorie_filtrate, autopct='%1.1f%%', startangle=140, colors=colori)
    ax.set_title('Percentuale di Impatto sul Totale', fontsize=12, fontweight='bold')
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100)
    plt.close(fig)
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# ROTTE 

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
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
        return redirect('/login')
    else: 
        return render_template('registration.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    email = session.get('user_email')
    if not email:
        return redirect('/login')

    if request.method == 'GET':
        return render_template('index.html', email=email, errore=None)

    try:
        # Lettura di tutti i dati dal questionario
        km_auto = float(request.form.get('km_auto', 0))
        dieta = request.form.get('dieta')
        ore_riscaldamento = float(request.form.get('ore_riscaldamento', 0))
        uso_plastica = request.form.get('uso_plastica', 'borraccia')
        minuti_doccia = float(request.form.get('minuti_doccia', 5))
    except (TypeError, ValueError):
        return render_template('index.html', email=email, error="Controlla i valori inseriti")

    # Calcolo
    co2_totale, maggior_impatto, impatto_dict = calcolo(km_auto, dieta, ore_riscaldamento, uso_plastica, minuti_doccia)

    # Salvataggio nel DB
    nuovo_test = TestResult(
        user_email=email,
        km_auto=km_auto,
        dieta=dieta,
        ore_riscaldamento=ore_riscaldamento,
        uso_plastica=uso_plastica,
        minuti_doccia=minuti_doccia,
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
        'plastica': round(impatto_dict['Consumo Plastica'], 2),
        'doccia': round(impatto_dict['Doccia e Acqua Calda'], 2),
        'maggiore': maggior_impatto
    }

    # Generazione di entrambi i grafici
    grafico_barre = grafico_a_barre(risultato)
    grafico_torta = grafico_a_torta(risultato)

    return render_template('result.html', email=email, risultato=risultato, grafico_barre=grafico_barre, grafico_torta=grafico_torta)

@app.route('/history')
def history():
    email = session.get('user_email')
    if not email:
        return redirect('/login')
    
    storico = TestResult.query.filter_by(user_email=email).all()
    return render_template('history.html', email=email, storico=storico)

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
