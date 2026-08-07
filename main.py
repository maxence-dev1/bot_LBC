import scraper_annonce
import annonce
import json_fun
import scraper_prix
import analyse
import ordinateur
import time
import questionary
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

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


def lancer_scrap_prix(comp):

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        data = json_fun.read_json("prix_composants.json")

        tot = sum(len(v) for v in data.values()) if comp == "tout" else len(data[comp])

        tache = progress.add_task(f"[cyan] mise à jour des prix du marché en cours...", total=tot)

        scraper_prix.update_all_price(progress, tache, tot, [comp])

    print(f"\n[bold green]✓[/bold green] mise à jour des prix du marché terminée avec succès !\n")


def lancer_scrap_PC(recherche):
    scrapped_annonces = json_fun.read_json("scraped_annonce.json")

    console = Console()

    with console.status("[bold cyan]Recherche des annonces en cours, veuillez patienter...", spinner="dots"):
        liste_annonce_PC, scrapped_annonces = scraper_annonce.get_liste_annonce(recherche, scrapped_annonces)

    console.print("[bold green]✓ Recherche des annonces terminé !")

    progress = Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn()
    )

    liste_pc = []
    tache = progress.add_task(f"[cyan] scrapping des annonces : {recherche} en cours...", total=len(liste_annonce_PC))

    for a in liste_annonce_PC:
        composants = analyse.extraire_composants(a.body, a.price, progress, tache)

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

    liste_pc_interessants = []
    for pc in liste_pc:
        inte, prix = pc.calculer_prix_revente_arrange()

        pc.printPC()

        if inte:
            liste_pc_interessants.append(pc)

    print("liste des pc interessants : ")
    for pc in liste_pc_interessants:
        pc.PrintPC()

    json_fun.save_json(scrapped_annonces, "scraped_annonce.json")


def main():
    while True:
        choix = questionary.select(
            "Que souhaitez-vous faire ?",
            choices=[
                "1. Mettre à jour les prix du marché",
                "2. Lancer un Scrapping",
                "3. Nettoyer les annonces déjà vues",
                "Quitter",
            ],
        ).ask()

        if choix == "Quitter" or choix is None:
            print("Au revoir !")
            break

        if choix == "1. Mettre à jour les prix du marché":
            choix_scrap_prix = questionary.select(
                "Quel catégorie voulez vous scrapper ?",
                choices=["gpu", "cpu", "ram", "stockage", "tout"],
            ).ask()
            lancer_scrap_prix(choix_scrap_prix)

        if choix == "2. Lancer un Scrapping":
            recherche = input("Sur quelle recherche voulez vous scrapper ?")
            lancer_scrap_PC(recherche)


main()
