from groq import Groq
import json
from dotenv import load_dotenv
import os
# Pour extraire j'utilise groq, l'api est gratuite pour mon usage. 
# Fonctionnement : 
  # Récupération description lbc -> envoie à Groq -> renvoie les composants au format json -> analyse et comparaison possible

load_dotenv()


client = Groq(api_key=os.environ["GROQ_API_KEY"])

INSTRUCTIONS = '''Tu reçois une annonce Leboncoin décrivant un PC. Extrait les composants et réponds UNIQUEMENT en JSON valide, sans texte autour, avec ce format exact :

{
  "cpu": "...",
  "gpu": "...",
  "ram_go": ...,
  "stockage": "...",
  "carte_mere": "...",
  "alimentation_w": ...,
  "prix": ...,
  "chance revente plus cher (%)": <estimation de Groq d'une revente plus cher que le prix d'achat>
}

Si une info n'est pas présente, mets null. Normalise les noms (ex: "3070 nvidia" -> "NVIDIA RTX 3070").'''

def extraire_composants(annonce: str) -> dict:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": annonce}
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)


annonce = """
Vends PC gamer, i5 12400f, carte graphique 3060 ti, 16go ram ddr4, 
ssd 500go + hdd 1to, alim 650w corsair, tres bon etat, 650 euros
"""

data = extraire_composants(annonce)
print(data)