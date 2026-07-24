from groq import Groq
import json
from dotenv import load_dotenv
import os
# Pour extraire j'utilise groq, l'api est gratuite pour mon usage. 
# Fonctionnement : 
  # Récupération description lbc -> envoie à Groq -> renvoie les composants au format json parmis une liste pré-selectionnée-> analyse et comparaison possible parmis ma base de donnée

load_dotenv()


client = Groq(api_key=os.environ["GROQ_API_KEY"])
INSTRUCTIONS = """Tu es un expert en composants PC d'occasion sur le marché français (Leboncoin).
Tu reçois une annonce décrivant un PC et tu dois extraire ses composants au format JSON strict.

RÈGLES D'EXTRACTION :
- Pour chaque composant, choisis UNE option dans la liste correspondante ci-dessous.
- Si l'annonce ne précise pas assez de détails (ex: "4060 Ti" sans préciser la VRAM), choisis la variante la plus répandue/vendue.
- Si le composant existe mais n'est pas dans la liste (modèle plus ancien, rare, ou serveur), réponds "autre : <ce que tu as compris>".
- Si le composant n'est pas mentionné du tout dans l'annonce, réponds null.
- Ne jamais inventer un prix, un état ou un composant non mentionné.

=== LISTE GPU (NVIDIA / AMD / Intel) ===
NVIDIA RTX 50 : RTX 5090, RTX 5080, RTX 5070 Ti, RTX 5070, RTX 5060 Ti 16GB, RTX 5060 Ti 8GB, RTX 5060, RTX 5050
NVIDIA RTX 40 : RTX 4090, RTX 4080 Super, RTX 4080, RTX 4070 Ti Super, RTX 4070 Ti, RTX 4070 Super, RTX 4070, RTX 4060 Ti 16GB, RTX 4060 Ti 8GB, RTX 4060
NVIDIA RTX 30 : RTX 3090 Ti, RTX 3090, RTX 3080 Ti, RTX 3080, RTX 3070 Ti, RTX 3070, RTX 3060 Ti, RTX 3060, RTX 3050
NVIDIA RTX/GTX 20 : RTX 2080 Ti, RTX 2080 Super, RTX 2080, RTX 2070 Super, RTX 2070, RTX 2060 Super, RTX 2060, GTX 1660 Ti, GTX 1660 Super, GTX 1660, GTX 1650 Super, GTX 1650
NVIDIA GTX 10 : GTX 1080 Ti, GTX 1080, GTX 1070 Ti, GTX 1070, GTX 1060 6GB, GTX 1060 3GB, GTX 1050 Ti, GTX 1050
AMD RX 9000 : RX 9070 XT, RX 9070, RX 9060 XT
AMD RX 7000 : RX 7900 XTX, RX 7900 XT, RX 7800 XT, RX 7700 XT, RX 7600 XT, RX 7600
AMD RX 6000 : RX 6800 XT, RX 6800, RX 6700 XT, RX 6650 XT, RX 6600 XT, RX 6600, RX 6500 XT
AMD RX 5000 : RX 5700 XT, RX 5700, RX 5600 XT, RX 5500 XT
Intel Arc : Arc B580, Arc B570, Arc A770, Arc A750

=== LISTE CPU (Intel / AMD) ===
Intel Core Ultra 200S (Arrow Lake) : Core Ultra 9 285K, Core Ultra 7 270K, Core Ultra 7 265K, Core Ultra 5 250K, Core Ultra 5 245K
Intel 12e-14e gen : i9-14900K, i7-14700K, i5-14600K, i9-13900K, i7-13700K, i5-13600K, i5-13400F, i7-12700K, i5-12600K, i5-12400F, i3-12100F
AMD Ryzen 9000 : Ryzen 9 9950X3D, Ryzen 9 9950X, Ryzen 9 9900X, Ryzen 7 9850X3D, Ryzen 7 9800X3D, Ryzen 7 9700X, Ryzen 5 9600X
AMD Ryzen 7000 : Ryzen 9 7950X3D, Ryzen 9 7950X, Ryzen 7 7800X3D, Ryzen 7 7700X, Ryzen 5 7600X, Ryzen 5 7600
AMD Ryzen 5000 : Ryzen 9 5900X, Ryzen 7 5800X3D, Ryzen 7 5800X, Ryzen 5 5600X, Ryzen 5 5600, Ryzen 5 5500

=== LISTE RAM ===
8GB DDR4, 16GB DDR4, 32GB DDR4, 64GB DDR4, 16GB DDR5, 32GB DDR5, 64GB DDR5, 128GB DDR5

=== LISTE STOCKAGE ===
256GB SSD, 500GB SSD, 1TB SSD, 2TB SSD, 4TB SSD, 500GB HDD, 1TB HDD, 2TB HDD, 4TB HDD

=== MARQUEUR DE VIGILANCE ===
Ce score ne sert pas à évaluer un prix exact (un système externe s'en charge), mais à repérer les annonces méritant une vérification manuelle malgré un filtre automatique. Mets un score élevé si :
- L'annonce mentionne des éléments de valeur difficiles à extraire automatiquement (facture, garantie restante, accessoires premium, upgrade récent)
- Le texte suggère une urgence de vente ou un vendeur peu au fait de la valeur de son matériel
- Les composants extraits sont incertains ("autre : ...") mais semblent potentiellement premium

interet_sur_10 : 0 = rien de notable, 10 = à vérifier manuellement en priorité
raison : une ligne expliquant le signal détecté

FORMAT DE SORTIE (JSON strict, sans texte autour) :
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
  "interet_sur_10": ...,
  "raison": "..."
}
"""




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

