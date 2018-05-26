from flask import Flask, jsonify, make_response
from flask_cors import CORS
from flask_restful import abort, Api, Resource

import settings
from esl_facebook import fetch_esl_event_streams, get_esl_event, get_esl_events, get_default_event_family_streams, \
    get_default_event_family_first_stream_url

app = Flask(__name__)
api = Api(app)
cors_origins = 'https:\/\/(.+\.)?atx\.sx' if not settings.CORS_ALL_ORIGINS else '*'
CORS(app, origins=cors_origins)


class EslFacebookStream(Resource):
    def get(self, esl_event_id):
        streams = fetch_esl_event_streams(esl_event_id)
        return jsonify(streams)


class EslDefaultEventFamilyFacebookStream(Resource):
    def get(self):
        streams = get_default_event_family_streams()
        return jsonify(streams)


class EslDefaultEventFamilyFirstFacebookStreamUrl(Resource):
    def get(self):
        stream = get_default_event_family_first_stream_url()
        resp = make_response(stream or '')
        resp.mimetype = 'text/plain'
        return resp


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
        resp = make_response('~atx')
        resp.mimetype = 'text/plain'
        return resp


api.add_resource(Root, '/')
api.add_resource(EslFacebookStream, '/streams/<int:esl_event_id>')
api.add_resource(EslEvent, '/events/<string:esl_sport>')
api.add_resource(EslEventList, '/events')
api.add_resource(EslDefaultEventFamilyFacebookStream, '/streams/default')
api.add_resource(EslDefaultEventFamilyFirstFacebookStreamUrl, '/default')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=settings.DEBUG)
