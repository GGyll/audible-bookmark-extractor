import os
from audible import log_helper
import audible
from httpx import Response
import requests
from pydub import AudioSegment
import ffmpeg
import subprocess as sp

AUDIBLE_URL_BASE = "https://www.audible"


log_helper.set_console_logger("debug")

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

# auth & activation_bytes
auth = audible.Authenticator.from_file("credentials.json")
if os.path.exists("activation_bytes.txt"):
    with open('activation_bytes.txt') as f:
        activation_bytes = f.readlines()[0]
        print(activation_bytes)
else:
    activation_bytes = auth.get_activation_bytes(
        "activation_bytes.txt", True)
    text_file = open("activation_bytes.txt", "w")
    n = text_file.write(activation_bytes)
    text_file.close()


# ATOMIC HABITS: 1473565421
# THINK AGAIN: 0593394763

COUNTRY_CODE = "uk"
ASIN = "1473565421"
START_POSITION_OFFSET = 10000
END_POSITION_OFFSET = 0

content_url = f"/1.0/content/{ASIN}/licenserequest"


def generate_url(country_code, url_type, asin=None):
    if asin and url_type == "download":
        return f"{AUDIBLE_URL_BASE}{country_code_mapping.get(country_code)}/library/download?asin={asin}&codec=AAX_44_128"


def get_download_link_callback(resp):
    return resp.next_request


def get_download_url(url, **kwargs):
    with audible.Client(auth=auth, response_callback=get_download_link_callback) as client:
        library = client.get(
            url,
            **kwargs
        )
        return library.url


def get(url, **kwargs):
    with audible.Client(auth=auth) as client:
        library = client.get(
            url,
            **kwargs
        )
        return library


def post(url, body, **kwargs):
    with audible.Client(auth=auth) as client:
        library = client.post(
            url,
            body,
            **kwargs
        )
        return library


def bookmark_response_callback(resp):
    return resp


def get_bookmarks(url, asin, **kwargs):
    with audible.Client(auth=auth, response_callback=bookmark_response_callback) as client:
        library = client.get(
            url,
            **kwargs
        )
        return library.json()


def convert_aax(aax_file):
    aax_instance = ffmpeg.input(aax_file)
    (
        ffmpeg
        .overlay(aax_instance.hflip())
        .drawbox(50, 50, 120, 120, color='red', thickness=5)
        .output('out.mp4')
        .run()
    )


my_body = {"asin": ASIN}
resp = get(
    f"{AUDIBLE_URL_BASE}{country_code_mapping.get(COUNTRY_CODE)}/1.0/library")
breakpoint()
# DOWNLOAD
print(generate_url(COUNTRY_CODE, "download", ASIN))
sample_url = ""
re = get_download_url(generate_url(COUNTRY_CODE, "download", ASIN),
                      num_results=1000, response_groups="product_desc, product_attrs")


audible_response = requests.get(re)

if audible_response.ok:
    with open('fkowwkfo.aax', 'wb') as f:
        f.write(audible_response.content)

else:
    print(audible_response.text)


os.system(
    f"ffmpeg -activation_bytes {activation_bytes} -i audiobooks/book.aax -c copy {ASIN}.m4b")

os.system(f"ffmpeg -i {ASIN}.m4b {ASIN}.wav")


# GET BOOKMARKS
bookmarks_url = f"https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/sidecar?type=AUDI&key={ASIN}"
bookmarks_dict = get_bookmarks(
    bookmarks_url, ASIN, num_results=1000, response_groups="product_desc, product_attrs")

li_bookmarks = bookmarks_dict.get("payload").get("records")
li_clips = sorted(li_bookmarks, key=lambda i: i["type"], reverse=True)
print(li_clips)
audio_book = AudioSegment.from_wav(f"{ASIN}.wav")

file_counter = 1
notes_dict = {}
for audio_clip in li_clips:

    raw_start_pos = int(audio_clip["startPosition"])
    if audio_clip.get("type", None) in ["audible.note"]:
        notes_dict[raw_start_pos] = audio_clip.get("text")
        print(f"CLIP: {notes_dict[raw_start_pos]}  {raw_start_pos}")
    if audio_clip.get("type", None) in ["audible.clip", "audible.bookmark"]:
        start_pos = raw_start_pos - START_POSITION_OFFSET
        end_pos = int(audio_clip.get(
            "endPosition", raw_start_pos + 30000)) + END_POSITION_OFFSET
        if start_pos == end_pos:
            end_pos += 30000

        clip = audio_book[start_pos:end_pos]

        file_name = notes_dict.get(raw_start_pos, f"clip{file_counter}")

        clip.export(f"clips/{ASIN}/{file_name}.flac", format="flac")
        file_counter += 1
