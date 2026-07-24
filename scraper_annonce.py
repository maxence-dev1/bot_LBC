import re

import requests

from annonce import Annonce

from dotenv import load_dotenv
import os
import scraper





# Peu importe la recherche Fonctionne en 2 temps : 
#     1. requête get en http : renvoie la liste des annonces 
#           Sélection des annonces non explorées et potentiellement interessantes
#     2. Visite des annonces sélectionnées :  
#           - Si annonce jamais vu (comparer avec le list_id) alors on l'explore
#           - on créé un objet annonce avec prix et description          
# 
# Lecture de la description -> 

# Ces variables peuvent expirer : pour le moment elles sont reconfigurées à la main

load_dotenv()

BUILD_ID_CACHE = None


def get_build_id():
      """Récupère (et met en cache) le buildId Next.js actuel du site Leboncoin."""
      global BUILD_ID_CACHE
      if BUILD_ID_CACHE is not None:
            return BUILD_ID_CACHE

      response = requests.get("https://www.leboncoin.fr/",
                        headers={"User-Agent": os.environ["USER_AGENT"], "Cookie": os.environ["COOKIE"]})
      match = re.search(r'"buildId":"(.*?)"', response.text)
      if match is None:
            raise Exception("buildId introuvable dans la page d'accueil Leboncoin")

      BUILD_ID_CACHE = match.group(1)
      return BUILD_ID_CACHE






def ad_body(list_id):
      """Renvoie la description de l'annonce d'id 'list_id'"""
      build_id = get_build_id()
      response = requests.get(f"https://www.leboncoin.fr/_next/data/{build_id}/ad/ordinateurs/{list_id}.json?cat=ordinateurs&id={list_id}",
                        headers= {"User-Agent" : os.environ["USER_AGENT"],
                                   "Cookie" : os.environ["COOKIE"]})
      if response.status_code != [200] :
            Exception(f"Erreur dans ad_body : status_code : {response.status_code}")
      return response.json()["pageProps"]["ad"]["body"]



def get_liste_annonce(keyword, scraped_annonces):
      """Renvoie la liste des annonces de la recherche sous forme d'objet Annonce"""
      liste_annonce = []
      for add in scraper.search_ads(keyword):
            annonce = Annonce(add["list_id"], add["subject"], ad_body(add["list_id"]), add["price"])
            if annonce.id in scraped_annonces : 
                  print("annonce num : ", annonce.id, " déjà vue")
            else :
                  scraped_annonces.append(annonce.id)

                  liste_annonce.append(annonce)
                  print("annonce num : ", annonce.id)
      return liste_annonce, scraped_annonces




