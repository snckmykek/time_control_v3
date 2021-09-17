"""
Переделал MDProgressBar
"""

__all__ = ("ReversedMDProgressBar",)

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.progressbar import ProgressBar

from kivymd.theming import ThemableBehavior
from kivy.core.audio import SoundLoader
from datetime import datetime


Builder.load_string(
    """
<ReversedMDProgressBar>
    canvas:
        Clear
        Color:
            rgba: self.theme_cls.divider_color
        Rectangle:
            size:
                (self.width, dp(6)) \
                if self.orientation == "horizontal" \
                else (dp(6), self.height)
            pos:
                (self.x, self.center_y - dp(6)) \
                if self.orientation == "horizontal" \
                else (self.center_x - dp(6),self.y)
        Color:
            rgba:
                self.color
        Rectangle:
            size:
                ( (self.width * (1 - self.value_normalized), sp(6)) \
                if self.orientation == "horizontal" \
                else (sp(6), self.height * (1 - self.value_normalized)) ) if not self.reversed \
                else ( (self.width * self.value_normalized, sp(6)) \
                if self.orientation == "horizontal" \
                else (sp(6), self.height * self.value_normalized) )
            pos:
                ( (self.x + self.width * (1 - self.value_normalized)) if \
                self.reversed else self.x + self.width * self.value_normalized, self.center_y - dp(6)) \
                if self.orientation == "horizontal" \
                else (self.center_x - dp(6), self.y)
"""
)


class ReversedMDProgressBar(ThemableBehavior, ProgressBar):
    orientation = OptionProperty(
        "horizontal", options=["horizontal", "vertical"]
    )
    """Orientation of progressbar. Available options are: `'horizontal '`,
    `'vertical'`.

    :attr:`orientation` is an :class:`~kivy.properties.OptionProperty`
    and defaults to `'horizontal'`.
    """

    color = ColorProperty([0, 1, 0, 1])
    """
    Progress bar color in ``rgba`` format.

    :attr:`color` is an :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    intermediate_mark = NumericProperty(.7)
    start_color = ColorProperty([0, 1, 0, 1])
    intermediate_color = ColorProperty([.94, .45, .15, 1])
    finish_color = ColorProperty([1, 0, 0, 1])
    """
    На старте полоска стартового цвета, подходя к middle_mark от 100% полоска плавно 
    сменяется на центральный цвет, затем сменяется на конечный
    """

    notify_deadline_time = NumericProperty(180)
    """
    По достижению конца полоски (когда закончилось время), через интервал вызывает функцию звук оповещения
    """

    _in_progress = BooleanProperty(False)
    """
    При старте тру, при стопе фолс, нужно, чтобы выходить из реверсивных функцию
    """

    _is_break = BooleanProperty(False)
    """
    Когда нажимаем на перерыв, полоска начинает заполняться обратно, но ничего не останавливается
    """
    break_time_start = datetime.now()

    first_duration = None
    second_duration = None
    """
    После переключения полоска заполняется обратно за время second_duration
    """

    reversed = BooleanProperty(False)

    sound = SoundLoader.load('water-drop-splash.wav')
    """
    Звук о дедлайне
    """

    running_transition = StringProperty("in_cubic")
    """Running transition.

    :attr:`running_transition` is an :class:`~kivy.properties.StringProperty`
    and defaults to `'in_cubic'`.
    """

    catching_transition = StringProperty("out_quart")
    """Catching transition.

    :attr:`catching_transition` is an :class:`~kivy.properties.StringProperty`
    and defaults to `'out_quart'`.
    """

    running_duration = NumericProperty(0.5)
    """Running duration.

    :attr:`running_duration` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `0.5`.
    """

    catching_duration = NumericProperty(0.8)
    """Catching duration.

    :attr:`running_duration` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `0.8`.
    """

    def __init__(self, **kwargs):
        self.schedule_func_notify_deadline = None
        self.running_anim = None
        self.running_anim2 = None
        super().__init__(**kwargs)

    def get_break_time(self):
        if not self._is_break:
            return 0

        delta = datetime.now() - self.break_time_start
        return delta.seconds

    def start(self):
        """Start outside from other funcs"""
        self._is_break = False
        self._start()

    def _start(self):
        self._set_default_value(0)
        self._in_progress = True
        self._create_determinate_animations()
        self.running_away()

        if self._is_break:
            self.break_time_start = datetime.now()

    def stop(self):
        """Stop outside from other funcs"""
        self._stop()

    def _stop(self):
        """Stop animation and schedule"""
        self._in_progress = False
        if self.schedule_func_notify_deadline is not None:
            self.schedule_func_notify_deadline.cancel()

        Animation.cancel_all(self)

    def change_mode(self):
        """
        переключает режим: работа/отдых
        :return:
        """
        self._stop()

        self._is_break = not self._is_break
        self.reversed = not self.reversed
        self.value = 0

        self._start()

    def running_away(self, *args):
        if self.value < 100 * self.intermediate_mark:
            self.running_anim.start(self)
        else:
            self.running_away2()

    def running_away2(self, *args):
        self.running_anim2.start(self)

    def notify_deadline(self, *args):
        self._notify_deadline()
        if "Проверка на необходимоть оповещения":
            self.schedule_func_notify_deadline = Clock.schedule_interval(self._notify_deadline, self.notify_deadline_time)

    def _notify_deadline(self, *args):
        self.sound.play()

    def _create_determinate_animations(self):
        if self.value < 100 * self.intermediate_mark:
            running_duration = (100 * self.intermediate_mark - self.value) / (100 - self.value) * self.running_duration
            running_duration2 = 100 * (1 - self.intermediate_mark) / (100 - self.value) * self.running_duration
        else:
            running_duration = 0
            running_duration2 = self.running_duration

        self.running_anim = Animation(
            value=100 * self.intermediate_mark,
            color=self.intermediate_color,
            t=self.running_transition,
            d=running_duration,
        )
        self.running_anim.bind(on_complete=self.running_away2)

        self.running_anim2 = Animation(
            value=100,
            color=self.finish_color,
            t=self.running_transition,
            d=running_duration2,
        )
        self.running_anim2.bind(on_complete=self.notify_deadline)

    def _set_default_value(self, interval):
        self._x = 0
        if self._is_break:
            if self.second_duration:
                self.running_duration = self.second_duration
            self.start_color = [1, 0, 0, 1]
            self.intermediate_color = [.94, .45, .15, 1]
            self.finish_color = [0, 1, 0, 1]
            self.intermediate_mark = .3
        else:
            if self.first_duration:
                self.running_duration = self.first_duration
            self.start_color = [0, 1, 0, 1]
            self.intermediate_color = [.94, .45, .15, 1]
            self.finish_color = [1, 0, 0, 1]
            self.intermediate_mark = .7

        before_intermediate_mark = self.value < 100 * self.intermediate_mark
        value = self.value if before_intermediate_mark else self.value - 100 * self.intermediate_mark
        coef = self.intermediate_mark if before_intermediate_mark else (1 - self.intermediate_mark)
        self.color = [a + (b - a) * value / (coef * 100)
                      for a, b in zip(self.start_color if before_intermediate_mark else self.intermediate_color,
                                      self.intermediate_color if before_intermediate_mark else self.finish_color)]