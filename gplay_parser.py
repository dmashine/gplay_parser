#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Парсер обработки данных по приложению из базы Google Play.
# Использует MongoDB в качестве кеша и aiohttp для получения данных

import aiohttp
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pprint import pprint

# connectstr = "mongodb://gplayuser:gplay12345@cluster0-shard-00-00-pm6zd.mongodb.net:27017,cluster0-shard-00-01-pm6zd.mongodb.net:27017,cluster0-shard-00-02-pm6zd.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true"
connectstr = "mongodb://mongodb:27017"

class gplay_parser:
    """Парсер Google Play.
    Параметры: gplay_id Идентификатор приложения в Маркете,
                hl - язык"""
    def __init__(self, gplay_id, hl = "en"):
        self.gplay_id = gplay_id
        self.hl = hl
        self.permissions = []

    async def parse(self):
        """Получим данные по странице и сохраним в self.permissions"""
        url = "https://play.google.com/store/xhr/getdoc?authuser=0"
        data = {
            "ids": self.gplay_id,
            "hl": self.hl,
            "xhr": 1,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                if resp.status == 500:
                    print("error reading")
                    text = "{}"
                else:
                    text = await resp.text()

        # На самом деле, Гугл  нам возвращает нечто jsonоподобное - protobuf
        # Так как у нас нет proto файла для него, немножко бьем в бубен
        # magic, see https://github.com/facundoolano/google-play-scraper
        text = text.replace(")]}'", "")
        text = text.replace(",,", ",null,")
        text = text.replace("[,", "[null,")

        msg = json.loads(text)
        try:
            permissions = msg[0][2][0][65]['42656262'][1]
            for permission in permissions:  # Докапываемся до нужного пермишена
                for permission1 in permission:
                    for permission2 in permission1:
                        if isinstance(permission2, list):
                            for p in permission2:
                                self.permissions.append(p[:2])
        except:
            print("permissions read error: '%s'" % text)
            pass

    async def save(self):
        """Сохраняет полученные данные из self.permissions в MongoDB"""
        client = MongoClient(connectstr)
        db = client['gplay-permissions']
        records = db.records
        data = {"name": self.gplay_id,
                "hl": self.hl,
                "permissions": self.permissions}
        await records.insert_one(data)

    async def read(self):
        """Считывает даннные из MongoDB и возвращает Permissions"""
        client = MongoClient(connectstr)
        db = client['gplay-permissions']
        records = db.records
        query = {"name":self.gplay_id, "hl":self.hl}
        if await records.count_documents(query) == 0:
            await self.parse()
            await self.save()
        ret = await records.find_one(query)
        return ret

    async def count(self):
        """Проверяет количество объектов в базе с такими gplay_id и hl"""
        client = MongoClient(connectstr)
        db = client['gplay-permissions']
        records = db.records
        query = {"name":self.gplay_id, "hl":self.hl}
        ret = await records.count_documents(query)
        return ret

async def produce(queue):
    apps = ["org.telegram.messenger", "com.vkontakte.android", "com.evernote", "org.mozilla.firefox",
            "ru.worldoftanks.mobile", "com.instagram.android", "com.whatsapp", "com.android.chrome"]
    hls = ["ru", "en"]
    for a in apps:
        for h in hls:
            await queue.put({"app": a, "hl": h})

async def consume(queue):
    while True:
        item = await queue.get()
        g_p = gplay_parser(item["app"], item["hl"])
        await g_p.parse()
        r = await g_p.count()
        if r == 0 and g_p.permissions:
            await g_p.save()
        queue.task_done()
        if queue.empty():
            break

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    producer_coro = produce(queue)
    consumer_coro = consume(queue)
    loop.run_until_complete(asyncio.gather(producer_coro, consumer_coro))
    loop.close()

    # wot = gplay_parser(gplay_id = "ru.worldoftanks.mobile")
    # for _ in wot.read():
    #    pprint(_)
