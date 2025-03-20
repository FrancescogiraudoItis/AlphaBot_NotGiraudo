from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify  # Importa le librerie necessarie di Flask
import sqlite3  # Per gestire la connessione e le operazioni sul database SQLite
import os  # Per lavorare con i percorsi dei file
import jwt  # Per la gestione dei JSON Web Token (JWT)
import datetime  # Per gestire le date e gli orari
import gpiozero  # Per la gestione dei pin GPIO
from gpiozero.pins.mock import MockFactory  # Simula i GPIO su Windows
from time import sleep  # Per aggiungere ritardi (non usato nel codice attuale)

#Simulazione GPIO per Windows (utile per test su macchina senza GPIO fisici)
gpiozero.Device.pin_factory = MockFactory()

app = Flask(__name__)  # Crea l'app Flask
app.secret_key = 'supersecretkey'  # Chiave segreta per la gestione delle sessioni in Flask
SECRET_KEY = 'secret_key'  # Chiave segreta per la creazione dei JWT

# Percorso del database SQLite (nella cartella 'Database')
db_path = os.path.join(os.path.dirname(__file__), "Database", "GiraudoNot.db")

# Funzione per ottenere una connessione al database
def get_db_connection():
    conn = sqlite3.connect(db_path)  # Connessione al database
    conn.row_factory = sqlite3.Row  # Permette di trattare i risultati delle query come oggetti (riga come dizionario)
    return conn

# Funzione per creare la tabella 'users' se non esiste
def create_users_table():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,  # ID autoincrementale
                        email TEXT UNIQUE NOT NULL,  # Email unica e non nulla
                        password TEXT NOT NULL)''')  # Password non nulla
        conn.commit()  # Salva le modifiche al database

create_users_table()  # Crea la tabella degli utenti all'avvio dell'app

# Simulazione del robot per test su Windows
class SimulatedRobot:
    def __init__(self):
        self.status = "stopped"  # Lo stato iniziale del robot è fermo

    def forward(self):
        self.status = "moving forward"  # Cambia lo stato a "avanti"
        print("Robot avanti")  # Stampa il comando

    def backward(self):
        self.status = "moving backward"  # Cambia lo stato a "indietro"
        print("Robot indietro")  # Stampa il comando

    def left(self):
        self.status = "turning left"  # Cambia lo stato a "gira a sinistra"
        print("Robot gira a sinistra")  # Stampa il comando

    def right(self):
        self.status = "turning right"  # Cambia lo stato a "gira a destra"
        print("Robot gira a destra")  # Stampa il comando

    def stop(self):
        self.status = "stopped"  # Cambia lo stato a "fermo"
        print("Robot fermo")  # Stampa il comando

# Usa il robot simulato per testare su Windows
robot = SimulatedRobot()  # Crea una nuova istanza del robot simulato

# Rotta principale che reindirizza alla pagina di login
@app.route('/')
def home():
    return redirect(url_for('login'))  # Reindirizza alla rotta di login

# Rotta per il login degli utenti (sia GET che POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Se il metodo è POST, l'utente sta cercando di fare login
        email = request.form['e-mail']  # Ottieni l'email dal modulo
        password = request.form['password']  # Ottieni la password dal modulo
        
        with get_db_connection() as conn:
            # Cerca l'utente nel database
            user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
            
            if user:  # Se l'utente è trovato
                # Crea un token JWT per l'autenticazione
                token = jwt.encode({'user_id': user['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)}, SECRET_KEY, algorithm='HS256')
                resp = make_response(redirect(url_for('controller')))  # Crea una risposta di redirect alla pagina del controller
                resp.set_cookie('token', token, max_age=60*60*24*30, httponly=True)  # Imposta il token come cookie
                return resp  # Restituisce la risposta con il cookie
            else:
                return "Errore: credenziali non valide", 401  # Se le credenziali non sono valide

    return render_template('login.html')  # Restituisce la pagina di login se il metodo è GET

# Rotta per la registrazione di nuovi utenti (sia GET che POST)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Se il metodo è POST, l'utente sta cercando di registrarsi
        email = request.form['e-mail']  # Ottieni l'email dal modulo
        password = request.form['password']  # Ottieni la password dal modulo
        
        with get_db_connection() as conn:
            try:
                # Inserisce un nuovo utente nel database
                conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
                conn.commit()  # Salva le modifiche al database
                return redirect(url_for('login'))  # Reindirizza alla pagina di login
            except sqlite3.IntegrityError:
                return "Errore: Email già registrata", 400  # Se l'email è già registrata, mostra un errore
    
    return render_template('register.html')  # Restituisce la pagina di registrazione se il metodo è GET

# Funzione per decodificare il token JWT e verificarne la validità
def decode_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])  # Decodifica il token
        return decoded  # Restituisce il token decodificato
    except jwt.ExpiredSignatureError:  # Se il token è scaduto
        return None
    except jwt.InvalidTokenError:  # Se il token è invalido
        return None

# Rotta per il controller, che richiede autenticazione tramite token JWT
@app.route('/controller')
def controller():
    token = request.cookies.get('token')  # Ottieni il token dai cookie
    if token:  # Se il token è presente
        decoded_token = decode_token(token)  # Decodifica il token
        if decoded_token:  # Se il token è valido
            return render_template('controller.html')  # Mostra la pagina del controller
    return redirect(url_for('login'))  # Se non autenticato, reindirizza alla pagina di login

# Rotta per ricevere e gestire i comandi del robot
@app.route('/command', methods=['POST'])
def command():
    token = request.cookies.get('token')  # Ottieni il token dai cookie
    if token:  # Se il token è presente
        decoded_token = decode_token(token)  # Decodifica il token
        if decoded_token:  # Se il token è valido
            data = request.get_json()  # Ottieni i dati JSON dal corpo della richiesta
            if not data or 'command' not in data:  # Se il comando non è valido
                return jsonify({"error": "Comando non valido"}), 400  # Risposta di errore
            
            command = data['command']  # Ottieni il comando
            # Esegui il comando sul robot
            if command == 'forward':
                robot.forward()
            elif command == 'backward':
                robot.backward()
            elif command == 'left':
                robot.left()
            elif command == 'right':
                robot.right()
            elif command == 'stop':
                robot.stop()
            else:
                return jsonify({"error": "Comando sconosciuto"}), 400  # Comando sconosciuto
            
            return jsonify({"success": True, "command": command, "status": robot.status})  # Restituisce lo stato del robot
    
    return jsonify({"error": "Autenticazione richiesta"}), 401  # Se non autenticato, richiede login

# Rotta per il logout, che rimuove il token
@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect(url_for('login')))  # Crea una risposta di redirect al login
    resp.delete_cookie('token')  # Rimuove il cookie del token
    return resp  # Restituisce la risposta

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)  # Avvia l'app Flask sulla porta 5000
    finally:
        robot.stop()  # Ferma il robot in caso di errore
