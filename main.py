import requests
from datetime import datetime
import pytz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

PARIS_TZ = pytz.timezone("Europe/Paris")
TODAY = datetime.now(PARIS_TZ)

MONTHS_FR = {
    1:"janvier",2:"février",3:"mars",4:"avril",5:"mai",6:"juin",
    7:"juillet",8:"août",9:"septembre",10:"octobre",11:"novembre",12:"décembre"
}
TODAY_STR = f"{TODAY.day} {MONTHS_FR[TODAY.month]} {TODAY.year}"

SPORTS_OLYMPIQUES = [
    "Judo","Escrime","Natation","Athlétisme","Cyclisme","Handball",
    "Badminton","Tennis de table","Rugby","Volley-ball","Basket-ball","Boxe",
    "Lutte","Taekwondo","Triathlon","Aviron","Canoë-kayak","Voile","Tir",
    "Gymnastique","Escalade","Skateboard","Surf","Équitation","Pentathlon",
    "Water-polo","Hockey","Plongeon","Haltérophilie","Biathlon","Ski"
]

def fetch_events():
    url = "https://www.equipe-france.fr/api/calendrier"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    events = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        for item in data:
            date_str = item.get("date","")
            if TODAY_STR in date_str or TODAY.strftime("%Y-%m-%d") in date_str:
                sport = item.get("sport","")
                title = item.get("title", item.get("name",""))
                lieu = item.get("lieu", item.get("location",""))
                heure = item.get("heure", item.get("time",""))
                events.append({
                    "sport": sport,
                    "title": title,
                    "lieu": lieu,
                    "heure": heure
                })
    except Exception:
        events = fetch_events_fallback()
    return events

def fetch_events_fallback():
    events = []
    sports_urls = {
        "Judo": "https://www.equipe-france.fr/judo/calendrier",
        "Escrime": "https://www.equipe-france.fr/escrime/calendrier",
        "Natation": "https://www.equipe-france.fr/natation/calendrier",
        "Athlétisme": "https://www.equipe-france.fr/athletisme/calendrier",
        "Handball": "https://www.equipe-france.fr/handball/calendrier",
        "Badminton": "https://www.equipe-france.fr/badminton/calendrier",
        "Rugby": "https://www.equipe-france.fr/rugby/calendrier",
        "Basket-ball": "https://www.equipe-france.fr/basket-ball/calendrier",
        "Cyclisme": "https://www.equipe-france.fr/cyclisme/calendrier",
        "Volley-ball": "https://www.equipe-france.fr/volley-ball/calendrier",
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    today_fmt = TODAY.strftime("%d/%m/%Y")
    today_alt = TODAY_STR

    for sport, url in sports_urls.items():
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if today_fmt in r.text or today_alt in r.text:
                events.append({
                    "sport": sport,
                    "title": f"Compétition en cours — voir {url}",
                    "lieu": "",
                    "heure": ""
                })
        except Exception:
            continue
    return events

def build_html(events):
    date_label = TODAY.strftime("%A %d %B %Y").capitalize()
    rows = ""
    if events:
        for e in events:
            detail = e.get("title","")
            if e.get("lieu"):
                detail += f" · {e['lieu']}"
            if e.get("heure"):
                detail += f" · {e['heure']}"
            rows += f"""
            
              {e['sport']}
              {detail}
            """
    else:
        rows = """
            Aucun événement trouvé aujourd'hui.

            Vérifier manuellement
        """

    return f"""
    
      

        
Les Bleus en compétition aujourd'hui

        

{date_label}


      

      
        {rows}
      

      


        Source : equipe-france.fr · Généré automatiquement chaque matin
      


    
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
    events = fetch_events()
    html = build_html(events)
    send_email(html)
