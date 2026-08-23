class Annonce:
    def __init__(self, id, title, body, price, link, image):
        self.id = id
        self.title = title
        self.body = body
        self.price = price[0]
        self.link = link
        self.image = image

    def printAnnonce(self):
        print("/////////")
        print(f"Annonce num : {self.id} \n{self.title}\n{self.price}\n{self.body}")
