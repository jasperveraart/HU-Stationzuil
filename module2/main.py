from hashlib import sha256
import psycopg2
import os
from dotenv import load_dotenv

import datetime

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.app import App
from kivy.properties import NumericProperty, StringProperty

load_dotenv()

def user_create(name, email, password):
    """
    Create a moderator
    :param name:
    :param email:
    :param password:
    :return: none
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query1 = "select exists (select email from moderators where email=%s)"
    data1 = email,

    cursor = conn.cursor()
    cursor.execute(query1, data1)

    if cursor.fetchone()[0]:
        print("Deze gebruiker bestaat al")
        return

    query = "insert into moderators(naam, email, password) values (%s, %s, %s)"

    salt = os.getenv("SALT")
    database_password = sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

    data = name, email, database_password

    cursor = conn.cursor()
    cursor.execute(query, data)

    conn.commit()

    conn.close()

def user_check(email, password):
    """
    Check if username and password exists and match
    :param email:
    :param password:
    :return: moderatorid
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query = "select id, password from moderators where email=%s"

    data = email,


    cursor = conn.cursor()
    cursor.execute(query, data)

    reply_non_format = cursor.fetchall()
    if reply_non_format == []:
        return -1
    reply = reply_non_format[0][1]

    _reply, salt = reply.split(':')
    if _reply == sha256(salt.encode() + password.encode()).hexdigest():
        return reply_non_format[0][0]
    else:
        return 0

    conn.close()

def get_moderator(id: int):
    """
    Get the ID and name of the moderator
    :param id:
    :return: {id, name}
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query = "select id, naam from moderators where id=%s"
    data = id,

    cursor = conn.cursor()
    cursor.execute(query, data)

    reply = cursor.fetchall()
    return {"id": id, "name": reply[0][1]}

def get_messages_to_moderate():
    """
    Get all messages with status 1 (not moderated yet)
    :return: [{id, message}]
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query = "select moderation.id, messages.message from moderation join messages on moderation.messagesid = messages.id where moderation.status=1"

    cursor = conn.cursor()
    cursor.execute(query)

    result = cursor.fetchall()
    messages = []

    for message in result:
        data = {"id": message[0], "message": message[1]}
        messages.append(data)

    return messages

def get_all_messages():
    """
    Get all messages with the status of the message
    Status:
    0 - Declined
    1 - Not moderated
    2 - Approved
    :return: [{id, message, status}]
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query = "select moderation.id, messages.message, moderation.status from moderation join messages on moderation.messagesid = messages.id"

    cursor = conn.cursor()
    cursor.execute(query)

    result = cursor.fetchall()
    messages = []

    for message in result:
        data = {"id": message[0], "message": message[1], "status": message[2]}
        messages.append(data)

    return messages

def change_status(messageid: int, new_status: int, moderator:int):
    """
    Change the status of a message
    :param messageid:
    :param new_status:
    :param moderator:
    :return: none
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    now = datetime.datetime.now()

    query = "update moderation set status=%s, moderatorsid=%s, moderationdate=%s WHERE id = %s;"
    data = new_status, moderator, now, messageid

    cursor = conn.cursor()
    cursor.execute(query, data)

    conn.commit()
    conn.close()

# Custom Carousel property for swiping the messages
class CustomCarousel(Carousel):
    def __init__(self, **kwargs):
        super(CustomCarousel, self).__init__(**kwargs)
        self._touch_distance = 0  # Definieer de attribuut voor de touch afstand

    def on_touch_down(self, touch):
        # Sla de originele touch down positie op
        self._touch_down_x = touch.x
        return super(CustomCarousel, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        # Check of deze Carousel het touch event verwerkt
        if not self.collide_point(*touch.pos):
            return False

        # Bereken hoe ver we zijn bewogen
        self._touch_distance = touch.x - self._touch_down_x
        # Pas de x positie van de huidige slide aan voor de animatie
        current_slide = self.current_slide
        current_slide.x += self._touch_distance
        # Reset de touch down positie voor de volgende move event
        self._touch_down_x = touch.x
        return True

    def on_touch_up(self, touch):
        # Reset de x positie van de huidige slide
        current_slide = self.current_slide
        anim = Animation(x=self.x, t='out_quad', duration=0.2)
        anim.start(current_slide)

        # Je kunt hier controleren hoe ver de slide is verplaatst en beslissen of je dit als een swipe actie ziet
        if abs(self._touch_distance) > self.width * 0.3:  # Bijvoorbeeld 30% van de breedte van de carousel
            # Implementeer je swipe logica hier...
            pass

        # Reset de touch_distance
        self._touch_distance = 0
        return super(CustomCarousel, self).on_touch_up(touch)

# Custom ImageButton for clickable images (NS Logo)
class ImageButton(ButtonBehavior, Image):
    pass

# Custom MessageLabel for storing message id behind screen
class MessageLabel(Label):
    message_id = NumericProperty(0)


    def __init__(self, **kwargs):
        super(MessageLabel, self).__init__(**kwargs)
        self.bind(size=self._update_font_size)

    def _update_font_size(self, *args):
        # Controleer of de tekst past in de label na schaling of venstergrootte aanpassing
        if self.texture_size[1] > self.height:
            # Als de tekst te hoog is, verklein de font_size
            while self.texture_size[1] > self.height and self.font_size > 10:
                self.font_size -= 1
        else:
            # Vergroot de font_size als er ruimte over is, met een maximum font_size
            while self.texture_size[1] < self.height and self.font_size < 35:
                self.font_size += 1

# Custom MessageRow for displaying all messages
class MessageRow(RecycleDataViewBehavior, BoxLayout):
    """ Custom view voor een rij in de tabel. """
    message_id = StringProperty()
    message_text = StringProperty()
    status = NumericProperty
    user_id = NumericProperty

    def refresh_view_attrs(self, rv, index, data):
        """ Update de view als de data verandert. """
        self.message_id = data['message_id']
        self.message_text = data['message_text']
        self.status = data['status']  # Zorg ervoor dat je de status hier instelt
        self.update_color()  # Update de kleur
        return super(MessageRow, self).refresh_view_attrs(rv, index, data)

    def on_status(self, instance, value):
        """ Wordt aangeroepen wanneer de status verandert. """
        self.update_color()  # Update de kleur ook hier

    def update_color(self):
        color_map = {
            0: (0.85882, 0, 0.16078, 1),
            1: (1, 1, 1, 1),
            2: (0, 0.60392, 0.25882, 1)
        }

        self.ids.label_id.color = color_map.get(self.status, (1, 1, 1, 1))  # Wit voor ongedefinieerde status

    def on_release_update(self):
        """ Functie die wordt aangeroepen wanneer de update-knop wordt ingedrukt. """
        if self.status == 0:
            change_status(self.message_id, 2, self.user_id)
            self.status = 2
            self.ids.label_id.color = (0, 0.60392, 0.25882, 1)
        elif self.status == 2:
            change_status(self.message_id, 2, self.user_id)
            self.status = 0
            self.ids.label_id.color = (0.85882, 0, 0.16078, 1)


# Login screen
class LoginWidget(Screen):
    user_id = NumericProperty()

    def on_user_id(self, instance, value):
        moderate_widget = self.manager.get_screen('moderate')
        settings_widget = self.manager.get_screen('settings')

        settings_widget.user_id =  value
        moderate_widget.user_id = value

    def login(self):
        email = self.ids.email.text
        password = self.ids.password.text

        user = user_check(email, password)

        if user == -1:
            print("Username does not exists")
            self.ids.email.text = ""
            self.ids.password.text = ""
        elif user == 0:
            print("Password not correct")
            self.ids.email.text = ""
            self.ids.password.text = ""
        else:
            self.user_id = user
            self.manager.current = 'moderate'

# Moderation screen
class ModerateWidget(Screen):
    user_id = NumericProperty()

    def settings(self):
        print("TEST")
        self.manager.current = 'settings'

    def __init__(self, **kwargs):
        super(ModerateWidget, self).__init__(**kwargs)
        self.touch_start_x = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_x = touch.x
        return super(ModerateWidget, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.touch_start_x:
            # Controleer veegrichting
            if touch.x > self.touch_start_x:  # Rechts swipen
                self.swipe(True)  # Goedkeuren
            elif touch.x < self.touch_start_x:  # Links swipen
                self.swipe(False)  # Afkeuren
            self.touch_start_x = None  # Reset de startpositie
        return super(ModerateWidget, self).on_touch_up(touch)

    def on_user_id(self, instance, value):
        mod = get_moderator(value)
        self.ids.moderator.text = f"Welkom, {mod.get('name')}"

    def on_enter(self, *args):
        # Ergens in je screen setup code
        self.ids.carousel.size_hint_x = None
        self.ids.carousel.width = Window.width  # Dit stelt de breedte in op de volledige vensterbreedte

        self.fill_carousel()

    def fill_carousel(self):
        self.messages = get_messages_to_moderate()  # Vul de messages list
        if not self.messages:
            self.show_reload_button()
        else:
            for message in self.messages:
                label = MessageLabel(
                    text=message.get("message"),
                    message_id=message.get("id"),
                    size_hint_y=None,
                    height=200  # of een andere vaste hoogte als dat nodig is
                )
                # Stel text_size in op de breedte van de carousel minus een beetje ruimte
                label.text_size = (self.ids.carousel.width * 0.95, None)
                label.size_hint_x = None
                label.width = self.ids.carousel.width * 0.95  # Dit maakt de breedte bijna even breed als de carousel
                self.ids.carousel.add_widget(label)

    def reload_messages(self):
        self.ids.carousel.clear_widgets()
        self.fill_carousel()

    def show_reload_button(self):
        reload_button = Button(text='Herlaad berichten',
                               font_size='20sp',
                               font_name='Arial',
                               size_hint_y=None,
                               height='50dp',
                               background_normal='',
                               background_color= (0x00 / 255.0, 0x30 / 255.0, 0x82 / 255.0, 1),
                               size_hint_x=0.6,
                               pos_hint={'center_x': 0.5} # Centreer de knop horizontaal
                               )
        reload_button.bind(on_release=lambda a: self.reload_messages())
        self.ids.carousel.add_widget(reload_button)

    def swipe(self, goedkeuren):
        current_slide = self.ids.carousel.current_slide

        if hasattr(current_slide, 'message_id'):
            message_id = current_slide.message_id
            if goedkeuren:
                change_status(message_id, 2, self.user_id)
            else:
                change_status(message_id, 0, self.user_id)

            self.ids.carousel.remove_widget(current_slide)

            self.messages = [m for m in self.messages if m['id'] != message_id]
            if not self.messages:
                self.show_reload_button()

# All messages screen
class SettingsWidget(Screen):
    user_id = NumericProperty()

    def __init__(self, **kwargs):
        super(SettingsWidget, self).__init__(**kwargs)
        self.data = [{'message_id': str(i), 'message_text': f"Bericht {i} tekst"} for i in range(100)]  # Voorbeeld data

    def on_user_id(self, instance, value):
        self.current_user_id = value
        mod = get_moderator(value)
        self.ids.moderator.text = f"Welkom, {mod.get('name')}"

    def on_enter(self, *args):
        self.load_messages()

    def load_messages(self):
        self.ids.messages_view.data = [{
            'message_text': message['message'],  # Change 'text' to 'message_text' to match the expected key
            'message_id': str(message['id']),
            'status': message['status'],
            'user_id': self.current_user_id
        } for message in get_all_messages()]

    def moderate(self):
        self.manager.current = 'moderate'


class ModeratieApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginWidget(name='signin'))
        sm.add_widget(ModerateWidget(name='moderate'))
        sm.add_widget(SettingsWidget(name='settings'))

        # Startup screen signin
        sm.current = 'signin'
        return sm

ModeratieApp().run()
# user_create("Jasper", "jasper@veraart.cloud", "Welkom123")
# user_create("Simone", "simone@student.hu.nl", "Welkom123")