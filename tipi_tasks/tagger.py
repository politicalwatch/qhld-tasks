import codecs
import pickle

import regex
from celery import shared_task

from tipi_tasks import app
from .infrastructure.config.settings import get_settings


def __append_tag_to_founds(tags_found, new_tag):
    found = False
    for tag in tags_found:
        if (
            tag["topic"] == new_tag["topic"]
            and tag["subtopic"] == new_tag["subtopic"]
            and tag["tag"] == new_tag["tag"]
        ):
            found = True
            tag["times"] = tag["times"] + new_tag["times"]
            break
    if not found:
        tags_found.append(new_tag)


@shared_task
def extract_tags_from_text(text, tags):
    tags = pickle.loads(codecs.decode(tags.encode(), "base64"))

    tags_found = []
    text = " ".join(text.splitlines())
    for line in text.split("."):
        # Skip lines with no value to make it faster.
        if len(line) < 2 or text.isdigit():
            continue

        for tag in tags:
            try:
                result = regex.findall(tag["compiletag"], line)
                times = len(result)
                if times > 0:
                    # Uncomment and change the tag to learn which line is getting tagged with the specific tag.
                    # if tag['tag'] == 'Inclusión multicultural':
                    # print(line)
                    tag_copy = tag.copy()
                    tag_copy.pop("compiletag")
                    tag_copy["times"] = times
                    __append_tag_to_founds(tags_found, tag_copy)
            except regex.error as e:
                print(e)

    excerpt_size = get_settings().scanned_text_excerpt_size
    return {
        "status": "SUCCESS",
        "excerpt": (
            text if len(text) <= excerpt_size else text[: excerpt_size - 3] + " [...]"
        ),
        "result": {
            "topics": sorted(list(set([tag["topic"] for tag in tags_found]))),
            "tags": sorted(
                tags_found, key=lambda t: (t["topic"], t["subtopic"], t["tag"])
            ),
        },
    }


def check_status_task(task_id):
    task = app.AsyncResult(task_id)
    excerpt = None
    result = None
    st = task.status
    if st == "SUCCESS":
        excerpt = task.get()["excerpt"]
        result = task.get()["result"]
    return {"status": st, "excerpt": excerpt, "result": result}
