import scraper_annonce
import annonce
import json_fun
import analyse
import ordinateur


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
    liste_annonce_PC, scrapped_annonces = scraper_annonce.get_liste_annonce("PC gamer", scrapped_annonces)

    liste_pc = []

    # Ici je peux donc récupérer et isoler les composants d'un ordinateur et les récupérer sous forme de dictionnaire

    i = 0
    for a in liste_annonce_PC:
        i += 1
        if i == 5:
            break
        composants = analyse.extraire_composants(a.body, a.price)
        print("\n----- composant : ", composants)

        liste_pc.append(
            ordinateur.Ordinateur(
                composants["cpu"],
                composants["gpu"],
                composants["stockage SSD"],
                composants["stockage HDD"],
                composants["ram"],
                composants["prix"],
                composants["opportunite"],
                analyse.get_comp_price("cpu", composants["cpu"]),
                analyse.get_comp_price("gpu", composants["gpu"]),
                analyse.get_comp_price("stockage", composants["stockage SSD"]),
                analyse.get_comp_price("stockage", composants["stockage HDD"]),
                analyse.get_comp_price("ram", composants["ram"]),
            )
        )

    for pc in liste_pc:
        pc.calculer_prix_revente_arrange()
        pc.printPC()

    # La prochaine étape est de les comparer au prix du marché

    # Sauvegarde des annonces déjà vues
    json_fun.save_json(scrapped_annonces, "scraped_annonce.json")


main()
