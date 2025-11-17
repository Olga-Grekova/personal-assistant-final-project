from pathlib import Path

from contacts.models import AddressBook
from contacts.services import (
    add_contact,
    change_contact,
    delete_contact,
    search_contacts,
    show_birthdays,
    show_contact_info,
    show_all,
    add_birthday,
)
from notes.services import NoteService
from storage.repo import ContactRepository


def init_address_book() -> tuple[AddressBook, ContactRepository]:
    """Завантажуємо контакти з диска в AddressBook."""
    repo = ContactRepository()
    book = AddressBook()
    contacts = repo.load_contacts()
    for contact in contacts:
        book.add_record(contact)
    return book, repo


def init_notes() -> NoteService:
    """Ініціалізуємо сервіс нотаток з файлом у теці користувача."""
    storage_dir = Path.home() / ".personal_assistant"
    storage_dir.mkdir(parents=True, exist_ok=True)
    notes_file = storage_dir / "notes.json"
    return NoteService(filename=str(notes_file))


def print_help() -> None:
    print(
        """
Доступні команди:

КОНТАКТИ:
  add [ім'я] [телефон] [email/None] [адреса/None] [ДД.ММ.РРРР/None]
  change [ім'я] [phone/email/address/birthday] [...]
  delete [ім'я]
  search [рядок_пошуку]
  show-info [ім'я]
  show-all
  birthdays [N]              – дні народження протягом N днів (за замовчуванням 7)
  add-birthday [ім'я] [ДД.ММ.РРРР]

НОТАТКИ:
  note-add
  note-edit
  note-delete
  note-list
  note-search
  note-tags
  note-by-tag

СИСТЕМА:
  help
  exit / вихід / quit
"""
    )


def run_cli() -> None:
    book, contact_repo = init_address_book()
    notes = init_notes()

    print("Персональний помічник запущено. Введіть 'help' для списку команд.")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо побачення!")
            break

        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()
        args = parts[1:]

        # Вихід
        if command in ("exit", "quit", "вихід"):
            # зберігаємо контакти перед виходом
            contact_repo.save_contacts(list(book.data.values()))
            print("До побачення!")
            break

        # Допомога
        if command in ("help", "допомога"):
            print_help()
            continue

        # КОМАНДИ ДЛЯ КОНТАКТІВ
        if command == "add":
            print(add_contact(args, book))
            contact_repo.save_contacts(list(book.data.values()))
            continue

        if command == "change":
            print(change_contact(args, book))
            contact_repo.save_contacts(list(book.data.values()))
            continue

        if command == "delete":
            print(delete_contact(args, book))
            contact_repo.save_contacts(list(book.data.values()))
            continue

        if command == "search":
            print(search_contacts(args, book))
            continue

        if command == "birthdays":
            print(show_birthdays(args, book))
            continue

        if command == "show-info":
            print(show_contact_info(args, book))
            continue

        if command == "show-all":
            print(show_all(args, book))
            continue

        if command == "add-birthday":
            print(add_birthday(args, book))
            contact_repo.save_contacts(list(book.data.values()))
            continue

        # КОМАНДИ ДЛЯ НОТАТОК – делегуємо в handlers
        from cli.handlers import handle_notes_command

        handled = handle_notes_command(command, args, notes)
        if handled:
            continue

        print("Невідома команда. Введіть 'help' для списку доступних команд.")
