from kivy.lang.builder import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.clock import Clock

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.theming import ThemableBehavior
from kivymd.uix.progressbar import MDProgressBar

from functools import partial

from db_requests import db

Builder.load_string("""
#: import ReversedMDProgressBar reversedprogressbar
<TaskBar>:
    orientation: 'vertical'
    
    canvas:
        Color:
            rgba:
                self.theme_cls.divider_color
        Line:
            points: 
                root.x ,root.y, root.x + self.width, root.y

    ReversedMDProgressBar:
        size_hint_y: None
        height: "16dp"
        id: progress
        type: "determinate"
        running_duration: 1800
        running_transition: 'linear'
        reversed: False

    MDBoxLayout:
        orientation: 'vertical'
        
        MDLabel:
            size_hint_y: .2
            text: "Возможно описание задачи или еще что-нибудь..."
            padding: ["16dp", "8dp"]
                
        MDBoxLayout:
            size_hint_y: .8
            MDBoxLayout: 
                padding: "8dp"
                md_bg_color: [*list(progress_pomodoro.finish_color)[:3], .3]  if progress_pomodoro.value == 100 else [1, 1, 1, 1]
                
                MDBoxLayout:
                    size_hint_x: .85
                    orientation: 'vertical'
                    Widget:
                        size_hint_y: .8
                    MDLabel:
                        size_hint_y: .2
                        padding: ["16dp", "8dp"]
                        pos_hint: {"center_x": .5}
                        halign: 'left'
                        text: "test test test test test test test test test test test test "
                        multiline: True 
                
                MDBoxLayout:
                    size_hint_x: .15
                    orientation: 'vertical'
                    ReversedMDProgressBar:
                        id: progress_pomodoro
                        size_hint_y: .7
                        pos_hint: {"center_x": .5}
                        start_color: [0, 1, 0, 1]
                        intermediate_color: [.94, .45, .15, 1]
                        finish_color: [1, 0, 0, 1]
                        intermediate_mark: .3
                        size_hint_x: None
                        width: "20dp"
                        type: "determinate"
                        running_duration: 25*60
                        running_transition: 'linear'
                        reversed: False
                        orientation: 'vertical'
                        value: 0
                    
                    MDLabel:
                        size_hint_y: .15
                        pos_hint: {"center_x": .5}
                        halign: 'center'
                        text: "{:02d}:{:02d}".format(*[int(x) for x in divmod( \
                            (1 - progress_pomodoro.value/100)*(root.pomodoro_work_duration \
                            if not progress_pomodoro._is_break else root.pomodoro_break_duration), 60)])
                    MDIconButton:         
                        icon: "play" if progress_pomodoro._is_break else "coffee"
                        on_release: root.change_mode()  
        
""")


class TaskBar(MDBoxLayout, ThemableBehavior):
    # Состояние задачи - выполнение или перерыв
    in_progress = BooleanProperty()
    current_task = ObjectProperty()

    pomodoro_work_duration = 1500
    pomodoro_break_duration = 300

    def __draw_shadow__(self, origin, end, context=None):
        pass

    def __init__(self, **kwargs):
        super(TaskBar, self).__init__(**kwargs)

    def start_task(self, current_task):
        self.current_task = current_task

        self.stop_task()

        task = db.get_task(self.current_task.task_id)
        self.in_progress = True
        self.ids.progress.value = task['passed_time'] / task['duration'] * 100 if task['passed_time'] < task[
            'duration'] else 100
        self.ids.progress.running_duration = (task['duration'] - task[
            'passed_time']) if task['passed_time'] < task['duration'] else 0
        self.ids.progress.start()

        self.ids.progress_pomodoro.value = 0
        self.ids.progress_pomodoro.first_duration = self.pomodoro_work_duration
        self.ids.progress_pomodoro.second_duration = self.pomodoro_break_duration
        self.ids.progress_pomodoro.start()

    def stop_task(self, *args):
        self.in_progress = False
        self.ids.progress.stop()
        self.ids.progress_pomodoro.stop()

    def change_mode(self):
        break_time = self.ids.progress_pomodoro.get_break_time()  # Возвращает 0 если сейчас не перерыв
        if break_time:
            db.save_break_time(self.current_task.task_id, break_time, self.current_task.label_id)
        self.ids.progress_pomodoro.change_mode()
