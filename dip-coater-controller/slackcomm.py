from urllib import request, parse
import json

SLACK_URL = "https://hooks.slack.com/services/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"

def send_message_to_slack(text):
    post = {"text": "{0}".format(text)}

    try:
        json_data = json.dumps(post)
        req = request.Request(SLACK_URL, data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'})
        resp = request.urlopen(req)
    except Exception as em:
        print("EXCEPTION: " + str(em))