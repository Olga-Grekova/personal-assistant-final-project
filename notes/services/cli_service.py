from services.note_manager import NoteManager


manager = NoteManager()


def add_note(text, tags=None):
    return manager.create(text, tags)


def edit_note(index, new_text=None, new_tags=None):
    manager.update(index, new_text, new_tags)


def delete_note(index):
    manager.delete(index)


def search_notes(keywords=None, tags=None):
    return manager.search(keywords=keywords, tags=tags)


def notes_by_tag(tag):
    return manager.sort_by_tag(tag)


def list_notes():
    return manager.read()


def list_tags():
    return manager.get_all_tags()