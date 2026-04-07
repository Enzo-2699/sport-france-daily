import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

TODAY = datetime.today()
MONTHS_FR = {
    1:"janvier",2:"février",3:"mars",4:"avril",5:"mai",6:"juin",
    7:"juillet",8:"août",9:"septembre",10:"octobre",11:"novembre",12:"décembre"
}
TODAY_STR = f"{TODAY.day} {MONTHS_FR[TODAY.month]} {TODAY.year}"

SPORTS_OLYMPIQUES = [
    "judo","escrime","natation","athlétisme","cyclisme","handball",
    "badminton","tennis de table","rugby","volley","basket","boxe",
    "lutte","taekwondo","triathlon","aviron","canoë","voile","tir",
    "gymnastique","escalade","skateboard","surf","equitation","pentathlon",
    "water-polo","hockey","plongeon","haltérophilie"
]

def scrape_events():
    url = "https://www.equipe-france.fr/calendrier"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        return []

    events = []
    all_text = soup.get_text(separator="\n")
    lines = [l.strip() for l in all_text.split("\n") if l.strip()]

    in_today = False
    for i, line in enumerate(lines):
        if TODAY_STR in line:
            in_today = True
        if in_today:
            lower = line.lower()
            for sport in SPORTS_OLYMPIQUES:
                if sport in lower:
                    context = " ".join(lines[max(0,i-1):i+3])
                    if context not in [e["text"] for e in events]:
                        events.append({"sport": sport.capitalize(), "text": context})
                    break
            if in_today and i > 0:
                is_new_day = any(f"{d} " in lines[i] for d in range(1, 32))
                if is_new_day:
                    if TODAY_STR not in lines[i]:
                        if len(lines[i]) < 30:
                            break

    return events

def build_html(events):
    date_label = TODAY.strftime("%A %d %B %Y").capitalize()
    rows = ""
    if events:
        for e in events:
            rows += f"""
            
              {e['sport']}
              {e['text']}
            """
    else:
        rows = 'Aucun événement trouvé aujourd\'hui — vérifie equipe-france.fr'

    return f"""
    
      

        
Les Bleus en compétition aujourd'hui

        

{date_label}


      

      
        {rows}
      

      


        Source : equipe-france.fr · Généré automatiquement
      


    
    """

def send_email(html):
    sender = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_PASS"]
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Les Bleus du jour — {TODAY.strftime('%d/%m/%Y')}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print("Email envoyé !")

if __name__ == "__main__":
    events = scrape_events()
    html = build_html(events)
    send_email(html)
