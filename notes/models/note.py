class Note:
    def __init__(self, text, tags = None):
        if not text.strip():
            raise ValueError("Нотатка не може бути порожньою!")
        
        self.text = text.strip()
        self.tags = tags if tags is not None else []

    def edit(self, new_text=None, new_tags=None):
        if new_text is not None:
            if new_text.strip() == "":
                raise ValueError("Текст нотатки не може бути порожнім!")
        self.text = new_text

        if new_tags is not None:
            self.tags = new_tags

    def to_dict(self):
        return {
            "text": self.text,
            "tags": self.tags
        }
    
    @staticmethod
    def from_dict(data: dict):
        return Note(text = data["text"], tags = data.get("tags", []))