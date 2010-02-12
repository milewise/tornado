#!/usr/bin/env python
#
# Copyright 2010 W-Mark Kubacki
#

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options
from tornado import validators

define("port", default=8888, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        if self.error_for('email'):
            message = '<font color="red">' + self.error_for('email') + '</font><br />'
        else:
            message = 'Please give us your email.'
        old_value = self.get_argument("email", '')
        self.write(
            message 
            + '<form method="post">Email: <input type="text" name="email" value="' 
            + old_value + '" />'
            + '<input type="submit" /></form>'
        )

    @validators.error_handler(get)
    @validators.validate(validators={'email': validators.Email(not_empty=True)})
    def post(self):
        self.write("Your email is <b>%s</b>." % self.get_argument("email"))


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application(trivial_handlers={
        "/": MainHandler,
    })
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
