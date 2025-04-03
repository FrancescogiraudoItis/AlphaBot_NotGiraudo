import sqlite3  
from werkzeug.security import check_password_hash, generate_password_hash 

# Funzione per verificare se un utente esiste nel database e se la password è corretta
def verifica_utente(username, password):
    conn = sqlite3.connect('users.db')  # Connessione al database SQLite
    cur = conn.cursor()  # Creazione del cursore per eseguire query SQL
    
    # Cerca l'utente nel database tramite il suo username
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    result = cur.fetchone()  # Recupera il primo risultato della query
    
    conn.close()  # Chiude la connessione al database
    
    # Controlla se l'utente esiste e se la password corrisponde a quella salvata nel database
    if result and result[1] == username and result[2] == password:
        return True  # L'utente è autenticato con successo
    
    return False  # fallito

# Funzione per aggiungere un nuovo utente al database
def aggiungi_utente(username, password):
    conn = sqlite3.connect('users.db')  # Connessione al database
    cur = conn.cursor()  # Creazione del cursore
    
    # Inserisce un nuovo utente con username e password nel database
    cur.execute('INSERT INTO users(username, password) VALUES(?,?)', (username, password))
    
    conn.commit()  # Salva le modifiche nel database
    conn.close()  # Chiude la connessione
    
    return True  # successo
