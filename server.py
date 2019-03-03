#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Сервер выдачи информации по базе разрешений Google play
# Запуск: ./server.py
# Открывает сервер на http://localhost:8080
# TODO:
# - Отрефакторить HTML текст в отдельные шаблоны, сделать дизайн
# - Передавать порт сервера в качестве параметра

from aiohttp import web
import asyncio
import json
# from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pprint import pprint
from gplay_parser import gplay_parser

async def main(request):
    """
    Главная функция, получает запрос и выдает:
    - Главную страницу, если параметры не переданы
    - Страницу с информацией по приложению, если переданы
    """
    if len(request.rel_url.query) == 0:  # Нет параметров
        response_text = """<!DOCTYPE html>
      <html>
      <head>
          <meta http-equiv="Content-Type" content="text/html; charset=utf-8"><body>
           <h1>Проверка прав приложения</h1>
        <form action="/" method="get">
            Google app ID: <input type="text" name="gplay_id" /><br />
            Language: <input type="text" name="hl" /><br />
            <input type="submit" value="Submit" />
        </form>
        </body>
        </html>"""
    else:  # Переданы gplay_id и возможно hl
        gplay_id = request.rel_url.query['gplay_id']
        hl = request.rel_url.query['hl']
        g_p = gplay_parser(gplay_id, hl)
        ans = await g_p.read()
        response_text = """<!DOCTYPE html>
            <html>
            <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"><body> <h1>%s %s</h1><ul>""" % (gplay_id, hl)
        for s in ans["permissions"]:
            response_text += "<li> %s (<i>%s</i>)" % (s[0], s[1])
        response_text += "</ul></body></html>"    
    return web.Response(text=response_text, content_type = "text/html")  # Отвечаем обязательно типом данных text/html


if __name__ == "__main__":
    print("started")
    app = web.Application()
    app.add_routes([web.get('/', main)])
    web.run_app(app)
