"""
Slack communication
JSON protocol
"""
from urllib import request
import json

SLACK_URL = "https://hooks.slack.com/services/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"

def send_message_to_slack(text):
    #text = parser(text)
    post = {"text": "{0}".format(text)}

    try:
        json_data = json.dumps(post)
        req = request.Request(SLACK_URL, data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'})
        resp = request.urlopen(req)
    except Exception as em:
        print("EXCEPTION: " + str(em))


def parser(msg):
    return ('*'+','.join(msg.decode("utf-8")[1:-3].split('\t')))


