


class Annonce :
    def __init__(self, id, title, body, price):
        self.id = id
        self.title = title
        self.body = body
        self.price = price

    def printAnnonce(self):
        print("/////////")
        print(f"Annonce num : {self.id} \n{self.title}\n{self.price}\n{self.body}")

