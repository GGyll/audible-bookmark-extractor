import os
import sys
import asyncio
import pandas as pd
import audible
import requests
from pydub import AudioSegment

import speech_recognition as sr
import os
# from notion import post_notion

# not currently in use, but so the user can choose their store
country_code_mapping = {
    "us": ".com",
    "ca": ".ca",
    "uk": ".co.uk",
    "au": ".co.au",
    "fr": ".fr",
    "de": ".de",
    "jp": ".co.jp",
    "it": ".it",
    "in": ".co.in",
    "es": ".es"
}

AUDIBLE_URL_BASE = "https://www.audible"
COUNTRY_CODE = "uk"

# set in ms, how long before and after the bookmark timestamp we want to slice the audioclips, useful for redundancy
# i.e to account for the time the user spends to dig up their phone and click bookmark
# Feel free to vary these, but Google Speech Recognition has a certain limit on their API...
START_POSITION_OFFSET = 10000
END_POSITION_OFFSET = 0

help_dict = {
    "download_books": "Downloads books and saves them locally",
    "get_bookmarks": "WIP, extracts all timestamps for bookmarks in the selected audiobook",
    "convert_audiobook": "Removes Audible DRM from the selected audiobooks and converts them to .wav so they can be sliced",
    "list_books": "Lists the users books",
    "show_library": "Probably does the same thing as above",
    "get_bookmarks": "Can only be run after audiobook has been converted. Gets the bookmarks and slices them into audiclips",
    "transcribe_bookmarks": "Self-explanatory, connects to Google Speech Recognition API and outputs the result"

}

# Errors from Audible's API creates one of these, so we can understand them properly


class ExternalError:

    def __init__(self, initiator, asin, error):
        self.initiator = initiator
        self.asin = asin
        self.error = error

    def show_error(self):
        print(
            f"Error while executing {self.initiator}, for ASIN: {self.asin}, msg: {self.error}")


class AudibleAPI:

    def __init__(self, auth):
        self.auth = auth
        self.books = []
        self.book_details = []
        self.library = {}

    # CLI loaded for first time
    async def welcome(self):
        print("Audible Bookmark Extractor v1.0")
        # print("To authenticate with Audible, enter authenticate_now")
        print("To download your audiobooks, ensure you are authenticated, then enter download_books")
        print("Enter help for a list of commands")

    # Gets information about a book
    async def get_book_infos(self, asin):
        async with audible.AsyncClient(self.auth) as client:
            try:
                book = await client.get(
                    path=f"library/{asin}",
                    params={
                        "response_groups": (
                            "contributors, media, price, reviews, product_attrs, "
                            "product_extended_attrs, product_desc, product_plan_details, "
                            "product_plans, rating, sample, sku, series, ws4v, origin, "
                            "relationships, review_attrs, categories, badge_types, "
                            "category_ladders, claim_code_url, is_downloaded, pdf_url, "
                            "is_returnable, origin_asin, percent_complete, provided_review"
                        )
                    }
                )
                return book
            except Exception as e:
                print(e)

    # Main command screen
    async def main(self):
        await self.enter_command()

    # Takes a command and splits it to see if any additional kwargs were supplied i.e --asin="B04EFJIFJI"
    async def enter_command(self):
        command_input = input("Enter command: ")
        command = command_input.split(" ")[0]
        additional_kwargs = command_input.replace(command, '')
        _kwargs = {}

        if additional_kwargs:
            for kwarg in additional_kwargs.split(" --"):
                if kwarg == "":
                    continue
                li_kwarg = kwarg.split("=")

                if not len(li_kwarg) > 1:
                    await self.invalid_kwarg_callback()

                _kwargs[li_kwarg[0]] = li_kwarg[1]

        # Takes the command supplied and sees if we have a function with the prefix cmd_ that we can execute with the given kwargs
        await getattr(self, f"cmd_{command}", self.invalid_command_callback)(**_kwargs)

    # Callbacks
    async def invalid_command_callback(self):
        print("Invalid command, try again")
        await self.enter_command()

    async def invalid_kwarg_callback(self):
        print("Invalid command or arguments supplied, try again")
        await self.enter_command()

    # Helper function for displaying the users books and allowing them to select one based on the index number
    async def get_book_selection(self):

        if not self.library:
            await self.get_library()

        li_books = []
        # if not self.lib
        for index, book in enumerate(self.library["items"]):
            li_books.append(book["asin"])
            book_title = book.get("title", "Unable to retrieve book name")
            print(f"{index}: {book_title}")

        book_selection = input(
            "Enter the index number of the book you would like to download, or enter --all for all available books: \n")

        if book_selection == "--all":
            li_books = [{"title": book.get("title", 'untitled'), "asin": book["asin"]}
                        for book in self.library["items"]]

        else:
            try:
                li_books = [{"title": self.library["items"][int(book_selection)],
                             "asin":self.library["items"][int(book_selection)].get("asin", None)}]
            except (IndexError, ValueError):
                print("Invalid selection")
                await self.invalid_command_callback()
        return li_books

    # Main download books function
    async def cmd_download_books(self):
        async with audible.AsyncClient(self.auth) as client:

            li_books = await self.get_book_selection()

            tasks = []
            for book in li_books:
                tasks.append(
                    asyncio.ensure_future(
                        self.get_book_infos(
                            book.get("asin"))))

            books = await asyncio.gather(*tasks)

            all_books = {}

            for book in books:
                if book is not None:
                    print(book["item"]["title"])
                    asin = book["item"]["asin"]
                    raw_title = book["item"]["title"]
                    title = raw_title.replace(" ", "_")
                    all_books[asin] = title

                    # Attempt to download book
                    try:
                        re = self.get_download_url(self.generate_url(
                            COUNTRY_CODE, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")

                    # Audible API throws error, usually for free books that are not allowed to be downloaded, we skip to the next
                    except audible.exceptions.NetworkError as e:
                        ExternalError(self.get_download_url,
                                      asin, e).show_error()
                        continue

                    audible_response = requests.get(re, stream=True)

                    path_exists = os.path.exists(f"audiobooks/{title}")
                    if not path_exists:
                        os.makedirs(f"audiobooks/{title}")

                    if audible_response.ok:
                        with open(f'audiobooks/{title}.aax', 'wb') as f:
                            print("Downloading %s" % raw_title)

                            total_length = audible_response.headers.get(
                                'content-length')

                            if total_length is None:  # no content length header
                                print(
                                    "Unable to estimate download size, downloading, this might take a while...")
                                f.write(audible_response.content)
                            else:
                                # Save book locally and calculate and print download progress (progress bar)
                                dl = 0
                                total_length = int(total_length)
                                for data in audible_response.iter_content(chunk_size=4096):
                                    dl += len(data)
                                    f.write(data)
                                    done = int(50 * dl / total_length)
                                    sys.stdout.write("\r[%s%s]" % (
                                        '=' * done, ' ' * (50-done)))

                                    sys.stdout.write(
                                        f"   {int(dl / total_length * 100)}%")
                                    sys.stdout.flush()
                                await self.main()

                    else:
                        print(audible_response.text)
                        await self.main()

    # WIP
    def generate_url(self, country_code, url_type, asin=None):
        if asin and url_type == "download":
            return f"{AUDIBLE_URL_BASE}{country_code_mapping.get(country_code)}/library/download?asin={asin}&codec=AAX_44_128"

    # Need the next_request for Audible API to give us the download link for the book
    def get_download_link_callback(self, resp):
        return resp.next_request

    # Sends a request to get the download link for the selected book
    def get_download_url(self, url, **kwargs):

        with audible.Client(auth=self.auth, response_callback=self.get_download_link_callback) as client:
            library = client.get(
                url,
                **kwargs
            )
            return library.url

    async def cmd_list_books(self):
        if not self.books:
            await self.cmd_show_library()

        await self.cmd_show_library()

        await self.main()

    async def cmd_help(self):
        for key in help_dict:
            print(f"{key} -- {help_dict[key]}")
        # print(help_dict)
        await self.main()

    # Gets all books and info for account and adds it to self.books, also returns ASIN for all books
    async def get_library(self):
        async with audible.AsyncClient(self.auth) as client:
            self.library = await client.get(
                path="library",
                params={
                    "num_results": 999
                }
            )
            asins = [book["asin"] for book in self.library["items"]]

            for book in self.library["items"]:
                asins.append(book["asin"])
                book_title = book.get("title", "Unable to retrieve book name")
                self.books.append(book_title)

            return asins

    async def cmd_show_library(self):
        if not self.books:
            await self.get_library()

        for index, book_title in enumerate(self.books):
            print(f"{index}: {book_title}")

        await self.main()

    # async def cmd_download_books(self):
    #     all_books = {}

    #     if not self.books:
    #         await self.get_library()

    #     for book in self.books:
    #         if book is not None:
    #             # breakpoint()
    #             print(book["item"]["title"])
    #             asin = book["item"]["asin"]
    #             raw_title = book["item"]["title"]
    #             title = raw_title.replace(" ", "_")
    #             all_books[asin] = title

    #             try:
    #                 re = self.get_download_url(self.generate_url(
    #                     COUNTRY_CODE, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")
    #             except audible.exceptions.NetworkError as e:
    #                 ExternalError(self.get_download_url,
    #                               asin, e).show_error()
    #                 continue

    #             audible_response = requests.get(re, stream=True)
    #             if audible_response.ok:
    #                 with open(f'audiobooks/{title}.aax', 'wb') as f:
    #                     print("Downloading %s" % raw_title)

    #                     total_length = audible_response.headers.get(
    #                         'content-length')

    #                     if total_length is None:  # no content length header
    #                         f.write(audible_response.content)
    #                     else:
    #                         dl = 0
    #                         total_length = int(total_length)
    #                         print(total_length)
    #                         for data in audible_response.iter_content(chunk_size=4096):
    #                             dl += len(data)
    #                             f.write(data)
    #                             done = int(50 * dl / total_length)
    #                             sys.stdout.write("\r[%s%s]" % (
    #                                 '=' * done, ' ' * (50-done)))

    #                             sys.stdout.write(
    #                                 f"   {int(dl / total_length * 100)}%")
    #                             sys.stdout.flush()

    #                     f.write(audible_response.content)

    #             else:
    #                 print(audible_response.text)

    async def cmd_get_bookmarks(self):
        li_books = await self.get_book_selection()

        for book in li_books:
            print(self.get_bookmarks(book))

    def get_bookmarks(self, book):
        asin = book.get("asin")
        _title = book.get("title", {}).get("title", 'untitled')
        if not _title:
            return

        title = _title.lower().replace(" ", "_")

        bookmarks_url = f"https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/sidecar?type=AUDI&key={asin}"
        with audible.Client(auth=self.auth, response_callback=self.bookmark_response_callback) as client:
            library = client.get(
                bookmarks_url,
                num_results=1000,
                response_groups="product_desc, product_attrs"
            )

            li_bookmarks = library.json().get("payload").get("records")
            li_clips = sorted(
                li_bookmarks, key=lambda i: i["type"], reverse=True)
            # print(li_clips)

            # Load audiobook into AudioSegment so we can slice it
            audio_book = AudioSegment.from_wav(f"/Users/julianlagier/Desktop/python projects/audible-bookmark-extractor/audiobooks/1473565421.wav")

            file_counter = 1
            notes_dict = {}

            # Check whether a folder in clips/ for the book exists or not
            path_exists = os.path.exists(f"clips/{title}")
            if not path_exists:
                os.makedirs(f"clips/{title}")

            for audio_clip in li_clips:
                # Get start position to slice
                raw_start_pos = int(audio_clip["startPosition"])

                # If we have a note then we save it so we can use it as the title for the bookmark text
                if audio_clip.get("type", None) in ["audible.note"]:
                    notes_dict[raw_start_pos] = audio_clip.get("text")
                    print(
                        f"CLIP: {notes_dict[raw_start_pos]}  {raw_start_pos}")

                if audio_clip.get("type", None) in ["audible.clip", "audible.bookmark"]:
                    start_pos = raw_start_pos - START_POSITION_OFFSET
                    end_pos = int(audio_clip.get(
                        "endPosition", raw_start_pos + 30000)) + END_POSITION_OFFSET
                    if start_pos == end_pos:
                        end_pos += 30000

                    # Slice it up
                    clip = audio_book[start_pos:end_pos]

                    file_name = notes_dict.get(
                        raw_start_pos, f"clip{file_counter}")

                    # Save the clip
                    clip.export(
                       f"/Users/julianlagier/Desktop/python projects/audible-bookmark-extractor/clips/{title}/{file_name}.flac", format="flac")
                    file_counter += 1

    async def cmd_convert_audiobook(self):
        # FFMPEG needs to be installed for this step! see readme for more details
        li_books = await self.get_book_selection()

        for book in li_books:
            asin = book.get("asin")
            # Weird for some reason the title is doubled nested here, fix later
            _title = book.get("title", {}).get("title", {})
            if not _title:
                return

            title = _title.replace(" ", "_")
            # Strips Audible DRM  from audiobook
            activation_bytes = self.get_activation_bytes()
            os.system(
                f"ffmpeg -activation_bytes {activation_bytes} -i audiobooks/{title}.aax -c copy audiobooks/{asin}.m4b")

            # Converts audiobook to .wav
            os.system(f"ffmpeg -i audiobooks/{asin}.m4b audiobooks/{asin}.wav")

    async def cmd_transcribe_bookmarks(self):
        li_books = await self.get_book_selection()

        r = sr.Recognizer()
        #Create dictionary to store titles and transcriptions and new folder to store transcriptions
        pairs = {}
        
        #Re check if path exists if not create one 
        path_exists = os.path.exists(os.getcwd()+"/Trancribed_bookmarks")
        if not path_exists:
            os.mkdir(str(os.getcwd())+"/Trancribed_bookmarks")
        
        for book in li_books:
            _title = book.get("title", {}).get("title", {})
            title = _title.lower().replace(" ", "_")
            directory = os.fsencode(f"clips/{title}/")

            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if filename.endswith(".flac") or filename.endswith(".py"):
                    print(os.path.join(os.fsdecode(directory), filename))
                    heading = filename.replace(".flac", "")

                    audioclip = sr.AudioFile(os.path.join(
                        os.fsdecode(directory), filename))
                    with audioclip as source:
                        audio = r.record(source)  
                        
                        #Append heading and Transcription & Make a Dataframe to be later imported as CSV
                        pairs[str(heading)]=r.recognize_google(audio)
                        xcel = pd.DataFrame(pairs.values(), index = pairs.keys(),columns=['Transcription'])
                        xcel.rename(columns = {'Unnamed: 0':'Book Name'}, inplace = True)
                        xcel.to_csv(str(os.getcwd()+"/Trancribed_bookmarks/"+title)+".csv")

                    # TODO Julian
                    # Heading is the name of the bookmark
                    # r.recognize_google(audio) is the transcribed text
                    # Have fun :)))

                    # print(heading)
                    #print(r.recognize_google(audio))

                    # Disabled as currently only working with my API key
                    # post_notion(heading, r.recognize_google(audio))
            else:
                continue 

    def get_activation_bytes(self):

        # we already have activation bytes
        if os.path.exists("activation_bytes.txt"):
            with open('activation_bytes.txt') as f:
                activation_bytes = f.readlines()[0]

        # we don't, so let's get them
        else:
            activation_bytes = auth.get_activation_bytes(
                "activation_bytes.txt", True)
            text_file = open("activation_bytes.txt", "w")
            n = text_file.write(activation_bytes)
            text_file.close()

        return activation_bytes

    def bookmark_response_callback(self, resp):
        return resp


if __name__ == "__main__":
    # authenticate with login
    auth = audible.Authenticator.from_file("credentials.json")

    loop = asyncio.get_event_loop()

    audible_obj = AudibleAPI(auth)
    loop.run_until_complete(audible_obj.welcome())
    loop.run_until_complete(audible_obj.main())
