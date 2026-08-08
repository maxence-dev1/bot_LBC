import requests
from dotenv import load_dotenv
import os
from annonce import Annonce
from ordinateur import Ordinateur


load_dotenv()
TOKEN = os.environ["API_TELEGRAM"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def get_prix_texte(nom_composant, valeur, prix_dict):
    if valeur is None:
        return f"{nom_composant} : —"

    if prix_dict == -1 or prix_dict is None:
        return f"{nom_composant} : {valeur} — prix inconnu"

    return (
        f"{nom_composant} : {valeur}\n"
        f"    min : {prix_dict['min']}€ | max : {prix_dict['max']}€\n"
        f"    moyenne : {prix_dict['moyenne']}€ | médiane : {prix_dict['mediane']}€"
    )


def creer_texte(PC, annonce):
    prix_annonce = annonce.price
    marge = round(PC.prix_revente_arrange["mediane"] - prix_annonce, 2)

    return f"""🔥 <b>{annonce.title}</b>

💰 Prix demandé : <b>{prix_annonce}€</b>
    Prix de revente estimé :\n  <b>min : {PC.prix_revente_arrange["min"]}€ | max : {PC.prix_revente_arrange["max"]} \n moyenne : {PC.prix_revente_arrange["moyenne"]} | mediane {PC.prix_revente_arrange["mediane"]}</b>
📈 Marge potentielle : <b>{marge}€</b>

<b>— Composants —</b>
🖥 {get_prix_texte("CPU", PC.cpu, PC.cpu_price)}

🎮 {get_prix_texte("GPU", PC.gpu, PC.gpu_price)}

🧠 {get_prix_texte("RAM", PC.ram, PC.ram_price)}

💾 {get_prix_texte("SSD", PC.stockage_ssd, PC.ssd_price)}

💿 {get_prix_texte("HDD", PC.stockage_hdd, PC.hdd_price)}

🔗 <a href="test.com">Voir l'annonce</a>

<i>{annonce.body[:300]}</i>"""


def envoyer_message(PC, annonce):
    texte = creer_texte(PC, annonce)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": texte, "parse_mode": "HTML"}  # <- ce paramètre est indispensable
    response = requests.post(url, data=params)
    return response.json()


annonce_1 = Annonce(
    id=2851234567,
    title="RTX 5080 Asus Prime oc edition",
    body="Je vends ma config gamer, très peu utilisée, achetée il y a 3 mois. Facture disponible, aucun problème technique. Vendu avec boîte d'origine.",
    price=[1100],
)

pc_1 = Ordinateur(
    cpu="Ryzen 7 7800X3D",
    gpu="RTX 5080",
    stockage_ssd="1TB SSD",
    stockage_hdd=None,
    ram="32GB DDR5",
    prix=[1100],
    opportunite=8,
    cpu_price={"min": 250, "max": 320, "mediane": 280, "moyenne": 283.5},
    gpu_price={"min": 900, "max": 1600, "mediane": 1150, "moyenne": 1181.55},
    ssd_price={"min": 50, "max": 170, "mediane": 100, "moyenne": 103.84},
    hdd_price=-1,
    ram_price={"min": 150, "max": 300, "mediane": 190, "moyenne": 195.2},
)


# --- Cas 2 : composants partiellement inconnus ("autre : ...") ---
annonce_2 = Annonce(
    id=2851234999,
    title="PC gamer Ryzen 5700G",
    body="Vends PC monté maison, fonctionne parfaitement, quelques micro-rayures sur le boîtier sinon RAS.",
    price=[750],
)

pc_2 = Ordinateur(
    cpu="autre : Ryzen 7 5700G",
    gpu="autre : Radeon RX 6750XT",
    stockage_ssd="3TB SSD",
    stockage_hdd=None,
    ram="16GB DDR4",
    prix=[750],
    opportunite=None,
    cpu_price=-1,
    gpu_price=-1,
    ssd_price=-1,
    hdd_price=-1,
    ram_price={"min": 40, "max": 90, "mediane": 70.0, "moyenne": 67.5},
)


# --- Cas 3 : quasi aucune info extraite (annonce vague) ---
annonce_3 = Annonce(
    id=2851235555,
    title="PC à vendre",
    body="PC en bon état, faire offre.",
    price=[400],
)

pc_3 = Ordinateur(
    cpu=None,
    gpu=None,
    stockage_ssd=None,
    stockage_hdd=None,
    ram=None,
    prix=[400],
    opportunite=None,
)  # tous les *_price restent à -1 par défaut


# --- Cas 4 : bonne affaire nette, config bien identifiée ---
annonce_4 = Annonce(
    id=2851236789,
    title="RTX 4090 MSI Suprim X",
    body="Vends carte graphique RTX 4090 MSI Suprim X, achetée en 2022, très bon état, sous garantie constructeur jusqu'en 2027, facture disponible.",
    price=[1400],
)

pc_4 = Ordinateur(
    cpu="i7-13700K",
    gpu="RTX 4090",
    stockage_ssd="2TB SSD",
    stockage_hdd="1TB HDD",
    ram="32GB DDR4",
    prix=[1400],
    opportunite=9,
    cpu_price={"min": 180, "max": 300, "mediane": 240, "moyenne": 245.1},
    gpu_price={"min": 1900, "max": 2500, "mediane": 1999, "moyenne": 1963.65},
    ssd_price={"min": 125, "max": 499, "mediane": 250, "moyenne": 277.16},
    hdd_price={"min": 10, "max": 55, "mediane": 25.0, "moyenne": 28.86},
    ram_price={"min": 75, "max": 200, "mediane": 150.0, "moyenne": 149.17},
)


annonces_test = [
    (annonce_1, pc_1),
    (annonce_2, pc_2),
    (annonce_3, pc_3),
    (annonce_4, pc_4),
]


for a, pc in annonces_test:
    pc.calculer_prix_revente_arrange()
    print("=" * 50)
    envoyer_message(pc, a)
