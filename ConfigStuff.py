import configparser
import io



#return if smart video choice feature is enable
def get_config_smart_video_enable(config):
    return config.getboolean('kinect', 'smart_video')

#return if kinect is enable
def get_config_kinect_enable(config):
    return config.getboolean('kinect', 'enable')

#return the video directory to be used
def get_config_video_fullscreen(config):
    return config.getboolean('video', 'fullscreen')

#return the video directory to be used
def get_config_video_directory(config):
    return config.get('video', 'directory')

#return the width seetting of the video
def get_config_video_width(config):
    return config.getint('video', 'width')

#return the height setting of the video
def get_config_video_height(config):
    return config.getint('video', 'height')

def get_config_image_delay(config):
    return config.getfloat('powerpoint', 'time_per_image')
