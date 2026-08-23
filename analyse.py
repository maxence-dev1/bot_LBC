from groq import Groq
import json
from dotenv import load_dotenv
import os
import json_fun
# Pour extraire j'utilise groq, l'api est gratuite pour mon usage.
# Fonctionnement :
# Récupération description lbc -> envoie à Groq -> renvoie les composants au format json parmis une liste pré-selectionnée-> analyse et comparaison possible parmis ma base de donnée

load_dotenv()


MODEL_ANALYSE = "openai/gpt-oss-120b"

client = Groq(api_key=os.environ["GROQ_API_KEY"])


REFS = json_fun.read_json("prix_composants.json")


def construire_instructions():
    gpu_liste = ", ".join(REFS["gpu"])
    cpu_liste = ", ".join(REFS["cpu"])
    ram_liste = ", ".join(REFS["ram"])
    stockage_liste = ", ".join(REFS["stockage"])

    return f"""Tu es un expert en composants PC d'occasion sur le marché français (Leboncoin).
Tu reçois une annonce décrivant un PC et tu dois extraire ses composants au format JSON strict.

RÈGLES D'EXTRACTION :
- Pour chaque composant, choisis UNE option EXACTE dans la liste correspondante ci-dessous.
- Recopie la chaîne EXACTEMENT comme elle apparaît dans la liste : mêmes espaces, même casse, mêmes tirets. Ne reformule jamais, ne raccourcis jamais, n'ajoute jamais de mot.
- Si l'annonce ne précise pas assez de détails, choisis la variante la plus répandue/vendue dans la liste.
- Si le composant existe mais n'est dans aucune option de la liste, réponds "autre : <ce que tu as compris>".
- Si le composant n'est pas mentionné du tout, réponds null.
- opportunite est une note sur 10 qui évalue la bonne affaire

=== LISTE GPU (valeurs exactes autorisées) ===
{gpu_liste}

=== LISTE CPU (valeurs exactes autorisées) ===
{cpu_liste}

=== LISTE RAM (valeurs exactes autorisées) ===
{ram_liste}

=== LISTE STOCKAGE (valeurs exactes autorisées) ===
{stockage_liste}

FORMAT DE SORTIE (JSON strict, sans texte autour) :
{{
    "cpu": "...",
    "gpu": "...",
    "ram": "...",
    "stockage SSD": "...",
    "stockage HDD": "...",
    "alimentation_w": ...,
    "prix": ...,
    "etat": "...",
    "opportunite": "...",
    "raison": "..."
}}
"""


INSTRUCTIONS = construire_instructions()


def extraire_composants(body, price, progress, tache):
    """Renvoie la liste des composants normalisées de annonce sous la forme
        {
      "cpu": "...",
      "gpu": "...",
      "ram": "...",
      "stockage SSD": "...",
      "stockage HDD": "...",
      "alimentation_w": ...,
      "prix": ...,
      "etat": "...",
      "opportunite": "...",
      "raison": "..."
    }"""
    completion = client.chat.completions.create(
        model=MODEL_ANALYSE,
        messages=[{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": body}],
        response_format={"type": "json_object"},
    )
    progress.update(tache, advance=1)
    jsonf = json.loads(completion.choices[0].message.content)
    jsonf["prix"] = price
    return jsonf


def get_comp_price(classe, comp):
    """Renvoie le prix du composant 'comp' si il est dans la base de données, sinon renvoie -1"""
    data = json_fun.read_json("prix_marche.json")

    if comp not in data[classe]:
        print(f"composant inconnu : {comp}, ajouté à la base de connaissances")
        json_fun.add_comp_to_json("prix_composants.json", comp, classe)
        return -1
    else:
        return data[classe][comp]
