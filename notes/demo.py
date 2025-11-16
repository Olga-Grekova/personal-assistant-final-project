from services.note_manager import NoteManager

if __name__ == "__main__":
    manager = NoteManager()

    # CREATE
    manager.create("Купити молоко", ["shopping"])
    manager.create("Повторити Python OOP", ["study", "python"])

    # READ
    for i, note in enumerate(manager.read()):
        print(f"{i}: {note.text} | Теги: {note.tags}")

    # UPDATE
    manager.update(0, new_text="Купити молоко та хліб")

    # DELETE
    manager.delete(1)

    print("\nПошук за 'купити':")
    for n in manager.search(keywords=["купити"]):
        print("-", n.text)

    print("Усі теги:", manager.get_all_tags())

    chosen = "shopping"
    print(f"\nНотатки з тегом '{chosen}':")

    for note in manager.sort_by_tag(chosen):
        print("-", note.text)