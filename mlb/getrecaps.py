from urllib.request import urlopen, Request
import json
from datetime import datetime, timedelta
from xml.etree import ElementTree
import sys, time

def search_video(query):
    query = query.replace(' ', "%2B")
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=" + query + "&page=1&sort=new&type=video"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))['docs']
    return s

def get_vid_info(id):
    url = "https://www.mlb.com/data-service/en/videos/" + id
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    return json.loads(urlopen(req).read().decode("utf-8"))


def search_mlbn():
    yest = datetime.now() - timedelta(days=1)
    yest_md = str(yest.month) + "/" + str(yest.day)
    yest_monthday = yest.strftime("%B") + " " + str(yest.day)
    date = str(yest.month) + "-" + str(yest.day)
    url = "https://www.mlb.com/data-service/en/search?tags.slug=mlb-network&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))['docs']
    output = ""
    for v in s:
        if yest_md in v['blurb'] or yest_monthday in v['blurb'] or date in v['id']:
            t = get_vid_info(v['id'])
            output = output + "[%s](%s) - %s\n\n" % (t['blurb'], t['url'], t['duration'][3:])
    return output

def get_recaps(return_str=False):
    now = datetime.now() - timedelta(days=1)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date + "&hydrate=team"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    recaps = []
    statcasts = []
    mustcs = []
    output = ""
    statout = ""
    mustcout = ""
    for game in games:
        content = "https://statsapi.mlb.com" + game['content']['link']
        req = Request(content, headers={'User-Agent' : "ubuntu"})
        c = json.loads(urlopen(req).read().decode("utf-8"))
        if game['status']['detailedState'] == "Final":
            deftitle = "%s %d, %s %d, no recap" % (game['teams']['away']['team']['abbreviation'],
                                                game['teams']['away']['score'],
                                                game['teams']['home']['team']['abbreviation'],
                                                game['teams']['home']['score'])
        else:
            output = output +  "%s, %s - %s\n\n" % (game['teams']['away']['team']['abbreviation'],
                                        game['teams']['home']['team']['abbreviation'],
                                        game['status']['detailedState'])
            continue

        highlights = ['Recap', 'Must C:', 'Statcast', 'CG:']
        recapstr = ""
        cgstr = ""
        for item in c['highlights']['highlights']['items']:
            if any(x in item['title'] for x in highlights):
                title = item['title']
                link = None
                for pb in item['playbacks']:
                    if pb['name'] == "mp4Avc":
                        link = pb['url']
                if link is None:
                    continue
                duration = item['duration'][3:]
                if 'Recap' in title:
                    # list = recaps
                    recapstr = "[%s](%s) - %s\n" % (title, link, duration)
                elif 'CG:' in title:
                    cgstr = "[Condensed game](%s) - %s\n" % (link, duration)
                elif 'Must C:' in title:
                    # list = mustcs
                    s = "[%s](%s) - %s\n" % (item['blurb'], link, duration)
                    mustcout = mustcout + s + "\n"
                elif 'Statcast' in title:
                    # list = statcasts
                    s = "[%s](%s) - %s\n" % (title, link, duration)
                    statout = statout + s + "\n"
                # print(s)
                # list.append((title, link, duration))

        if recapstr == "":
            recapstr = deftitle
        if cgstr != "":
            output = output + recapstr + " | " + cgstr + "\n\n"
        else:
            output = output + recapstr + " | No condensed game\n\n"
    if len(mustcout) > 0:
        output = mustcout + "****\n" + output
    if len(statout) > 0:
        output = statout + "****\n" + output
    if return_str:
        return output
    return recaps

def get_sound_smarts():
    now = datetime.now() - timedelta(days=1)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date + "&hydrate=team"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    recaps = []
    output = ""
    line = "<p><b>SOUND SMART</b><br />"
    readarticles = []
    urls = []
    for game in games:
        url = "https://securea.mlb.com/gen/hb/content/mlb/" + str(game['gamePk']) + ".json"
        print(url)
        try:
            req = Request(url, headers={'User-Agent' : "ubuntu"})
            articles = json.loads(urlopen(req).read().decode("utf-8"))['list']
        except:
            continue
        items = []
        for article in articles:
            link = 'https://www.mlb.com/news/'+ article['seo-headline'] + '/c-' + str(article['contentId'])
            if link not in urls:
                urls.append(link)
            if 'body' not in article:
                continue
            if line in article['body']:
                if article['contentId'] in readarticles:
                    continue
                readarticles.append(article['contentId'])
                body = article['body']
                lineidx = body.find(line) + len(line)
                body = body[lineidx:]
                if '<p><b>' in body:
                    body = body[:body.find('<p><b>')-6].strip()
                if '<p><p.><b>' in body:
                    body = body[:body.find('<p><p.><b>')-9].strip()
                if '<p><span class="token token-video"' in body:
                    body = body[:body.find('<p><span class="token token-video"')].strip()
                body = body.replace('</span>', '')
                body = body.replace('\n', ' ')
                body = body.replace('<p>', '')
                body = body.replace('</p>', '')
                body = body.replace('</a>', '')
                while "<a" in body:
                    # print(body)
                    idx = body.find("<a")
                    endidx = body[idx:].find(">") + 1 + idx
                    start = body[:idx]
                    end = body[endidx:]
                    body = start + end
                while "<span" in body:
                    print(body)
                    idx = body.find("<span")
                    endidx = body.find(">") + 1
                    start = body[:idx]
                    end = body[endidx:]
                    body = start + end
                if body not in items:
                    items.append(body)
        awayteam = game['teams']['away']['team']['teamName']
        hometeam = game['teams']['home']['team']['teamName']
        awayscore,homescore = "",""
        if 'score' in game['teams']['away']:
            awayscore = game['teams']['away']['score']
        if 'score' in game['teams']['home']:
            homescore = game['teams']['home']['score']
        outstr = "**%s %s, %s %s:**\n\n" % (awayteam, str(awayscore), hometeam, str(homescore))
        output = output + outstr
        # print(outstr)
        if len(items) > 0:
            for item in items:
                outstr = "* " + item + "\n\n"
                output = output + outstr
                # print(outstr)
        else:
            outstr = "* No quirky (significant but *under-the-radar*) events took place. :(\n\n"
            # print(outstr)
            output = output + outstr
    listofarts = "List of articles:\n\n"
    for link in urls:
        # print("[%s](%s)  \n" % (link[0],link[1]))
        listofarts = listofarts + "%s  \n" % link
    return (output, listofarts)

def get_direct_video_url(indirecturl):
    url = indirecturl
    one=url[-3]
    two=url[-2]
    thr=url[-1]
    cid = url[url.rfind('c-')+2:]
    mlburl = "http://www.mlb.com/gen/multimedia/detail/%s/%s/%s/%s.xml"%(one,two,thr,cid)
    try:
        req = Request(mlburl, headers={'User-Agent' : "ubuntu"})
        tree = ElementTree.fromstring(urlopen(req).read().decode("utf-8"))
        media = tree.findall('url')
        for tag in media:
            if "2500K.mp4" in tag.text:
                url = tag.text
                return url
                break
    except Exception as e:
        print("error parsing/receiving XML from url " + mlburl)
        return

def find_fastcast(return_str=False):
    url = "https://www.mlb.com/data-service/en/search?tags.slug=fastcast&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    now = datetime.now()
    date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    for item in s['docs']:
        if date in item['date'] and "fastcast" in item['title'].lower():
            url = "https://www.mlb.com/data-service/en/videos/" + item['id']
            print(url)
            req = Request(url, headers={'User-Agent' : "ubuntu"})
            t = json.loads(urlopen(req).read().decode("utf-8"))
            for p in t['playbacks']:
                if p['name'] == "mp4Avc":
                    blurb = t['blurb']
                    url = p['url']
                    duration = t['duration'][3:]
                    s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
                    if return_str:
                        return s
                    return (blurb,url,duration)
    if return_str:
        return ""

def find_realfast():
    url = "https://www.mlb.com/data-service/en/search?tags.slug=real-fast&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    now = datetime.now()
    date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    for item in s['docs']:
        if date in item['date'] and "real fast" in item['blurb'].lower():
            url = "https://www.mlb.com/data-service/en/videos/" + item['id']
            print(url)
            req = Request(url, headers={'User-Agent' : "ubuntu"})
            t = json.loads(urlopen(req).read().decode("utf-8"))
            for p in t['playbacks']:
                if p['name'] == "mp4Avc":
                    blurb = t['blurb']
                    url = p['url']
                    duration = t['duration'][3:]
                    s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
                    return s
    return ""


    # url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=fastcast&page=1"
    # print(url)
    # req = Request(url, headers={'User-Agent' : "ubuntu"})
    # s = json.loads(urlopen(req).read().decode("utf-8"))
    # result = s['docs'][0]
    # title = result['title']
    # now = datetime.now()
    # date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    # print(date)
    # if "MLB.com FastCast".lower() in title.lower() and date in result['display_timestamp']:
    #     blurb = result['blurb']
    #     url = result['url']
    #     dir = get_direct_video_url(url)
    #     if dir is not None:
    #         url = dir
    #     duration = result['duration'][3:]
    #     s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
    #     print(s)
    #     if return_str:
    #         return s
    #     return (blurb,url,duration)
    # if return_str:
    #     return ""

def find_top_plays(return_str=False):
    url = "https://www.mlb.com/data-service/en/videos/top-5-plays-of-the-day"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    now = datetime.now()# - timedelta(days=1)
    yesterday = now - timedelta(days=1)
    yest = "%d/%d/%s:" % (yesterday.month, yesterday.day, str(yesterday.year)[2:])
    date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    if yest in s['blurb']:
        duration = s['duration'][3:]
        s = "[%s](%s) - %s\n\n" % (s['blurb'],s['url'],duration)
        if return_str:
            return s
        return (s['blurb'],s['url'],duration)
    return ""

    # url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=top%2Bplays&page=1"
    # print(url)
    # req = Request(url, headers={'User-Agent' : "ubuntu"})
    # s = json.loads(urlopen(req).read().decode("utf-8"))
    # results = s['docs']
    # now = datetime.now()# - timedelta(days=1)
    # yesterday = now - timedelta(days=1)
    # yest = "%d/%d/%s:" % (yesterday.month, yesterday.day, str(yesterday.year)[2:])
    # date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    # vids = []
    # output = ""
    # for res in results:
    #     if (date in res['display_timestamp'] or (res['blurb'] is not None and yest in res['blurb'])) and 'daily dash' not in res['blurb'].lower():
    #         blurb = res['blurb']
    #         if "top" in blurb.lower() and ("plays" in blurb.lower() or "home runs" in blurb.lower()):
    #             url = res['url']
    #             dir = get_direct_video_url(url)
    #             if dir is not None:
    #                 url = dir
    #             duration = res['duration'][3:]
    #             s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
    #             print(s)
    #             if return_str:
    #                 output = output + s
    #             vids.append((blurb,url,duration))
    # if return_str:
    #     return output
    # return vids

def find_daily_dash(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=daily%2Bdash&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    results = s['docs']
    now = datetime.now()# - timedelta(days=1)
    yesterday = now - timedelta(days=1)
    yest = "%d/%d/%s:" % (yesterday.month, yesterday.day, str(yesterday.year)[2:])
    date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    vids = []
    output = ""
    for res in results:
        if date in res['display_timestamp'] or (res['blurb'] is not None and yest in res['blurb']):
            blurb = res['blurb']
            if "daily dash" in blurb.lower():
                url = res['url']
                dir = get_direct_video_url(url)
                if dir is not None:
                    url = dir
                duration = res['duration'][3:]
                s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
                print(s)
                if return_str:
                    output = output + s
                vids.append((blurb,url,duration))
    if return_str:
        return output
    return vids

def find_quick_pitch(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=quick%2Bpitch&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    result = s['docs'][0]
    blurb = result['blurb']
    now = datetime.now() - timedelta(days=1)
    date = "%d/%d/%s" % (now.month, now.day, str(now.year)[2:])
    if "quick pitch recap" in blurb.lower() and date in blurb:
        url = result['url']
        dir = get_direct_video_url(url)
        if dir is not None:
            url = dir
        duration = result['duration'][3:]
        s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
        print(s)
        if return_str:
            return s
        return (blurb,url,duration)
    if return_str:
        return ""
    return None

def find_youtube_homeruns(return_str=False):
    url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=mlb+all+home+runs&order=date&channelId=UCoLrcjPV5PbUrUyXq5mjc_A"
    with open("../keys.json",'r') as f:
        f = json.loads(f.read())
    key = None
    for k in f['keys']:
        if k['name'] == "youtube":
            key = k['key']
    if key is not None:
        d = datetime.now() - timedelta(days=1)
        url = url + "&key=" + key
        print(url)
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        s = json.loads(urlopen(req).read().decode("utf-8"))
        import calendar
        month = calendar.month_name[d.month]
        for res in s['items']:
            datestr = "%s %d, %d" % (month, d.day, d.year)
            otherdatestr = "%d/%d/%s" % (d.month, d.day, str(d.year)[2:])
            if datestr in res['snippet']['title'] or otherdatestr in res['snippet']['title']:
                id = res['id']['videoId']
                title = res['snippet']['title']
                if 'FastCast' in title:
                    continue
                url = "https://www.googleapis.com/youtube/v3/videos?id=" + id + "&part=contentDetails&key=" + key
                print(url)
                req = Request(url, headers={'User-Agent' : "ubuntu"})
                s = json.loads(urlopen(req).read().decode("utf-8"))
                duration = s['items'][0]['contentDetails']['duration']
                duration = duration[2:]
                m = duration.find('M')
                min = int(duration[:m])
                if 'S' not in duration:
                    sec = 0
                else:
                    sec = int(duration[m+1:duration.find('S')])
                duration = "%d:%02d" % (min, sec)
                url = "https://www.youtube.com/watch?v=" + id
                s = "[%s](%s) - %s\n\n" % (title,url,duration)
                print(s)
                if return_str:
                    return s
                return (title,url,duration)
        if return_str:
            return ""

def find_must_cs(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=must%2Bc&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    results = s['docs']
    yesterday = datetime.now() - timedelta(days=1)
    vids = []
    output = ""
    for res in results:
        if res['blurb'].startswith("Must C"):
            date = None
            for tag in res['tags']:
                if tag['type'] == 'event_date':
                    date = tag['value']
            if date is None:
                continue
            if date[:10] == "%d-%02d-%02d" % (yesterday.year, yesterday.month, yesterday.day):
                blurb = res['blurb']
                url = get_direct_video_url(res['url'])
                duration = res['duration'][3:]
                s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
                print(s)
                if return_str:
                    output = output + s
                vids.append((blurb,url,duration))
    if return_str:
        return output
    return vids

def find_statcasts(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=statcast&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    results = s['docs']
    yesterday = datetime.now() - timedelta(days=1)
    vids = []
    output = ""
    for res in results:
        date = ""
        for tag in res['tags']:
            if tag['type'] == 'event_date':
                date = tag['value']
        if date[:10] == "%d-%02d-%02d" % (yesterday.year, yesterday.month, yesterday.day):
            blurb = res['blurb']
            url = get_direct_video_url(res['url'])
            duration = res['duration'][3:]
            s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
            print(s)
            if return_str:
                output = output + s
            vids.append((blurb,url,duration))
    if return_str:
        return output
    return vids

def post_on_reddit(cron=False):
    import praw
    with open('.fitz.json', 'r') as f:
        f = json.loads(f.read())['keys']['efitz11']
    reddit = praw.Reddit(client_id=f['client_id'],
                         client_secret=f['token'],
                         user_agent='recap bot on ubuntu (/u/efitz11)',
                         username=f['user'],password=f['password'])
    user = reddit.redditor('baseballbot')
    posted = False
    while not posted:
        for submission in user.submissions.new(limit=5):
            if 'Around the Horn' in submission.title:
                #idx = submission.title.find('-')
                #date = submission.title[idx+2:]
                now = datetime.now()
                today = "%d/%d/%s" % (now.month,now.day,str(now.year)[2:])
                todayalt = "%d/%d/%s" % (now.month,now.day,str(now.year))
                # print(comment)
                #if date == today:
                if today in submission.title or todayalt in submission.title:
                    print("Adding comment to thread: %s - %s" % (submission.title, submission.url))
                    comment = get_all_outputs()
                    submission.reply(comment)
                    posted = True
                break
        if not cron:
            posted = True
        elif not posted:
            print("didn't find ATH, checking in 5 minutes...")
            time.sleep(5*60)

def post_self_submission(selftext, cron=False):
    import praw
    with open('.fitz.json', 'r') as f:
        f = json.loads(f.read())['keys']['efitz11']
    reddit = praw.Reddit(client_id=f['client_id'],
                         client_secret=f['token'],
                         user_agent='recap bot on ubuntu (/u/efitz11)',
                         username=f['user'],password=f['password'])
    yest = datetime.now() - timedelta(days=1)
    title = "%d/%d Highlight Roundup: FastCast, top plays, recaps/condensed games and longest dongs of the day" % (yest.month, yest.day)
    post = reddit.subreddit('baseball').submit(title, selftext=selftext)

    # check every 30 minutes for new videos
    if cron:
        numchecks = 0
        while numchecks <= 8:
            time.sleep(30*60)
            newout = get_all_outputs()
            if newout != selftext:
                post.edit(newout)
                selftext = newout
            numchecks += 1

def pm_user(subject, body, user="efitz11"):
    import praw
    with open('.fitz.json', 'r') as f:
        f = json.loads(f.read())['keys']['efitz11']
    reddit = praw.Reddit(client_id=f['client_id'],
                         client_secret=f['token'],
                         user_agent='recap bot on ubuntu (/u/efitz11)',
                         username=f['user'],password=f['password'])
    reddit.redditor(user).message(subject, body)

def get_all_outputs():
    output = find_fastcast(return_str=True)
    # output = output + find_quick_pitch(return_str=True)
    # output = output + find_youtube_homeruns(return_str=True)
    # output = output + find_top_plays(return_str=True)
    # output = output + find_daily_dash(return_str=True)
    # output = output + "****\n"
    # output = output + find_must_cs(return_str=True)
    # output = output + "****\n"
    # output = output + find_statcasts(return_str=True)
    output = output + find_realfast()
    output = output + search_mlbn()
    output = output + "****\n"
    output = output + get_recaps(return_str=True)
    output = output + "****\n"
    import sys, os
    sys.path.insert(1, os.path.join(sys.path[0],'..'))
    import mymlbstats
    output = output + "Longest dongs of the day:\n\n" + mymlbstats.print_long_dongs(-1, reddit=True)
    return output

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "post":
        if len(sys.argv) > 2 and sys.argv[2] == "cron":
            post_self_submission(get_all_outputs(), cron=True)
        else:
            post_self_submission(get_all_outputs())

        # if len(sys.argv) > 2 and sys.argv[2] == "cron":
        #     post_on_reddit(cron=True)
        # else:
        #     post_on_reddit()
    elif len(sys.argv) == 2 and sys.argv[1] == "smart":
        out = get_sound_smarts()
        #print(out[1])
        pm_user('sound smart!', out[0], user='HeSawTheLight')
        pm_user('list of articles:', out[1], user='HeSawTheLight')
    else:
        print(get_all_outputs())
        # get_sound_smarts()
