\*\* This tool allows a user to download their audiobooks from Audible and transcribes their bookmarks into text, which can be exported to Notion and Excel (.csv)

The main file which holds 90% of logic is main_file.py, this is where I am taking the existing logic from "main copy.py" and "transcribe.py" and developing a Command-line interface on top of it

\*\* To start

pip install -r requirements.txt

Then run main_file.py

\*\* On top of ffmpeg-pyton, you need FFMPEG installed on your computer, refer to python-ffmpeg github doc
https://github.com/kkroening/ffmpeg-python

\*\*Anti-Piracy Notice
Note that this project does NOT 'crack' the DRM. It simplys allows the user to use their own encryption key (fetched from Audible servers) to decrypt the audiobook in the same manner that the official audiobook playing software does.

Please only use this application for gaining full access to your own audiobooks for archiving/converson/convenience. DeDRMed audiobooks should not be uploaded to open servers, torrents, or other methods of mass distribution. No help will be given to people doing such things. Authors, retailers, and publishers all need to make a living, so that they can continue to produce audiobooks for us to hear, and enjoy. Don't be a parasite.

This message is borrowed from the https://apprenticealf.wordpress.com/ page.

Icon attributed to:
https://www.flaticon.com/free-icons/bass"
