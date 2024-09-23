from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivymd.toast import toast
import openai

Window.size = (360, 640)

openai.api_key = 'YOUR_OPENAI_API_KEY'

class LimitedTextField(MDTextField):
    max_chars = 2

    def insert_text(self, substring, from_undo=False):
        if len(self.text) + len(substring) > self.max_chars:
            return
        super().insert_text(substring, from_undo=from_undo)

class TimePickerDialog(MDDialog):
    def __init__(self, on_time_selected, **kwargs):
        self.on_time_selected = on_time_selected
        super().__init__(
            title="Выберите время",
            type="custom",
            content_cls=MDBoxLayout(
                orientation="vertical",
                spacing="12dp",
                size_hint_y=None,
                height="180dp",
            ),
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text="OK",
                    on_release=self.select_time
                ),
            ],
        )
        self.hour_field = LimitedTextField(
            hint_text="Часы",
            input_filter="int",
            multiline=False,
            size_hint_x=None,
            width="100dp",
        )
        self.minute_field = LimitedTextField(
            hint_text="Минуты",
            input_filter="int",
            multiline=False,
            size_hint_x=None,
            width="100dp",
        )
        self.content_cls.add_widget(self.hour_field)
        self.content_cls.add_widget(self.minute_field)

    def select_time(self, *args):
        hour = self.hour_field.text
        minute = self.minute_field.text
        if hour.isdigit() and minute.isdigit():
            hour = int(hour)
            minute = int(minute)
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                self.on_time_selected(hour, minute)
                self.dismiss()
            else:
                toast("Неверное время. Пожалуйста, введите корректный час (0-23) и минуту (0-59).")
        else:
            toast("Неверный ввод. Пожалуйста, введите только числа.")

class AddEventDialog(MDDialog):
    def __init__(self, add_event_callback, **kwargs):
        self.add_event_callback = add_event_callback
        super().__init__(
            title="Добавить событие",
            type="custom",
            content_cls=MDBoxLayout(
                MDTextField(
                    hint_text="Название события",
                    id="event_title",
                    multiline=False,
                ),
                MDRaisedButton(
                    text="Выбрать время",
                    on_release=self.open_time_picker
                ),
                MDRaisedButton(
                    text="Выбрать день",
                    on_release=self.open_day_picker
                ),
                orientation="vertical",
                spacing="12dp",
                size_hint_y=None,
                height="220dp",
            ),
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text="Добавить",
                    on_release=self.add_event
                ),
            ],
        )
        self.selected_time = ""
        self.selected_day = ""

    def open_time_picker(self, *args):
        time_picker = TimePickerDialog(on_time_selected=self.set_selected_time)
        time_picker.open()

    def set_selected_time(self, hour, minute):
        self.selected_time = f"{hour:02}:{minute:02}"

    def open_day_picker(self, *args):
        day_items = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        menu_items = [
            {
                "text": day,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=day: self.set_selected_day(x),
            } for day in day_items
        ]
        self.day_menu = MDDropdownMenu(
            caller=self.content_cls.children[1],
            items=menu_items,
            width_mult=4,
        )
        self.day_menu.open()

    def set_selected_day(self, day):
        self.selected_day = day
        self.day_menu.dismiss()

    def add_event(self, *args):
        event_title = self.content_cls.ids.event_title.text
        event_time = self.selected_time
        event_day = self.selected_day
        if event_title and event_time and event_day:
            self.add_event_callback(event_title, event_time, event_day)
            self.dismiss()

class EditEventDialog(MDDialog):
    def __init__(self, event_item, **kwargs):
        self.event_item = event_item
        self.time = event_item.event_time
        self.day = event_item.event_day
        super().__init__(
            title="Редактировать событие",
            type="custom",
            content_cls=MDBoxLayout(
                MDTextField(
                    hint_text="Название события",
                    text=event_item.event_title,
                    id="event_title",
                    multiline=False,
                ),
                MDRaisedButton(
                    text="Выбрать время",
                    on_release=self.open_time_picker
                ),
                MDRaisedButton(
                    text="Выбрать день",
                    on_release=self.open_day_picker
                ),
                orientation="vertical",
                spacing="12dp",
                size_hint_y=None,
                height="220dp",
            ),
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text="Сохранить",
                    on_release=self.save_event
                ),
            ],
        )
        self.selected_time = self.time
        self.selected_day = self.day

    def open_time_picker(self, *args):
        time_picker = TimePickerDialog(on_time_selected=self.set_selected_time)
        time_picker.open()

    def set_selected_time(self, hour, minute):
        self.selected_time = f"{hour:02}:{minute:02}"

    def open_day_picker(self, *args):
        day_items = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        menu_items = [
            {
                "text": day,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=day: self.set_selected_day(x),
            } for day in day_items
        ]
        self.day_menu = MDDropdownMenu(
            caller=self.content_cls.children[1],
            items=menu_items,
            width_mult=4,
        )
        self.day_menu.open()

    def set_selected_day(self, day):
        self.selected_day = day
        self.day_menu.dismiss()

    def save_event(self, *args):
        self.event_item.event_title = self.content_cls.ids.event_title.text
        self.event_item.event_time = self.selected_time
        self.event_item.event_day = self.selected_day
        self.event_item.update_event_text()
        self.dismiss()

class EventItem(MDCard):
    event_title = StringProperty('')
    event_time = StringProperty('')
    event_day = StringProperty('')
    remove_event_callback = ObjectProperty(None)
    edit_event_callback = ObjectProperty(None)

    def __init__(self, remove_event_callback, edit_event_callback, **kwargs):
        super(EventItem, self).__init__(**kwargs)
        self.remove_event_callback = remove_event_callback
        self.edit_event_callback = edit_event_callback
        self.orientation = 'vertical'
        self.padding = '10dp'
        self.size_hint = (None, None)
        self.size = ('280dp', '100dp')
        self.elevation = 0

    def remove_event(self):
        self.remove_event_callback(self)

    def edit_event(self):
        self.edit_event_callback(self)

    def update_event_text(self):
        self.ids.event_label.text = f'{self.event_day} {self.event_time}: {self.event_title}'

class UAQYT_BETA(Screen):
    days_of_week = ListProperty(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'])

    def __init__(self, **kwargs):
        super(UAQYT_BETA, self).__init__(**kwargs)
        self.event_list = []

        layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        self.add_event_button = MDRaisedButton(text='Добавить событие', pos_hint={'center_x': 0.5}, on_press=self.open_add_event_dialog)
        layout.add_widget(self.add_event_button)

        self.generate_schedule_button = MDRaisedButton(text='Сгенерировать расписание', pos_hint={'center_x': 0.5}, on_press=self.generate_schedule)
        layout.add_widget(self.generate_schedule_button)

        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.event_layout = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.event_layout.bind(minimum_height=self.event_layout.setter('height'))
        self.scroll_view.add_widget(self.event_layout)
        layout.add_widget(self.scroll_view)

        self.add_widget(layout)

    def open_add_event_dialog(self, instance):
        dialog = AddEventDialog(add_event_callback=self.add_event)
        dialog.open()

    def open_edit_event_dialog(self, event_item):
        dialog = EditEventDialog(event_item=event_item)
        dialog.open()

    def add_event(self, title, time, day):
        event_item = EventItem(remove_event_callback=self.remove_event, edit_event_callback=self.open_edit_event_dialog)
        event_item.event_title = title
        event_item.event_time = time
        event_item.event_day = day
        event_item.update_event_text()
        self.event_layout.add_widget(event_item)
        self.event_list.append(event_item)
        self.sort_events()

    def remove_event(self, event_item):
        self.event_layout.remove_widget(event_item)
        self.event_list.remove(event_item)

    def sort_events(self):
        self.event_layout.clear_widgets()
        self.event_list.sort(key=lambda e: (self.days_of_week.index(e.event_day), e.event_time))
        for event_item in self.event_list:
            self.event_layout.add_widget(event_item)

    def generate_schedule(self, instance):
        # Call OpenAI API to generate schedule
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Generate a weekly schedule with various tasks."}
            ]
        )
        generated_schedule = response['choices'][0]['message']['content'].strip()

        # Add the generated schedule to the event list
        for line in generated_schedule.split('\n'):
            parts = line.split(':')
            if len(parts) == 3:
                day, time, title = parts
                self.add_event(title.strip(), time.strip(), day.strip())

class ScheduleApp(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(UAQYT_BETA(name='UAQYT_BETA'))
        self.title = "Мое расписание"
        return sm

if __name__ == '__main__':
    ScheduleApp().run()