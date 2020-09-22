import discord
import asyncio
import os
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def find_trade(query, is_simple):
    url_query = query.strip().replace(" ","%20")

    if len(url_query) == 0:
        return []

    simple_categories = [
        "divinationcards",
        "prophecies",
        "skill-gems",
        "unique-jewels",
        "unique-flasks",
        "unique-weapons",
        "unique-armours",
        "unique-accessories"
    ]

    categories = [
        "delirium-orbs",
        "watchstones",
        "oils",
        "incubators",
        "scarabs",
        "fossils",
        "resonators",
        "essences",
        "divinationcards",
        "prophecies",
        "skill-gems",
        "base-types",
        "helmet-enchants",
        "unique-maps",
        "maps",
        "unique-jewels",
        "unique-flasks",
        "unique-weapons",
        "unique-armours",
        "unique-accessories",
        "beasts",
        "vials"
    ]

    unit_replace = {
        "엑잘티드 오브": "Exilted",
        "카오스 오브": "Chaos"
    }

    res = []

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    
    driver = webdriver.Chrome('driver-linux/chromedriver', chrome_options=options)

    target_cat = simple_categories if is_simple else categories

    for cat in target_cat:
        url = 'https://poe.ninja/challenge/{}?name={}'.format(cat, url_query)
        driver.get(url)

        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "item-overview"))
        )

        lang = driver.find_element_by_xpath("//img[starts-with(@src,'https://web.poecdn.com/image/lang/')]")
        if lang.get_attribute('title') != 'Korean':
            lang.click()
            
            kr_xpath = "//img[@src='https://web.poecdn.com/image/lang/KR.png']"

            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, kr_xpath))
            )
            
            btn = driver.find_element_by_xpath(kr_xpath)
            btn.click()

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find_all('table', class_='table-striped')
        if len(table) > 0:
            body = table[0].find_all('tbody')
            if len(body):
                trs = body[0].find_all('tr')
                for t in trs:
                    tds = t.find_all('td')
                    name = tds[0].find_all('div')[0].find_all('div')[0].get_text()
                    trand = tds[-3].find_all('span')[0].find_all('div')[1].find_all('span')[0].get_text()
                    price_list = []
                    price_span = tds[-2].find_all('div')[0].find_all('span')
                    for p in price_span:
                        img = p.find_all('img')
                        if len(img) > 0:        
                            pr = p.get_text()
                            unit = unit_replace[img[0].get('title')]
                            price_list.append(pr + unit)
                    price = ' / '.join(price_list)
                    res.append({
                        "name": name,
                        "trand": trand,
                        "price": price
                    })
        
    return res


if __name__ == "__main__":
    t = open('token.txt', 'r')
    token = t.read().rstrip()
    blank = '\u200B'

    client = discord.Client()

    @client.event
    async def on_ready():
        print('start')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!help_poe'):
            embed = discord.Embed(title = "PoE Bot")
            embed.add_field(name = '!가격, !price', value = "자주 쓰이는 카테고리 내에서 검색")
            embed.add_field(name = '!상세가격, !detail_price', value = "모든 카테고리 내에서 검색")

        if message.content.startswith('!price') or message.content.startswith('!가격') or message.content.startswith('!detail_price') or message.content.startswith('!상세가격'):

            await message.channel.send("검색중...")

            query = ""
            is_simple = True

            if message.content.startswith('!price'):
                query = message.content[7:]
            elif message.content.startswith('!가격'):
                query = message.content[4:]
            elif message.content.startswith('!detail_price'):
                query = message.content[11:]
                is_simple = False
            else:
                query = message.content[6:]
                is_simple = False

            result = find_trade(query, is_simple)

            embed = discord.Embed(title = (query + ' 가격 검색 결과'))
            embed.add_field(name = '이름', value = blank, inline = True)
            embed.add_field(name = '추세', value = blank, inline = True)
            embed.add_field(name = '가격', value = blank, inline = True)

            if len(result) == 0:
                embed.add_field(name = blank, value = "There's", inline = True)
                embed.add_field(name = blank, value = 'no', inline = True)
                embed.add_field(name = blank, value = 'result', inline = True)
            elif len(result) > 20:
                embed.add_field(name = blank, value = "Too", inline = True)
                embed.add_field(name = blank, value = 'many', inline = True)
                embed.add_field(name = blank, value = 'result', inline = True)
            else:
                for r in result:
                    embed.add_field(name = blank, value = r['name'], inline = True)
                    embed.add_field(name = blank, value = r['trand'], inline = True)
                    embed.add_field(name = blank, value = r['price'], inline = True)

            await message.channel.send(embed = embed)

    client.run(token)
