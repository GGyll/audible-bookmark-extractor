## This tool allows a user to download their audiobooks from Audible and transcribes their bookmarks into text, which can be exported to Notion and Excel (.csv)

main_file.py contains the CLI and most of the application login

### To start

pip install -r requirements.txt

Then run main_file.py

Type help for a list of useful commands

### On top of ffmpeg-python, you need FFMPEG installed on your computer, refer to python-ffmpeg github doc
https://github.com/kkroening/ffmpeg-python



### Anti-Piracy Notice
Note that this project does NOT 'crack' Audible DRM or download audiobooks which the user does not own. It simplys allows the user to use their own encryption key (fetched from Audible servers) to decrypt the audiobook in the same manner that the official audiobook playing software does, and download audiobooks which they have purchased.

Please only use this application for gaining full access to your own audiobooks for archiving/converson/convenience. DeDRMed audiobooks should not be uploaded to open servers, torrents, or other methods of mass distribution. No help will be given to people doing such things. Authors, retailers, and publishers all need to make a living, so that they can continue to produce audiobooks for us to hear, and enjoy. Don't be a parasite.

This message is paraphrased from the https://apprenticealf.wordpress.com/ page.

Icon attributed to:
https://www.flaticon.com/free-icons/bass"


The purpose of this software is not to circumvent the DRM restrictions for audio books that you do not own in that you do not have them on your personal Audible account. The purpose of this software is to create a method for you to download and store your books just in case Audible fails for some reason.

##FAQ:
sh: 1: ffmpeg: not found
You need to install ffmpeg

