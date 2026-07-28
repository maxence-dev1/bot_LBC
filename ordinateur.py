# Classe ordinateur :
# Créé un objet ordinateur avec chaque composant pour l'instant : cpu, gpu, stockage_ssd, stockage_hdd, ram


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

    def printPC(self):
        print("--------")
        print(
            f"cpu : {self.cpu} : {self.cpu_price}\ngpu : {self.gpu} : {self.gpu_price}\nssd : {self.stockage_ssd} : {self.ssd_price}\nhdd : {self.stockage_hdd} : {self.hdd_price}\nram : {self.ram} : {self.ram_price}\nprix : {self.prix}\nopportunité : {self.opportunite} "
        )
