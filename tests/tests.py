import unittest
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contacts.validators import ContactValidator
from contacts.models import Field, Name, Phone, Email, Address, Birthday, Contact, AddressBook
from contacts.services import (
    add_contact, change_contact, search_contacts, show_birthdays,
    show_contact_info, show_all, delete_contact, add_birthday
)
from notes.models import Note
from notes.services import NoteService
from storage.repo import Repository, ContactRepository, NoteRepository


class TestContactValidators(unittest.TestCase):
    
    def test_validate_phone_valid(self):
        self.assertEqual(ContactValidator.validate_phone("1234567890"), "1234567890")
        self.assertEqual(ContactValidator.validate_phone("+38(050)123-45-67"), "380501234567")
        self.assertEqual(ContactValidator.validate_phone("123-456-7890"), "1234567890")
    
    def test_validate_phone_invalid_length(self):
        with self.assertRaises(ValueError):
            ContactValidator.validate_phone("123")
        with self.assertRaises(ValueError):
            ContactValidator.validate_phone("12345678901234")
    
    def test_validate_phone_invalid_type(self):
        with self.assertRaises(TypeError):
            ContactValidator.validate_phone(1234567890)
    
    def test_validate_email_valid(self):
        self.assertEqual(ContactValidator.validate_email("test@example.com"), "test@example.com")
        self.assertEqual(ContactValidator.validate_email("user.name+tag@domain.co.uk"), "user.name+tag@domain.co.uk")
    
    def test_validate_email_invalid_format(self):
        with self.assertRaises(ValueError):
            ContactValidator.validate_email("invalid-email")
        with self.assertRaises(ValueError):
            ContactValidator.validate_email("@example.com")
        with self.assertRaises(ValueError):
            ContactValidator.validate_email("user@")
    
    def test_validate_email_consecutive_dots(self):
        with self.assertRaises(ValueError):
            ContactValidator.validate_email("user..name@example.com")
    
    def test_validate_email_invalid_type(self):
        with self.assertRaises(TypeError):
            ContactValidator.validate_email(12345)
    
    def test_validate_birthday_valid(self):
        result = ContactValidator.validate_birthday("01.01.1990")
        self.assertEqual(result, datetime(1990, 1, 1).date())
    
    def test_validate_birthday_future_date(self):
        future_date = (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y")
        with self.assertRaises(ValueError):
            ContactValidator.validate_birthday(future_date)
    
    def test_validate_birthday_invalid_format(self):
        with self.assertRaises(ValueError):
            ContactValidator.validate_birthday("1990-01-01")
        with self.assertRaises(ValueError):
            ContactValidator.validate_birthday("32.01.1990")
    
    def test_validate_birthday_invalid_type(self):
        with self.assertRaises(TypeError):
            ContactValidator.validate_birthday(19900101)


class TestContactModels(unittest.TestCase):
    
    def test_field_creation(self):
        field = Field("test value")
        self.assertEqual(field.value, "test value")
        self.assertEqual(str(field), "test value")
    
    def test_field_value_setter(self):
        field = Field("initial")
        field.value = "updated"
        self.assertEqual(field.value, "updated")
    
    def test_name_field(self):
        name = Name("John Doe")
        self.assertEqual(name.value, "John Doe")
    
    def test_phone_field_valid(self):
        phone = Phone("1234567890")
        self.assertEqual(phone.value, "1234567890")
    
    def test_phone_field_invalid(self):
        with self.assertRaises(ValueError):
            Phone("123")
    
    def test_email_field_valid(self):
        email = Email("test@example.com")
        self.assertEqual(email.value, "test@example.com")
    
    def test_email_field_invalid(self):
        with self.assertRaises(ValueError):
            Email("invalid-email")
    
    def test_birthday_field_valid(self):
        birthday = Birthday("01.01.1990")
        self.assertEqual(str(birthday), "01.01.1990")
    
    def test_contact_creation_minimal(self):
        contact = Contact("John")
        self.assertEqual(contact.name.value, "John")
        self.assertEqual(len(contact.phones), 0)
        self.assertIsNone(contact.email)
        self.assertIsNone(contact.address)
        self.assertIsNone(contact.birthday)
    
    def test_contact_creation_full(self):
        contact = Contact("John", address="Main St", email="john@example.com", birthday="01.01.1990")
        self.assertEqual(contact.name.value, "John")
        self.assertEqual(contact.address.value, "Main St")
        self.assertEqual(contact.email.value, "john@example.com")
        self.assertIsNotNone(contact.birthday)
    
    def test_contact_add_phone(self):
        contact = Contact("John")
        contact.add_phone("1234567890")
        self.assertEqual(len(contact.phones), 1)
        self.assertEqual(contact.phones[0].value, "1234567890")
    
    def test_contact_edit_phone(self):
        contact = Contact("John")
        contact.add_phone("1234567890")
        contact.edit_phone("1234567890", "0987654321")
        self.assertEqual(contact.phones[0].value, "0987654321")
    
    def test_contact_edit_phone_not_found(self):
        contact = Contact("John")
        contact.add_phone("1234567890")
        with self.assertRaises(ValueError):
            contact.edit_phone("9999999999", "0987654321")
    
    def test_contact_edit_field(self):
        contact = Contact("John")
        contact.edit_field("email", "new@example.com")
        self.assertEqual(contact.email.value, "new@example.com")
        
        contact.edit_field("address", "New Street")
        self.assertEqual(contact.address.value, "New Street")
        
        contact.edit_field("birthday", "15.05.1995")
        self.assertIsNotNone(contact.birthday)
    
    def test_contact_edit_field_invalid(self):
        contact = Contact("John")
        with self.assertRaises(ValueError):
            contact.edit_field("invalid_field", "value")
    
    def test_contact_to_dict(self):
        contact = Contact("John", email="john@example.com")
        contact.add_phone("1234567890")
        data = contact.to_dict()
        
        self.assertEqual(data['name'], "John")
        self.assertEqual(data['phones'], ["1234567890"])
        self.assertEqual(data['email'], "john@example.com")
    
    def test_contact_from_dict(self):
        data = {
            'name': 'John',
            'phones': ['1234567890', '0987654321'],
            'email': 'john@example.com',
            'address': 'Main St',
            'birthday': '01.01.1990'
        }
        contact = Contact.from_dict(data)
        
        self.assertEqual(contact.name.value, "John")
        self.assertEqual(len(contact.phones), 2)
        self.assertEqual(contact.email.value, "john@example.com")
        self.assertEqual(contact.address.value, "Main St")


class TestAddressBook(unittest.TestCase):
    
    def setUp(self):
        self.book = AddressBook()
    
    def test_add_record(self):
        contact = Contact("John")
        result = self.book.add_record(contact)
        self.assertIn("успішно додано", result)
        self.assertIn("John", self.book.data)
    
    def test_add_record_duplicate(self):
        contact = Contact("John")
        self.book.add_record(contact)
        result = self.book.add_record(contact)
        self.assertIn("вже існує", result)
    
    def test_find_contact(self):
        contact = Contact("John")
        self.book.add_record(contact)
        found = self.book.find("john")
        self.assertIsNotNone(found)
        self.assertEqual(found.name.value, "John")
    
    def test_find_contact_not_found(self):
        found = self.book.find("NonExistent")
        self.assertIsNone(found)
    
    def test_delete_contact(self):
        contact = Contact("John")
        self.book.add_record(contact)
        result = self.book.delete("john")
        self.assertIn("видалено", result)
        self.assertNotIn("John", self.book.data)
    
    def test_delete_contact_not_found(self):
        result = self.book.delete("NonExistent")
        self.assertIn("не знайдено", result)
    
    def test_search_by_name(self):
        contact = Contact("John Doe")
        self.book.add_record(contact)
        results = self.book.search("john")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name.value, "John Doe")
    
    def test_search_by_phone(self):
        contact = Contact("John")
        contact.add_phone("1234567890")
        self.book.add_record(contact)
        results = self.book.search("1234567890")
        self.assertEqual(len(results), 1)
    
    def test_search_by_email(self):
        contact = Contact("John", email="john@example.com")
        self.book.add_record(contact)
        results = self.book.search("john@example.com")
        self.assertEqual(len(results), 1)
    
    def test_search_no_results(self):
        results = self.book.search("nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_get_upcoming_birthdays(self):
        today = datetime.now().date()
        next_week = today + timedelta(days=5)
        birthday_past_year = next_week.replace(year=1990)
        birthday_str = birthday_past_year.strftime("%d.%m.%Y")
        
        contact = Contact("John", birthday=birthday_str)
        self.book.add_record(contact)
        
        result = self.book.get_upcoming_birthdays(7)
        self.assertIn("John", result)
    
    def test_get_upcoming_birthdays_none(self):
        result = self.book.get_upcoming_birthdays(7)
        self.assertIn("Жодного дня народження", result)


class TestContactServices(unittest.TestCase):
    
    def setUp(self):
        self.book = AddressBook()
    
    def test_add_contact_minimal(self):
        result = add_contact(["John", "1234567890"], self.book)
        self.assertIn("додано", result)
        self.assertIsNotNone(self.book.find("John"))
    
    def test_add_contact_full(self):
        result = add_contact(["John", "1234567890", "john@example.com", "Main St", "01.01.1990"], self.book)
        self.assertIn("додано", result)
        contact = self.book.find("John")
        self.assertIsNotNone(contact.email)
        self.assertIsNotNone(contact.address)
        self.assertIsNotNone(contact.birthday)
    
    def test_add_contact_insufficient_args(self):
        result = add_contact(["John"], self.book)
        self.assertIn("аргументів", result)
    
    def test_change_contact_phone(self):
        add_contact(["John", "1234567890"], self.book)
        result = change_contact(["John", "phone", "1234567890", "0987654321"], self.book)
        self.assertIn("змінено", result)
    
    def test_change_contact_email(self):
        add_contact(["John", "1234567890"], self.book)
        result = change_contact(["John", "email", "new@example.com"], self.book)
        self.assertIn("змінено", result)
    
    def test_change_contact_not_found(self):
        result = change_contact(["NonExistent", "email", "test@example.com"], self.book)
        self.assertIn("не знайдено", result)
    
    def test_search_contacts_found(self):
        add_contact(["John", "1234567890"], self.book)
        result = search_contacts(["John"], self.book)
        self.assertIn("Результати пошуку", result)
    
    def test_search_contacts_not_found(self):
        result = search_contacts(["NonExistent"], self.book)
        self.assertIn("не знайдено", result)
    
    def test_show_birthdays_default(self):
        result = show_birthdays([], self.book)
        self.assertIsNotNone(result)
    
    def test_show_birthdays_custom_days(self):
        result = show_birthdays(["14"], self.book)
        self.assertIsNotNone(result)
    
    def test_show_birthdays_invalid_days(self):
        result = show_birthdays(["invalid"], self.book)
        self.assertIn("аргументів", result)
    
    def test_show_contact_info_found(self):
        add_contact(["John", "1234567890"], self.book)
        result = show_contact_info(["John"], self.book)
        self.assertIn("John", result)
    
    def test_show_contact_info_not_found(self):
        result = show_contact_info(["NonExistent"], self.book)
        self.assertIn("не знайдено", result)
    
    def test_show_all_empty(self):
        result = show_all([], self.book)
        self.assertIn("порожня", result)
    
    def test_show_all_with_contacts(self):
        add_contact(["John", "1234567890"], self.book)
        result = show_all([], self.book)
        self.assertIn("John", result)
        self.assertIn("Всього контактів", result)
    
    def test_delete_contact_success(self):
        add_contact(["John", "1234567890"], self.book)
        result = delete_contact(["John"], self.book)
        self.assertIn("видалено", result)
    
    def test_delete_contact_not_found(self):
        result = delete_contact(["NonExistent"], self.book)
        self.assertIn("не знайдено", result)
    
    def test_add_birthday_success(self):
        add_contact(["John", "1234567890"], self.book)
        result = add_birthday(["John", "01.01.1990"], self.book)
        self.assertIn("встановлено", result)
    
    def test_add_birthday_contact_not_found(self):
        result = add_birthday(["NonExistent", "01.01.1990"], self.book)
        self.assertIn("не знайдено", result)


class TestNoteModels(unittest.TestCase):
    
    def test_note_creation_valid(self):
        note = Note("Test note", ["tag1", "tag2"])
        self.assertEqual(note.text, "Test note")
        self.assertEqual(note.tags, ["tag1", "tag2"])
    
    def test_note_creation_no_tags(self):
        note = Note("Test note")
        self.assertEqual(note.text, "Test note")
        self.assertEqual(note.tags, [])
    
    def test_note_creation_empty_text(self):
        with self.assertRaises(ValueError):
            Note("")
        with self.assertRaises(ValueError):
            Note("   ")
    
    def test_note_edit_text(self):
        note = Note("Original text")
        note.edit(new_text="Updated text")
        self.assertEqual(note.text, "Updated text")
    
    def test_note_edit_tags(self):
        note = Note("Test note", ["tag1"])
        note.edit(new_tags=["tag2", "tag3"])
        self.assertEqual(note.tags, ["tag2", "tag3"])
    
    def test_note_edit_empty_text(self):
        note = Note("Test note")
        with self.assertRaises(ValueError):
            note.edit(new_text="")
    
    def test_note_to_dict(self):
        note = Note("Test note", ["tag1", "tag2"])
        data = note.to_dict()
        self.assertEqual(data["text"], "Test note")
        self.assertEqual(data["tags"], ["tag1", "tag2"])
    
    def test_note_from_dict(self):
        data = {"text": "Test note", "tags": ["tag1", "tag2"]}
        note = Note.from_dict(data)
        self.assertEqual(note.text, "Test note")
        self.assertEqual(note.tags, ["tag1", "tag2"])
    
    def test_note_from_dict_no_tags(self):
        data = {"text": "Test note"}
        note = Note.from_dict(data)
        self.assertEqual(note.text, "Test note")
        self.assertEqual(note.tags, [])


class TestNoteService(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_notes.json")
        self.service = NoteService(self.test_file)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_note(self):
        note = self.service.create("Test note", ["tag1"])
        self.assertEqual(note.text, "Test note")
        self.assertEqual(len(self.service.notes), 1)
    
    def test_read_notes(self):
        self.service.create("Note 1")
        self.service.create("Note 2")
        notes = self.service.read()
        self.assertEqual(len(notes), 2)
    
    def test_update_note(self):
        self.service.create("Original note")
        self.service.update(0, new_text="Updated note")
        self.assertEqual(self.service.notes[0].text, "Updated note")
    
    def test_update_note_invalid_index(self):
        with self.assertRaises(IndexError):
            self.service.update(999, new_text="Test")
    
    def test_delete_note(self):
        self.service.create("Note to delete")
        self.service.delete(0)
        self.assertEqual(len(self.service.notes), 0)
    
    def test_delete_note_invalid_index(self):
        with self.assertRaises(IndexError):
            self.service.delete(999)
    
    def test_search_by_keywords(self):
        self.service.create("Python programming")
        self.service.create("Java development")
        results = self.service.search(keywords=["python"])
        self.assertEqual(len(results), 1)
        self.assertIn("Python", results[0].text)
    
    def test_search_by_tags(self):
        self.service.create("Note 1", ["important"])
        self.service.create("Note 2", ["work"])
        results = self.service.search(tags=["important"])
        self.assertEqual(len(results), 1)
    
    def test_search_combined(self):
        self.service.create("Python note", ["work"])
        self.service.create("Java note", ["personal"])
        results = self.service.search(keywords=["python"], tags=["work"])
        self.assertEqual(len(results), 1)
    
    def test_get_all_tags(self):
        self.service.create("Note 1", ["tag1", "TAG2"])
        self.service.create("Note 2", ["tag2", "tag3"])
        tags = self.service.get_all_tags()
        self.assertEqual(len(tags), 3)
        self.assertIn("tag1", tags)
        self.assertIn("tag2", tags)
        self.assertIn("tag3", tags)
    
    def test_sort_by_tag(self):
        self.service.create("Note 1", ["important"])
        self.service.create("Note 2", ["work"])
        self.service.create("Note 3", ["important"])
        results = self.service.sort_by_tag("important")
        self.assertEqual(len(results), 2)
    
    def test_save_and_load(self):
        self.service.create("Persistent note", ["tag1"])
        self.service.save()
        
        new_service = NoteService(self.test_file)
        self.assertEqual(len(new_service.notes), 1)
        self.assertEqual(new_service.notes[0].text, "Persistent note")


class TestRepository(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo = Repository("test.json", storage_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_storage_directory(self):
        self.assertTrue(self.temp_dir.exists())
    
    def test_save_and_load(self):
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        result = self.repo.save(data)
        self.assertTrue(result)
        
        loaded = self.repo.load()
        self.assertEqual(loaded, data)
    
    def test_load_nonexistent_file(self):
        repo = Repository("nonexistent.json", storage_dir=self.temp_dir)
        data = repo.load()
        self.assertEqual(data, [])
    
    def test_exists(self):
        self.assertFalse(self.repo.exists())
        self.repo.save([{"test": "data"}])
        self.assertTrue(self.repo.exists())
    
    def test_clear(self):
        self.repo.save([{"test": "data"}])
        self.assertTrue(self.repo.exists())
        result = self.repo.clear()
        self.assertTrue(result)
        self.assertFalse(self.repo.exists())
    
    def test_clear_nonexistent(self):
        result = self.repo.clear()
        self.assertFalse(result)


class TestContactRepository(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo = ContactRepository("test_contacts.json")
        self.repo.repo.storage_dir = self.temp_dir
        self.repo.repo.filepath = self.temp_dir / "test_contacts.json"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_contacts(self):
        contact1 = Contact("John", email="john@example.com")
        contact1.add_phone("1234567890")
        contact2 = Contact("Jane", email="jane@example.com")
        contact2.add_phone("0987654321")
        
        contacts = [contact1, contact2]
        result = self.repo.save_contacts(contacts)
        self.assertTrue(result)
        
        loaded = self.repo.load_contacts()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].name.value, "John")
        self.assertEqual(loaded[1].name.value, "Jane")
    
    def test_clear_contacts(self):
        contacts = [Contact("John")]
        self.repo.save_contacts(contacts)
        result = self.repo.clear()
        self.assertTrue(result)


class TestNoteRepository(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo = NoteRepository("test_notes.json")
        self.repo.repo.storage_dir = self.temp_dir
        self.repo.repo.filepath = self.temp_dir / "test_notes.json"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_notes(self):
        note1 = Note("First note", ["tag1"])
        note2 = Note("Second note", ["tag2"])
        
        notes = [note1, note2]
        result = self.repo.save_notes(notes)
        self.assertTrue(result)
        
        loaded = self.repo.load_notes()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].text, "First note")
        self.assertEqual(loaded[1].text, "Second note")
    
    def test_clear_notes(self):
        notes = [Note("Test note")]
        self.repo.save_notes(notes)
        result = self.repo.clear()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
