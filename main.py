import db_helper
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen

class HomeScreen(Screen):
    pass

class MasterDataScreen(Screen):
    pass

class DashboardScreen(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class AutocompleteInput(TextInput):
    def __init__(self, items=None, **kwargs):
        super().__init__(**kwargs)
        self.items = items or []
        self.suggestions = []
        self.selected_index = -1
        self.dropdown = DropDown(auto_dismiss=False)
        self.bind(text=self.on_text_change)

    def on_text_change(self, instance, value):
        self.dropdown.dismiss()
        self.selected_index = -1
        self.dropdown = DropDown(auto_dismiss=False)
        self.suggestions = []

        if not value.strip():
            return

        self.suggestions = [item for item in self.items if value.lower() in item.lower()]
        if not self.suggestions:
            return

        for item in self.suggestions:
            btn = Button(text=item, size_hint_y=None, height=40, background_color=(1, 1, 1, 1))
            btn.bind(on_release=lambda btn: self.select_item(btn.text))
            self.dropdown.add_widget(btn)

        self.dropdown.open(self)

    def select_item(self, text):
        self.text = text
        self.dropdown.dismiss()
        self.cursor = (len(text), 0)

    # ini kuncinya: override keyboard handling
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        key = keycode[1]  # nama key, contoh: 'down', 'up', 'enter'

        if self.dropdown.parent:
            if key == 'down':
                self.selected_index = (self.selected_index + 1) % len(self.suggestions)
                self.highlight_selected()
                return True
            elif key == 'up':
                self.selected_index = (self.selected_index - 1) % len(self.suggestions)
                self.highlight_selected()
                return True
            elif key == 'enter':
                if 0 <= self.selected_index < len(self.suggestions):
                    self.select_item(self.suggestions[self.selected_index])
                    return True

        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def highlight_selected(self):
        for i, child in enumerate(self.dropdown.container.children):
            if i == len(self.dropdown.container.children) - 1 - self.selected_index:
                child.background_color = (0.3, 0.5, 1, 1)  # biru
            else:
                child.background_color = (1, 1, 1, 1)  # putih

class Main(App):
    Builder.load_file("main.kv")
    active_data_getter = None
    active_load_function = None
    current_page = 1
    items_per_page = 10
    
    def build(self):
        db_helper.init_db()
        sm = WindowManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(MasterDataScreen(name='masterdata'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        return sm
    
    def pop_up_notif(self, message, duration=2):
        from kivy.uix.popup import Popup
        from kivy.clock import Clock

        notif = Popup(title='Notifikasi',
                      content=Label(text=message),
                      size_hint=(None, None),
                      size=(350,150),
                      auto_dismiss=True)
        notif.open()
        Clock.schedule_once(lambda dt: notif.dismiss(), duration)

    def load_data_customer(self):
        data_tab = self.root.get_screen('dashboard')
        container = data_tab.ids.data_customer
        container.clear_widgets()

        # ambil semua data
        data = db_helper.get_data_customer()
        total_pages = max(1, (len(data) - 1) // self.items_per_page + 1)

        # data per halaman
        start = ((self.current_page - 1) * self.items_per_page)
        end = (start + self.items_per_page)
        page_data = data[start:end]

        # header
        container.add_widget(Label(text='No', bold=True))
        container.add_widget(Label(text='Nama Customer', bold=True))
        container.add_widget(Label(text='Total Tabung 6m3', bold=True))
        container.add_widget(Label(text='Total Tabung 1m3', bold=True))

        # data
        for i, row in enumerate(page_data, start=start + 1):
            container.add_widget(Label(text=str(i)))
            container.add_widget(Label(text=row[1]))
            container.add_widget(Label(text=str(row[5])))
            container.add_widget(Label(text=str(row[6]))) 

        # nomor halaman
        page_label = data_tab.ids.page_label_customer
        page_label.text = f"Page {self.current_page} of {total_pages}"

    def set_active_table(self, data_getter, load_function):
        self.active_data_getter = data_getter.__name__
        self.active_load_function = load_function.__name__

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            if self.active_data_getter == 'load_data_customer' :
                self.load_data_customer()
            else:
                self.load_data_tabung()

    def next_page(self):
        if self.active_data_getter == 'load_data_customer' :
            data = db_helper.get_data_customer()
        else:
            data = db_helper.get_data_tabung()

        total_pages = max(1, (len(data) - 1) // self.items_per_page + 1)
        if self.current_page < total_pages:
            self.current_page += 1
            if self.active_data_getter == 'load_data_customer' :
                self.load_data_customer()
            else:
                self.load_data_tabung()

    def on_start(self):
        self.load_data_customer()
        self.load_data_tabung()
        customer_list = db_helper.get_customer_list()
        data_tab = self.root.get_screen('masterdata')
        data_tab.ids.customer_autocomplete.items = customer_list

    def save_data_customer(self):
        data_tab = self.root.get_screen('masterdata')

        name = data_tab.ids.customer_name.text

        if name:
            db_helper.insert_customer(name)
            self.pop_up_notif('Data disimpan!')
            data_tab.ids.customer_name.text = ''
            self.load_data_customer()
        else:
            self.pop_up_notif('Nama Customer wajib diisi.')

    def save_data_tabung(self):
        data_input = self.root.get_screen('masterdata')

        code_tabung = data_input.ids.code_tabung.text
        type_tabung = data_input.ids.type_tabung.text
        customer = data_input.ids.customer_autocomplete.text

        if code_tabung and type_tabung and customer:
            db_helper.insert_tabung(code_tabung, type_tabung, customer)
            self.pop_up_notif('Data disimpan!')
            data_input.ids.code_tabung.text = ''
            data_input.ids.type_tabung.text = 'Pilih Jenis Tabung'
            data_input.ids.customer_autocomplete.text = ''
            self.load_data_tabung()
        else:
            self.pop_up_notif('Code, Jenis dan Customer wajib diisi.')

    def load_data_tabung(self):
        data_tab = self.root.get_screen('dashboard')
        container = data_tab.ids.data_tabung
        container.clear_widgets()

        # ambil semua data
        data = db_helper.get_data_tabung()
        total_pages = max(1, (len(data) - 1) // self.items_per_page + 1)

        # data per halaman
        start = ((self.current_page - 1) * self.items_per_page)
        end = (start + self.items_per_page)
        page_data = data[start:end]

        # header
        container.add_widget(Label(text='No', bold=True))
        container.add_widget(Label(text='Code Tabung', bold=True))
        container.add_widget(Label(text='Type Tabung', bold=True))
        container.add_widget(Label(text='Nama Customer', bold=True))

        # data
        for i, row in enumerate(page_data, start=start + 1):
            container.add_widget(Label(text=str(i)))
            container.add_widget(Label(text=row[0]))
            container.add_widget(Label(text=str(row[1])))
            container.add_widget(Label(text=str(row[2]))) 

        # nomor halaman
        page_label = data_tab.ids.page_label_tabung
        page_label.text = f"Page {self.current_page} of {total_pages}"

if __name__ == "__main__":
    Main().run()
