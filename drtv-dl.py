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

def _reportHook(count, block_size, total_size):
    ''' progress bar for urlretrieve '''
    percent = int(count*block_size*100/total_size)
    # progress_size = int(count*block_size) # currently not in use. use it for downloaded mb later
    # sys.stdout.write("\rDownloading...%d%%, %d MB" % (percent, progress_size/(1024*1024)))
    sys.stdout.write("\rDownloading...%d%%" % percent)
    sys.stdout.flush()

def downloadDRTV(url, output=None):
    print('Finding json data URL...')
    # find json data
    siteContent = getUrlContent(url)
    jsonUrl = parseString(siteContent, 'resource: "', '"')
    print('- Resource file found: ' + jsonUrl)

    print('Finding video file...')
    # get json data
    jsonContent = getUrlContent(jsonUrl)
    jsonData = json.loads(jsonContent.decode('utf-8'))

    # find the highest bitrate
    bitrates = []
    stream_urls = {}
    try:
        # loop through json to find correct list
        for data in jsonData['Data'][0]['Assets']:
            if 'Links' in data:
                # we found it, now lets find the different bitrates and pair them with the stream urls
                for i in range(len(data['Links'])):
                    if 'Bitrate' in data['Links'][i]:

                        # make sure this is for pc streaming
                        if data['Links'][i]['Target'] == 'Streaming':
                            temp_bitrate = data['Links'][i]['Bitrate']
                            temp_streamurl = data['Links'][i]['Uri']

                            bitrates.append(temp_bitrate)
                            stream_urls[temp_bitrate] = temp_streamurl

                # todo: make sure we found a bitrate
                break
    except:
        # todo: error handling
        print("Error occured while parsing JSON. Quitting")
        sys.exit()

    print('Highest bitrate found: ' + str(max(bitrates)))

    streamUrl = stream_urls[max(bitrates)]
    if streamUrl is not None:
        print('- Video file found: ' + str(streamUrl))
        print('Starting download...')
    else:
        print('An error occured while fetching the download URL. Exiting')
        sys.exit()

    # replace some text in the url
    streamUrl = streamUrl.replace('rtmp://vod.dr.dk/cms/mp4:', 'http://vodfiles.dr.dk/')

    # gather some more details about the show
    filmData = gatherInformation(jsonData)

    # download the film
    if output is None:
        urllib.urlretrieve(streamUrl, filmData['title'] + '.mp4', reporthook=_reportHook)
    else:
        urllib.urlretrieve(streamUrl, output, reporthook=_reportHook)

    print('Download finished! Quitting')

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
