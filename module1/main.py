from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.app import App

import database


# main screen
class RootWidget(Screen):
    def send_message(self):
        message_text = self.ids.message.text
        name_text = self.ids.name.text
        # read city of zuil
        f = open("module1/stationzuil.txt", "r")
        city = f.read()



        if message_text == "admin" and name_text == "admin":
            self.ids.message.text = ""
            self.ids.name.text = ""
            self.manager.current = 'dynamic'
            return

        if name_text == "":
            database.add_message(message=message_text, city=city)
        else:
            database.add_message(message=message_text, city=city, name=name_text)


        self.ids.message.text = ""
        self.ids.name.text = ""

# Admin screen (change station)
class DynamicGrid(Screen):
    def __init__(self, **kwargs):
        super(DynamicGrid, self).__init__(**kwargs)

        data_list = database.get_station_list()

        grid = GridLayout(cols=4)
        self.add_widget(grid)

        for item in data_list:
            btn = Button(text=item)
            btn.bind(on_press=self.button_click)
            grid.add_widget(btn)

    def button_click(self, instance):
        # Set station of the zuil
        with open("module1/stationzuil.txt", "w") as f:
            f.write(instance.text)
        self.manager.current = 'root'



class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(RootWidget(name='root'))
        sm.add_widget(DynamicGrid(name='dynamic'))

        # check is station is set
        with open("module1/stationzuil.txt", "r") as f:
            city = f.read()
            print(city)
            if city == "":
                sm.current = 'dynamic'
            else:
                sm.current = 'root'

        return sm


MainApp().run()
