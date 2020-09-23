import discord
import asyncio
import os
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def find_trade(driver, query, is_simple):
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

def find_wiki(driver, query):
    url = 'https://pathofexile.gamepedia.com/index.php?search=intitle%3A%2F{}%2F'.format(query)

    driver.get(url)

    WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'searchresults'))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    sr = soup.find_all('div', class_='searchresults')
    no_result = sr[0].find_all('p', class_='mw-search-nonefound')

    if len(no_result) > 0:
        return []
    
    res = []

    result_boxes = sr[0].find_all('li', class_='mw-search-result')

    top_results = result_boxes if len(result_boxes) <= 5 else result_boxes[:5]

    for r in top_results:
        content = r.find_all('div')[0]
        title = content.get_text()
        link = "https://pathofexile.gamepedia.com" + content.find_all('a')[0].get('href')
        res.append({
            'title': title,
            'link': link
        })
    
    return res

def find_wiki_korean(driver, query):
    url = 'https://poedb.tw/kr/search.php?q={}'.format(query)

    driver.get(url)

    WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'form-search'))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    page = soup.find_all('div', class_='page')

    res = []

    result_boxes = page[0].find_all('li', class_='list-group-item')

    top_results = result_boxes if len(result_boxes) <= 5 else result_boxes[:5]

    for r in top_results:
        content = r.find_all('a')[0]
        title = content.get_text()
        link = "https://poedb.tw/" + content.get('href')
        res.append({
            'title': title,
            'link': link
        })

    return res

if __name__ == "__main__":

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    
    driver = webdriver.Chrome('driver-linux/chromedriver', chrome_options=options)


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
            embed.add_field(name = '!가격 ... , !price ...', value = "자주 쓰이는 카테고리 내에서 검색 (take ~10s)", inline = False)
            embed.add_field(name = '!상세가격 ... , !detail_price ...', value = "모든 카테고리 내에서 검색 (take ~25s)", inline = False)
            embed.add_field(name = '!wiki ...', value = "영어 위키에서 검색", inline = False)
            embed.add_field(name = '!위키 ...', value = "한글 위키에서 검색", inline = False)
            await message.channel.send(embed = embed)

        if message.content.startswith('!price') or message.content.startswith('!가격') or message.content.startswith('!detail_price') or message.content.startswith('!상세가격'):

            await message.channel.send("가격 검색중...")

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

            result = find_trade(driver, query, is_simple)

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
        
        if message.content.startswith('!wiki'):
            await message.channel.send("wiki searching...")
            query = message.content[6:]

            result = find_wiki(driver, query)

            embed_title = query + ' wiki search result'

            if len(result) == 5:
                embed_title += ' (top 5)'

            embed = discord.Embed(title = embed_title)

            if len(result) == 0:
                embed.add_field(name = 'There is', value = "no result", inline = False)
                await message.channel.send(embed = embed)
            else:
                for r in result:
                    embed.add_field(name = r['title'], value = r['link'], inline = False)
                await message.channel.send(embed = embed)

        if message.content.startswith('!위키'):
            await message.channel.send("위키 검색중...")
            query = message.content[4:]

            result = find_wiki_korean(driver, query)

            embed_title = query + ' 위키 검색 결과'

            if len(result) == 5:
                embed_title += ' (top 5)'

            embed = discord.Embed(title = embed_title)

            if len(result) == 0:
                embed.add_field(name = '검색 결과가', value = "없습니다", inline = False)
                await message.channel.send(embed = embed)
            else:
                for r in result:
                    embed.add_field(name = r['title'], value = r['link'], inline = False)
                await message.channel.send(embed = embed)
                
    client.run(token)
