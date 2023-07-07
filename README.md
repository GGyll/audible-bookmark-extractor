## This tool allows a user to download their audiobooks from Audible and transcribes their bookmarks into text, which can be exported to Notion and Excel (.csv)

main_file.py contains the CLI and most of the application logic

### To start

```
pip install -r requirements.txt
```
After everything is installed:

```
python main_file.py
```

Type help for a list of useful commands

### Authentication
Run command 
```
authenticate
```
Then when prompted enter your email and password, a separate window will open to display your CAPTCHA, which the program will prompt you for as well. NOTE: The CAPTCHAS for Audible seem to be pretty tough (as in not easily readable) lately, so you may need to retry a few times to get one you can solve.

Then you are logged into the Audible API and your credentials are stored in credentials.json, you won't need to authenticate again as long as you have this file.


### On top of ffmpeg-python, you need FFMPEG installed on your computer, refer to python-ffmpeg github doc
https://github.com/kkroening/ffmpeg-python



### Anti-Piracy Notice
Note that this project does NOT 'crack' Audible DRM or download audiobooks which the user does not own. It simply allows the user to use their own encryption key (fetched from Audible servers) to decrypt the audiobook in the same manner that the official audiobook playing software does, and download audiobooks which they have purchased.

Please only use this application for gaining full access to your own audiobooks for archiving/converson/convenience. DeDRMed audiobooks should not be uploaded to open servers, torrents, or other methods of mass distribution. No help will be given to people doing such things. Authors, retailers, and publishers all need to make a living, so that they can continue to produce audiobooks for us to hear, and enjoy. Don't be a parasite.

This message is paraphrased from the https://apprenticealf.wordpress.com/ page.

Also, the purpose of the software is not to circumvent the DRM restrictions for audio books that you do not own in that you do not have them on your personal Audible account. The purpose of this software is to create a method for you to download and store your books just in case Audible fails for some reason, as well as provide a way to export your bookmarks into an Excel file so that you may refer to your notes more easily, than having to rely on the Audible app.

## FAQ:
sh: 1: ffmpeg: not found
You need to install ffmpeg

