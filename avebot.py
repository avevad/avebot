#!/usr/bin/python3

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from subprocess import *
from time import sleep

import time, os, re, sys, random

VERSION = "1.4" # bot version
PREF=";"        # command prefix
MAXLEN=4096     # maximum message length

# edits message and waits if necessary (FloodWait)
def edit_wait(msg, text):
    try:
        msg.edit(text)
    except FloodWait as ex:
        sleep(ex.x)

# appends report text to message, truncates text if necessary
def report(msg, what, keep=0):
    what = str(what)
    spl = what.split('\n')
    what = "\n".join(spl[:-keep - 1])
    to_keep = "\n".join(spl[-keep - 1:])
    text = msg.text
    text += "\n\n"
    text += f"avebot: {what}"
    oldlen = len(text) + 1 + len(to_keep)

    if oldlen > MAXLEN:
        newlen = MAXLEN - 100
        cut = oldlen - newlen
        text = text[:-cut-1] + f"\n(avebot: {cut} bytes truncated)\n"

    text += f"\n{to_keep}"
    msg.edit(text)

# strips out command name
def strip_cmd(msg):
    return msg.text[1 + len(msg.command[0]) + 1:]

if __name__ == "__main__":
    app = Client("avebot" if len(sys.argv) < 2 else sys.argv[1])

    @app.on_message(filters.command("help", prefixes=PREF) & filters.me)
    def help_msg(_, msg):
        help_str = f""" Available commands (prefix='{PREF}'):
    help - show this help
    test - show bot version
    stop - stop bot
    restart - restart bot
    eval - evaluate Python expression
    system - run system command"""
        report(msg, f"\n```{help_str}```")

    @app.on_message(filters.command("test", prefixes=PREF) & filters.me)
    def ping(_, msg):
        report(msg, f"v{VERSION} running")

    @app.on_message(filters.command("stop", prefixes=PREF) & filters.me)
    def halt(_, msg):
        report(msg, "stopped")
        exit(0)

    @app.on_message(filters.command("restart", prefixes=PREF) & filters.me)
    def restart(_, msg):
        report(msg, "restarting...")
        try:
            os.execv(sys.argv[0], sys.argv)
        except Exception as ex:
            report(msg, f"\n```{ex}\n```", keep=1)

    @app.on_message(filters.command(["eval", "="], prefixes=PREF) & filters.me)
    def eval_msg(_, msg):
        expr = strip_cmd(msg)
        try:
            report(msg, f"\n```{eval(expr)}\n```", keep=1)
        except Exception as ex:
            report(msg, f"\n```{ex}\n```", keep=1)

    @app.on_message(filters.command(["system", ";"], prefixes=PREF) & filters.me)
    def system_msg(_, msg):
        cmd = strip_cmd(msg)
        proc = Popen(cmd, shell=True, stdin=DEVNULL, stdout=PIPE, stderr=STDOUT, text=False, bufsize=0)
        msgtext = msg.text
        output = ""
        while True:
            app = proc.stdout.read(MAXLEN - (len(msgtext) + 3 + len(output) + 3)).decode(errors="ignore")
            if len(app) == 0:
                break
            output += app
            text = msgtext + f"\n```{output}```"
            if len(text) > MAXLEN:
                break
            try:
                edit_wait(msg, text)
            except Exception:
                pass
        output += proc.stdout.read().decode(errors="ignore")
        retcode_text = f"Exit code {proc.returncode or 0}"
        overflow = (len(msgtext) + 3 + len(output) + 3 + len(retcode_text)) - MAXLEN
        trunc_text = ""
        if overflow > 0:
            trunc_text = f"Truncated output (was {len(output)} bytes)\n"
            output = output[:-(overflow + len(trunc_text))]
        text = msgtext + f"\n```{output}```" + trunc_text + retcode_text
        edit_wait(msg, text)

    app.run()

