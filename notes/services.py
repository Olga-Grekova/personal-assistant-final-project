import json
import os
from models.note import Note


class NoteServices:
    def __init__(self, filename="notes.json"):
        self.filename = filename
        self.notes = self.load()

    # -- FILE OPERATIONS --
    def load(self):
        if not os.path.exists(self.filename):
            return []

        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                return [Note.from_dict(note) for note in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(
                [note.to_dict() for note in self.notes],
                file,
                ensure_ascii=False,
                indent=4
            )

    # -- CRUD --
    def create(self, text, tags=None):
        note = Note(text, tags)
        self.notes.append(note)
        self.save()
        return note

    def read(self):
        return self.notes

    def update(self, index, new_text=None, new_tags=None):
        if not (0 <= index < len(self.notes)):
            raise IndexError("Нотатки з таким індексом не існує!")

        self.notes[index].edit(new_text=new_text, new_tags=new_tags)
        self.save()

    def delete(self, index):
        if not (0 <= index < len(self.notes)):
            raise IndexError("Нотатки з таким індексом не існує!")

        del self.notes[index]
        self.save()

    # -- SEARCH --
    def search(self, keywords=None, tags=None):
        results = []

        for note in self.notes:
            text_match = True
            tags_match = True

            if keywords:
                text_match = all(word.lower() in note.text.lower() for word in keywords)

            if tags:
                tags_match = any(tag.lower() in [t.lower() for t in note.tags] for tag in tags)

            if text_match and tags_match:
                results.append(note)

        return results

    # -- TAG OPERATIONS --
    def get_all_tags(self):
        tags = set()
        for note in self.notes:
            for tag in note.tags:
                tags.add(tag.lower())
        return sorted(tags)

    def sort_by_tag(self, tag):
        return [
            note for note in self.notes
            if tag.lower() in [t.lower() for t in note.tags]
        ]