from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import abort, Api, Resource

import settings
from esl_facebook import fetch_esl_event_streams, get_esl_event, get_esl_events

app = Flask(__name__)
api = Api(app)
CORS(app, origins='https:\/\/(.+\.)?atx\.sx')


class EslFacebookStream(Resource):
    def get(self, esl_event_id):
        streams = fetch_esl_event_streams(esl_event_id)
        return jsonify(streams)


class EslEvent(Resource):
    def get(self, esl_sport):
        event = get_esl_event(esl_sport)
        if not event:
            abort(404, message='invalid sport')
        return jsonify(event)


class EslEventList(Resource):
    def get(self):
        return jsonify(get_esl_events())


class Root(Resource):
    def get(self):
        return '~atx'


api.add_resource(Root, '/')
api.add_resource(EslFacebookStream, '/streams/<int:esl_event_id>')
api.add_resource(EslEvent, '/events/<string:esl_sport>')
api.add_resource(EslEventList, '/events')

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
