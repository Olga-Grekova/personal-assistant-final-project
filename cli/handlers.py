from typing import List

from notes.services import NoteService


def _print_notes(notes) -> str:
    if not notes:
        return "Нотаток поки немає."
    lines = []
    for idx, note in enumerate(notes, 1):
        tags_part = f" [теги: {', '.join(note.tags)}]" if note.tags else ""
        lines.append(f"{idx}. {note.text}{tags_part}")
    return "\n".join(lines)


def handle_notes_command(command: str, args: List[str], notes: NoteService) -> bool:
    """
    Обробляє команди, що починаються з 'note-'.
    Повертає True, якщо команда розпізнана і оброблена.
    """
    if not command.startswith("note-"):
        return False

    if command == "note-add":
        text = input("Введіть текст нотатки: ").strip()
        tags_raw = input("Введіть теги через кому (або залиште порожнім): ").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        try:
            notes.create(text, tags)
            print("Нотатку додано.")
        except ValueError as e:
            print(f"Помилка: {e}")
        return True

    if command == "note-list":
        print(_print_notes(notes.read()))
        return True

    if command == "note-edit":
        print(_print_notes(notes.read()))
        index_raw = input("Введіть номер нотатки для редагування: ").strip()
        try:
            index = int(index_raw) - 1
        except ValueError:
            print("Номер має бути цілим числом.")
            return True

        new_text = input("Новий текст (або Enter, щоб залишити): ").strip()
        new_text = new_text if new_text else None

        tags_raw = input("Нові теги через кому (або Enter, щоб залишити): ").strip()
        new_tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None

        try:
            notes.update(index, new_text=new_text, new_tags=new_tags)
            print("Нотатку оновлено.")
        except Exception as e:
            print(f"Помилка: {e}")
        return True

    if command == "note-delete":
        print(_print_notes(notes.read()))
        index_raw = input("Введіть номер нотатки для видалення: ").strip()
        try:
            index = int(index_raw) - 1
            notes.delete(index)
            print("Нотатку видалено.")
        except Exception as e:
            print(f"Помилка: {e}")
        return True

    if command == "note-search":
        text_part = input("Ключові слова для пошуку в тексті (через пробіл, або Enter): ").strip()
        tags_raw = input("Теги для пошуку (через кому, або Enter): ").strip()

        keywords = text_part.split() if text_part else None
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None

        results = notes.search(keywords=keywords, tags=tags)
        print(_print_notes(results))
        return True

    if command == "note-tags":
        tags = notes.get_all_tags()
        if not tags:
            print("Тегів поки немає.")
        else:
            print("Усі теги:", ", ".join(tags))
        return True

    if command == "note-by-tag":
        tag = input("Введіть тег: ").strip()
        results = notes.sort_by_tag(tag)
        print(_print_notes(results))
        return True

    return False
