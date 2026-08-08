# Classe ordinateur :
# Créé un objet ordinateur avec chaque composant pour l'instant : cpu, gpu, stockage_ssd, stockage_hdd, ram
# Cette classe permet de calculer le prix de revente des pièces de l'ordinateur en fonction des prix du marché
# Problème, les annonces LBC sont manquent souvent de détail, il est rare d'avoir une annonce ou chaque composant et sa référence est présent
# Exemple : cpu : autre : Intel Core i7-3770 : -1
# gpu : GTX 1660 Super : {'min': 75, 'max': 130, 'mediane': 99.0, 'moyenne': 96.05, 'nb': 22}
# ssd : 256GB SSD : {'min': 15, 'max': 45, 'mediane': 25.0, 'moyenne': 25.75, 'nb': 20}
# hdd : 1TB HDD : {'min': 10, 'max': 55, 'mediane': 25.0, 'moyenne': 28.86, 'nb': 14}
# ram : autre : 19,5 Go DDR3 : -1
# prix : [350]
# opportunité : None
# prix revente : {'min': 100, 'max': 230, 'moyenne': 150.66, 'mediane': 149.0}
# --------
# cpu : i5-12400F : {'min': 70, 'max': 150, 'mediane': 115, 'moyenne': 118.55, 'nb': 11}
# gpu : RTX 4060 : {'min': 180, 'max': 400, 'mediane': 250.0, 'moyenne': 265.7, 'nb': 20}
# ssd : null : -1
# hdd : null : -1
# ram : null : -1
# prix : [750]
# opportunité : 6
# prix revente : {'min': 250, 'max': 550, 'moyenne': 384.25, 'mediane': 365.0}
# Solution : appliquer un poids à chaque composant pour le prix final d'un PC. Ce n'est pas une solution magique mais ça ammorti la chute du prix de revente si un composant n'est pas précisé
# Par exemple : la RAM représente en moyenne 15% du prix d'une config, le prix de revente affiché après ajustement sera de 1150€


import statistics


# Poid par défaut (totalement subjectif) à adapter en fonction des recherches
POIDS = {"cpu": 0.2, "gpu": 0.45, "ram": 0.1, "hdd": 0.05, "ssd": 0.1, "CM": 0.1, "alim": 0.05, "boitier": 0.05}


class Ordinateur:
    def __init__(
        self,
        cpu,
        gpu,
        stockage_ssd,
        stockage_hdd,
        ram,
        prix,
        opportunite,
        cpu_price=-1,
        gpu_price=-1,
        ssd_price=-1,
        hdd_price=-1,
        ram_price=-1,
    ):
        self.cpu = cpu
        self.gpu = gpu
        self.stockage_ssd = stockage_ssd
        self.stockage_hdd = stockage_hdd
        self.ram = ram
        self.prix = prix
        self.opportunite = opportunite
        self.cpu_price = cpu_price
        self.gpu_price = gpu_price
        self.ssd_price = ssd_price
        self.hdd_price = hdd_price
        self.ram_price = ram_price
        self.interessant = False

    def printPC(self):
        print("--------")
        print(
            f"cpu : {self.cpu} : {self.cpu_price}\ngpu : {self.gpu} : {self.gpu_price}\nssd : {self.stockage_ssd} : {self.ssd_price}\nhdd : {self.stockage_hdd} : {self.hdd_price}\nram : {self.ram} : {self.ram_price}\nprix : {self.prix}\nopportunité : {self.opportunite} \nprix revente : {self.prix_revente} \nprix revente arrangé : {self.prix_revente_arrange} \ninteressant : {self.interessant}"
        )

    def caluler_prix_revente(self):
        components = (self.cpu_price, self.gpu_price, self.ssd_price, self.hdd_price, self.ram_price)

        mins = [p["min"] for p in components if isinstance(p, dict) and p.get("min", -1) != -1]
        maxs = [p["max"] for p in components if isinstance(p, dict) and p.get("max", -1) != -1]
        moyenness = [p["moyenne"] for p in components if isinstance(p, dict) and p.get("moyenne", -1) != -1]
        medianes = [p["mediane"] for p in components if isinstance(p, dict) and p.get("mediane", -1) != -1]

        self.prix_revente_min = sum(mins) if mins else 0
        self.prix_revente_max = sum(maxs) if maxs else 0
        self.prix_revente_moyenne = sum(moyenness) if moyenness else 0
        self.prix_revente_mediane = sum(medianes) if medianes else 0

        self.prix_revente = {
            "min": self.prix_revente_min,
            "max": self.prix_revente_max,
            "moyenne": self.prix_revente_moyenne,
            "mediane": self.prix_revente_mediane,
        }

    def calculer_prix_revente_arrange(self):
        self.caluler_prix_revente()

        self.poid_manquant = 0
        for prix, comp in zip(
            [self.cpu_price, self.gpu_price, self.ram_price, self.hdd_price, self.ssd_price],
            ["cpu", "gpu", "ram", "hdd", "ssd"],
        ):
            if prix == -1:
                self.poid_manquant += POIDS[comp]

        if (1 - self.poid_manquant) <= 0:
            self.prix_revente_arrange = {t: None for t in ["min", "max", "moyenne", "mediane"]}
            return self.prix_revente_arrange

        self.prix_revente_arrange = {
            t: round(self.prix_revente[t] / (1 - self.poid_manquant), 2) for t in ["min", "max", "moyenne", "mediane"]
        }

        if self.prix_revente_arrange["mediane"] > self.prix[0]:
            print("mediane : ", self.prix_revente_arrange["mediane"], " prix : ", self.prix[0])
            self.interessant = True

        return self.interessant, self.prix_revente_arrange
