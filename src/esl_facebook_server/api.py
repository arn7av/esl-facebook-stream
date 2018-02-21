from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS

import settings
from esl_facebook import fetch_esl_event_streams, get_esl_event

app = Flask(__name__)
api = Api(app)
CORS(app)


class EslFacebookStream(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('esl_event_id')
        super(EslFacebookStream, self).__init__()

    def get(self, esl_event_id):
        streams = fetch_esl_event_streams(esl_event_id)
        return streams


class EslEvent(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('esl_sport')
        super(EslEvent, self).__init__()

    def get(self, esl_sport):
        event_id = get_esl_event(esl_sport)
        return event_id


class Root(Resource):
    def get(self):
        return '~atx'


api.add_resource(Root, '/')
api.add_resource(EslFacebookStream, '/streams/<esl_event_id>')
api.add_resource(EslEvent, '/events/<esl_sport>')

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
