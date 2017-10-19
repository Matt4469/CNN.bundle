NAME = 'CNN'
PREFIX = '/video/cnn'
ICON = 'icon-default.jpg'

BASE_URL = "http://www.cnn.com"
DIGITAL_SHORTS = "http://www.cnn.com/specials/videos/digital-shorts"
# This gets the related video sections http://www.cnn.com/specials/videos/digital-shorts
RELATED_JSON = 'http://www.cnn.com/video/data/3.0/video/%s/relateds.json'
RELATED_SECTION = ['Business', 'Entertainment', 'Health', 'Justice', 'Living', 'CNNMoney', 'Politics', 'Style', 'Technology', 'Travel', 'TV', 'US', 'World', 'Weather']
# Search for just videos with options for pages(page), npp(number per page), searchquery(text)
SEARCH_URL  = 'http://searchapp.cnn.com/search/query.jsp?page=%s&npp=30&start=%s&text=%s&type=all&sort=relevance&collection=VIDEOS'
RE_SEARCH_JSON  = Regex('"results":\[(.+?)\],"didYouMean"')

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

####################################################################################################
@handler(PREFIX, NAME, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(VideosMenu, title = 'Digital Shorts', url='http://www.cnn.com/specials/videos/digital-shorts'), title = 'Digital Shorts'))
    oc.add(DirectoryObject(key = Callback(PlaylistPull, title = 'Video Playlists'), title = 'Video Playlists'))
    oc.add(InputDirectoryObject(key=Callback(VideoSearch), title='Search for CNN Videos', summary="Click here to search for videos", prompt="Search for videos by entering key words"))

    return oc

####################################################################################################
# This function pulls the videos listed in a section of the main video page
@route(PREFIX + '/videosmenu')
def VideosMenu(title, url):

    oc = ObjectContainer(title2 = title)

    html = HTML.ElementFromURL(url)

    for video in html.xpath('//section//article'):
        vid_url = video.xpath('.//h3/a/@href')[0].split('/video/playlists')[0]
        if not vid_url.startswith('http'):
            vid_url = BASE_URL + vid_url
        # these are videos that go to the cnn.go website and do not work
        if vid_url.startswith('http://cnn.it'):
            continue
        if not '/video' in vid_url:
            continue
        title = video.xpath('.//h3/a/span[@class="cd__headline-text"]//text()')[0].strip()
        try: thumb = video.xpath('.//img/@data-src-large')[0]
        except: thumb = ''
        try: duration = Datetime.MillisecondsFromString(video.xpath('.//i/@data-post-text')[0])
        except: duration = 0

        oc.add(VideoClipObject(
            url = vid_url,
            title = title,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb),
            duration = duration))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc
####################################################################################################
# This function creates the list of known sections for the related json playlists
@route(PREFIX + '/playlistpull')
def PlaylistPull(title):  

    oc = ObjectContainer(title2 = title)

    for item in RELATED_SECTION:
        playlist_url = RELATED_JSON %item.lower()
        oc.add(DirectoryObject(
            key = Callback(PlaylistJSON, title = item, url = playlist_url), 
            title = item))

    return oc

####################################################################################################
# This function uses the related json url to pull a playlist of top videos
@route(PREFIX + '/playlistjson')
def PlaylistJSON(title, url):  

    oc = ObjectContainer(title2 = title)

    json = JSON.ObjectFromURL(url)

    for item in json['videos']:
        url = BASE_URL + item['clickback_url']
        duration = Datetime.MillisecondsFromString(item['duration'])

        oc.add(VideoClipObject(
            url = url,
            title = item['headline'],
            summary = item['description'],
            thumb = Resource.ContentsOfURLWithFallback(url=item['fullsize_url']),
            duration = duration))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc

####################################################################################################
@route(PREFIX + '/videosearch', page=int, start=int)
def VideoSearch(query, page=1, start=1):

    oc = ObjectContainer()

    query_url = SEARCH_URL %(str(page), str(start), String.Quote(query, usePlus = True))
    content = HTTP.Request(query_url).content
    json_data = RE_SEARCH_JSON.search(content).group(1)
    json = JSON.ObjectFromString(json_data)

    for item in json:
        url = item['url']
        if not url.startswith('http'):
            url = BASE_URL + url
        date = item['mediaDateUts'].split(', ')[1]
        try: date = Datetime.ParseDate(date).date()
        except: date = Datetime.Now()
        try: duration = int(item['duration']) * 1000
        except: duration = 0

        oc.add(VideoClipObject(
            url = url,
            title = item['title'],
            originally_available_at = date,
            summary = item['description'],
            duration = duration,
            thumb = Resource.ContentsOfURLWithFallback(url=item['thumbnail'])))

    if len(oc) == 30:
        oc.add(NextPageObject(key = Callback(VideoSearch, query=query, page=page+1, start=start+30), title = L("Next Page ...")))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc

