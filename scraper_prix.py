# Fonctionnement : assez couteux donc s'active 1 fois tous les jours / 2 jours:
# Récupère chaque composant dans "prix_composants.json"
# Le recherche sur LBC
# Prend toutes les annonces de la recherche puis calcule la moyenne des prix (en enlevant les prix absurde)
# Sauvegarde le fichier json actualisé avec les prix de la journée

# Changement de plan :
#   Cause : Lors d'une recherche (RTX 4090) par exemple, des annonces de PC sortent aussi. Pour isoler uniquement celles de cartes graphiques, c'est difficile
#   Solution : Récupérer tous les prix et description des toutes les annonces, envoyer les annonces à Groq, il me renvoie un Json de booléen -> calcul de la moyenne des prix valides

# Fonctionnement Final pour 1 composant (par exemple RTX 4090)
# 1. L'appel initial part de calculer_moyenne(comp) qui appelle filtrer_comp_seuls
# 2. filtrer_comp_seuls fait un premier tris dans les données en enlevant les annonces qui contiennent un mot exclus puis découpe les données en chunk de X annonces (ici 5) et appelle filtrer_comp_seuls_chunk sur ces chunk
# 3. filtrer_comp_seuls_chunk les envoie à Groq pour qu'il vérifie si les annonces sont bien pour un composant unique.
#       Groq renvoie les données au format json sous cette forme : "resultats": [
#   {"id": <id annonce>, "composant_seul": true},
#    {"id": <id annonce>, "composant_seul": false}
#  ]
# 4. Le resultat est ensuite renvoyé à calculer_moyenne qui fait le tris dans les annonces, applique le filtre IQR (qui élimine les valeurs trop éloignées de la moyenne : filet de sécurité), calcule le min, le max, la moyenne et le médiane


# Problème 2 : L'utilisation du modèle d'IA puissant ici n'est pas adaptée, la limite journalière de token est rapidement brulée
# Solution prendre un autre modèle plus petit : Problème : 6000 TPM (token par minute). On les dépasse facilement. Solution : mettre en place des délais adaptatifs en fonction du nombre de token utilisés + envoyer petit paquet d'annonce au lieu de tout d'un coup


from groq import Groq
import json
from dotenv import load_dotenv
import os
import scraper
import json_fun
import statistics
from groq import RateLimitError, APIError, APIConnectionError
import time

load_dotenv()

MODEL_FILTRE = "openai/gpt-oss-20b"

MOTS_EXCLUS = [
    "pc ",
    "pc gamer",
    "pc complet",
    "pc portable",
    "config complete",
    "configuration complete",
    "unité centrale",
    "unite centrale",
    "setup complet",
    "tour complete",
    "tour gaming",
]
CHUNK_SIZE = 5
client = Groq(api_key=os.environ["GROQ_API_KEY"])


def exlure_annonce(titre):
    """retourne true si le titre contient un des mots exclus"""
    titre_lower = titre.lower()
    return any(mot in titre_lower for mot in MOTS_EXCLUS)


def get_list_comp(comp):
    """Récupère la liste des annonces des composants 'comp' et renvoie un string de la forme 'id Prix Body'"""
    list_comp = scraper.search_ads(comp)
    # print("Nombre annonce à traiter : ", len(list_comp), " pour : ", comp)
    return list_comp


INSTRUCTIONS = """Tu reçois des titres d'annonces Leboncoin avec prix, pour un composant PC donné.

Réponds composant_seul = true SEULEMENT si le titre décrit la vente d'UN SEUL composant desktop, seul, complet, standard, fonctionnel, dans sa configuration d'origine.

Réponds false si le titre correspond à un de ces cas :

PC ou multi-composants :
- "PC", "config", "setup", "tour", "unité centrale", ou mention d'un CPU/RAM/carte mère/alim en plus

Laptop / non-desktop :
- Zephyrus, ROG Strix G/G14/G16, Legion, TUF Gaming (modèle laptop), Predator, "portable", "laptop"

Accessoire ou pièce seule (pas le composant lui-même) :
- boîte, carton, waterblock, ventirad, radiateur, câble, backplate, support, adaptateur, bracket

Non fonctionnel / incomplet :
- "pour pièces", "HS", "en panne", "ne fonctionne plus", "ne s'allume pas", "défectueux", "à réparer", "sans PCB", "sans GPU", "sans puce", "carte morte", "artefacts", "SAV", "sous garantie constructeur en cours de réparation"

Pas une vraie vente au prix affiché :
- "échange", "troc", "recherche", "achète", "réservé", "vendu" (déjà vendu), "annulé"

Édition non standard / non comparable au marché classique :
- "collector", "édition limitée", "moddé", "modifié", VRAM non standard (ex: 48Go sur une carte qui existe normalement en 24Go), "watercooling custom" (loop sur mesure, pas juste un waterblock ajouté)

Lot ou plusieurs unités :
- "x2", "x3", "lot de", "plusieurs", "en gros"

Prix incohérent :
- Prix anormalement bas par rapport aux autres annonces du même modèle dans la liste (ex: moins de 20% du prix médian observé) -> signale un problème (accessoire seul, arnaque, erreur de prix, échange déguisé)
- Prix à 0, prix symbolique (1€, 10€), ou clairement un placeholder

En cas de doute, même léger : false. Il vaut mieux exclure une annonce valide que laisser passer une annonce invalide.

Réponds UNIQUEMENT en JSON, sans texte autour :
{
  "resultats": [
    {"id": <id>, "composant_seul": true},
    {"id": <id>, "composant_seul": false}
  ]
}
"""


def filtre_iqr(prices):
    """Applique le filrte IQR aux prix (élimine les valeurs trop éloignées du peloton)"""
    if len(prices) < 4:
        return prices
    prices_sorted = sorted(prices)
    q1, q3 = statistics.quantiles(prices_sorted, n=4)[0], statistics.quantiles(prices_sorted, n=4)[2]
    iqr = q3 - q1
    return [p for p in prices_sorted if q1 - 1.5 * iqr <= p <= q3 + 1.5 * iqr]


def filtrer_comp_seuls_chunk(annonces, max_retries=3):
    """Filtre les composants qui sont bien seul dans l'annonce. renvoie un dictionnaire pour ce chunk de cette forme : "resultats": [
      {"id": <id annonce>, "composant_seul": true},
      {"id": <id annonce>, "composant_seul": false}
    ]"""
    text_annonces = ""
    for c in annonces:
        try:
            # body = scraper.ad_body(c["list_id"])
            titre = c["subject"]
        except Exception as e:
            print(f"Erreur récupération annonce {c['list_id']}: {e}")
            continue  # on ignore cette annonce plutôt que de planter tout le chunk
        text_annonces += f"\n\n [{c['list_id']}] Prix : {c['price'][0]}€ - {titre}"

    if not text_annonces:
        return []

    for tentative in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=MODEL_FILTRE,
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


def filtrer_comp_seuls(all_annonces):
    """Renvoie la liste des ID des composants seuls"""
    annonces = [a for a in all_annonces if not exlure_annonce(a["subject"])]

    result = []
    for i in range(0, len(annonces), CHUNK_SIZE):
        chunk = annonces[i : i + CHUNK_SIZE]
        tr = filtrer_comp_seuls_chunk(chunk)
        result += tr
    return result


def calculer_moyenne(comp, progress, tache):
    """Calcule la moyenne des annonces valides du composant 'comp'"""
    annonces = get_list_comp(comp)
    data = filtrer_comp_seuls(annonces)
    id_valides = {r["id"] for r in data if r["composant_seul"]}  # Les ID qui ont été marqué comme valide

    # print(
    #     "\n--------------------------------\n\n".join(
    #         f"{a['subject']} : {a['price']}" for a in annonces if a["list_id"] in id_valides
    #     )
    # )
    price_list = [a["price"][0] for a in annonces if a["list_id"] in id_valides]  # La liste des prix valides
    price_list_final = filtre_iqr(price_list)
    if not price_list_final:
        return {"min": None, "max": None, "mediane": None, "moyenne": None, "nb": 0}

    print("prix calculée pour : ", comp)
    progress.update(tache, advance=1)

    # [min , max , moyenne , mediane]
    return {
        "min": min(price_list_final),
        "max": max(price_list_final),
        "mediane": round(statistics.median(price_list_final), 2),
        "moyenne": round(statistics.mean(price_list_final), 2),
        "nb": len(price_list_final),
    }


def calculer_moyenne_auto(comp):
    """Calcule la moyenne des annonces valides du composant 'comp'"""
    annonces = get_list_comp(comp)
    data = filtrer_comp_seuls(annonces)
    id_valides = {r["id"] for r in data if r["composant_seul"]}  # Les ID qui ont été marqué comme valide

    price_list = [a["price"][0] for a in annonces if a["list_id"] in id_valides]  # La liste des prix valides
    price_list_final = filtre_iqr(price_list)
    if not price_list_final:
        return {"min": None, "max": None, "mediane": None, "moyenne": None, "nb": 0}

    # [min , max , moyenne , mediane]
    return {
        "min": min(price_list_final),
        "max": max(price_list_final),
        "mediane": round(statistics.median(price_list_final), 2),
        "moyenne": round(statistics.mean(price_list_final), 2),
        "nb": len(price_list_final),
    }


def update_all_price(progress, tache, tot, comp_to_scrap=["gpu", "cpu", "ram", "stockage"]):
    """Lance la mise à jour des prix actuels du marché de tous les composants de 'prix_composants.json'"""

    print("lancement du scan pour : ", comp_to_scrap, " ", tot, " élément à scanner")

    data = json_fun.read_json("prix_composants.json")
    res = json_fun.read_json("prix_marche.json") if os.path.exists("prix_marche.json") else {}

    for categorie in comp_to_scrap:
        res.setdefault(categorie, {})

        for comp in data[categorie]:
            try:
                res[categorie][comp] = calculer_moyenne(comp, progress, tache)
                print(comp, "->", res[categorie][comp])
            except Exception as e:
                print(f"✗ Erreur sur {comp}, ignoré : {e}")
                continue

            json_fun.save_json(res, "prix_marche.json")


def update_all_price_auto():
    """Lance la mise à jour des prix actuels du marché de tous les composants de 'prix_composants.json'"""

    data = json_fun.read_json("prix_composants.json")
    res = json_fun.read_json("prix_marche.json") if os.path.exists("prix_marche.json") else {}

    for categorie in ["gpu", "cpu", "ram", "stockage"]:
        res.setdefault(categorie, {})

        for comp in data[categorie]:
            try:
                res[categorie][comp] = calculer_moyenne_auto(comp)
                print(comp, "->", res[categorie][comp])
            except Exception as e:
                print(f"✗ Erreur sur {comp}, ignoré : {e}")
                continue

            json_fun.save_json(res, "prix_marche.json")
