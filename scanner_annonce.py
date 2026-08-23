import scraper_annonce
import json_fun
import analyse
import ordinateur
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
import bot_telegram


scrapped_annonces = json_fun.read_json("scraped_annonce.json")
recherche = "PC gamer"

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

    pc = ordinateur.Ordinateur(
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

    liste_pc.append(pc)
    inte, prix = pc.calculer_prix_revente_arrange()

    if inte:
        liste_pc.append(pc)
        bot_telegram.envoyer_message(pc, a)

json_fun.save_json(scrapped_annonces, "scraped_annonce.json")
