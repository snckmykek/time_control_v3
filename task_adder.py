# todo: очищать данные перед новым заполнением и открытием по кнопке Add
import datetime
import re

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.uix.modalview import ModalView

from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty, ListProperty, \
    OptionProperty, ColorProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.theming import ThemableBehavior

from kivymd.uix.list import TwoLineAvatarIconListItem
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.tab import MDTabsBase

from task_card import TaskCard
from db_requests import db
from common import RightCheckbox, refresh_indexes

is_initialization = False
time_dialog = None


def change_is_initialization():
    global is_initialization
    is_initialization = not is_initialization


def init_time_dialog():
    global time_dialog
    time_dialog = TimeDialog(title="Task",
                             type="custom",
                             content_cls=TimeDialogContent(),
                             buttons=[
                                 MDFlatButton(
                                     text="CANCEL"),
                                 MDFlatButton(
                                     text="OK")])

    time_dialog.bind(on_pre_open=time_dialog.update_height)
    for button in time_dialog.buttons:
        if button.text == "CANCEL":
            button.bind(on_release=time_dialog.cancel)
        elif button.text == "OK":
            button.bind(on_release=time_dialog.add_task_to_current)


Builder.load_string("""
<TaskAdder>:
    background: ''
    background_color: 0, 0, 0, 0
    
    MDCard:
        orientation: "vertical"
        padding: "8dp"
        # size_hint: None, None
        # size: "280dp", "560dp"
        pos_hint: {"center_x": .5, "center_y": .5}
        
        MDTabs:
            id: tabs
            
            Tab:
                title: "tree"
                RecycleView:
                    viewclass: "TreeListItem"
                    id: tasks_tree
                    RecycleBoxLayout:
                        default_size: None, dp(56)
                        default_size_hint: 1, None
                        size_hint_y: None
                        height: self.minimum_height
                        orientation: 'vertical'
                        
            Tab:
                title: "added"
                MDBoxLayout:
                    orientation: 'vertical'
                    MyMDTextField:
                        task_adder: root
                        hint_text: "Search"
                        mode: "rectangle"
                        theme_text_color: "Secondary"
                        size_hint: None, None
                        width: "300dp"
                        font_size: "16sp"
                        pos_hint: {"center_x": .5, "center_y": .5}
                        icon_right: "plus"
                        icon_right_color: app.theme_cls.primary_light
                    
                    Widget:
                        size_hint_y: None
                        height: "4dp"
                        
                    MDSeparator:
                        height: "1dp"
            
                    ScrollView:
                        MDList:
                            id: added_tasks
             
                      
<TreeListItem>:
    
    Widget:
        size_hint_x: None
        width: dp(10) * root.level

    OneLineAvatarIconListItem:
        text: root.text
        on_release: root.row_on_release()

        IconLeftWidget:
            icon: "plus" if root.is_button else (\
                'arrow-down-drop-circle-outline' if not root.deployed else 'arrow-up-drop-circle-outline')
            on_release: root.icon_on_release()
            theme_text_color: "Custom"
            text_color: app.theme_cls.icon_color
    
        RightCheckbox:
            id: checkbox
            checkbox_icon_normal: "" if root.is_button else "checkbox-blank-outline"
            checkbox_icon_down: "" if root.is_button else "checkbox-marked"
            active: root.active
            on_release: root.checkbox_on_release()
    
    
<MyMDTextField>:


<EmptyWidget@Widget, ILeftBody>:


<Tab>:
    title: 'Tab'
    
           
<PriorityToggleButton@ToggleButton>:
    background_normal: ""
    background_down: "images/checkmark.png"
    background_color: (0, 1, 0, 1)
    border: [0, 0, 0, 0]
    group: "x"


<TimeInputTextField>
    size_hint: None, 1
    width: dp(96)
    mode: "fill"
    active_line: False
    font_size: dp(56)
    line_color_normal: 0, 0, 0, 0
    on_text: root.on_text
    on_text_validate: root._set_new_focus()
    radius: [dp(10), ]


<TimeInput>
    size_hint: None, None
    _hour: hour
    _minute: minute

    TimeInputTextField:
        id: hour
        num_type: "hour"
        pos: 0, 0
        text_color: root.text_color
        disabled: root.disabled
        on_text: root.dispatch("on_time_input")
        radius: root.hour_radius
        on_select:
            root.dispatch("on_hour_select")
            root.state = "hour"
        fill_color:
            [*root.bg_color_active[:3], 0.5] \
            if root.state == "hour" else [*root.bg_color[:3], 0.5]
        focus_next: minute


    MDLabel:
        text: ":"
        size_hint: None, None
        size: dp(24), dp(80)
        halign: "center"
        valign: "center"
        font_size: dp(50)
        pos: dp(96), 0
        theme_text_color: "Custom"
        text_color: root.text_color

    TimeInputTextField:
        id: minute
        num_type: "minute"
        pos: dp(120), 0
        text_color: root.text_color
        disabled: root.disabled
        on_text: root.dispatch("on_time_input")
        radius: root.minute_radius
        on_select:
            root.dispatch("on_minute_select")
            root.state = "minute"
        fill_color:
            [*root.bg_color_active[:3], 0.5] \
            if root.state == "minute" else [*root.bg_color[:3], 0.5]
        focus_previous: hour

<TimeDialogContent>:
    orientation: 'vertical'
    spacing: '10dp'
    size_hint_y: None
    height: '200dp'
    
    _time_input: _time_input
    _description: description
    
    TimeInput:
        id: _time_input
        size: dp(216), dp(62)
        pos_hint: {'center_x': .5}
        bg_color:
            root.accent_color if root.accent_color else \
            root.theme_cls.primary_light
        bg_color_active:
            root.selector_color if root.selector_color \
            else root.theme_cls.primary_color
        text_color:
            root.input_field_text_color if root.input_field_text_color else \
            root.theme_cls.text_color
        on_time_input: root._get_time_input(*self.get_time())
        minute_radius: root.minute_radius
        hour_radius: root.hour_radius
    
    MDBoxLayout: 
        size_hint_y: None
        height: '48dp'
        id: priority_buttons
        MDCheckbox:
            unselected_color: (.13, .59, .95, .5)
            selected_color: (.13, .59, .95, 1)
            radio_icon_normal: 'numeric-1-circle-outline'
            radio_icon_down: 'numeric-1-circle-outline'
            group: 'x'
            on_press: root._set_priority(0)
        MDCheckbox:
            unselected_color: (.13, .59, .95, .5)
            selected_color: (.13, .59, .95, 1)
            radio_icon_normal: 'numeric-2-circle-outline'
            radio_icon_down: 'numeric-2-circle-outline'
            group: 'x'
            on_press: root._set_priority(1)
        MDCheckbox:
            unselected_color: (.13, .59, .95, .5)
            selected_color: (.13, .59, .95, 1)
            radio_icon_normal: 'numeric-3-circle-outline'
            radio_icon_down: 'numeric-3-circle-outline'
            group: 'x'
            on_press: root._set_priority(2)
        MDCheckbox:
            unselected_color: (.13, .59, .95, .5)
            selected_color: (.13, .59, .95, 1)
            radio_icon_normal: 'numeric-4-circle-outline'
            radio_icon_down: 'numeric-4-circle-outline'
            group: 'x'
            on_press: root._set_priority(3) 
    
    
    
    MDTextField:
        id: description
        hint_text: "Description"
        mode: "rectangle"
        multiline: True
        
""")


class Tab(MDFloatLayout, MDTabsBase):
    pass


class TaskAdder(ModalView):
    """
    Окно, в котором можно выбрать задачи на текущий день.
    2 варианта выбора задачи: деревом и из списка.

    Принцип работы дерева:
    При открытии запрос возвращает задачи верхнего уровня (без родителей),
    при нажатии на кнопку в начале строки задачи, запрос тянет ее детей, и
    так можно но бесконечности.
    С точки зрения кодирования, это всё один список, у элементов которого есть
    атрибут Уровень, это уровень вложенности, от которого зависит отступ от начала
    экрана (для наглядности).
    При повторном нажатии на кнопку все подчиненные элементы рекурсивно
    удаляются из списка.

    Принцип работы списка:
    Сортированный список, при изменении текста окна поиска отправляет запрос
    на возврат нового списка с учетом вхождения текста поиска в наименование.

    TODO: добавить выбор сотртировки: наименование, частота использования, последние
    """

    def __init__(self, **kwargs):
        super(TaskAdder, self).__init__(**kwargs)
        self.task_card = None
        self.init_task_card()

    def init_task_card(self):
        if not self.task_card:
            self.task_card = TaskCard()
            self.task_card.bind(on_dismiss=lambda *args: self.refresh_tasks_in_tree())

    def on_pre_open(self):
        self.refresh_tasks_in_tree()

    def refresh_tasks_in_tree(self):
        """
        Очищает список задач на вкладке "Дерево" и заново его формирует.
        """
        self._add_tasks_to_tree(deploy=True)

    def change_task_active(self, custom_index):
        data = self.ids.tasks_tree.data

        try:
            self.set_data_attr(custom_index, 'active', not data[custom_index]['active'])
        except IndexError:
            return

        elem = data[custom_index]
        if elem['active']:
            if not time_dialog:
                init_time_dialog()

            time_dialog.task_id = elem['task_id']
            time_dialog.cancel_func = lambda *x: self._cancel_adding_to_current(custom_index)
            time_dialog.open()
        else:
            db.remove_current_task(elem['task_id'])

    def _cancel_adding_to_current(self, custom_index):
        self.set_data_attr(custom_index, 'active', False)

        # TODO: в списке и даже объекте проставляется active = False, а в чекбоксе хуй, разобраться
        # МБ мз-за того что я в чекбокс добавил ButtonBehavior
        for elem in self.ids.tasks_tree.children[0].children:
            if elem.custom_index == custom_index:
                elem.ids.checkbox.active = False

    def change_nesting_level(self, custom_index):
        data = self.ids.tasks_tree.data

        try:
            self.set_data_attr(custom_index, 'deployed', not data[custom_index]['deployed'])
        except IndexError:
            return

        elem = data[custom_index]
        self._add_tasks_to_tree(elem['level'] + 1, elem['task_id'], elem['custom_index'], elem['deployed'])

    def open_task_card(self, task_id):
        self.task_card.show(task_id=task_id)

    # все изменения объектов нужно вносить в список, а не в объекты
    def set_data_attr(self, custom_index, attr_name, new_value):
        data = self.ids.tasks_tree.data
        try:
            data[custom_index][attr_name] = new_value
        except IndexError:
            return
        except AttributeError:
            return

    def _add_tasks_to_tree(self, level=0, parent_id=0, custom_index=0, deploy=False):

        data = list(self.ids.tasks_tree.data)

        if deploy:

            if parent_id == 0:
                end_part = list()
                new_data = list()
            else:
                end_part = data[custom_index + 1:]
                new_data = data[:custom_index + 1]

            for task_row in db.tasks_by_parent_id(parent_id):
                task = dict(is_button=False,
                            text=task_row['name'],
                            level=level,
                            task_id=task_row['id'],
                            custom_index=0,
                            parent_id=task_row['parent_id'] if task_row['parent_id'] else 0,
                            active=task_row['added'],
                            deployed=False,
                            icon_press_func=self.change_nesting_level,
                            row_press_func=self.open_task_card,
                            checkbox_press_func=self.change_task_active)
                new_data.append(task)

            parent_task = db.get_task(parent_id)
            if parent_task:
                inscription = f" to \"{parent_task['name']}\""
            else:
                inscription = ""

            task = dict(is_button=True,
                        text="Add" + inscription,
                        level=level,
                        task_id=0,
                        custom_index=0,
                        parent_id=parent_id,
                        active=False,
                        deployed=False,
                        icon_press_func=None,
                        row_press_func=self.add_new_task,
                        checkbox_press_func=None)
            new_data.append(task)

            new_data = new_data + end_part

        else:  # свернуть
            # Т.к. список упорядоченный, удаляем до тех пор, пока не настанет индекс <= того, до которого сворачиваем

            new_data = data

            while True:
                try:
                    elem = new_data[custom_index + 1]
                except IndexError:
                    break

                if elem['level'] >= level:
                    new_data.remove(elem)
                else:
                    break

        refresh_indexes(new_data, 'custom_index')

        self.ids.tasks_tree.data = new_data

    def add_new_task(self, task_name="", parent_id=0):
        self.task_card.show(task_id=None, task_name=task_name, parent_id=parent_id)


class TreeListItem(MDBoxLayout):
    '''Custom list item.'''

    text = StringProperty("")  # Для передачи в текстоприемник:)
    icon = StringProperty("android")
    custom_index = NumericProperty(0)
    level = NumericProperty(1)  # Уровень вложенности
    deployed = BooleanProperty(False)  # Развернут на детей
    is_button = BooleanProperty(False)

    task_id = NumericProperty(0)
    parent_id = ObjectProperty(None)
    active = BooleanProperty(False)

    icon_press_func = None
    row_press_func = None
    checkbox_press_func = None

    def __init__(self, **kwargs):
        super(TreeListItem, self).__init__(**kwargs)

    def icon_on_release(self):
        if self.icon_press_func:
            self.icon_press_func(self.custom_index)

    def checkbox_on_release(self):
        if self.checkbox_press_func:
            self.checkbox_press_func(self.custom_index)

    def row_on_release(self):
        if self.row_press_func:
            if self.is_button:
                # открытие нового таска и передача туда айди родителя в иерархии
                self.row_press_func(parent_id=self.parent_id)
            else:
                # открытие текущего таска по айди
                self.row_press_func(task_id=self.task_id)


class AddedListItem(TwoLineAvatarIconListItem):
    '''Custom list item.'''

    icon = StringProperty("android")
    index = NumericProperty()
    level = 1  # Уровень вложенности

    task_id = 0
    parent_id = 0

    def __init__(self, **kwargs):
        super(AddedListItem, self).__init__(**kwargs)


class MyMDTextField(MDTextField):
    task_adder = ObjectProperty()

    def __init__(self, **kwargs):
        super(MyMDTextField, self).__init__(**kwargs)

    def on_touch_down(self, touch):

        # Определено нажатие на правую иконку
        if self.collide_point(*touch.pos):
            if self.icon_right:
                icon_x = (self.width + self.x) - (self._lbl_icon_right.texture_size[1]) - dp(8)
                icon_y = self.center[1] - self._lbl_icon_right.texture_size[1] / 2
                if self.mode == "rectangle":
                    icon_y -= dp(4)
                elif self.mode != 'fill':
                    icon_y += dp(8)

                if touch.pos[0] > icon_x and touch.pos[1] > icon_y:
                    self.task_adder.add_new_task(self.text)

        return super(MyMDTextField, self).on_touch_down(touch)


class TimeDialogContent(MDBoxLayout, ThemableBehavior):
    _func_set_priority = ObjectProperty()
    _description = ObjectProperty()

    # TimeInput
    _time_input = ObjectProperty()
    accent_color = ColorProperty(None)
    selector_color = ColorProperty(None)
    input_field_text_color = ColorProperty(None)
    hour = StringProperty("00")
    minute = StringProperty("00")
    minute_radius = ListProperty([dp(5), ])
    hour_radius = ListProperty([dp(5), ])

    def __init__(self, **kwargs):
        super(TimeDialogContent, self).__init__(**kwargs)

        self.hour = "00"
        self.minute = "00"

    def _set_priority(self, new_priority):
        if self._func_set_priority:
            self._func_set_priority(new_priority)

    def _get_time_input(self, hour, minute):
        if hour:
            self.hour = f"{int(hour):01d}"
        if minute:
            self.minute = f"{int(minute):01d}"


class TimeDialog(MDDialog):
    cancel_func = None
    task_id = NumericProperty(0)
    auto_dismiss = False

    # Задумка такая, что кнопка в списке кнопок (self.content_cls.ids.priority_buttons.children) зажимается по
    # порядкому номеру приорити, например, если приорити 0, то это первая в списке кнопка (список[0].state = "down")
    # НО список детей собирается в обратном порядке, поэтому приорити 0, тогда список[длина - 1 - 0].state = "down"
    priority = 0

    def __init__(self, **kwargs):
        super(TimeDialog, self).__init__(**kwargs)

        self.content_cls._func_set_priority = self._set_priority

    def on_pre_open(self):
        task = db.get_task(self.task_id)
        if task:
            self.title = str(task['name'])
        priority = 0

        buttons = self.content_cls.ids.priority_buttons.children
        buttons[len(buttons) - 1 - priority].state = "down"

        self.content_cls._time_input.set_time(["00", "00"])

    def on_open(self):
        self.content_cls._time_input._hour.focus = True

    def cancel(self, *args):
        if self.cancel_func:
            self.cancel_func()
        self.dismiss()

    def _set_priority(self, new_priority):
        self.priority = new_priority

    def add_task_to_current(self, *args):
        hours = self.content_cls.hour  # HH:mm
        minutes = self.content_cls.minute  # HH:mm
        duration = int(hours) * 3600 + int(minutes) * 60
        label_id = 0  # todo: временно, пока хз чо с ними делать self.content_cls.ids.label.text
        db.add_task_to_current(self.task_id, label_id, is_active=False, priority=self.priority, duration=duration)
        self.dismiss()


class TimeInputTextField(MDTextField):
    num_type = OptionProperty("hour", options=["hour", "minute"])
    hour_regx = "^[0-9]$|^[0-1][0-9]$|^2[0-3]$"
    minute_regx = "^[0-9]$|^0[0-9]$|^[1-5][0-9]$"
    _entered_character_number = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.on_text)
        self.register_event_type("on_select")
        self.bind(text_color=self.setter("_current_hint_text_color"))
        self.bind(text_color=self.setter("current_hint_text_color"))

    def get_cursor_from_index(self, index):
        return [2, 0]

    def get_cursor_from_xy(self, x, y):
        return [2, 0]

    def do_backspace(self, from_undo=False, mode='bkspc'):
        self.text = "".join(["0", self.text[:1]])
        self._entered_character_number = max(self._entered_character_number - 1, 0)

    def validate_time(self, s):
        reg = self.hour_regx if self.num_type == "hour" else self.minute_regx
        return re.match(reg, s)

    def insert_text(self, s, from_undo=False):
        if len(s) > 2:
            return

        if self._entered_character_number == 0:  # вводится первый символ
            self.text = "00"

        text = self.text[len(s):].strip()
        current_string = "".join([text, s])
        if not self.validate_time(current_string):
            s = ""
        else:
            self.text = self.text[len(s):]
            if self._entered_character_number >= 1:  # в этом окне введен уже второй символ, переходим в некст окно
                self._set_new_focus()
            self._entered_character_number += 1

        return super().insert_text(s, from_undo=from_undo)

    def _set_new_focus(self):
        if self.num_type == "hour":
            self.focus_next.focus = True
        else:
            self.focus_previous.focus = True

    def on_text(self, *args):
        """
        Texts should be center aligned. now we are setting the padding of text
        to somehow make them aligned.
        """

        self._refresh_text(self.text)
        max_size = max(self._lines_rects, key=lambda r: r.size[0]).size
        dx = (self.width - max_size[0]) / 2.0
        dy = (self.height - max_size[1]) / 2.0
        self.padding = [dx, dy, dx, dy]

    def on_focus(self, *args):
        if not self.focus:  # Зануляю при анфокусе потому что при фокусе криво работает
            self._entered_character_number = 0
        super().on_focus(*args)
        if not self.text.strip():
            self.text = "00"

    def on_select(self, *args):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch("on_select")
            super().on_touch_down(touch)


class TimeInput(MDRelativeLayout, EventDispatcher):
    bg_color = ColorProperty()
    bg_color_active = ColorProperty()
    text_color = ColorProperty()
    disabled = BooleanProperty(False)
    minute_radius = ListProperty([0, 0, 0, 0])
    hour_radius = ListProperty([0, 0, 0, 0])
    state = StringProperty("hour")
    _hour = ObjectProperty()
    _minute = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_time_input")
        self.register_event_type("on_hour_select")
        self.register_event_type("on_minute_select")

    def set_time(self, time_list):
        hour, minute = time_list
        self._hour.text = hour
        self._minute.text = minute

    def get_time(self):
        hour = self._hour.text.strip()
        minute = self._minute.text.strip()
        return [hour, minute]

    def _update_padding(self, *args):
        self._hour.on_text()
        self._minute.on_text()

    def on_time_input(self, *args):
        pass

    def on_minute_select(self, *args):
        pass

    def on_hour_select(self, *args):
        pass
