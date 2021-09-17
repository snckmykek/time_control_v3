"""
TODO: Сейчас выполненные задания отбираются только по дате старта, типо сегодня стартанул, значит действие сеодняшнее
но заполняются они целиком, не рубятся до 23.59.59, то есть надо сделать чтобы при выполнении действия
на стыки нескольких дней была разбика по действиям от 0:00 до 23:59:59
"""
from abc import ABC

from kivy.config import Config

Config.set('graphics', 'resizable', '1')
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')

from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import IRightBodyTouch, ThreeLineAvatarIconListItem, OneLineIconListItem
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import MDList
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar

from task_bar import TaskBar
from task_adder import TaskAdder
from db_requests import db


class MainApp(MDApp):
    def build(self):
        return Builder.load_file('timecontrol.kv')


class TimeControlScreen(MDScreen):
    menu_dropdown = ObjectProperty()
    task_items = list()
    shorttask_items = list()

    def __init__(self, **kwargs):
        super(TimeControlScreen, self).__init__(**kwargs)
        Clock.schedule_once(lambda *args: self.refresh_tasks())

        self.task_bar = TaskBar(size_hint_y=None, height=dp(300), opacity=0)
        self.task_adder = TaskAdder()
        self.task_adder.bind(on_dismiss=lambda *args: self.refresh_tasks())
        self.init_dropdown()

    def init_dropdown(self):
        self.task_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"Item {i}",
                "height": dp(56),
                "on_release": lambda x=f"Item {i}": self.task_items_callback(x),
            } for i in range(5)
        ]
        self.shorttask_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"Item {i}",
                "height": dp(56),
                "on_release": lambda x=f"Item {i}": self.task_items_callback(x),
            } for i in range(5, 10)
        ]
        self.menu_dropdown = MDDropdownMenu(
            items=self.task_items,
            width_mult=4,
        )

    def open_dropdown(self, button):
        self.menu_dropdown.caller = button
        if self.ids.main_navigator.current_tab == 'task screen':
            self.menu_dropdown.items = self.task_items
        elif self.ids.main_navigator.current_tab == 'short task screen':
            self.menu_dropdown.items = self.shorttask_items
        else:
            pass  # todo
            self.menu_dropdown.items = self.shorttask_items
        self.menu_dropdown.open()

    def task_items_callback(self, text_item):
        self.menu_dropdown.dismiss()
        Snackbar(text=text_item).open()

    # region tasks_page
    def refresh_tasks(self):
        self.ids.tasks_page.clear_widgets()
        for i, task_row in enumerate(db.current_tasks()):
            wid = TasksListItem(text=task_row['name'],
                                secondary_text=task_row['parent_name'] if task_row['parent_name'] else "Общий")
            wid.task_id = task_row['id']
            wid.label_id = task_row['label_id']
            wid.all_time = task_row['duration']
            wid.passed_time = task_row['passed_time']
            wid.priority = task_row['priority']
            wid.index = i
            wid.func_show_task = self.show_task
            self.ids.tasks_page.add_widget(wid)

    def round_button(self, screen=None):
        if not screen:
            print("Ошибка round_button")
            return

        if screen == 'task screen':
            self.task_adder.open()
        elif screen == 'short task screen':
            self.ids.shorttasks_box.task_card.show()

    def show_task(self, index, in_progress=None):

        current_task_bar_opened = self.ids.tasks_page.children[len(self.ids.tasks_page.children) - index - 2
                                                               ] == self.task_bar

        if in_progress:
            current_task = None
            for task in self.ids.tasks_page.children:
                if not isinstance(task, TasksListItem):
                    continue
                if task.index == index:
                    current_task = task
                else:
                    if task.ids.buttons.ids.play_button.in_progress:
                        task.ids.buttons.ids.play_button.in_progress = False

            if current_task_bar_opened:
                self.start_task(current_task)
            else:
                self.ids.tasks_page.remove_widget(self.task_bar)
                self.task_bar.opacity = 0

                self.ids.tasks_page.add_widget(self.task_bar, len(self.ids.tasks_page.children) - index - 1)
                anim = Animation(opacity=1, d=1)
                anim.bind(on_start=lambda *args: self.start_task(current_task))
                anim.start(self.task_bar)
                Clock.schedule_once(lambda *args: self._set_new_pos_y(index))
        elif in_progress is not None:
            self.ids.tasks_page.remove_widget(self.task_bar)
            self.task_bar.opacity = 0
            self.stop_task()
        else:  # Только показать, ничего не включать/выключать

            self.ids.tasks_page.remove_widget(self.task_bar)
            self.task_bar.opacity = 0

            # Если нажат тот же самый элемент списка, то не открываем еще раз там же, получается, только закрываем
            # то есть первым нажатием открылся таск, вторым закрылся
            if not current_task_bar_opened:
                self.ids.tasks_page.add_widget(self.task_bar, len(self.ids.tasks_page.children) - index - 1)
                anim = Animation(opacity=1, d=1)
                anim.start(self.task_bar)

                Clock.schedule_once(lambda *args: self._set_new_pos_y(index))

    def _set_new_pos_y(self, index):
        current_task = self.task_by_index(index)
        new_pos_y = (self.ids.tasks_page.parent.height - (
                current_task.y + current_task.height)) / -(
                    self.ids.tasks_page.height - self.ids.tasks_page.parent.height)
        anim = Animation(scroll_y=new_pos_y if new_pos_y >= 0 else 0, d=.3)
        anim.start(self.ids.tasks_page.parent)

    def task_by_index(self, index):
        for task in self.ids.tasks_page.children:
            if not isinstance(task, TasksListItem):
                continue
            if task.index == index:
                return task

    def start_task(self, current_task):
        self.task_bar.start_task(current_task)

    def stop_task(self):
        self.task_bar.stop_task()

    # endregion


class TasksListItem(ThreeLineAvatarIconListItem):
    '''Custom list item.'''

    icon = StringProperty("numeric-3-circle")
    index = NumericProperty()
    func_show_task = ObjectProperty()

    task_id = NumericProperty(0)
    all_time = NumericProperty(1800)
    passed_time = NumericProperty(0)
    label_id = NumericProperty(0)
    priority = NumericProperty(0)
    priority_colors = [(1, 0, 0, 1), (.94, .45, .15, 1), (.96, .79, .09, 1), (0, 1, 0, 1)]
    priority_icons = ['numeric-1-circle-outline', 'numeric-2-circle-outline',
                      'numeric-3-circle-outline', 'numeric-4-circle-outline']

    def show_task(self):
        self.func_show_task(self.index)

    def on_press_play_button(self, button):
        button.in_progress = not button.in_progress
        self.func_show_task(self.index, button.in_progress)
        if button.in_progress:
            db.set_active(self.task_id, self.label_id, True)
        else:
            db.save_completed_action(self.task_id, self.label_id)

    def on_press_stop_button(self, button):
        if button.in_progress:
            button.in_progress = False
            self.func_show_task(self.index, False)
            db.save_completed_action(self.task_id, self.label_id)
        db.remove_current_task(self.task_id)
        MDApp.get_running_app().root.refresh_tasks()


class TasksListItemRightField(IRightBodyTouch, MDBoxLayout):
    '''Custom right container.'''

    adaptive_width = True
    index = NumericProperty()
    task_list_item = ObjectProperty()

    def __draw_shadow__(self, origin, end, context=None):
        pass


class ContentNavigationDrawer(BoxLayout):
    pass


class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        '''Called when tap on a menu item.'''

        # Set the color of the icon and text for the menu item.
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color


class ItemDrawer(OneLineIconListItem):
    icon = StringProperty()


if __name__ == '__main__':
    MainApp().run()
