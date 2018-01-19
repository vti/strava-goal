#!/usr/bin/env python

import json
import http.client
import re
from wsgiref.simple_server import make_server
from cgi import parse_qs, escape

def application(env, start_response):
    path_info = env.get('PATH_INFO')
    request_method = env.get('REQUEST_METHOD')

    if request_method == 'GET':
        if path_info == '/':
            start_response('302 OK', [('Location','/index.html')])
            return [b""]

        if path_info == '/index.html':
            content = slurp('public/index.html', 'r')
            start_response('200 OK', [('Content-Type', 'text/html; chartset=utf-8'), ('Content-Length', str(len(content)))])
            return [bytes(content.encode('utf-8'))]

        if path_info == '/strava-64.png':
            content = slurp('public/strava-64.png', 'rb')
            start_response('200 OK', [('Content-Type', 'image/png'), ('Content-Length', str(len(content)))])
            return [bytes(content)]
    elif request_method == 'POST':
        if path_info == '/':
            try:
                request_body_size = int(env.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            request_body = env['wsgi.input'].read(request_body_size)
            post_data = parse_qs(request_body)

            athlete_id = post_data.get(bytes('athlete_id'.encode('utf-8')), 0)[0].decode('utf-8')
            if athlete_id == "":
                return bad_request(start_response)

            html = fetch_profile(athlete_id)

            m = re.search("<td>(\d+(?:\.\d+)?)<abbr class='unit' title='kilometers'>", html)
            if not m:
                return bad_request(start_response)

            distance = m.group(1);

            m = re.search("<title>(.*?)<\/title>", html)
            if not m:
                return bad_request(start_response)

            name = m.group(1);

            body = json.dumps({'distance': distance, 'name': name})

            start_response('200 OK', [('Content-Type','application/json'), ('Content-Length', str(len(body)))])

            return [bytes(body.encode('utf-8'))]

    start_response('404 Not Found', [('Content-Type','text/html'), ('Content-Length', str(9))])

    return [b"Not Found"]

def slurp(path, mode):
    with open(path, mode=mode) as x: content = x.read()
    return content

def fetch_profile(athlete_id):
    c = http.client.HTTPSConnection("www.strava.com")
    c.request("GET", "/athletes/" + athlete_id)
    response = c.getresponse()
    data = response.read()
    return data.decode('utf-8')

def bad_request(start_response):
    body = 'Bad Request'

    start_response('400 Bad Request', [('Content-Type','text/plain'), ('Content-Length', str(len(body)))])

    return [bytes(body.encode('utf-8'))]

httpd = make_server('localhost', 5000, application)
httpd.serve_forever()
