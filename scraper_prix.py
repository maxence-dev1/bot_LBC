# Fonctionnement : assez couteux donc s'active 1 fois tous les jours / 2 jours: 
    # Récupère chaque composant dans "prix_composants.json"
    # Le recherche sur LBC
    # Prend toutes les annonces de la recherche puis calcule la moyenne des prix (en enlevant les prix absurde)
    # Sauvegarde le fichier json actualisé avec les prix de la journée

import re

import requests

from annonce import Annonce

from dotenv import load_dotenv
import os
import scraper_annonce
import scraper
import json_fun

load_dotenv()

prix_composants = json_fun.read_json("prix_composants.json")



def get_mean_comp(comp):
    # Problème : sur LBC quand tu cherches un composant, tu tombes aussi sur les PC qui le contienne. Solution ajouter des filtres. Sinon, vérifier dans la description si d'autres composants sont mentionnés
    list_comp = scraper.search_ads(comp)
    for c in list_comp:
        print(c["price"])

get_mean_comp(prix_composants["gpu"][0])