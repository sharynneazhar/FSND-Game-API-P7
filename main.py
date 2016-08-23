#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""

import webapp2
from google.appengine.api import mail, app_identity

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)

        for user in users:
            games = Game.query(Game.user == user.key,
                               Game.game_over != False)
            for game in games:
                if game:
                    subject = 'This is a reminder!'
                    body = 'Hey {}, the battle isn\'t over!'.format(user.name)
                    # This sends test emails, the arguments to send_mail are:
                    # from, to, subject, body
                    mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                                   user.email,
                                   subject,
                                   body)

app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)
