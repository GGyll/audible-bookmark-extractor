import os
import json
import sys
import asyncio
import requests
from getpass import getpass

import pandas as pd
import pandas.io.formats.excel
import audible
import httpx

from pydub import AudioSegment

import speech_recognition as sr
from openai import OpenAI

from errors import ExternalError
from constants import artifacts_root_directory

# not currently in use, but so the user can choose their store
country_code_mapping = {
    "us": ".com",
    "ca": ".ca",
    "uk": ".co.uk",
    "au": ".com.au",
    "fr": ".fr",
    "de": ".de",
    "jp": ".co.jp",
    "it": ".it",
    "in": ".co.in",
    "es": ".es"
}

AUDIBLE_URL_BASE = "https://www.audible"

# set in ms, how long before and after the bookmark timestamp we want to slice the audioclips, useful for redundancy
# i.e to account for the time the user spends to dig up their phone and click bookmark
# Feel free to vary these, but free Speech Recognition API's have certain limits...
START_POSITION_OFFSET = 10000
END_POSITION_OFFSET = 0

# Configuration for transcription output location
# Change this path to customize where transcriptions are saved
# Default: Desktop/Audible Transcriptions
TRANSCRIPTION_OUTPUT_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "Audible Transcriptions")

class AudibleAPI:

    def __init__(self, auth):
        self.auth = auth
        self.books = []
        self.library = {}

    @classmethod
    async def authenticate(self) -> "AudibleAPI":
        secrets_dir_path = os.path.join(artifacts_root_directory, "secrets")
        credentials_path = os.path.join(secrets_dir_path, "credentials.json")
        if os.path.exists(credentials_path):
            print(f"You are already authenticated, to switch accounts, delete secrets directory under {artifacts_root_directory} and try again")
        email = input("Audible Email: ")
        password = getpass(
            "Enter Password (will be hidden, press ENTER when done): ")
        print(', '.join(country_code_mapping))
        locale = input("\nPlease enter your locale from the list above: ")

        auth = audible.Authenticator.from_login(
            email,
            password,
            locale=locale,
            with_username=False
        )
        
        os.makedirs(secrets_dir_path, exist_ok=True)
        auth.to_file(credentials_path)
        print("Credentials saved locally successfully")
        return AudibleAPI(auth)

    # Gets information about a book
    async def get_book_infos(self, asin):
        # Configure a longer timeout (60 seconds) for API requests
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with audible.AsyncClient(self.auth, timeout=timeout) as client:
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
        return li_books

    # Main download books function
    async def cmd_download_books(self):
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
                title = raw_title.lower().replace(" ", "_")
                all_books[asin] = title

                # Attempt to download book
                try:
                    re = self.get_download_url(self.generate_url(self.auth.locale.country_code, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")

                # Audible API throws error, usually for free books that are not allowed to be downloaded, we skip to the next
                except audible.exceptions.NetworkError as e:
                    ExternalError(self.get_download_url,
                                  asin, e).show_error()
                    continue

                audible_response = requests.get(re, stream=True)

                title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
                path_exists = os.path.exists(title_dir_path)
                if not path_exists:
                    os.makedirs(title_dir_path)
                    

                if audible_response.ok:
                    title_file_path = os.path.join(title_dir_path, f"{title}.aax")
                    with open(title_file_path, 'wb') as f:
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
                            for data in audible_response.iter_content(chunk_size=1024*1024):
                                dl += len(data)
                                f.write(data)
                                done = int(50 * dl / total_length)
                                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)))

                                sys.stdout.write(f"   {int(dl / total_length * 100)}%")
                                sys.stdout.flush()

                else:
                    print(audible_response.text)

    # WIP
    def generate_url(self, country_code, url_type, asin=None):
        if asin and url_type == "download":
            return f"{AUDIBLE_URL_BASE}{country_code_mapping.get(country_code)}/library/download?asin={asin}&codec=AAX"

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
        await self.cmd_show_library()
        
    # Gets all books and info for account and adds it to self.books, also returns ASIN for all books
    async def get_library(self):
        # Configure a longer timeout (60 seconds) for large library requests
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with audible.AsyncClient(self.auth, timeout=timeout) as client:
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
        print(f"Getting bookmarks for {_title}")
        with audible.Client(auth=self.auth, response_callback=self.bookmark_response_callback) as client:
            library = client.get(
                bookmarks_url,
                num_results=1000,
                response_groups="product_desc, product_attrs"
            )

            li_bookmarks = library.json().get("payload", {}).get("records", [])
            li_clips = sorted(
                li_bookmarks, key=lambda i: i["type"], reverse=True)

            title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
            title_aax_path = os.path.join(title_dir_path, f"{title}.aax")
            title_m4b_path = os.path.join(title_dir_path, f"{title}.m4b")
            title_mp3_path = os.path.join(title_dir_path, f"{title}.mp3")

            # Load audiobook into AudioSegment so we can slice it
            audio_book = AudioSegment.from_mp3(
                title_mp3_path)

            file_counter = 1
            notes_dict = {}

            # Check whether a folder in clips/ for the book exists or not
            clips_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title, "clips")
            path_exists = os.path.exists(clips_dir_path)
            if not path_exists:
                os.makedirs(clips_dir_path)

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
                    clip_path = os.path.join(clips_dir_path, f"{file_name}.flac")
                    clip.export(
                        clip_path, format="flac")
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

            title = _title.replace(" ", "_").lower()
            # Strips Audible DRM  from audiobook
            activation_bytes = self.get_activation_bytes()
            title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
            title_aax_path = os.path.join(title_dir_path, f"{title}.aax")
            title_m4b_path = os.path.join(title_dir_path, f"{title}.m4b")
            title_mp3_path = os.path.join(title_dir_path, f"{title}.mp3")
            os.system(
                f"ffmpeg -activation_bytes {activation_bytes} -i {title_aax_path} -c copy {title_m4b_path}")

            # Converts audiobook to .mp3
            os.system(
                f"ffmpeg -i {title_m4b_path} {title_mp3_path}")

    async def cmd_transcribe_bookmarks(self, openai_api_key=None):
        li_books = await self.get_book_selection()

        # Initialize OpenAI client if API key is provided, otherwise fall back to Google
        use_openai = openai_api_key is not None
        if use_openai:
            client = OpenAI(api_key=openai_api_key)
            print("Using OpenAI Whisper API for transcription")
        else:
            r = sr.Recognizer()
            print("Using Google Speech Recognition for transcription (no API key required)")

        # Create dictionary to store titles and transcriptions and new folder to store transcriptions
        pairs = {}
        jsonHighlights = []
        
        for book in li_books:

            _title = book.get("title", {}).get("title", {})
            _authors = book.get("title", {}).get("authors", {})
            allAuthors = ", ".join(item['name'] for item in _authors)
            title = _title.lower().replace(" ", "_")
            title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
            clips_dir_path = os.path.join(title_dir_path, "clips")
            directory = os.fsencode(clips_dir_path)

            path_exists = os.path.exists(directory)
            if not path_exists:
                os.makedirs(directory)

            # Save transcriptions to Desktop
            desktop_path = os.path.join(TRANSCRIPTION_OUTPUT_PATH, _title)
            transcribed_clips_dir_path = desktop_path
            trancribed_clips_path_exists = os.path.exists(transcribed_clips_dir_path)
            if not trancribed_clips_path_exists:
                os.makedirs(transcribed_clips_dir_path)
                print(f"Saving transcriptions to: {transcribed_clips_dir_path}")

            for file in os.listdir(directory):
                highlight = {}
                filename = os.fsdecode(file)
                highlight["title"] = _title
                highlight["author"] = allAuthors
                if not filename.startswith("clip"):
                    highlight["note"] = filename.replace(".flac", "")
                highlight["source_type"] = "audible_bookmark_extractor"
                if filename.endswith(".flac"):
                    print(os.path.join(os.fsdecode(directory), filename))
                    heading = filename.replace(".flac", "")

                    try:
                        if use_openai:
                            # Use OpenAI Whisper API
                            audio_file_path = os.path.join(os.fsdecode(directory), filename)
                            with open(audio_file_path, "rb") as audio_file:
                                transcription = client.audio.transcriptions.create(
                                    model="gpt-4o-transcribe",
                                    file=audio_file
                                )
                                text = transcription.text
                        else:
                            # Use Google Speech Recognition
                            audioclip = sr.AudioFile(os.path.join(
                                os.fsdecode(directory), filename))
                            with audioclip as source:
                                audio = r.record(source)
                            text = r.recognize_google(audio)
                        
                        pairs[str(heading)] = text
                        highlight["text"] = text
                    except Exception as e:
                        highlight["text"] = ""
                        print(f"Error while recognizing this clip {heading}: {e}")
                    
                    xcel = pd.DataFrame(pairs.values(), index=pairs.keys())

                    # Change header format so that rows can be edited
                    pandas.io.formats.excel.ExcelFormatter.header_style = None

                    if highlight["text"]:
                        jsonHighlights.append(highlight)
                    
                    # Create writer instance with desired path
                    all_transcriptions_path = os.path.join(transcribed_clips_dir_path, "All_Transcriptions.xlsx")
                    writer = pd.ExcelWriter(
                        all_transcriptions_path, engine='xlsxwriter')

                    # Create a sheet in the same workbook for each file in the directory
                    sheet_name = title[:31].replace(":", "").replace("?", "")
                    xcel.to_excel(writer, sheet_name=sheet_name)
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]

                    # Create header format to be used in all headers
                    header_format = workbook.add_format({
                        "valign": "vcenter",
                        "align": "center",
                        "bg_color": "#FFA500",
                        "bold": True,
                        "font_color": "#FFFFFF"})  # transcribe_bookmarks

                    # Set desired cell format
                    cell_format = workbook.add_format()
                    cell_format.set_align("vcenter")
                    cell_format.set_align("center")
                    cell_format.set_text_wrap(True)

                    # Apply header format and format columns to fit data
                    worksheet.write(0, 0, 'Clip Note', header_format)
                    worksheet.write(0, 1, 'Transcription', header_format)
                    worksheet.set_column("B:B", 100)
                    worksheet.set_column("A:A", 50)

                    # Format cells for appropiate size, wrap the text for style points
                    for i in range(1, (len(xcel)+1)):
                        worksheet.set_row(i, 100, cell_format)

                    # Apply changes and save xlsx to Transcribed bookmarks folder.
                    writer.close()

            # Save JSON
            transcription_contents_path = os.path.join(transcribed_clips_dir_path, "contents.json")
            with open(transcription_contents_path, "w") as f:
                json.dump(jsonHighlights, f, indent=4)

            # Save Markdown
            markdown_path = os.path.join(transcribed_clips_dir_path, f"Bookmarks - {_title}.md")
            with open(markdown_path, "w") as f:
                # Write header
                f.write(f"# {_title}\n")
                f.write(f"By {allAuthors}\n\n")

                # Write each highlight as a paragraph
                for highlight in jsonHighlights:
                    if highlight.get("text"):
                        f.write(f"{highlight['text']}\n\n")

            print(f"Saved markdown to: {markdown_path}")                

    def get_activation_bytes(self):

        activation_bytes_path = os.path.join(artifacts_root_directory, "secrets", "activation_bytes.txt")
        # we already have activation bytes
        if os.path.exists(activation_bytes_path):
            with open(activation_bytes_path) as f:
                activation_bytes = f.readlines()[0]

        # we don't, so let's get them
        else:
            activation_bytes = self.auth.get_activation_bytes(
                activation_bytes_path, True)
            text_file = open(activation_bytes_path, "w")
            n = text_file.write(activation_bytes)
            text_file.close()

        return activation_bytes

    def bookmark_response_callback(self, resp):
        return resp

    async def cmd_process_book(self, index=None, skip_download=None, skip_convert=None, skip_bookmarks=None, skip_transcribe=None):
        """
        Runs the full pipeline for a single book: download, convert, get bookmarks, and transcribe.
        Requires --index parameter with the book number from list_books.

        Optional flags to skip steps:
        --skip-download=true: Skip download step
        --skip-convert=true: Skip conversion step
        --skip-bookmarks=true: Skip bookmark extraction step
        --skip-transcribe=true: Skip transcription step

        By default, steps are automatically skipped if their output files already exist.
        """
        if index is None:
            print("Error: --index parameter is required. Usage: process_book --index=<book_number>")
            print("Run 'list_books' first to see available books and their index numbers.")
            return

        # Get library if not already loaded
        if not self.library:
            await self.get_library()

        # Validate index
        try:
            book_index = int(index)
            if book_index < 0 or book_index >= len(self.library["items"]):
                print(f"Error: Invalid index {book_index}. Please choose a number between 0 and {len(self.library['items'])-1}")
                return
        except ValueError:
            print(f"Error: Invalid index '{index}'. Please provide a numeric index.")
            return

        # Get the book at the specified index
        book_item = self.library["items"][book_index]
        # Structure matches what get_bookmarks and other methods expect
        book = {
            "title": book_item,  # Pass the entire book item as 'title' (legacy structure)
            "asin": book_item.get("asin")
        }

        # Prepare file paths for checking
        title = book_item.get("title", "untitled").lower().replace(" ", "_")
        title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
        title_aax_path = os.path.join(title_dir_path, f"{title}.aax")
        title_mp3_path = os.path.join(title_dir_path, f"{title}.mp3")
        clips_dir_path = os.path.join(title_dir_path, "clips")
        # Transcriptions saved to Desktop
        desktop_transcriptions_path = os.path.join(TRANSCRIPTION_OUTPUT_PATH, book_item.get("title", "untitled"))
        transcription_contents_path = os.path.join(desktop_transcriptions_path, "contents.json")

        # Convert flag strings to boolean
        skip_download = skip_download in ["true", "True", "1", "yes"]
        skip_convert = skip_convert in ["true", "True", "1", "yes"]
        skip_bookmarks = skip_bookmarks in ["true", "True", "1", "yes"]
        skip_transcribe = skip_transcribe in ["true", "True", "1", "yes"]

        print(f"\n{'='*60}")
        print(f"Processing book: {book_item.get('title', 'untitled')}")
        print(f"{'='*60}\n")

        # Step 1: Download the book
        print("\n[Step 1/4] Downloading book...")
        print("-" * 60)
        if skip_download:
            print("⊘ Skipped (manual flag)")
        elif os.path.exists(title_aax_path):
            print(f"✓ Already downloaded: {title_aax_path}")
            print("⊘ Skipping download (file exists)")
        else:
            await self._download_single_book(book)

        # Step 2: Convert audiobook
        print("\n[Step 2/4] Converting audiobook to MP3...")
        print("-" * 60)
        if skip_convert:
            print("⊘ Skipped (manual flag)")
        elif os.path.exists(title_mp3_path):
            print(f"✓ Already converted: {title_mp3_path}")
            print("⊘ Skipping conversion (file exists)")
        else:
            await self._convert_single_book(book)

        # Step 3: Get bookmarks
        print("\n[Step 3/4] Extracting bookmarks...")
        print("-" * 60)
        if skip_bookmarks:
            print("⊘ Skipped (manual flag)")
        elif os.path.exists(clips_dir_path) and os.listdir(clips_dir_path):
            clip_count = len([f for f in os.listdir(clips_dir_path) if f.endswith('.flac')])
            print(f"✓ Bookmarks already extracted: {clip_count} clips found")
            print("⊘ Skipping bookmark extraction (clips exist)")
        else:
            self.get_bookmarks(book)

        # Step 4: Transcribe bookmarks
        print("\n[Step 4/4] Transcribing bookmarks...")
        print("-" * 60)
        if skip_transcribe:
            print("⊘ Skipped (manual flag)")
        elif os.path.exists(transcription_contents_path):
            print(f"✓ Already transcribed: {transcription_contents_path}")
            print("⊘ Skipping transcription (file exists)")
        else:
            # Check if OpenAI is configured
            openai_key = None
            try:
                with open(f"{artifacts_root_directory}/secrets/openai_key.json", "r") as file:
                    openai_key = file.read().strip()
            except FileNotFoundError:
                pass

            await self._transcribe_single_book(book, openai_key)

        print(f"\n{'='*60}")
        print(f"✓ Successfully processed: {book_item.get('title', 'untitled')}")
        print(f"{'='*60}\n")

    async def _download_single_book(self, book):
        """Helper method to download a single book without user selection."""
        try:
            book_info = await self.get_book_infos(book.get("asin"))
            if book_info is None:
                print(f"Error: Could not retrieve book information")
                return

            asin = book_info["item"]["asin"]
            raw_title = book_info["item"]["title"]
            title = raw_title.lower().replace(" ", "_")

            print(f"Downloading: {raw_title}")

            try:
                re = self.get_download_url(
                    self.generate_url(self.auth.locale.country_code, "download", asin),
                    num_results=1000,
                    response_groups="product_desc, product_attrs"
                )
            except audible.exceptions.NetworkError as e:
                ExternalError(self.get_download_url, asin, e).show_error()
                return

            audible_response = requests.get(re, stream=True)

            title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
            if not os.path.exists(title_dir_path):
                os.makedirs(title_dir_path)

            if audible_response.ok:
                title_file_path = os.path.join(title_dir_path, f"{title}.aax")
                with open(title_file_path, 'wb') as f:
                    total_length = audible_response.headers.get('content-length')

                    if total_length is None:
                        print("Unable to estimate download size, downloading...")
                        f.write(audible_response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for data in audible_response.iter_content(chunk_size=1024*1024):
                            dl += len(data)
                            f.write(data)
                            done = int(50 * dl / total_length)
                            sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)))
                            sys.stdout.write(f"   {int(dl / total_length * 100)}%")
                            sys.stdout.flush()
                        print()  # New line after progress bar
            else:
                print(f"Error downloading: {audible_response.text}")

        except Exception as e:
            print(f"Error downloading book: {e}")

    async def _convert_single_book(self, book):
        """Helper method to convert a single book without user selection."""
        try:
            # Extract title from nested structure
            _title = book.get("title", {}).get("title", "untitled")
            title = _title.replace(" ", "_").lower()

            activation_bytes = self.get_activation_bytes()
            title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
            title_aax_path = os.path.join(title_dir_path, f"{title}.aax")
            title_m4b_path = os.path.join(title_dir_path, f"{title}.m4b")
            title_mp3_path = os.path.join(title_dir_path, f"{title}.mp3")

            print(f"Converting {_title} to M4B...")
            os.system(f"ffmpeg -activation_bytes {activation_bytes} -i {title_aax_path} -c copy {title_m4b_path}")

            print(f"Converting {_title} to MP3...")
            os.system(f"ffmpeg -i {title_m4b_path} {title_mp3_path}")

        except Exception as e:
            print(f"Error converting book: {e}")

    async def _transcribe_single_book(self, book, openai_api_key=None):
        """Helper method to transcribe bookmarks for a single book without user selection."""
        try:
            use_openai = openai_api_key is not None
            if use_openai:
                client = OpenAI(api_key=openai_api_key)
                print("Using OpenAI Whisper API for transcription")
            else:
                r = sr.Recognizer()
                print("Using Google Speech Recognition for transcription")

            pairs = {}
            jsonHighlights = []

            # Extract title and authors from nested structure
            _title = book.get("title", {}).get("title", "untitled")
            _authors = book.get("title", {}).get("authors", [])
            allAuthors = ", ".join(item['name'] for item in _authors) if _authors else ""

            title = _title.lower().replace(" ", "_")
            title_dir_path = os.path.join(artifacts_root_directory, "audiobooks", title)
            clips_dir_path = os.path.join(title_dir_path, "clips")
            directory = os.fsencode(clips_dir_path)

            if not os.path.exists(directory):
                print(f"No clips directory found at {clips_dir_path}")
                return

            # Save transcriptions to Desktop
            desktop_path = os.path.join(TRANSCRIPTION_OUTPUT_PATH, _title)
            transcribed_clips_dir_path = desktop_path
            if not os.path.exists(transcribed_clips_dir_path):
                os.makedirs(transcribed_clips_dir_path)
                print(f"Saving transcriptions to: {transcribed_clips_dir_path}")

            for file in os.listdir(directory):
                highlight = {}
                filename = os.fsdecode(file)
                highlight["title"] = _title
                highlight["author"] = allAuthors
                if not filename.startswith("clip"):
                    highlight["note"] = filename.replace(".flac", "")
                highlight["source_type"] = "audible_bookmark_extractor"

                if filename.endswith(".flac"):
                    print(f"Transcribing: {filename}")
                    heading = filename.replace(".flac", "")

                    try:
                        if use_openai:
                            audio_file_path = os.path.join(os.fsdecode(directory), filename)
                            with open(audio_file_path, "rb") as audio_file:
                                transcription = client.audio.transcriptions.create(
                                    model="gpt-4o-transcribe",
                                    file=audio_file
                                )
                                text = transcription.text
                        else:
                            audioclip = sr.AudioFile(os.path.join(os.fsdecode(directory), filename))
                            with audioclip as source:
                                audio = r.record(source)
                            text = r.recognize_google(audio)

                        pairs[str(heading)] = text
                        highlight["text"] = text
                    except Exception as e:
                        highlight["text"] = ""
                        print(f"Error transcribing {heading}: {e}")

                    xcel = pd.DataFrame(pairs.values(), index=pairs.keys())
                    pandas.io.formats.excel.ExcelFormatter.header_style = None

                    if highlight["text"]:
                        jsonHighlights.append(highlight)

                    all_transcriptions_path = os.path.join(transcribed_clips_dir_path, "All_Transcriptions.xlsx")
                    writer = pd.ExcelWriter(all_transcriptions_path, engine='xlsxwriter')

                    sheet_name = title[:31].replace(":", "").replace("?", "")
                    xcel.to_excel(writer, sheet_name=sheet_name)
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]

                    header_format = workbook.add_format({
                        "valign": "vcenter",
                        "align": "center",
                        "bg_color": "#FFA500",
                        "bold": True,
                        "font_color": "#FFFFFF"
                    })

                    cell_format = workbook.add_format()
                    cell_format.set_align("vcenter")
                    cell_format.set_align("center")
                    cell_format.set_text_wrap(True)

                    worksheet.write(0, 0, 'Clip Note', header_format)
                    worksheet.write(0, 1, 'Transcription', header_format)
                    worksheet.set_column("B:B", 100)
                    worksheet.set_column("A:A", 50)

                    for i in range(1, (len(xcel)+1)):
                        worksheet.set_row(i, 100, cell_format)

                    writer.close()

            # Save JSON
            transcription_contents_path = os.path.join(transcribed_clips_dir_path, "contents.json")
            with open(transcription_contents_path, "w") as f:
                json.dump(jsonHighlights, f, indent=4)

            # Save Markdown
            markdown_path = os.path.join(transcribed_clips_dir_path, f"Bookmarks - {_title}.md")
            with open(markdown_path, "w") as f:
                # Write header
                f.write(f"# {_title}\n")
                f.write(f"By {allAuthors}\n\n")

                # Write each highlight as a paragraph
                for highlight in jsonHighlights:
                    if highlight.get("text"):
                        f.write(f"{highlight['text']}\n\n")

            print(f"Transcribed {len(pairs)} clips")
            print(f"Saved markdown to: {markdown_path}")

        except Exception as e:
            print(f"Error transcribing bookmarks: {e}")
