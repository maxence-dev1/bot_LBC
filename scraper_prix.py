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

# Problème 2 : L'utilisation du modèle d'IA puissant ici n'est pas adaptée, la limite journalière de token est rapidement brulée
# Solution prendre un autre modèle plus petit : Problème : 6000 TPM (token par minute). On les dépasse facilement. Solution : mettre en place des délais adaptatifs en fonction du nombre de token utilisés + envoyer petit paquet d'annonce au lieu de tout d'un coup

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
from groq import RateLimitError, APIError, APIConnectionError
import time

load_dotenv()

prix_composants = json_fun.read_json("prix_composants.json")


load_dotenv()


def get_list_comp(comp):
    """Récupère la liste des annonces des composants 'comp' et renvoie un string de la forme 'id Prix Body'"""
    list_comp = scraper.search_ads(comp)
    print("Nombre annonce à traiter : ", len(list_comp), " pour : ", comp)
    return list_comp


client = Groq(api_key=os.environ["GROQ_API_KEY"])
INSTRUCTIONS = """Tu reçois une liste d'annonces Leboncoin avec leur ID et leur prix. Pour chaque annonce, détermine si elle concerne UNIQUEMENT le composant seul fonctionnel, vendu seul, sans aucun autre composant avec.

Marque composant_seul = false si l'annonce mentionne, même en passant, un AUTRE composant du PC (CPU, carte mère, RAM, alimentation, boîtier, autre GPU...) en plus du composant recherché. Marque aussi false si l'annonce est un PC complet, une config, une tour, ou vend plusieurs pièces ensemble.

Exemples :
- "RTX 3070 MSI Gaming X, très bon état, ventirad nickel" -> true (composant seul, "ventirad" fait partie du GPU lui-même, pas un autre composant)
- "Vends PC gamer i5 12400f + RTX 3070 + 16go ram, tout fonctionne" -> false (PC complet, plusieurs composants)
- "RTX 3070 + alimentation 650w offerte" -> false (deux composants vendus ensemble, même si l'un est "offert")
- "Carte mère MSI + RTX 3070, vendu ensemble uniquement" -> false (deux composants)
- "i5-12400F seul, sans ventirad ni boite" -> true (composant seul, précise même qu'il manque des accessoires)
- "RTX 3070 pour pièces, ne s'allume plus" -> false (pour pièces, non fonctionnel)

Réponds UNIQUEMENT en JSON, sans texte autour, sous cette forme :
{
  "resultats": [
    {"id": <id annonce>, "composant_seul": true},
    {"id": <id annonce>, "composant_seul": false}
  ]
}
"""


def filtrer_comp_seuls_chunk(annonces, max_retries=3):
    text_annonces = ""
    for c in annonces:
        try:
            body = scraper.ad_body(c["list_id"])
        except Exception as e:
            print(f"Erreur récupération annonce {c['list_id']}: {e}")
            continue  # on ignore cette annonce plutôt que de planter tout le chunk
        text_annonces += f"\n\n [{c['list_id']}] Prix : {c['price'][0]}€ - {body}"

    if not text_annonces:
        return []

    for tentative in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": text_annonces}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            return json.loads(completion.choices[0].message.content)["resultats"]

        # Gestion des erreurs
        except RateLimitError:
            attente = 30 * (tentative + 1)
            print(f"Rate limit atteint, pause de {attente}s (tentative {tentative + 1}/{max_retries})")
            time.sleep(attente)

        except (APIConnectionError, APIError) as e:
            print(f"Erreur API Groq : {e}, nouvelle tentative dans 10s")
            time.sleep(10)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Réponse Groq mal formée : {e}")
            return []  # on abandonne ce chunk plutôt que de planter tout le script

    print(f"Échec après {max_retries} tentatives, chunk ignoré")
    return []


def filtrer_comp_seuls(annonces) -> dict:
    """Renvoie la moyenne du prix d'un composant"""

    # Récupère la liste des description des annonces

    result = []
    for i in range(0, len(annonces), 10):
        chunk = annonces[i : i + 10]
        tr = filtrer_comp_seuls_chunk(chunk)
        result += tr
    return result


def calculer_moyenne(comp):
    annonces = get_list_comp(comp)
    data = filtrer_comp_seuls(annonces)
    id_valides = {r["id"] for r in data if r["composant_seul"]}  # Les ID qui ont été marqué comme valide

    # print(
    #     "--------------------------------\n\n".join(
    #         scraper.ad_body(a["title"]) for a in annonces if a["list_id"] in id_valides
            
    #     )
    # )

    price_list = [a["price"][0] for a in annonces if a["list_id"] in id_valides]  # La liste des prix valides

    print("prix calculée pour : ", comp)

    # [min , max , moyenne , mediane]
    return {
        "min": min(price_list),
        "max": max(price_list),
        "mediane": round(statistics.median(price_list), 2),
        "moyenne": round(statistics.mean(price_list), 2),
        "nb": len(price_list),
    }


def update_all_price():
    data = json_fun.read_json("prix_composants.json")
    res = json_fun.read_json("prix_marche.json") if os.path.exists("prix_marche.json") else {}

    for categorie in ["gpu", "cpu", "ram", "stockage"]:
        res.setdefault(categorie, {})

        for comp in data[categorie]:
            try:
                res[categorie][comp] = calculer_moyenne(comp)
                print(comp, "->", res[categorie][comp])
            except Exception as e:
                print(f"✗ Erreur sur {comp}, ignoré : {e}")
                continue

            json_fun.save_json(res, "prix_marche.json")  # sauvegarde après CHAQUE composant


update_all_price()
