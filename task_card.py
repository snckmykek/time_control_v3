from kivy.lang import Builder
from kivy.uix.modalview import ModalView

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

from db_requests import db

Builder.load_string("""
<TaskCard>:
    background: ''
    background_color: 0, 0, 0, 0

    MDCard:
        orientation: "vertical"
        padding: "8dp"
        size_hint: None, None
        width: "240dp"
        height: self.minimum_height
        pos_hint: {"center_x": .5, "center_y": .5}
        
        MDBoxLayout:
            size_hint: None, None
            size: "224dp", self.minimum_height
             
            Widget:

            MDRectangleFlatIconButton:
                text: "Delete"
                icon: "delete-forever"
                on_release: root.show_del_dialog()
                        
        MDTextField:
            id: task_name
            hint_text: "task name"
            mode: "rectangle"
            theme_text_color: "Secondary"
            size_hint_x: None
            width: "200dp"
            pos_hint: {"center_x": .5, "center_y": .5}
        
        MDTextField:
            id: parent_task_name
            # todo сделать чт сюда нельзя писать а надо нажать на что то и выбирать из списка
            hint_text: "parent task"
            mode: "rectangle"
            theme_text_color: "Secondary"
            size_hint_x: None
            width: "200dp"
            pos_hint: {"center_x": .5, "center_y": .5}
            
        Widget:
            size_hint_y: None
            height: "20dp"
        
        MDBoxLayout:
            size_hint: None, None
            size: "224dp", self.minimum_height
            
            MDRectangleFlatIconButton:
                text: "Cancel"
                icon: "cancel"
                on_release: root.dismiss()
                
            Widget:
            
            MDRectangleFlatIconButton:
                text: "Save"
                icon: "check"
                on_release: root.create_task()
            
            
<ShortTaskCard>:
    background: ''
    background_color: 0, 0, 0, 0

    MDCard:
        orientation: "vertical"
        padding: "8dp"
        size_hint: None, None
        width: "240dp"
        height: self.minimum_height
        pos_hint: {"center_x": .5, "center_y": .5}
        
        MDBoxLayout:
            size_hint: None, None
            size: "224dp", self.minimum_height
             
            Widget:

            MDRectangleFlatIconButton:
                text: "Delete"
                icon: "delete-forever"
                on_release: root.show_del_dialog()
                        
        MDTextField:
            id: task_name
            hint_text: "task name"
            mode: "rectangle"
            theme_text_color: "Secondary"
            size_hint_x: None
            width: "200dp"
            pos_hint: {"center_x": .5, "center_y": .5}
            
        Widget:
            size_hint_y: None
            height: "20dp"
        
        MDBoxLayout:
            size_hint: None, None
            size: "224dp", self.minimum_height
            
            MDRectangleFlatIconButton:
                text: "Cancel"
                icon: "cancel"
                on_release: root.dismiss()
                
            Widget:
            
            MDRectangleFlatIconButton:
                text: "Save"
                icon: "check"
                on_release: root.create_task()        
""")


class TaskCard(ModalView):
    task_id = None
    task_name = ""
    parent_id = None
    full_card = False

    del_dialog = None

    def __init__(self, **kwargs):
        super(TaskCard, self).__init__(**kwargs)

    def show(self, task_id=None, task_name="", parent_id=0):
        if task_id:  # Открытие старого таска для редактирования
            self.task_id = task_id
            task_row = db.get_task(self.task_id)
            self.task_name = task_row['name']
            self.parent_id = task_row['parent_id']
        else:  # Создание нового таска
            self.task_name = task_name
            self.parent_id = parent_id

        self.ids.task_name.set_text(self.ids.task_name, self.task_name)

        self.refresh_form()

        self.ids.parent_task_name.focus = True  # todo Иначе уебищно отрисовывает
        self.ids.task_name.focus = True  # todo Иначе уебищно отрисовывает

        self.open()

    def refresh_form(self):
        parent_task = db.get_task(self.parent_id)
        if parent_task:
            self.ids.parent_task_name.set_text(self.ids.parent_task_name, parent_task['name'])
        else:
            self.ids.parent_task_name.set_text(self.ids.parent_task_name, "")

    def create_task(self):
        if not self.task_id:
            db.create_new_task(self.ids.task_name.text, self.parent_id)
        else:
            db.update_task(self.task_id, self.ids.task_name.text, self.parent_id)
        self.dismiss()

    def delete_task(self):
        if not self.task_id:  # новую несохраненную удалить нельзя
            return

        db.delete_task(self.task_id)
        self.del_dialog.dismiss()
        self.dismiss()

    def show_del_dialog(self):
        if not self.task_id:  # новую несохраненную удалить нельзя
            return

        if not self.del_dialog:
            self.del_dialog = MDDialog(
                text="Delete task and ALL dependent tasks?",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda *x: self.del_dialog.dismiss()
                    ),
                    MDFlatButton(
                        text="YES",
                        on_release=lambda *x: self.delete_task()
                    ),
                ],
            )

        self.del_dialog.open()


class ShortTaskCard(ModalView):
    task_id = None
    task_name = ""
    full_card = False

    del_dialog = None

    def __init__(self, **kwargs):
        super(ShortTaskCard, self).__init__(**kwargs)

    def show(self, task_id=None, task_name="", parent_id=0):
        self.task_id = task_id
        if task_id:  # Открытие старого таска для редактирования
            task_row = db.get_shorttask(self.task_id)
            self.task_name = task_row['name']
        else:  # Создание нового таска
            self.task_name = task_name

        self.ids.task_name.set_text(self.ids.task_name, self.task_name)

        self.ids.task_name.focus = True  # todo Иначе уебищно отрисовывает

        self.open()

    def create_task(self):
        if not self.task_id:
            db.create_new_shorttask(self.ids.task_name.text)
        else:
            db.update_shorttask(self.task_id, self.ids.task_name.text)
            # todo: Добавить остальные параметры шорт таска, типа приоритет и время напоминалки
        self.dismiss()

    def delete_task(self):
        if not self.task_id:  # новую несохраненную удалить нельзя
            return

        db.delete_shorttask(self.task_id)
        self.del_dialog.dismiss()
        self.dismiss()

    def show_del_dialog(self):
        if not self.task_id:  # новую несохраненную удалить нельзя
            return

        if not self.del_dialog:
            self.del_dialog = MDDialog(
                text="Delete short task?",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda *x: self.del_dialog.dismiss()
                    ),
                    MDFlatButton(
                        text="YES",
                        on_release=lambda *x: self.delete_task()
                    ),
                ],
            )

        self.del_dialog.open()

