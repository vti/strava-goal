#!/usr/bin/env python3

import json
import re
import http.client
from wsgiref.simple_server import make_server
from webob import Request, Response

def application(env, start_response):
    req = Request(env)

    if req.method == 'GET':
        if req.path_info == '/':
            res = Response(status=302, headers=[('Location', '/index.html')])
            return res(env, start_response)
        elif req.path_info == '/index.html':
            content = slurp('public/index.html', 'r')
            res = Response(headers=[('Content-Type', 'text/html; chartset=utf-8')], body=content)
            return res(env, start_response)
        elif req.path_info == '/strava-64.png':
            content = slurp('public/strava-64.png', 'rb')
            res = Response(headers=[('Content-Type', 'image/png')], body=content)
            return res(env, start_response)
    elif req.method == 'POST':
        if req.path_info == '/':
            athlete_id = req.POST['athlete_id']
            if athlete_id == "":
                return bad_request(start_response)

            html = fetch_profile(athlete_id)

            m = re.search(r"<td>(\d+(?:\.\d+)?)<abbr class='unit' title='kilometers'>", html)
            if not m:
                return bad_request(start_response)

            distance = m.group(1)

            m = re.search(r"<title>(.*?)<\/title>", html)
            if not m:
                return bad_request(start_response)

            name = m.group(1)

            body = json.dumps({'distance': distance, 'name': name})

            res = Response(headers=[('Content-Type', 'application/json')], body=body)
            return res(env, start_response)

    res = Response(status=404, headers=[('Content-Type', 'text/html')], body="Not Found")
    return res(env, start_response)

def slurp(path, mode):
    with open(path, mode=mode) as handle:
        content = handle.read()
    return content

def fetch_profile(athlete_id):
    conn = http.client.HTTPSConnection("www.strava.com")
    conn.request("GET", "/athletes/" + athlete_id)
    response = conn.getresponse()
    data = response.read()
    return data.decode('utf-8')

def bad_request(start_response):
    body = 'Bad Request'

    start_response('400 Bad Request', [('Content-Type', 'text/plain'), ('Content-Length', str(len(body)))])

    return [bytes(body.encode('utf-8'))]

if __name__ == "__main__":
    hostname = 'localhost'
    port = 5000
    print('Listening on {}:{}'.format(hostname, str(port)))
    httpd = make_server(hostname, port, application)
    httpd.serve_forever()
