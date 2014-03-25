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
from bs4 import BeautifulSoup

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
    print('Finding json data URL from DR TV...')
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
        print('')
    else:
        urllib.urlretrieve(streamUrl, output, reporthook=_reportHook)
        print('')

    print('Download finished! Quitting')

def downloadDRBonanza(url, output=None):
    print('Finding video files from DR Bonanza...')

    # fetch html content
    site_content = getUrlContent(url)

    # initialize beautifulsoup
    html_soup = BeautifulSoup(site_content)

    # parse the html into json
    programs = []
    for link in html_soup.find_all(class_='listItem Video'):
        program = {}
        # parse onclick event from links
        onclick_string = link['onclick']

        # fetch json
        i = onclick_string.find('{')
        json_string = onclick_string[i:-2]
        json_obj = json.loads(json_string)

        # fetch program information
        program['id'] = link['id']
        program['title'] = json_obj['Title']
        program['description'] = json_obj['Description']

        # find highest quality
        for file_obj in json_obj['Files']:
            if 'VideoHigh' in file_obj['Type']:
                # highest video stream found, generate download link
                video_link = 'http://vodfiles.dr.dk/' + file_obj['Location'].split(':')[-1]
                program['video'] = video_link

        programs.append(program)

    # get user input
    print('There are ' + str(len(programs)) + ' programs available for download:')
    i = 1 # start from 1 as 0 == ALL
    for program in programs:
        print(str(i) + ') ' + program['title'])
        i += 1

    # python2 input support
    try:
        get_input = raw_input
    except NameError:
        get_input = input

    # get user input for download
    input_waiting = True
    while input_waiting:
        print('')
        cmd = get_input('Enter a selection (default=all): ')
        if cmd == '':
            # default=all
            input_waiting = False
        elif 0 < int(cmd) < len(programs)+1:
            input_waiting = False
        else:
            print('error: invalid value: ' + str(cmd) + ' is not between 1 and ' + str(len(programs)))

    # parse user input
    if cmd == '':
        print('You chose to download all listed programs!')

        # loop through programs and download each one 
        for program in programs:
            print('Starting download of: "' + program['title'] + '"...')
            urllib.urlretrieve(program['video'], program['title'] + '.mp4', reporthook=_reportHook)
            print('')

    else:
        desired_program = programs[int(cmd)-1]
        print('You selected: "' + desired_program['title'] + '"')
        
        # download the program
        if output is None:
            urllib.urlretrieve(desired_program['video'], desired_program['title'] + '.mp4', reporthook=_reportHook)
            print('')
        else:
            urllib.urlretrieve(desired_program['video'], output, reporthook=_reportHook)
            print('')

    # assume that download has finished
    print('Download finished! Quitting')

if __name__ == '__main__':
    # init parser
    parser = argparse.ArgumentParser(prog='drtv-dl', description='Small command-line program to download videos from DR TV (www.dr.dk/tv/) and DR Bonanza (www.dr.dk/bonanza/)')
    parser.add_argument('URL', nargs='+', help='The URL of the DR TV or DR Bonanza stream')
    parser.add_argument('-o', help='Output file')

    args = vars(parser.parse_args())

    # handle arguments
    url = args['URL'][0]
    outputFile = args['o']

    # start application
    if 'bonanza' in url.lower():
        downloadDRBonanza(url, outputFile)
    elif 'tv' in url.lower():
        downloadDRTV(url, outputFile)
    else:
        print('Error occured. URL is not valid!')

