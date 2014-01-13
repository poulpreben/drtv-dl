#!/usr/bin/env python

try:
    import urllib.request as urllib
except ImportError:
    # python2 compatibility
    # probably not the best way to ensure compatibility, but it works - for now
    import urllib

import sys
import json
import argparse

def parseString(data, findStart, findEnd):
    ''' returns string between findStart and findEnd '''

    # decode
    data = data.decode('utf-8')

    start = data.find(findStart) + len(findStart)
    end = data.find(findEnd, start)

    return data[start:end]

def getUrlContent(url):
    page = urllib.urlopen(url)
    content = page.read()

    return content

def gatherInformation(jsonData):
    data = {}

    data['title'] = jsonData["Data"][0]['Title']

    return data

def downloadDRTV(url, output=None):
    print('Finding json data URL...')
    # find json data
    siteContent = getUrlContent(url)
    jsonUrl = parseString(siteContent, 'resource: "', '"')
    print('- Resource file find: ' + jsonUrl)

    print('Finding the video file...')
    # get json data
    jsonContent = getUrlContent(jsonUrl)
    jsonData = json.loads(jsonContent.decode('utf-8'))

    # find the highest bitrate
    bitrates = []
    try:
        for i in range(len(jsonData["Data"][0]['Assets'][0]["Links"])):
            if "Bitrate" in jsonData["Data"][0]['Assets'][0]['Links'][i]:
                bitrates.append(jsonData["Data"][0]['Assets'][0]["Links"][i]['Bitrate'])
    except KeyError:
        # json data is different (hot fix, should be replaced in the future)
        for i in range(len(jsonData["Data"][0]['Assets'][1]["Links"])):
            if 'Bitrate' in jsonData['Data'][0]['Assets'][1]['Links'][i]:
                bitrates.append(jsonData["Data"][0]['Assets'][1]["Links"][i]['Bitrate'])

    print('Highest bitrate found was: ' + str(max(bitrates)))

    # find the stream url
    streamUrl = None
    try:
        for i in range(len(jsonData["Data"][0]['Assets'][0]["Links"])):
            if jsonData["Data"][0]['Assets'][0]["Links"][i]['Target'] == 'Streaming' and jsonData["Data"][0]['Assets'][0]["Links"][i]['Bitrate'] == max(bitrates):

                streamUrl = jsonData["Data"][0]['Assets'][0]["Links"][i]['Uri']
                break
    except KeyError:
        # json data is different (hot fix, should be replaced in the future)
        for i in range(len(jsonData["Data"][0]['Assets'][1]["Links"])):
            if jsonData["Data"][0]['Assets'][1]["Links"][i]['Target'] == 'Streaming' and jsonData["Data"][0]['Assets'][1]["Links"][i]['Bitrate'] == max(bitrates):

                streamUrl = jsonData["Data"][0]['Assets'][1]["Links"][i]['Uri']
                break

    if streamUrl is not None:
        print('- Video file found: ' + str(streamUrl))
        print('Downloading...')
    else:
        print('An error occured while fetching the download URL. Exiting')
        sys.exit()

    # replace some text in the url
    streamUrl = streamUrl.replace('rtmp://vod.dr.dk/cms/mp4:', 'http://vodfiles.dr.dk/')

    # gather some more details about the show
    filmData = gatherInformation(jsonData)

    # download the film
    if output is None:
        urllib.urlretrieve(streamUrl, filmData['title'] + '.mp4')
    else:
        urllib.urlretrieve(streamUrl, output)

if __name__ == '__main__':
    # init parser
    parser = argparse.ArgumentParser(prog='drtv-dl', description='Small command-line program to download videos from DR TV (www.dr.dk/tv/)')
    parser.add_argument('URL', nargs='+', help='The URL of the DR TV stream')
    parser.add_argument('-o', help='Output file')

    args = vars(parser.parse_args())

    # handle arguments
    url = args['URL'][0]
    outputFile = args['o']

    # start application
    downloadDRTV(url, outputFile)
