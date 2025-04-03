from flask import Flask, render_template, request, redirect, url_for, make_response, flash
from werkzeug.security import generate_password_hash, check_password_hash
from gestione_db import *
from AlphaBot import AlphaBot as AB

# Inizializzazione dell'applicazione Flask
app = Flask(__name__)
# Creazione di un'istanza del robot AlphaBot
alphabot = AB()
# Arresto iniziale del robot per sicurezza
alphabot.stop()
# Route principale che indirizza alla pagina di login
@app.route('/')
def index():
    # Renderizza il template della pagina di login
    return render_template('login.html')

# Route per gestire il login con supporto per metodi GET e POST
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Verifica se la richiesta è di tipo POST (invio del form)
    if request.method == 'POST':
        # Estrazione delle credenziali dal form
        username = request.form.get('e-mail')
        password = request.form.get('password')
        
        # Verifica le credenziali usando la funzione del modulo gestione_db
        if verifica_utente(username, password):
            # Se l'autenticazione ha successo, prepara la risposta e imposta un cookie
            risposta = make_response(redirect(url_for('home')))
            risposta.set_cookie('e-mail', username)
            return risposta
        
        else:
            # Se l'autenticazione fallisce, reindirizza al login
            return redirect(url_for('login'))
    
    # Se la richiesta è GET, mostra la pagina di login
    return render_template('login.html')

# Route per il logout che cancella il cookie di sessione
@app.route('/logout', methods=['GET','POST'])
def logout():
    # Prepara la risposta che reindirizza al login
    risposta = make_response(redirect(url_for('login')))
    # Elimina il cookie e-mail
    risposta.delete_cookie('e-mail')
    return risposta

# Route per la creazione di un nuovo account
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    # Verifica se la richiesta è di tipo POST (invio del form)
    if request.method == 'POST':
        # Estrazione delle credenziali dal form
        username = request.form.get('e-mail')
        password = request.form.get('password')
        
        # Tenta di aggiungere il nuovo utente tramite la funzione del modulo gestione_db
        if aggiungi_utente(username, password):
            # Se la registrazione ha successo, reindirizza al login
            return redirect(url_for('login'))
    
    # Se la richiesta è GET o la registrazione fallisce, mostra la pagina di creazione account
    return render_template('create_account.html')


# Route per la home page, protetta da autenticazione
@app.route('/home', methods=['GET', 'POST'])
def home():
    # Controlla se esiste il cookie e-mail che indica un utente autenticato
    if not request.cookies.get('e-mail'):
        # Se non c'è il cookie, reindirizza al login
        return redirect(url_for('login'))
    # Recupera l'username dal cookie
    username = request.cookies.get('e-mail')
    # Renderizza la home page passando l'username al template
    return render_template('home.html', username = username)

# Route per gestire i movimenti del robot AlphaBot
@app.route('/move', methods=['POST'])
def move():
    # Controlla se esiste il cookie e-mail che indica un utente autenticato
    if not request.cookies.get('e-mail'):
        # Se non c'è il cookie, reindirizza al login
        return redirect(url_for('login'))
    
    # Ottiene la direzione dai dati del form
    direction = request.form['direction']
    # Esegue l'azione corrispondente alla direzione
    if direction == 'forward':
        print('Forward')
        # Imposta i motori per andare avanti (velocità negativa a sinistra, positiva a destra)
        alphabot.setMotor(-50,50)
    elif direction == 'backward':
        print('Backward')
        # Imposta i motori per andare indietro (velocità positiva a sinistra, negativa a destra)
        alphabot.setMotor(50,-50)
    elif direction == 'left':
        print('Left')
        # Imposta i motori per girare a sinistra
        alphabot.setMotor(0,-25)
    elif direction == 'right':
        print('Right')
        # Imposta i motori per girare a destra
        alphabot.setMotor(25,0)
    elif direction == 'stop':
        print('Stop')
        # Ferma entrambi i motori
        alphabot.stop()
    # Restituisce la direzione come risposta
    return direction

# Verifica se lo script è eseguito direttamente e non importato
if __name__ == '__main__':
    # Avvia l'applicazione Flask in modalità debug
    app.run(host='0.0.0.0', port=5000)
