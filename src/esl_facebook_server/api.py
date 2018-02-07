from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS

import settings
from esl_facebook import fetch_streams

app = Flask(__name__)
api = Api(app)
CORS(app)

parser = reqparse.RequestParser()
parser.add_argument('esl_event_id')


class EslFacebookStream(Resource):
    def get(self, esl_event_id):
        streams = fetch_streams(esl_event_id)
        return streams


class Root(Resource):
    def get(self):
        return '~atx'


api.add_resource(Root, '/')
api.add_resource(EslFacebookStream, '/streams/<esl_event_id>')

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
