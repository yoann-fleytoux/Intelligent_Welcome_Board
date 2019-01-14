# kivy GUI stuff

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.animation import Animation

# other library
from functools import partial
import re
import time
import configparser
import io
import os
import pyautogui

pyautogui.FAILSAFE = False

# my own files
import PlaylistFromDir
import HandTracking
import ConfigStuff
import apiFaceAndEmotion


# Had to make an edit to /kivy/core/window/__init__.py , line 1246 , targettop = max(0, target.to_window(0, target.y)[1]) to:-> if target and 'to_window' in dir(target):targettop = max(0, target.to_window(0, target.y)[1])else:targettop = 0

# see ~/.kivy/config.ini for showing fps

# todo remove pyautogui and use Xlib

class TestApp(App):
    def build(self):

        # open config.ini to access the user's settings

        self.config = configparser.ConfigParser()
        self.config.read(os.environ['HOME'] + "/.config_showoff.ini")

        # ******************* DECIDE WINDOW SIZE *******************
        # in fullscreen is enable go full screen; otherwise use width and height provided
        if ConfigStuff.get_config_video_fullscreen(self.config):
            Window.fullscreen = "auto"
        else:
            # set the width and height from config.ini
            Window.size = (
            ConfigStuff.get_config_video_width(self.config), ConfigStuff.get_config_video_height(self.config))

        # ******************* DECIDE WHAT VIDEO IS PLAYED *******************
        # set the directory where the videos will be taken from
        self.video_directory = ConfigStuff.get_config_video_directory(self.config)

        # get the list of video files found
        self.video_list = PlaylistFromDir.create_playlist(self.video_directory)
        # the number of the file form video_list currently played
        self.curr_video_iterator = -1

        # todo: [ERROR  ] [Image       ] Error loading texture , try to deal with it at some point
        self.video1 = Video(source="./1_Second_of_Blank.mp4", state="play", volume=0)
        self.video1.fullscreen = True
        self.video1.allow_stretch = True
        self.video1.image_loading = "./GUI/loading.png"

        self.video1.pos_hint = {"center_x": .5, "center_y": .5}
        # when the video reaches its end, on_eos is called (eos= end of stream)
        self.video1.bind(position=self.on_position_change, eos=self.on_eos)

        # ******************* DEAL UI STUFF *******************
        self.label_help = Label(
            text="Approach your hand to control the Billboard. Hover over a button for 2s to activate it.",
            color=(1, 0, 0, 1))
        self.label_help.pos_hint = {"center_x": .5, "center_y": 0.98}

        self.button_loop = Button(text="Reset", background_normal="./GUI/loop.png", border=(0, 0, 0, 0),
                                  size_hint=(.2, .2), color=(1, 0, 0, 1))
        self.button_loop.pos_hint = {"center_x": 0.85, "center_y": 0.2}
        self.button_loop.opacity = 0.5
        self.button_loop.bind(on_press=self.callback_button_loop)

        self.button_next = Button(text="NEXT", background_normal="./GUI/arrow_next.png", border=(0, 0, 0, 0),
                                  size_hint=(.2, .2), color=(1, 0, 0, 1))
        self.button_next.pos_hint = {"center_x": 0.85, "center_y": 0.5}
        self.button_next.opacity = 0.5
        self.button_next.bind(on_press=self.callback_button_next)

        self.button_previous = Button(text="PREVIOUS", background_normal="./GUI/arrow_previous.png",
                                      border=(0, 0, 0, 0), size_hint=(.2, .2), color=(1, 0, 0, 1))
        self.button_previous.pos_hint = {"center_x": 0.15, "center_y": 0.5}
        self.button_previous.opacity = 0.5
        self.button_previous.bind(on_press=self.callback_button_previous)

        self.button_next_ppt = Button(text="NEXT SLIDE", background_normal="./GUI/arrow_next_2.png",
                                      border=(0, 0, 0, 0), size_hint=(.2, .2), color=(1, 0, 0, 1))
        self.button_next_ppt.pos_hint = {"center_x": 0.85, "center_y": 0.7}
        self.button_next_ppt.opacity = 0.5
        self.button_next_ppt.bind(on_press=self.callback_button_next_ppt)

        self.button_previous_ppt = Button(text="PREVIOUS SLIDE", background_normal="./GUI/arrow_previous_2.png",
                                          border=(0, 0, 0, 0), size_hint=(.2, .2), color=(1, 0, 0, 1))
        self.button_previous_ppt.pos_hint = {"center_x": 0.15, "center_y": 0.7}
        self.button_previous_ppt.opacity = 0.5
        self.button_previous_ppt.bind(on_press=self.callback_button_previous_ppt)

        self.label_help_ppt = Label(text="The power point will pause if you approach your hand", color=(1, 0, 0, 1))
        self.label_help_ppt.pos_hint = {"center_x": .5, "center_y": 0.02}

        # ******************* DEAL WITH LAYOUT *******************
        self.root = FloatLayout(size=Window.size)
        self.root_video = FloatLayout(size=Window.size)
        self.root_UI = FloatLayout(size=Window.size)
        self.root_UI.opacity=0.8

        if ConfigStuff.get_config_kinect_enable(self.config):
            self.faceAndEmotionAnalyser = apiFaceAndEmotion.apiFaceDetectAndClassifier()
            self.handTracking = HandTracking.MyHandTrackingApp()
            self.handTracking.pos_hint = {"center_x": .5, "center_y": .5}
            self.root_UI.add_widget(self.label_help)

        self.root_video.add_widget(self.video1)

        self.root.add_widget(self.root_video)
        self.root.add_widget(self.root_UI)

        # ******************* VIDEO MANAGEMENT ATTRIBUTES *******************
        self.playlist_management_event = None
        # ******************* PPT MANAGEMENT ATTRIBUTES *******************
        self.list_of_correct_extension_image = (".jpg", ".png")
        self.delay_image = ConfigStuff.get_config_image_delay(self.config)
        self.playing_ppt = False
        self.bool_ppt_UI_shown = False
        self.next_slide = False
        self.previous_slide = False
        self.bool_show_UI = False
        self.event_ppt = None  # used to cancel several power point management at the same time
        self.iterator_check_if_click = 0
        self.time_limit_beetween_clicks = 2  # in seconds

        # ******************* USER MANAGEMENT ATTRIBUTES *******************
        self.seen_users = set()
        self.current_people = None
        self.smart_video_choice = ConfigStuff.get_config_smart_video_enable(
            self.config) and ConfigStuff.get_config_kinect_enable(self.config)

        # ******************* CALL LOOPS *******************
        Clock.schedule_interval(self.check_mouse_position, 1)
        Clock.schedule_interval(self.hide_mouse_if_unmoved, 10)
        return self.root

    def callback_button_loop(self, instance):
        print("button loop")
        if(self.video1.source.endswith(self.list_of_correct_extension_image)):
            filename, file_extension = os.path.splitext(self.video1.source)
            # extract image number
            number_old = re.search('(\d+)$', filename).group(0)
            number_new = 1
            # replace the current image number to the next one
            filename = re.sub(str(number_old) + "$", str(number_new), filename)
            self.video1.source = filename + file_extension
            self.video1.reload()
            self.set_ppt_event(Clock.schedule_once(self.play_next_image, self.delay_image))
        else:
            self.video1.seek(0)

    def callback_button_next(self, instance):
        print("from button next")
        self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_next), 0))

    def callback_button_previous(self, instance):
        print("from button previous")
        self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_previous), 0))

    def callback_button_next_ppt(self, instance):
        self.next_slide = True
        self.set_ppt_event(Clock.schedule_once(self.play_next_image, 0))

    def callback_button_previous_ppt(self, instance):
        self.previous_slide = True
        self.set_ppt_event(Clock.schedule_once(self.play_next_image, 0))

    def check_users(self):
        self.current_people = self.faceAndEmotionAnalyser.check_who_it_is()
        for name in self.current_people:
            if name not in self.seen_users:
                self.seen_users.add(name)
                self.show_greetings("Hi " + name, 400, (1, 0, 0, 1))
        self.faceAndEmotionAnalyser.quitAndSave()
        self.faceAndEmotionAnalyser = apiFaceAndEmotion.apiFaceDetectAndClassifier()

    def check_users_watching_habits(self):
        # sort the list in accordance to what they have seen
        # print("Before:", self.video_list)
        list_video_with_score = []
        for video in self.video_list:
            list_video_with_score.append([video, 0])
        # print("Before 0:", list_video_with_score)
        # for all the people in front
        for person in self.current_people:
            parser = configparser.ConfigParser()
            parser.read("./pics/" + person + '.ini')
            # for all the videos found
            for i in range(len(self.video_list)):
                # if the video has been seen
                if parser.has_option("WATCHING_HABITS", self.video_list[i]):
                    # add a score base on how many time it was seen, and when was the last time
                    # todo: maybe think of a better formula
                    list_video_with_score[i] = (list_video_with_score[i][0],
                                                list_video_with_score[i][1] + parser.getint("WATCHING_HABITS",
                                                                                            self.video_list[i]) / (
                                                time.time() - parser.getfloat("WATCHING_HABITS_TIME_TICKS",
                                                                              self.video_list[i])))

                    # for all the video
                    # sort based on their score
        # print("Before1:", list_video_with_score)
        list_video_with_score = sorted(list_video_with_score, key=lambda score: score[1])  # sort by score
        # print("After 1:", list_video_with_score)
        # put the previously shown video at the end
        index = -1
        for i in range(len(list_video_with_score)):
            if (list_video_with_score[i][0] == self.video1.source):
                index = i
                break
        if (index != -1):
            list_video_with_score.append(list_video_with_score.pop(index))
        self.video_list = []
        for video in list_video_with_score:
            self.video_list.append(video[0])
            # print("After 2:", self.video_list)

    def update_users_watching_habits(self):
        if (not self.video1.source == "./1_second_of_blank.mp4"):
            # for all the people in front
            for person in self.current_people:
                parser = configparser.ConfigParser()
                parser.read("./pics/" + person + '.ini')
                # if the person has already seen the video
                if (parser.has_section("WATCHING_HABITS")):
                    try:
                        parser.set("WATCHING_HABITS", self.video1.source,
                                   str(parser.getint("WATCHING_HABITS", self.video1.source) + 1))

                    except:
                        parser.set("WATCHING_HABITS", self.video1.source, str(1))
                    # set it to the current time
                    parser.set("WATCHING_HABITS_TIME_TICKS", self.video1.source, str(time.time()))
                    parser.set("WATCHING_HABITS_TIME_DATE", self.video1.source,
                               str(time.asctime(time.localtime(time.time()))))

                else:
                    # create the section
                    parser.add_section("WATCHING_HABITS")
                    parser.add_section("WATCHING_HABITS_TIME_TICKS")
                    parser.add_section("WATCHING_HABITS_TIME_DATE")
                    parser.set("WATCHING_HABITS", self.video1.source, str(1))
                    # set it to the current time
                    parser.set("WATCHING_HABITS_TIME_TICKS", self.video1.source, str(time.time()))
                    parser.set("WATCHING_HABITS_TIME_DATE", self.video1.source,
                               str(time.asctime(time.localtime(time.time()))))
                # print("writing in:",person+'.ini' )
                with open("./pics/" + person + '.ini', "w") as config_file:
                    parser.write(config_file)

    # decide which video is played next
    def playlist_management_next(self, dt=None):
        if (self.playing_ppt or self.video1.source.endswith(self.list_of_correct_extension_image)):
            self.root_UI.remove_widget(self.label_help_ppt)
            if (self.bool_show_UI):
                self.root_UI.remove_widget(self.button_next_ppt)
                self.root_UI.remove_widget(self.button_previous_ppt)
                self.bool_ppt_UI_shown = False
            self.playing_ppt = False

            filename, file_extension = os.path.splitext(self.video1.source)
            # extract image number
            number_old = re.search('(\d+)$', filename).group(0)
            number_new = 1
            # replace the current image number to the next one
            filename = re.sub(str(number_old) + "$", str(number_new), filename)
            self.video1.source = filename + file_extension
            # print("new:", self.video1.source)

        self.video1.state = 'pause'
        self.video_list = PlaylistFromDir.create_playlist(self.video_directory)

        if not self.video_list:
            print("no video to play")
            self.video1.source = "./1_Second_of_Blank.mp4"
            self.video1.state = 'play'
        else:

            # todo check users activity with App and adjust list
            if (self.smart_video_choice):
                # check who is there
                self.check_users()
                if(self.current_people):
                    # check what the people there have seen and choose a content
                    self.check_users_watching_habits()
                    self.video1.source = self.video_list[0]  # the most appropriate is the first one
                    # for those there, add the chosen content to their watching habits
                    self.update_users_watching_habits()

            if(not self.current_people):
                self.curr_video_iterator = self.video_list.index(
                    self.video1.source) if self.video1.source in self.video_list else 0
                self.curr_video_iterator += 1
                if (len(self.video_list) == self.curr_video_iterator):
                    self.curr_video_iterator = 0
                self.video1.source = self.video_list[self.curr_video_iterator]

            if (self.video1.source.endswith(self.list_of_correct_extension_image)):
                self.video1.source = self.video1.source
                self.playing_ppt = True
                self.root_UI.add_widget(self.label_help_ppt)
                if (self.bool_show_UI):
                    self.root_UI.add_widget(self.button_next_ppt)
                    self.root_UI.add_widget(self.button_previous_ppt)
                    self.bool_ppt_UI_shown = True
                self.set_ppt_event(Clock.schedule_once(self.play_next_image, self.delay_image))
            else:
                self.video1.state = 'play'
        print("Playing:", self.video1.source)

    # decide which video is played next
    def playlist_management_previous(self, dt=None):
        if (self.playing_ppt):
            self.root_UI.remove_widget(self.label_help_ppt)
            if (self.bool_show_UI):
                self.root_UI.remove_widget(self.button_next_ppt)
                self.root_UI.remove_widget(self.button_previous_ppt)
                self.bool_ppt_UI_shown = False
            self.playing_ppt = False
            filename, file_extension = os.path.splitext(self.video1.source)
            # extract image number
            number_old = re.search('(\d+)$', filename).group(0)
            number_new = 1
            # replace the current image number to the next one
            filename = re.sub(str(number_old) + "$", str(number_new), filename)
            self.video1.source = filename + file_extension

        self.video1.state = 'pause'
        self.video_list = PlaylistFromDir.create_playlist(self.video_directory)

        if not self.video_list:
            print("no video to play")
            self.video1.source = "./1_Second_of_Blank.mp4"
            self.video1.state = 'play'
        else:
            self.curr_video_iterator = self.video_list.index(
                self.video1.source) if self.video1.source in self.video_list else 0
            self.curr_video_iterator -= 1
            if (self.curr_video_iterator < 0):
                self.curr_video_iterator = len(self.video_list) - 1
            self.video1.source = self.video_list[self.curr_video_iterator]

            # todo check users activity with App and adjust list
            if (self.smart_video_choice):
                # check who is there
                self.check_users()
                if(self.current_people):
                    # for those there, add the chosen content to their watching habits
                    self.update_users_watching_habits()

            # if ppt treat it accordingly
            if (self.video1.source.endswith(self.list_of_correct_extension_image)):
                self.video1.source = self.video1.source
                self.playing_ppt = True
                self.root_UI.add_widget(self.label_help_ppt)
                if (self.bool_show_UI):
                    self.root_UI.add_widget(self.button_next_ppt)
                    self.root_UI.add_widget(self.button_previous_ppt)
                    self.bool_ppt_UI_shown = True
                self.set_ppt_event(Clock.schedule_once(self.play_next_image, self.delay_image))
            else:
                self.video1.state = 'play'
        print("Playing:", self.video1.source)

    def set_ppt_event(self, event):
        if (self.event_ppt != None):
            self.event_ppt.cancel()
        self.event_ppt = event

    def set_playlist_management_event(self, event):
        if (self.playlist_management_event != None):
            self.playlist_management_event.cancel()
        self.playlist_management_event = event

    def play_next_image(self, dt):
        print("Entering play_next_image")
        if (self.playing_ppt):
            if (self.previous_slide):
                # print("play next")
                # get name and extension
                filename, file_extension = os.path.splitext(self.video1.source)
                # extract image number
                number_old = re.search('(\d+)$', filename).group(0)
                number_new = int(number_old) - 1

                # print("before :",filename)
                # replace the current image number to the next one
                filename = re.sub(str(number_old) + "$", str(number_new), filename)

                # print("after :", filename)
                # if the file does no exist we pass to the video/powerpoint
                if (os.path.isfile(filename + file_extension)):
                    # if it exist we update the image drawn
                    new_source = filename + file_extension
                    # print(self.video1.source," new image is :",new_source)
                    self.video1.source = new_source
                    self.previous_slide = False
                    self.next_slide = False
                    self.set_ppt_event(Clock.schedule_once(self.play_next_image, self.delay_image))

            elif (self.next_slide):
                # print("play next")
                # get name and extension
                filename, file_extension = os.path.splitext(self.video1.source)
                # extract image number
                number_old = re.search('(\d+)$', filename).group(0)
                number_new = int(number_old) + 1

                # print("before :",filename)
                # replace the current image number to the next one
                filename = re.sub(str(number_old) + "$", str(number_new), filename)

                # print("after :", filename)
                # if the file does no exist we pass to the video/powerpoint
                if (os.path.isfile(filename + file_extension)):
                    # if it exist we update the image drawn
                    new_source = filename + file_extension
                    # print(self.video1.source," new image is :",new_source)
                    self.video1.source = new_source
                    self.previous_slide = False
                    self.next_slide = False
                    self.set_ppt_event(Clock.schedule_once(self.play_next_image, self.delay_image))
            else:
                # print("play next")
                # get name and extension
                filename, file_extension = os.path.splitext(self.video1.source)
                # extract image number
                number_old = re.search('(\d+)$', filename).group(0)
                number_new = int(number_old) + 1

                # print("before :",filename)
                # replace the current image number to the next one
                filename = re.sub(str(number_old) + "$", str(number_new), filename)

                # print("after :", filename)
                # if the file does no exist we pass to the video/powerpoint
                if (not os.path.isfile(filename + file_extension)):
                    print("from play_next_image")
                    self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_next), 0))
                else:
                    # if it exist we update the image drawn
                    new_source = filename + file_extension
                    # print(self.video1.source," new image is :",new_source)
                    self.video1.source = new_source
                    self.previous_slide = False
                    self.next_slide = False
                    self.set_ppt_event(Clock.schedule_once(self.play_next_image, self.delay_image))

    def show_overlay(self):
        if (self.bool_show_UI == False):
            self.root_UI.add_widget(self.handTracking.painter)
            self.root_UI.add_widget(self.button_next)
            self.root_UI.add_widget(self.button_previous)
            self.root_UI.add_widget(self.button_loop)
            if (not self.bool_ppt_UI_shown and self.playing_ppt):
                self.root_UI.add_widget(self.button_next_ppt)
                self.root_UI.add_widget(self.button_previous_ppt)
                self.bool_ppt_UI_shown = True
            self.bool_show_UI = True

            self.check_users()

    def hide_overlay(self):
        if (self.bool_show_UI == True):
            self.root_UI.remove_widget(self.handTracking.painter)
            self.root_UI.remove_widget(self.button_next)
            self.root_UI.remove_widget(self.button_previous)
            self.root_UI.remove_widget(self.button_loop)
            if (self.bool_ppt_UI_shown):
                self.root_UI.remove_widget(self.button_next_ppt)
                self.root_UI.remove_widget(self.button_previous_ppt)
                self.bool_ppt_UI_shown = False
            self.bool_show_UI = False

    # move the mouse to the middle of the window and hide fullscreen (works best when full screen)
    def hide_mouse_if_unmoved(self, dt):
        if (Window.mouse_pos[0] == self.last_mouse_pose[0] and Window.mouse_pos[1] == self.last_mouse_pose[
            1] and self.bool_show_UI == False):
            pyautogui.moveTo(Window.width / 2, Window.height / 2)
            Window.show_cursor = False

    # check the mouse position, if situated on the right, the grid is show
    def check_mouse_position(self, dt):
        # show mouse cursor if hidden and not in the center of the screen
        x = Window.mouse_pos[0]
        y = Window.mouse_pos[1]
        if (x != Window.width / 2 and y != Window.height / 2 and Window.show_cursor == False):
            Window.show_cursor = True
        # todo: check if mouse over widget for click
        if (self.bool_show_UI):
            if (self.iterator_check_if_click == self.time_limit_beetween_clicks):
                self.check_if_click(0)
                self.iterator_check_if_click = 0
            else:
                self.iterator_check_if_click += 1
        self.last_mouse_pose = (Window.mouse_pos[0], Window.mouse_pos[1])
        # print(Window.mouse_pos)

    def check_if_click(self, dt):

        x = Window.mouse_pos[0]
        y = Window.mouse_pos[1]
        if (self.button_next.collide_point(x, y)):
            self.callback_button_next(None)

        if (self.button_previous.collide_point(x, y)):
            self.callback_button_previous(None)

        if (self.button_loop.collide_point(x, y)):
            self.callback_button_loop(None)

        if (self.bool_ppt_UI_shown):
            if (self.button_next_ppt.collide_point(x, y)):
                self.callback_button_next_ppt(None)

            if (self.button_previous_ppt.collide_point(x, y)):
                self.callback_button_previous_ppt(None)

    # todo: that may be a bit heavy on processing
    def on_position_change(self, instance, value):
        if (value > 30):
            print("from 30 sec !")
            self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_next), 0))

    def show_greetings(self, text, size=200, color=(1, 1, 1, 1)):
        label_hello = Label(
            text=text
        )
        self.root_UI.add_widget(label_hello)
        # Animate and fade out the message
        anim = Animation(font_size=size,
                         color=color, t='in_quad', s=1 / 30)
        anim.start(label_hello)

        def tick_hello_anim(dt):
            label_hello.canvas.ask_update()
            Clock.schedule_once(tick_hello_anim)

            tick_hello_anim(0)

        def end_hello_anim(dt):
            self.root_UI.remove_widget(label_hello)
            Clock.unschedule(end_hello_anim)

        Clock.schedule_once(end_hello_anim, 1)

    # on end of stream, playlist_management is shown
    def on_eos(self, instance, value):
        if (not self.video1.source.endswith(self.list_of_correct_extension_image)):
            print("from eos", self.video1.source)
            self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_next), 0))

    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, *args):
        # print ('down', args)
        if args[1][1] == 'f':
            Window.fullscreen = "auto"
        if args[1][1] == 'right':
            print("from right")
            self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_next), 0))
        if args[1][1] == 'left':
            print("from left")
            self.set_playlist_management_event(Clock.schedule_once(partial(self.playlist_management_previous), 0))
        if args[1][1] == 'enter':
            self.show_greetings("Hi Yoann")
        if args[1][1] == 's':
            self.faceAndEmotionAnalyser.quitAndSave()
            self.faceAndEmotionAnalyser = apiFaceAndEmotion.apiFaceDetectAndClassifier()
        if args[1][1] == 'c':
            self.faceAndEmotionAnalyser.changeName("36", "Yoann", self.faceAndEmotionAnalyser.personsDB)

    def _on_keyboard_up(self, *args):
        print(args[1][1])


if __name__ == '__main__':
    TestApp().run()