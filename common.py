from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.list import IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox


def refresh_indexes(data, index_name):
    for i, task in enumerate(data):
        task[index_name] = i


class RightCheckbox(IRightBodyTouch, MDCheckbox, ButtonBehavior):
    '''Custom right container.'''
    pass

