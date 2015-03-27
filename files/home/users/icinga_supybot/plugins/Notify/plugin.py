###
# Copyright (c) 2010, Ricky Zhou
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.ircmsgs as ircmsgs
import threading
import SocketServer
import select

class NotifyServerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        try:
            while True:
                line = self.rfile.readline()
                if not line:
                    break
                line = line.strip()
                (channel, text) = line.split(' ', 1)
                if not channel or not text:
                    continue
                if self.server.channel_states.get(channel, "on") == "on":
                    if self.server.registryValue('use_notice'):
                        msg = ircmsgs.notice(channel, text)
                    else:
                        msg = ircmsgs.privmsg(channel, text)
                    for irc in world.ircs:
                        if channel in irc.state.channels:
                            irc.queueMsg(msg)
        except BaseException as e:
            """In the future there should be specific exception
            handlers here. Until then we'll just print out the base
            one."""
            print e

class StoppableThreadingTCPServer(SocketServer.ThreadingTCPServer):
    '''ThreadingTCPServer with shutdown capability copied from Python SVN'''
    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)
        self.__is_shut_down = threading.Event()
        self.__serving = False

    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self.__serving = True
        self.__is_shut_down.clear()
        while self.__serving:
            # XXX: Consider using another file descriptor or
            # connecting to the socket to wake this up instead of
            # polling. Polling reduces our responsiveness to a
            # shutdown request and wastes cpu at all other times.
            r, w, e = select.select([self], [], [], poll_interval)
            if r:
                self._handle_request_noblock()
        self.__is_shut_down.set()

    def shutdown(self):
        """Stops the serve_forever loop.

        Blocks until the loop has finished. This must be called while
        serve_forever() is running in another thread, or it will
        deadlock.
        """
        self.__serving = False
        self.__is_shut_down.wait()

    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that select.select has returned that the socket is
        readable before this function was called, so there should be
        no risk of blocking in get_request().
        """
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.close_request(request)

class NotifyServer(StoppableThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        StoppableThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)
        self.channel_states = {}

class Notify(callbacks.Plugin):
    """This plugin relays messages passed to its TCP server to an IRC channel."""
    threaded = True
    def __init__(self, irc):
        self.__parent = super(Notify, self)
        self.__parent.__init__(irc)
        self.host = self.registryValue('server_address')
        self.port = self.registryValue('server_port')
        self.server = NotifyServer((self.host, self.port), NotifyServerHandler)
        self.server.registryValue = self.registryValue
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def notifications(self, irc, msg, args, channel, state):
        """Turn notifications on or off in the current channel."""
        if state is None:
            irc.reply("Notifications for %s: %s" % (channel,
                self.server.channel_states.get(channel, "on")))
        else:
            if state:
                self.server.channel_states[channel] = "on"
                irc.reply("Notifications for %s are now on" % channel )
            else:
                self.server.channel_states[channel] = "off"
                irc.reply("Notifications for %s are now off" % channel )

    notifications = wrap(notifications, ['inChannel', optional('boolean')])

    def die(self):
        self.server.shutdown()
        self.server.server_close()
        self.__parent.die()

Class = Notify


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
