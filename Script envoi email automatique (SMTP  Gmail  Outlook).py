# =========================================================
#  SCRIPT ALERTES EMAIL AUTOMATIQUES (POSTGRESQL + SMTP)
# Compatible : Gmail / Outlook / SMTP entreprise
# =========================================================

import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# =========================================================
# 1. CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "database": "ma_base",
    "user": "postgres",
    "password": "motdepasse"
}

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",   # Gmail: smtp.gmail.com | Outlook: smtp.office365.com
    "smtp_port": 587,
    "email": "tonemail@gmail.com",
    "password": "mot_de_passe_app",  #  utiliser mot de passe d'application
    "destinataire": "admin@entreprise.com"
}

# =========================================================
# 2. CONNEXION DB
# =========================================================

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# =========================================================
# 3. RÉCUPÉRATION DES ALERTES NON TRAITÉES
# =========================================================

def get_alertes():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, date_alerte, type_alerte, gravite, message, data
        FROM alertes
        WHERE statut = 'NOUVELLE'
        ORDER BY date_alerte DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows

# =========================================================
# 4. ENVOI EMAIL
# =========================================================

def send_email(alerte):
    id, date, type_a, gravite, message, data = alerte

    subject = f"[ALERTE {gravite}] {type_a}"

    body = f"""
     ALERTE DÉTECTÉE 

    ID        : {id}
    Date      : {date}
    Type      : {type_a}
    Gravité   : {gravite}
    Message   : {message}

    Détails :
    {data}
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_CONFIG["email"]
    msg['To'] = EMAIL_CONFIG["destinataire"]
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
        server.send_message(msg)
        server.quit()

        print(f"[OK] Email envoyé pour alerte ID {id}")
        return True

    except Exception as e:
        print(f"[ERREUR] Email ID {id} : {e}")
        return False

# =========================================================
# 5. MARQUER COMME TRAITÉ
# =========================================================

def mark_as_sent(id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE alertes
        SET statut = 'TRAITEE'
        WHERE id = %s
    """, (id,))

    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# 6. BOUCLE AUTOMATIQUE (SURVEILLANCE)
# =========================================================

def main():
    print(" Surveillance des alertes démarrée...")

    while True:
        alertes = get_alertes()

        for alerte in alertes:
            success = send_email(alerte)
            if success:
                mark_as_sent(alerte[0])

        time.sleep(30)  # vérifie toutes les 30 secondes

# =========================================================
# 7. LANCEMENT
# =========================================================

if __name__ == "__main__":
    main()
