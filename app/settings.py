class downloader_settings:
    def __init__(self, id, title, author, format='mp3', trimFromStart="", trimFromEnd=""):
        self.id = id
        self.title = title
        self.author = author
        self.format = format
        self.trimFromStart = trimFromStart
        self.trimFromEnd = trimFromEnd

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "format": self.format,
            "trimFromStart": self.trimFromStart,
            "trimFromEnd": self.trimFromEnd,
        }