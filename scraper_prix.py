# Fonctionnement : assez couteux donc s'active 1 fois tous les jours / 2 jours:
# Récupère chaque composant dans "prix_composants.json"
# Le recherche sur LBC
# Prend toutes les annonces de la recherche puis calcule la moyenne des prix (en enlevant les prix absurde)
# Sauvegarde le fichier json actualisé avec les prix de la journée

# Changement de plan :
#   Cause : Lors d'une recherche (RTX 4090) par exemple, des annonces de PC sortent aussi. Pour isoler uniquement celles de cartes graphiques, c'est difficile
#   Solution : Récupérer tous les prix et description des toutes les annonces, envoyer les annonces à Groq, il me renvoie un Json de booléen -> calcul de la moyenne des prix valides

# Fonctionnement Final pour 1 composant (par exemple RTX 4090)
# 1. get_list_comp récupère la liste des annonces de RTX 4090 actuellement en vente
# 2. get_mean_price_comp récupère cette liste, formatte les données, les envoie à Groq pour qu'il vérifie si les annonces sont bien pour un composant unique puis il renvoie le minimum, le max, la moyenne et la médiane


import re
from groq import Groq
import requests
from annonce import Annonce
import json
from dotenv import load_dotenv
import os
import scraper_annonce
import scraper
import json_fun
import math
import statistics

load_dotenv()

prix_composants = json_fun.read_json("prix_composants.json")


load_dotenv()


def get_list_comp(comp):
    """Récupère la liste des annonces des composants 'comp' et renvoie un string de la forme 'id Prix Body'"""
    list_comp = scraper.search_ads(comp)
    return list_comp


client = Groq(api_key=os.environ["GROQ_API_KEY"])
INSTRUCTIONS = """Tu reçois une liste d'annonces Leboncoin avec leur ID et leur prix. Pour chaque annonce, détermine si elle concerne UNIQUEMENT le composant seul (pas un PC complet, pas plusieurs composants vendus ensemble).

Réponds UNIQUEMENT en JSON, sans texte autour, sous cette forme :
{
  "resultats": [
    {"id": <id annonce>, "composant_seul": true},
    {"id": <id annonce>, "composant_seul": false}
  ]
}
"""


def get_mean_price_comp(comp) -> dict:
    """Renvoie la moyenne du prix d'un composant"""

    annonces = get_list_comp(comp)  # Récupère la liste des description des annonces

    # Créé le texte qui sera envoyé à Groq au format 'list_id Prix Description'
    text_annonces = ""
    for c in annonces:
        text_annonces = text_annonces + (
            f"\n\n [{c['list_id']}] Prix : {c['price'][0]}€ - {scraper.ad_body(c['list_id'])}"
        )

    # Partie IA
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": text_annonces},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    # Récupération du resultat
    result = json.loads(completion.choices[0].message.content)["resultats"]

    id_valides = {r["id"] for r in result if r["composant_seul"]}  # Les ID qui ont été marqué comme valide

    # print([scraper.ad_body(a["list_id"]) for a in annonces if a["list_id"] in id_valides])

    price_list = [a["price"][0] for a in annonces if a["list_id"] in id_valides]  # La liste des prix valides

    # [min , max , moyenne , mediane]
    return [min(price_list), max(price_list), statistics.mean(price_list), statistics.median(price_list)]
