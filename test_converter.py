import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
import tkinter as tk
#Принудительно очищаем переменные окружения, чтобы избежать конфликтов путей Windows
if "TCL_LIBRARY" in os.environ: del os.environ["TCL_LIBRARY"]
if "TK_LIBRARY" in os.environ: del os.environ["TK_LIBRARY"]
from app import FinalConverter
def bulletproof_load(instance):
    instance.saved_input_path = os.getcwd()
    instance.saved_output_path = os.path.join(os.path.expanduser("~"), "Desktop", "Converted_Files")
FinalConverter.load_settings = bulletproof_load
class TestFinalConverter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем окно Tkinter один раз для всех тестов, чтобы ничего не сломать(было два раза)"""
        cls.root = tk.Tk()
        cls.root.withdraw()  #Скрываем графическое окно
    @classmethod
    def tearDownClass(cls):
        """Уничтожаем окно после выполнения всех тестов"""
        try:
            cls.root.destroy()
        except:
            pass
    def setUp(self):
        """Инициализация перед каждым тестом"""
        #Создаем экземпляр приложения, используя общее стабильное окно root
        self.app = FinalConverter(self.root)
        #Устанавливаем фиксированные пути для тестов
        self.app.input_path_var.set("/test/input")
        self.app.selected_output_path.set("/test/output")

    #==========================================
    #1. МОДУЛЬНЫЕ (ЮНИТ) ТЕСТЫ (КРУТО)
    #==========================================

    def test_save_settings(self):
        """Тест 1.1: Проверка корректности сохранения настроек в JSON"""
        self.app.input_path_var.set("/new/in")
        self.app.selected_output_path.set("/new/out")
        with patch("builtins.open", mock_open()) as mocked_file:
            self.app.save_settings()
            mocked_file.assert_called_once_with("settings.json", "w", encoding="utf-8")

    def test_on_file_select_image_category(self):
        """Тест 1.2: Проверка определения категории файла (Изображение PNG)"""
        self.app.listbox.insert(0, "🖼️ photo.png")
        self.app.listbox.selection_set(0)
        self.app.on_file_select(None)
        self.assertEqual(self.app._current_category, "Изображения")
        self.assertEqual(self.app.entry_var.get(), "photo.png")
        self.assertNotIn("PNG", self.app.fmt_combo['values'])

    #==========================================
    #2. ИНТЕГРАЦИОННЫЕ ТЕСТЫ (ЗАМЕЧАТЕЛЬНО)
    #==========================================

    @patch("os.path.isfile", return_value=True)
    @patch("os.listdir")
    def test_update_autocomplete_filtering(self, mock_listdir, mock_isfile):
        """Тест 2.1: Проверка фильтрации файлов при автодополнении"""
        mock_listdir.return_value = ["photo.png", "document.docx", "music.mp3"]
        self.app.entry_var.set("pho")
        with patch("os.path.exists", return_value=True):
            self.app.update_autocomplete()
        listbox_items = self.app.listbox.get(0, tk.END)
        self.assertEqual(len(listbox_items), 1)
        self.assertEqual(listbox_items[0], "🖼️ photo.png")  # Исправлено: берем первый элемент из кортежа через [0]

    @patch("tkinter.messagebox.showwarning")
    def test_start_conversion_empty_text(self, mock_showwarning):
        """Тест 2.2: Конвертация пустого текстового файла (DOCX/TXT)"""
        self.app._current_category = "Тексты"
        self.app.entry_var.set("empty.txt")
        self.app.fmt_combo.set("PDF")
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="")):
            self.app.start_conversion()
            mock_warning = mock_showwarning
            mock_warning.assert_called_once_with("Предупреждение", "Файл пуст!")

    #==========================================
    #3. ФУНКЦИОНАЛЬНЫЕ ТЕСТЫ (ФУНКЦИОНАЛЬНО)
    #==========================================

    @patch("PIL.Image.open")
    @patch("tkinter.messagebox.showinfo")
    def test_functional_image_conversion(self, mock_showinfo, mock_img_open):
        """Тест 3.1: Успешный сквозной сценарий конвертации PNG -> JPG"""
        self.app._current_category = "Изображения"
        self.app.entry_var.set("test_image.png")
        self.app.fmt_combo.set("JPG")
        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_img_open.return_value = mock_img
        with patch("os.path.exists", return_value=True):
            self.app.start_conversion()
        mock_img.convert.assert_called_once_with("RGB")
        mock_showinfo.assert_called_once()