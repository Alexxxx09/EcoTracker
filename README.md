# EcoTracker - Calcolatore di Impronta di CO2

EcoTracker è un'applicazione web sviluppata in Python con Flask per calcolare e monitorare l'impronta di carbonio giornaliera.

L'utente risponde a un questionario sulle proprie abitudini, visualizza i risultati tramite grafici e può consultare lo storico dei test effettuati.

---

## Funzionalità

* Home page informativa sul progetto.
* Registrazione e login per la gestione dell'account.
* Questionario in 5 punti (trasporti, alimentazione, riscaldamento, uso della plastica e consumo di acqua calda).
* Risultati visualizzati tramite grafico a barre e grafico a torta.
* Pagina per la cronologia dei test salvati nel database.

---

## Tecnologie utilizzate

* Backend: Python, Flask, Flask-SQLAlchemy
* Database: SQLite
* Grafici: Matplotlib, Seaborn
* Frontend: HTML, CSS

---

## Struttura delle cartelle

* main.py: Codice principale dell'applicazione, calcoli e rotte.
* templates/: Pagine HTML del sito.
* static/: Fogli di stile CSS e immagini.
* instance/: Database creato automaticamente all'avvio dell'app.
