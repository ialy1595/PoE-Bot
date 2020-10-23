import discord
import asyncio
import os
import datetime
from pytz import timezone, utc
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3

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

        WebDriverWait(driver, 10, 0.1).until(
            EC.presence_of_element_located((By.CLASS_NAME, "item-overview"))
        )

        lang = driver.find_element_by_xpath("//img[starts-with(@src,'https://web.poecdn.com/image/lang/')]")
        if lang.get_attribute('title') != 'Korean':
            lang.click()
            
            kr_xpath = "//img[@src='https://web.poecdn.com/image/lang/KR.png']"

            WebDriverWait(driver, 10, 0.1).until(
                EC.element_to_be_clickable((By.XPATH, kr_xpath))
            )
            
            btn = driver.find_element_by_xpath(kr_xpath)
            btn.click()

            WebDriverWait(driver, 10, 0.1).until(
                EC.presence_of_element_located((By.CLASS_NAME, "item-overview"))
            )

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        tbody = soup.select_one('table.table-striped > tbody')
        if tbody is not None:
            trs = tbody.select('tr')
            for t in trs:
                tds = t.select('td')
                name = tds[0].select_one('div > div').get_text()
                trand = tds[-3].select('span > div')[1].select_one('span').get_text()
                price_list = []
                price_span = tds[-2].select_one('div').select('span')
                for p in price_span:
                    img = p.select_one('img')
                    if img is not None:
                        pr = p.get_text()
                        unit = unit_replace[img.get('title')]
                        price_list.append(pr + unit)
                price = ' / '.join(price_list)
                res.append({
                    "name": name,
                    "trand": trand,
                    "price": price
                })
    
    return res

def find_wiki(driver, query):

    swap_query = query.swapcase()

    reg_query = ""

    for i in range(len(query)):
        if query[i] != swap_query[i]:
            reg_query += '[' + query[i] + swap_query[i] + ']'
        else:
            reg_query += query[i]

    url = 'https://pathofexile.gamepedia.com/index.php?search=intitle%3A%2F{}%2F'.format(reg_query)

    driver.get(url)

    WebDriverWait(driver, 10, 0.1).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'searchresults'))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    sr = soup.select_one('div.searchresults')
    no_result = sr.select('p.mw-search-nonefound')

    if len(no_result) > 0:
        return []
    
    res = []

    result_boxes = sr.select('li.mw-search-result')

    top_results = result_boxes if len(result_boxes) <= 5 else result_boxes[:5]

    for r in top_results:
        content = r.select_one('div')
        title = content.get_text()
        link = "https://pathofexile.gamepedia.com" + content.select_one('a').get('href')
        res.append({
            'title': title,
            'link': link
        })
    
    return res

def find_wiki_korean(driver, query):
    url = 'https://poedb.tw/kr/search.php?q={}'.format(query)

    driver.get(url)

    WebDriverWait(driver, 10, 0.1).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'form-search'))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    page = soup.select_one('div.page')

    res = []

    result_boxes = page.select('li.list-group-item')

    top_results = result_boxes if len(result_boxes) <= 5 else result_boxes[:5]

    for r in top_results:
        content = r.select_one('a')
        title = content.get_text()
        link = "https://poedb.tw/" + content.get('href')
        res.append({
            'title': title,
            'link': link
        })

    return res

def find_currency(driver):
    url = 'https://poe.ninja/challenge/currency'

    driver.get(url)

    WebDriverWait(driver, 10, 0.1).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'currency-table'))
    )

    lang = driver.find_element_by_xpath("//img[starts-with(@src,'https://web.poecdn.com/image/lang/')]")
    if lang.get_attribute('title') != 'Korean':
        lang.click()
        
        kr_xpath = "//img[@src='https://web.poecdn.com/image/lang/KR.png']"

        WebDriverWait(driver, 10, 0.1).until(
            EC.element_to_be_clickable((By.XPATH, kr_xpath))
        )
        
        btn = driver.find_element_by_xpath(kr_xpath)
        btn.click()

        WebDriverWait(driver, 10, 0.1).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'currency-table'))
        )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    res = []

    result_boxes = soup.select('table.currency-table > tbody > tr')

    for r in result_boxes:
        not_enough = r.select_one('td.not-enough-data')
        if not_enough is not None:
            continue
        tds = r.select('td')

        res.append({
            'name': tds[0].select_one('span').get_text(),
            'buy': tds[2].select_one('span').get_text() + 'chaos',
            'sell': tds[7].select_one('span').get_text() + 'chaos'
        })

        if len(res) >= 10:
            break

    return res        

def calc_d_day(doom):
    KST = datetime.timezone(datetime.timedelta(hours=9))
    utc_now = datetime.datetime.utcnow()
    kr_now = utc.localize(utc_now).astimezone(KST)

    delta = doom - kr_now    

    if delta.days < 0:
        d_days = -1 - delta.days
        d_hour = (86400 - delta.seconds) // 3600
        d_minutes = ((86400 - delta.seconds) // 60) % 60
        d_seconds = (86400 - delta.seconds) % 60
        return [False, d_days, d_hour, d_minutes, d_seconds]
    else:
        d_days = delta.days
        d_hour = delta.seconds // 3600
        d_minutes = (delta.seconds // 60) % 60
        d_seconds = delta.seconds % 60
        return [True, d_days, d_hour, d_minutes, d_seconds]

def adapt_datetime(dt):
    ts = dt.strftime('%c')
    tz = dt.strftime('%z')
    if len(tz) == 0:
        tz = '+0000'
    return '{} {}'.format(ts, tz)

def convert_datetime(dt):
    return datetime.datetime.strptime(dt.decode(), '%c %z')

if __name__ == "__main__":

    sqlite3.register_adapter(datetime.datetime, adapt_datetime)
    sqlite3.register_converter('datetime', convert_datetime)
    
    conn = sqlite3.connect("poe.db", detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    cur = conn.cursor()

    create_table_query = '''
                         CREATE TABLE IF NOT EXISTS Dday (
                            id INTEGER AUTO_INCREMENT PRIMARY KEY,
                            guild TEXT NOT NULL,
                            name TEXT NOT NULL,
                            date datetime
                         );
                         '''
    cur.execute(create_table_query)
    conn.commit()

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    
    driver = webdriver.Chrome('driver-linux/chromedriver', chrome_options=options)

    price_result_channel = {}

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

        if message.content.startswith('!'):
            query = message.content[1:]
            query_words = query.split()
            if len(query_words) == 1:
                find_date_query = 'SELECT date from Dday where guild = ? and name = ?'
                cur.execute(find_date_query, (message.guild.id, query))
                result = cur.fetchall()
                for row in result:
                    delta = calc_d_day(row[0])
                    if delta[0]:
                        await message.channel.send('{}일 {}시간 {}분 {}초 남았습니다.'.format(delta[1], delta[2], delta[3], delta[4]))
                    else:
                        await message.channel.send('{}일 {}시간 {}분 {}초 지났습니다.'.format(delta[1], delta[2], delta[3], delta[4]))

        if message.content.startswith('!디데이'):
            query = message.content[4:]
            query_words = query.split()

            if len(query_words) == 0:
                return
            elif len(query_words) == 1:
                d_name = query_words[0]
                find_date_query = 'SELECT date from Dday where guild = ? and name = ?'
                cur.execute(find_date_query, (message.guild.id, query))
                result = cur.fetchall()
                if len(result) > 0:
                    for row in result:
                        delta = calc_d_day(row[0])
                        if delta[0]:
                            await message.channel.send('{}일 {}시간 {}분 {}초 남았습니다.'.format(delta[1], delta[2], delta[3], delta[4]))
                        else:
                            await message.channel.send('{}일 {}시간 {}분 {}초 지났습니다.'.format(delta[1], delta[2], delta[3], delta[4]))
                else:
                    await message.channel.send('{} 디데이가 아직 등록되지 않았습니다.'.format(d_name))
                    await message.channel.send('!디데이 추가 (이름) (YYYY-MM-DD) ?(HH:MM:SS) 로 등록해주세요.')
                
            else:
                if query_words[0] == '추가':
                    d_name = query_words[1]
                    d_date = query_words[2].split('-')
                    d_time = [23, 59, 59] if len(query_words) <= 3 else query_words[3].split(':')

                    KST = datetime.timezone(datetime.timedelta(hours=9))
                    d_datetime = datetime.datetime(int(d_date[0]), int(d_date[1]), int(d_date[2]), int(d_time[0]), int(d_time[1]), int(d_time[2]), tzinfo=KST)

                    insert_date_query = 'insert into Dday(guild, name, date) VALUES (?, ?, ?)'
                    cur.execute(insert_date_query, (message.guild.id, d_name, d_datetime))
                    conn.commit()

                    delta = calc_d_day(d_datetime)
                    if delta[0]:
                        await message.channel.send('{}일 {}시간 {}분 {}초 남은 {} 디데이가 등록되었습니다.'.format(delta[1], delta[2], delta[3], delta[4], d_name))
                    else:
                        await message.channel.send('{}일 {}시간 {}분 {}초 지난 {} 디데이가 등록되었습니다.'.format(delta[1], delta[2], delta[3], delta[4], d_name))

                elif query_words[0] == '삭제':
                    d_name = query_words[1]

                    find_date_query = 'SELECT date from Dday where guild = ? and name = ?'
                    cur.execute(find_date_query, (message.guild.id, d_name))
                    result = cur.fetchall()

                    if len(result) > 0:
                        delete_date_query = 'delete from Dday where guild = ? and name = ?'
                        cur.execute(delete_date_query, (message.guild.id, d_name))
                        result = cur.fetchall()
                        conn.commit()
                        await message.channel.send('{} 디데이가 삭제되었습니다.'.format(d_name))
                    else:
                        await message.channel.send('{} 디데이가 아직 등록되지 않았습니다.'.format(d_name))
                        await message.channel.send('!디데이 추가 (이름) (YYYY-MM-DD) ?(HH:MM:SS) 로 등록해주세요.')
            


        if message.content.startswith('!help') or message.content.startswith('!도움'):
            embed = discord.Embed(title = "PoE Bot")
            embed.add_field(name = '!가격 ... , !price ...', value = "점술카드, 예언, 스킬 젬, 고유 주얼, 고유 플라스크, 고유 무기, 고유 방어구, 고유 장신구 내에서 검색", inline = False)
            embed.add_field(name = '!상세가격 ... , !detail_price ...', value = "모든 카테고리 내에서 검색", inline = False)
            embed.add_field(name = '!set_price_result_channel', value = "가격 결과를 출력할 채널 설정", inline = False)
            embed.add_field(name = '!wiki ...', value = "영어 위키에서 검색", inline = False)
            embed.add_field(name = '!위키 ...', value = "한글 위키에서 검색", inline = False)
            embed.add_field(name = '!currency', value = "화폐 시세", inline = False)
            embed.add_field(name = '!디데이 추가 ... YYYY-MM-DD (HH-MM-SS)', value = "디데이 추가", inline = False)
            embed.add_field(name = '!디데이 삭제 ...', value = "디데이 삭제", inline = False)
            embed.add_field(name = '!디데이 ... or !...', value = "디데이 확인", inline = False)
            await message.channel.send(embed = embed)

        if message.content.startswith('!price') or message.content.startswith('!가격') or message.content.startswith('!detail_price') or message.content.startswith('!상세가격'):

            result_channel = price_result_channel[message.guild.id]['channel'] if message.guild.id in price_result_channel else message.channel

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

            process_message = await message.channel.send(query + " 가격 검색중...")

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
            
            await process_message.delete()
            await result_channel.send(embed = embed)
            if message.channel != result_channel:
                await message.channel.send('{} 채널에 {} 가격 검색 결과를 출력했습니다.'.format(result_channel.name, query))
        
        if message.content.startswith('!set_price_result_channel'):
            price_result_channel[message.guild.id] = {
                'channel': message.channel,
                'name': message.channel.name
            }
            await message.channel.send("이제부터 여기에 가격 검색 결과를 출력합니다.")
        
        if message.content.startswith('!wiki'):
            query = message.content[6:]

            process_message = await message.channel.send(query + " wiki searching...")
            
            result = find_wiki(driver, query)

            embed_title = query + ' wiki search result'

            if len(result) == 5:
                embed_title += ' (top 5)'

            embed = discord.Embed(title = embed_title)

            if len(result) == 0:
                embed.add_field(name = 'There is', value = "no result", inline = False)
            else:
                for r in result:
                    embed.add_field(name = r['title'], value = r['link'], inline = False)
            
            await process_message.delete()
            await message.channel.send(embed = embed)

        if message.content.startswith('!위키'):
            query = message.content[4:]
            
            process_message = await message.channel.send(query + " 위키 검색중...")
            
            result = find_wiki_korean(driver, query)

            embed_title = query + ' 위키 검색 결과'

            if len(result) == 5:
                embed_title += ' (top 5)'

            embed = discord.Embed(title = embed_title)

            if len(result) == 0:
                embed.add_field(name = '검색 결과가', value = "없습니다", inline = False)
            else:
                for r in result:
                    embed.add_field(name = r['title'], value = r['link'], inline = False)
            
            await process_message.delete()
            await message.channel.send(embed = embed)
        
        if message.content.startswith('!currency'):
            process_message = await message.channel.send("화폐 시세 검색중...")

            result = find_currency(driver)

            embed = discord.Embed(title = "현재 화폐 시세")
            embed.add_field(name = '화폐', value = blank, inline = True)
            embed.add_field(name = '살 때', value = blank, inline = True)
            embed.add_field(name = '팔 때', value = blank, inline = True)

            for r in result[:5]:
                embed.add_field(name = blank, value = r['name'], inline = True)
                embed.add_field(name = blank, value = r['buy'], inline = True)
                embed.add_field(name = blank, value = r['sell'], inline = True)
            
            await process_message.delete()
            await message.channel.send(embed = embed)

            embed = discord.Embed()

            for r in result[5:]:
                embed.add_field(name = blank, value = r['name'], inline = True)
                embed.add_field(name = blank, value = r['buy'], inline = True)
                embed.add_field(name = blank, value = r['sell'], inline = True)
            
            await message.channel.send(embed = embed)
                
    client.run(token)
