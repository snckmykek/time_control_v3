import datetime

from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty, ListProperty, StringProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineAvatarIconListItem

from common import RightCheckbox, refresh_indexes
from db_requests import db
from task_card import ShortTaskCard

Builder.load_string("""
<ShortTasksBox>:
    orientation: 'vertical'
    shorttasks: shorttasks

    RecycleView:
        viewclass: "ShortTaskRow"
        data: root.shorttasks_data
        id: shorttasks
        RecycleBoxLayout:
            default_size: None, dp(56)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            
<ShortTaskRow>:
    on_release: root.row_on_release()
    text: "{}, {} / {}".format(root.task_name, root.count, root.qty)

    IconLeftWidget:
        # icon: "plus"
        on_release: root.icon_on_release()
        theme_text_color: "Custom"
        text_color: app.theme_cls.icon_color

    RightCheckbox:
        id: checkbox
        # checkbox_icon_normal: "" if root.is_button else "checkbox-blank-outline"
        # checkbox_icon_down: "" if root.is_button else "checkbox-marked"
        active: root.count == root.qty
        on_release: root.checkbox_on_release()
""")


class ShortTasksBox(MDBoxLayout):
    shorttasks_data = ListProperty()
    shorttasks = ObjectProperty()
    task_card = ObjectProperty()

    def __init__(self, **kwargs):
        super(ShortTasksBox, self).__init__(**kwargs)
        Clock.schedule_once(lambda *args: self.refresh_tasks())
        self.init_task_card()

    def init_task_card(self):
        if not self.task_card:
            self.task_card = ShortTaskCard()
            self.task_card.bind(on_dismiss=lambda *args: self.refresh_tasks())

    def refresh_tasks(self):
        _shorttasks = list()
        for shorttask_row in db.shorttasks():
            elem = {
                'shorttask_id': shorttask_row['id'],
                'custom_index': 0,
                'task_name': shorttask_row['name'],
                'count': shorttask_row['count'],
                'qty': shorttask_row['qty'],
                'priority': shorttask_row['priority'],
                'remind_time': shorttask_row['remind_time'],
                'reminded': shorttask_row['reminded'],
                'func_checkbox_on_release': self.change_shorttasks_data,
                'func_row_on_release': self.open_task_card
            }
            _shorttasks.append(elem)

        self.shorttasks_data = _shorttasks

        refresh_indexes(self.shorttasks_data, 'custom_index')

    def change_shorttasks_data(self, index, key, value):
        self.shorttasks_data[index][key] = value

    def open_task_card(self, task_id):
        self.task_card.show(task_id=task_id)


class ShortTaskRow(OneLineAvatarIconListItem):
    shorttask_id = NumericProperty(0)
    task_name = StringProperty()
    count = NumericProperty()
    qty = NumericProperty()
    priority = NumericProperty()
    remind_time = datetime.datetime.now()
    reminded = BooleanProperty(False)
    custom_index = NumericProperty()

    func_row_on_release = ObjectProperty()
    func_icon_on_release = ObjectProperty()
    func_checkbox_on_release = ObjectProperty()

    def __init__(self, **kwargs):
        super(ShortTaskRow, self).__init__(**kwargs)

    def icon_on_release(self):
        pass

    def checkbox_on_release(self):
        if self.count == self.qty:
            self.count = 0
        else:
            self.count += 1

        if self.func_checkbox_on_release:
            self.func_checkbox_on_release(self.custom_index, 'count', self.count)

        db.set_shorttasks_count(self.shorttask_id, self.count)

    def row_on_release(self):
        if self.func_row_on_release:
            self.func_row_on_release(self.shorttask_id)
