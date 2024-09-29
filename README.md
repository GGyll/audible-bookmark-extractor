## This tool allows a user to download their audiobooks from Audible and transcribes their bookmarks into text, which can be exported

Right now, this tool supports exporting to Excel and [Readwise] (https://readwise.io/)

main.py is the main entry point and it mostly off-loads to command.py
command.py is the command line processor
audible_api.py is the audible api wrapper that handles authentication and downloads audiobooks from Audible
transcribe_api.py is the Google Cloud Speech API wrapper that handles transcribing audiobooks into
readwise_api.py is the Readwise API wrapper that handles exporting audiobooks to Readwise
notion_api.py is the Notion API wrapper that handles exporting audiobooks to Notion (WIP)

### To start

```
pip install -r requirements.txt
```

After everything is installed:

```
python main.py
```

Type help for a list of useful commands

### Authentication

#### Note: you need 2FA activated on your Audible account

#### For posting to Readwise: Go to https://readwise.io/access_token to get your access token. Copy and paste that into the command line when prompted.

Run command

```
authenticate
```

Then when prompted enter your email and password, a separate window will open to display your CAPTCHA, which the program will prompt you for as well. NOTE: The CAPTCHAS for Audible seem to be pretty tough (as in not easily readable) lately, so you may need to retry a few times to get one you can solve.

Then you are logged into the Audible API and your credentials are stored in credentials.json, you won't need to authenticate again as long as you have this file.

```
readwise_authenticate
```
If you are using this program to post your highlights from audible to readwise, authenticate with readwise first. Your credentials are stored in readwise_token.json and you won't need to authenticate again as long as you have this file.

```
readwise_post_highlights
```
All the highlights you have extracted and converted is stored in ~/audibleextractor/<<bookname>>/trascribed_clips/contents.json. After you run this command, go to https://readwise.io/books to see the highlights uploaded from this app.

### On top of ffmpeg-python, you need FFMPEG installed on your computer, refer to python-ffmpeg github doc

https://github.com/kkroening/ffmpeg-python

### Anti-Piracy Notice

This project does not crack Audible DRM or facilitate the download of audiobooks that users do not rightfully own. Instead, it enables users to utilize their own encryption key (retrieved from Audible’s servers) to decrypt audiobooks in the same manner as Audible’s official software. This is limited to audiobooks that have been legally purchased by the user.

Please ensure that this application is used solely for personal purposes such as archiving, conversion, or convenience with your own purchased content. Decrypted audiobooks must not be shared through public servers, torrents, or any other means of mass distribution. Assistance will not be provided to anyone engaging in such activities. Remember, authors, retailers, and publishers depend on fair compensation to continue producing the audiobooks we enjoy. Please respect their work and livelihood.

This message is paraphrased from the https://apprenticealf.wordpress.com/ page.

Also, the purpose of the software is not to circumvent the DRM restrictions for audio books that you do not own in that you do not have them on your personal Audible account. The purpose of this software is to create a method for you to download and store your books just in case Audible fails for some reason, as well as provide a way to export your bookmarks into an Excel file so that you may refer to your notes more easily, than having to rely on the Audible app.

## FAQ:

sh: 1: ffmpeg: not found
You need to install ffmpeg, refer to python-ffmpeg github doc
https://github.com/kkroening/ffmpeg-python

I'm prompted for a CVF code when trying to authenticate, and then the program crashes
You need to enable 2FA on your Amazon account

I get error "Exception: Login failed. Please check the log." when trying to authenticate
You need to enable 2FA on your Amazon account
