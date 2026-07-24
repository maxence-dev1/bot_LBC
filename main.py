import scraper_annonce
import annonce
import json_fun
import analyse


# Fonctionnement global
      # Régulièrement 1 fois toute les 2h par exemple, une session de scrapping se lance :
            # 1. Pour le premier de la journée : actualisation des prix moyens des composants
            # 2. Chargement des annonces déjà explorées depuis le fichier json [X]
            # 3. Lecture des annonces depuis plusieurs recherches ('PC', 'PC gamer'...)
            # 4. Création d'une liste d'objets Annonce [X]
            # 5. Annalyse de chaque annonce et des composants [X]
            # 6. Comparaison avec les prix du marché actuel
            # 7. Si intéressant sélectionné 
            # 8. Ecriture du fichier json


def main():
    # Chargement des annonces déjà vues
    scrapped_annonces = json_fun.read_json("scraped_annonce.json")

    # Visite des annonces non vues pour la recherche 'PC'
    liste_annonce_PC, scrapped_annonces = scraper_annonce.get_liste_annonce("PC", scrapped_annonces)

    # Ici je peux donc récupérer et isoler les composants d'un ordinateur et les récupérer sous forme de dictionnaire

    # La prochaine étape est de les comparer au prix du marché


    #Sauvegarde des annonces déjà vues
    json_fun.save_json(scrapped_annonces, "scraped_annonce.json")

main()


