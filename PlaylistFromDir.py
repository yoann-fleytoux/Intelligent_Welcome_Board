from os import listdir
from os.path import isfile, isdir,join

#fill f with every file and directory found in dir_path and its directory
def read_file_from_dir(dir_path,f):
    for element in listdir(dir_path):
        str=join(dir_path, element)
        if isfile(str):
            f.append(str)
        else:
            if isdir(str):
                read_file_from_dir(str,f)

#remove all the file not ending with the correct extension from f
def remove_if_not_playable(f):
    list_of_correct_extension_video=(".mkv", ".mp4", ".mov", ".3gp", ".avi", ".flv", ".gifv")
    list_of_correct_extension_image = ("/1.jpg", "/1.png")
    incorrect=[]
    for file in f:
        if(not file.endswith(list_of_correct_extension_video) and not file.endswith(list_of_correct_extension_image)) :
            incorrect.append(file)

    for file in incorrect:
        f.remove(file)

    f.sort()
    """
    for file in f:
        print(file)
    """

#get all the video files to be played from dir_path and its directories
def create_playlist(dir_path):
    f = []
    read_file_from_dir(dir_path, f)
    #print("before:", f)
    remove_if_not_playable(f)
    #print("after :", f)
    return f

if __name__ == '__main__':
    create_playlist("./src_video")