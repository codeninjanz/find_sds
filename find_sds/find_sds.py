# import sys
# print(sys.path)

# #!/usr/bin/python

"""
Author: Khoi Van, 2020 - 2021

This program is designed to find and download safety data sheet (SDS)
using multithreading
"""


import json
import os
import re
import sys
import traceback
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

debug = False
# print out extra info in debug mode in case SDS is not found
if len(sys.argv) == 2 and sys.argv[1] in ['--debug=True', '--debug=true', '--debug', '-d']:
    debug = True


def find_sds(cas_list: List[str], download_path: str = None, pool_size: int = 10) -> None:
    """Find safety data sheet (SDS) for list of CAS numbers

    Parameters
    ----------
    cas_list : List[str]
        List of CAS numbers
    download_path : str, optional
        the path for downloaded file,
        by default None. If so, SDS will be downloaded into folder 'SDS'
            inside folder containing the python file
    pool_size : int, optional
        the number of multithread that are running simultaneously,
        by default 10

    Returns
    -------
    None:
        Summary of result is print to screen
    """
    import timeit

    start = timeit.default_timer()

    # global debug

    # If the list of CAS is empty, exit the program
    if not cas_list:
        print('List of CAS numbers is empty!')
        exit(0)

    # # print out extra info in debug mode in case SDS is not found
    # if len(sys.argv) == 2 and sys.argv[1] in ['--debug=True', '--debug=true', '--debug', '-d']:
    #     debug = True
    # print('debug value: {}'.format(debug))

    # Set download_path to 'SDS' folder inside the parent folder of python file
    if not download_path:
        download_path = Path(__file__).resolve().parent / 'SDS'

    # Get the set of CAS for molecule missing sds:
    to_be_downloaded = set(cas_list)

    # Step 1: downloading sds file
    # Check if download path directory exists. If not, create it
    # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    # https://docs.python.org/3/library/os.html#os.makedirs
    os.makedirs(download_path, exist_ok=True)

    print('Downloading missing SDS files. Please wait!')

    download_result = []
    try:
        # # Using multiprocessing (need to protect on Windows)
        if not debug:
            # On Windows, multiprocessing requires the main module to be protected
            if __name__ == '__main__':
                with Pool(pool_size) as p:
                    download_result = p.map(partial(
                                            download_sds,
                                            download_path=download_path),
                                        to_be_downloaded)
            else:
                # Fall back to sequential processing if not in main
                download_result = []
                for cas_nr in to_be_downloaded:
                    download_result.append(download_sds(cas_nr=cas_nr, download_path=download_path))
        else:
            download_result = []
            for cas_nr in to_be_downloaded:
                download_result.append(download_sds(cas_nr=cas_nr, download_path=download_path))
    except Exception as error:
        # if debug:
        traceback.print_exc()


    # Step 2: print out summary
    finally:
        # Sometimes Pool worker return 'None', remove 'None' as the following
        # print(download_result)
        download_result = [x for x in download_result if x]

        missing_sds = set()
        updated_sds = set()

        for cas_nr, sds_existed, sds_source in download_result:
            if sds_existed:
                updated_sds.add(cas_nr)
            else:
                missing_sds.add(cas_nr)

        if missing_sds:
            print('\nStill missing SDS:\n{}'.format(missing_sds))

        print('\nSummary: ')
        print('\t{} SDS files are missing.'.format(len(missing_sds)))
        print('\t{} SDS files downloaded.'.format(len(updated_sds)))

        # Advice user about turning on debug mode for more error printing
        if not debug:
            print('\n\n(Optional): you can turn on debug mode (more error printing during search) using the following command:')
            print('python find_sds/find_sds.py  --debug\n')

        # All the program statements
        stop = timeit.default_timer()
        execution_time = stop - start

        print(f"Program executed in {str(execution_time)} seconds.") # It returns time in seconds

def download_sds(cas_nr: str, download_path: str) -> Tuple[str, bool, Optional[str]]:
    """Download SDS from variety of sources

    Parameters
    ----------
    cas_nr : str
        The CAS number of the molecule of interest
    download_path : str
        The path to download folder

    Returns
    -------
    Tuple[str, bool, Optional[str]]
        - str: CAS number of the input chemical
        - bool: True if SDS file downloaded or exists
        - Optional[str]: the name of the SDS source or None
    """

    # global debug
    '''This function is used to extract a single sds file
    See here for more info: http://stackabuse.com/download-files-with-python/'''

    # Set initial return value for if SDS is downloaded (or existed)
    downloaded = False

    file_name = cas_nr + '-SDS.pdf'
    download_file = Path(download_path) / file_name
    # Check if the file not exists and download
    # check file exists: https://stackoverflow.com/questions/82831/how-do-i-check-whether-a-file-exists
    if download_file.exists():
        # print('{} already downloaded'.format(file_name))
        # print('.', end='')
        downloaded = True
        return cas_nr, downloaded, None

    else:
        print('\nSearching for {} ...'.format(file_name))
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'}

        try:
            # print('CAS {} ...'.format(file_name))
            sds_source, full_url = (
                extract_download_url_from_chemblink(cas_nr) or \
                extract_download_url_from_vwr(cas_nr) or \
                extract_download_url_from_fisher(cas_nr) or \
                extract_download_url_from_tci(cas_nr) or \
                extract_download_url_from_chemicalsafety(cas_nr) or \
                extract_download_url_from_fluorochem(cas_nr) or \
                (None, None)
            )
            # sds_source, full_url = extract_download_url_from_tci(cas_nr)

            # print('full url is: {}'.format(full_url))
            if full_url:    # extract with chemicalsafety
                r = requests.get(full_url, headers=headers, timeout=20)
                # Check to see if give OK status (200) and not redirect
                if r.status_code == 200 and len(r.history) == 0:
                    # print('\nDownloading {} ...'.format(file_name))
                    open(download_file, 'wb').write(r.content)
                    # print()
                    # return (0, sds_source)
                    downloaded = True
                    return (cas_nr, downloaded, sds_source)

            else:
                # return download_sds_tci(cas_nr, download_path)    # May 5, 2020: TCI has updated to newer website, scraping currently not working
                return (cas_nr, downloaded, None)

        except Exception as error:
            if debug:
                # traceback_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))
                # print(traceback_str)
                traceback.print_exception(error)
            return (cas_nr, downloaded, None)


def extract_download_url_from_chemblink(cas_nr: str) -> Optional[Tuple[str, str]]:
    """Search for url to download SDS for chemical with cas_nr
    from https://www.chemblink.com/

    Parameters
    ----------
    cas_nr : str
        CAS# for chemical of interest

    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple[str, str]:
            the name of the SDS source
            the URL from Fisher for SDS file
        None: if URL cannot be found

    Examples
    --------
    >>> print(extract_download_url_from_chemblink(cas_nr='681128-50-7'))
    ('Matrix', 'https://www.chemblink.com/MSDS/MSDSFiles/681128-50-7_Matrix.pdf')
    """

    # global debug

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'
    }

    # get url from chemicalsafety.com to get url to download sds file
    extract_info_url = f'https://www.chemblink.com/MSDS/{cas_nr}MSDS.htm'

    if debug:
        print('Searching on https://www.chemblink.com')

    try:
        r1 = requests.get(extract_info_url, headers=headers, timeout=20)
        # print(r1)

        # Check to see if give OK status (200) and not redirect
        if r1.status_code == 200 and len(r1.history) == 0:
            soup = BeautifulSoup(r1.text, 'html.parser')
            if soup:
                # Find all <a> tags with content "View / download", example: https://www.chemblink.com/MSDS/64-19-7_MSDS.htm
                # Example of a correct <a> tag for SDS download: '<a href="/MSDS/MSDSFiles/64-19-7_Alfa-Aesar.pdf" class="blue" onclick="blur()" target="_blank">View / download</a>'
                a_tags = soup.find_all('a', string=re.compile(r'View / download'))
                if a_tags:
                    domain = 'https://www.chemblink.com'
                    sds_link = a_tags[0]['href']
                    # # Get source name from sds_link, example of sds_link href: '/MSDS/MSDSFiles/64-19-7_Alfa-Aesar.pdf' (before Jul 21 2024)
                    # source = re.search(r'\S+_(\S*)\.pdf', sds_link).group(1)
                    # Get source name from sds_link, example of sds_link href: '/MSDS/MSDSFiles/64-19-7Alfa-Aesar.pdf'
                    source = re.search(r'([a-zA-Z\-]+)\.pdf', sds_link).group(1)
                    full_url = f'{domain}{sds_link}'
                    return source, full_url

    except Exception as error:
        # print('.', end='')
        if debug:
            # traceback_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))
            # print(traceback_str)
            traceback.print_exception(error)
        # return None


def extract_download_url_from_vwr(cas_nr: str) -> Optional[Tuple[str, str]]:
    """Search for url to download SDS for chemical with cas_nr
    from Avantor Sciences (formerly VWR)

    Parameters
    ----------
    cas_nr : str
        CAS# for chemical of interest

    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple[str, str]:
            the name of the SDS source
            the URL from Avantor for SDS file
        None: if URL cannot be found
    """
    global debug

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    if debug:
        print('Searching on Avantor Sciences (formerly VWR)')

    # Try multiple Avantor search approaches
    search_urls = [
        # Try the certificates/SDS search page
        f'https://www.avantorsciences.com/us/en/certificates/search?q={cas_nr}',
        # Try general product search  
        f'https://www.avantorsciences.com/us/en/search?q={cas_nr}',
        # Try the old VWR redirect
        f'https://us.vwr.com/store/msds?keyword={cas_nr}'
    ]

    try:
        with requests.Session() as session:
            for search_url in search_urls:
                try:
                    response = session.get(search_url, headers=headers, timeout=20, allow_redirects=True)
                    
                    if response.status_code == 200:
                        html = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for various SDS link patterns
                        sds_patterns = [
                            # Direct SDS/MSDS links
                            'a[href*="sds"]',
                            'a[href*="msds"]', 
                            'a[href*="SDS"]',
                            'a[href*="MSDS"]',
                            # Links with SDS text
                            'a:contains("SDS")',
                            'a:contains("MSDS")',
                            'a:contains("Safety Data Sheet")',
                            # PDF links (many SDS are PDFs)
                            'a[href$=".pdf"]'
                        ]
                        
                        for pattern in sds_patterns:
                            sds_links = html.select(pattern)
                            
                            for link in sds_links:
                                href = link.get('href', '')
                                if href and any(term in href.lower() for term in ['sds', 'msds', 'safety']):
                                    # Make URL absolute if needed
                                    if not href.startswith('http'):
                                        from urllib.parse import urljoin
                                        href = urljoin(response.url, href)
                                    
                                    # Try to determine source/manufacturer
                                    source = 'Avantor'
                                    
                                    # Look for manufacturer info near the link
                                    parent = link.parent
                                    if parent:
                                        parent_text = parent.get_text(strip=True)
                                        # Extract potential manufacturer name
                                        for word in parent_text.split():
                                            if len(word) > 3 and word[0].isupper():
                                                source = word
                                                break
                                    
                                    return source, href
                        
                        # If no SDS links found, check if this is a search results page
                        # and look for product links to follow
                        product_links = html.select('a[href*="product"]')
                        if product_links and len(product_links) > 0:
                            # Could potentially follow product links to find SDS
                            # For now, just indicate that search worked but no direct SDS found
                            if debug:
                                print(f"  Found {len(product_links)} product links but no direct SDS")
                                
                except requests.RequestException as e:
                    if debug:
                        print(f"  Error with {search_url}: {e}")
                    continue
                    
    except Exception as error:
        if debug:
            print(f"VWR/Avantor search failed: {error}")

    return None


def extract_download_url_from_fisher(cas_nr: str) -> Optional[Tuple[str, str]]:
    """Search for url to download SDS for chemical with cas_nr
    from https://www.fishersci.com

    Parameters
    ----------
    cas_nr : str
        CAS# for chemical of interest

    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple[str, str]:
            the name of the SDS source
            the URL from Fisher for SDS file
        None: if URL cannot be found
    """

    # global debug

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }

    # get url from Fisher to get url to download sds file
    extract_info_url = 'https://www.fishersci.com/us/en/catalog/search/sds'
    payload = {
        'selectLang': '',
        'store': '',
        'msdsKeyword': cas_nr}

    if debug:
        print('Searching on https://www.fishersci.com/us/en/catalog/search/sdshome.html')

    try:
        r = requests.get(extract_info_url, headers=headers, timeout=10, params=payload)
        # Check to see if give OK status (200) and not redirect
        if r.status_code == 200 and len(r.history) == 0:
            # BeautifulSoup ref: https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3
            # Using BeautifulSoup to scrap text
            html = BeautifulSoup(r.text, 'html.parser')
            # The list of found sds is in class 'catalog_num', with each item in class 'catlog_items'
            # cat_no_list = html.find(class_='catalog_num')    # This is to find all of the sds

            # Check if there is error message. Fisher automatically does a close search with error message
            # breakpoint()
            # error_message = html.find(class_='errormessage search_results_error_message')
            # # Fisher give non-display message for un-real error message
            # if error_message.attrs['style'] == 'display: none;':
            #     error_message = None
            # cat_no_list = exact_compound_row.find(class_='catlog_items')    # This will find the first sds

            # Find the row with the image (first column in the result table) name containing the CAS number:
            exact_compound_row = html.select_one(f'.msds_img:has(img[src*="{cas_nr}"]) + *.catalog_data .catlog_items')

            if exact_compound_row:
                cat_no_items = exact_compound_row.find_all('a')   #
                # download info
                rel_download_url = cat_no_items[0].get('href')
                catalogID = cat_no_items[0].contents[0]
                full_url = 'https://www.fishersci.com' + rel_download_url
                # print(f'rel_download_url is {rel_download_url}')
                return 'Fisher', full_url

    except Exception as error:
        # print('.', end='')
        if debug:
            # traceback_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))
            # print(traceback_str)
            traceback.print_exception(error)
        # return None


def extract_download_url_from_chemicalsafety(cas_nr: str) -> Optional[Tuple[str, str]]:
    """Search for url to download SDS for chemical with cas_nr
    from https://chemicalsafety.com/sds-search/

    Parameters
    ----------
    cas_nr : str
        CAS# for chemical of interest

    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple[str, str]:
            the name of the SDS source
            the URL from Fisher for SDS file
        None: if URL cannot be found
    """

    # global debug

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36',
        'accept-encoding': 'gzip, deflate, br',
        'content-type': 'application/json',
        # 'Referer': 'https://chemicalsafety.com/sds-search/',
    }
    # get url from chemicalsafety.com to get url to download sds file
    # extract_info_url = 'https://chemicalsafety.com/sds1/retriever.php'
    extract_info_url = 'https://chemicalsafety.com/sds1/sds_retriever.php?action=search'
    # form1 = {
    #     "action": "search",
    #     # "bee": "honey",
    #     # "p1": "MSMSDS.COMMON|",
    #     # "p2": "MSMSDS.MANUFACT|",
    #     # "p3": "MSCHEM.CAS|" + cas_nr,
    #     # "hostName": "cs website",
    #     # "isContains": "0",
    #     # 'searchUrl': "",
    #     }
    form1 = {
        "IsContains":"false",
        "IncludeSynonyms":"false",
        "SearchSdsServer":"false",
        "Criteria":[f"cas|{cas_nr}"],
        "HostName":"sfs website",
        # "Remote":"97.64.216.42",
        "Bee":"stevia","Action":"search","SearchUrl":"","ResultColumns":["revision_date"]
    }

    if debug:
        print('Searching on https://chemicalsafety.com/sds-search/')

    try:
        with requests.Session() as s:
            r1 = s.post(extract_info_url, headers=headers,
                           # params={'action': 'search'},
                data=json.dumps(form1), timeout=20)

            '''Example of r1.json():
{'cols': [{'name': 'MSDS_ID', 'prompt': 'MSDS_ID'},
          {'name': 'COMMON', 'prompt': 'Product Name'},
          {'name': 'MANUFACT', 'prompt': 'MANUFACTURER'},
          {'name': 'CAS', 'prompt': 'CAS'},
          {'name': 'CSDISPMSDSID', 'prompt': 'CS DISTRIBUTION ID'},
          {'name': 'HASMSDS', 'prompt': 'HASMSDS'},
          {'name': 'HPHRASES_IDS', 'prompt': 'HPHRASES_IDS'},
          {'name': 'SDSSERVER', 'prompt': 'SDSSERVER'},
          {'name': 'RS', 'prompt': 'MSDS/SDS #'},
          {'name': 'DATE1', 'prompt': 'REVISION DATE'},
          {'name': 'HTTPMSDSREF', 'prompt': 'HTTP REF'}],
 'rows': [['31303512',
           'Ethyl 2-mercaptoacetate',
           'Alfa Aesar',
           '623-51-8',
           '3395929',
           '1',
           '',
           '',
           '31303512',
           '2020-02-14',
           'https://www.alfa.com/en/msds/?language=EN&subformat=AGHS&sku=A14321'],
          ['33075495',
           'Ethyl 2-mercaptoacetate',
           'ThermoFisher',
           '623-51-8',
           '32571684',
           '1',
           '',
           '',
           '33075495',
           '2020-12-10',
           'https://assets.thermofisher.com/directwebviewer/private/results.aspx?page=NewSearch&LANGUAGE=d__EN&SUBFORMAT=d__CGV4&SKU=ACR11867&PLANT=d__ACR'],
          ['30060560',
           'Ethyl thioglycolate',
           'Aldrich',
           '623-51-8',
           '2260561',
           '1',
           '',
           '',
           '30060560',
           '2023-10-27',
           'https://www.sigmaaldrich.com/us/en/sds/ALDRICH/E34307'],
          ['33110417',
           'Ethyl thioglycolate',
           'Ambeed, Inc.',
           '623-51-8',
           '32606604',
           '1',
           '',
           '',
           '33110417',
           '2023-11-26',
           'https://file.ambeed.com/static/upload/prosds/am/306/SDS-A305712.pdf'],
          ['32508606',
           'Ethyl Thioglycolate',
           'Tokyo Chemical Industry Co., Ltd.',
           '623-51-8',
           '32407940',
           '1',
           '',
           '',
           '32508606',
           '2018-07-06',
           'https://www.tcichemicals.com/US/en/sds/T0211_US_EN.pdf']]}
            '''
            cols = [row['name'] for row in r1.json()['cols']]
            cas_col_index = cols.index('CAS')
            manufacture_col_index = cols.index('MANUFACT')
            sds_url_col_index = cols.index('HTTPMSDSREF')
            correct_compounds = [(row[sds_url_col_index], row[manufacture_col_index])
                        for row in r1.json()['rows']
                        if (row[cas_col_index] == cas_nr
                            and re.search(r'^http.+\.pdf$', row[sds_url_col_index]))
                        ]
            if correct_compounds:
                url = correct_compounds[-1][0]
                manufacture = correct_compounds[-1][1]
                return manufacture, url

            # # Check to see if give OK status (200) and not redirect
            # if r1.status_code == 200 and len(r1.history) == 0 and r1.json():
            #     id_list = r1.json()['rows']
            #     msds_id = ''
            #     for item in id_list:
            #         if item[3] == cas_nr:
            #             msds_id = item[0]
            #             break
            #     if msds_id != '':
            #         # sds_viewer_url = 'https://chemicalsafety.com/sds1/sdsviewer.php'
            #         url2 = 'https://chemicalsafety.com/sds1/retriever.php'
            #         form2 = {"Action": "msdsdetail",
            #              "P1": msds_id,
            #              "Bee": "chemsafe",
            #              }
            #         r2 = s.post(url2,
            #                     headers=headers,
            #             data=json.dumps(form2), timeout=20)
            #         breakpoint()
            #         result = r2.json()['rows'][0]
            #         #Confirm the msds_id and cas_nr:
            #         if msds_id == result[0] and cas_nr == result[3]:
            #             sds_pdf_file = result[10].rstrip(',')
            #             form3 = {"action":"getpdfurl","p1":sds_pdf_file,"p2":"","p3":"", "bee": "chemsafe", "isContains":""}
            #             r3 = s.post(extract_info_url, headers=headers, data=json.dumps(form3), timeout=20)
            #             #Get the url
            #             # Translate curl to python https://curl.trillworks.com/
            #             # urllib.parse doc: https://docs.python.org/3.6/library/urllib.parse.html
            #             full_url = r3.json()['url']
            #             # print(f'{full_url=}'); exit()
            #             return 'ChemicalSafety', full_url
    except Exception as error:
        # print('.', end='')
        if debug:
            # traceback_str = ''.join(traceback.format_exception(etype=type(error), value=error, tb=error.__traceback__))
            # print(traceback_str)
            traceback.print_exception(error)
        # return None


def extract_download_url_from_fluorochem(cas_nr: str) -> Optional[Tuple[str, str]]:
    """Search for url to download SDS for chemical with cas_nr
    from Fluorochem (UK) using their search form

    Parameters
    ----------
    cas_nr : str
        CAS# for chemical of interest

    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple[str, str]:
            the name of the SDS source
            the URL from Fluorochem for SDS file
        None: if URL cannot be found
    """
    global debug

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    if debug:
        print('Searching on https://www.fluorochem.co.uk')

    try:
        with requests.Session() as session:
            # Use the search form found during investigation
            search_urls = [
                # Main site search form (found in investigation)
                f'https://fluorochem.co.uk/?s={cas_nr}',
                # Product search page
                f'https://www.fluorochem.co.uk/Products/Search?q={cas_nr}',
                # Alternative search format
                f'https://fluorochem.co.uk/shop/?s={cas_nr}'
            ]
            
            for search_url in search_urls:
                try:
                    response = session.get(search_url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        html = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for product results that might contain SDS
                        product_elements = html.select('div.product, .product-item, .result-item, .search-result')
                        
                        if product_elements:
                            if debug:
                                print(f"  Found {len(product_elements)} product elements")
                        
                        # Look for direct SDS/MSDS links
                        sds_selectors = [
                            'a[href*="sds"]',
                            'a[href*="msds"]', 
                            'a[href*="SDS"]',
                            'a[href*="MSDS"]',
                            'a:contains("SDS")',
                            'a:contains("MSDS")',
                            'a:contains("Safety Data Sheet")',
                            'a[href$=".pdf"]'  # PDF files might be SDS
                        ]
                        
                        for selector in sds_selectors:
                            sds_links = html.select(selector)
                            
                            for link in sds_links:
                                href = link.get('href', '')
                                text = link.get_text(strip=True).lower()
                                
                                # Check if this looks like an SDS link
                                if href and (
                                    any(term in href.lower() for term in ['sds', 'msds', 'safety']) or
                                    any(term in text for term in ['sds', 'msds', 'safety data sheet'])
                                ):
                                    # Make URL absolute if needed
                                    if not href.startswith('http'):
                                        from urllib.parse import urljoin
                                        href = urljoin(response.url, href)
                                    
                                    return 'Fluorochem', href
                        
                        # If no direct SDS links, look for product detail pages to potentially follow
                        product_links = html.select('a[href*="product"], a[href*="shop"]')
                        if product_links and debug:
                            print(f"  Found {len(product_links)} product links - could follow for detailed search")
                            
                except requests.RequestException as e:
                    if debug:
                        print(f"  Error with {search_url}: {e}")
                    continue
                        
    except Exception as error:
        if debug:
            print(f"Fluorochem search failed: {error}")
    
    return None


def extract_download_url_from_tci(cas_nr: str) -> Optional[Tuple[str, str]]:
    """Search for url of SDS from TCI Chemicals (www.tcichemicals.com)

    Parameters
    ----------
    cas_nr : str
        The CAS number of the molecule of interest

    Returns
    -------
    Tuple[str, bool, Optional[str]]
        - str: CAS number of the input chemical
        - bool: True if SDS file downloaded or exists
        - str: the name of the SDS source or None
    """
    global debug


    # adv_search_url = 'https://www.tcichemicals.com/US/en/search/?text={}&resulttype=product'.format(cas_nr)
    # adv_search_url = 'https://www.tcichemicals.com/US/en/search/?text={}'.format(cas_nr)
    adv_search_url = 'https://www.tcichemicals.com/US/en/search/'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': adv_search_url,
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode':'navigate',
        'Sec-Fetch-Site':'same-origin',
        'Sec-Fetch-User':'?1',
    }

    # # Set initial return value for if SDS is downloaded (or existed)
    # downloaded = False

    # file_name = cas_nr + '.pdf'
    # # download_file = Path(download_path) / file_name

    if debug:
        print('Searching on https://www.tcichemicals.com')

    try:
        with requests.Session() as s:
            # Try multiple approaches with different timeouts
            search_approaches = [
                # Simple GET with CAS in URL
                (f'{adv_search_url}?text={cas_nr}', 'GET', None, 15),
                # Original POST approach but with shorter timeout
                (adv_search_url, 'GET', {'text': cas_nr}, 25),
                # Try alternative search format
                (f'https://www.tcichemicals.com/US/en/search?q={cas_nr}', 'GET', None, 15)
            ]
            
            for url, method, params, timeout in search_approaches:
                try:
                    if debug:
                        print(f'  Trying TCI approach: {method} {url}')
                    
                    if method == 'GET':
                        get_id = s.get(url, headers=headers, timeout=timeout, params=params)
                    else:
                        get_id = s.post(url, headers=headers, timeout=timeout, data=params)
                    
                    if get_id.status_code == 200 and len(get_id.history) == 0:
                        break  # Success, continue with processing
                        
                except requests.exceptions.Timeout:
                    if debug:
                        print(f'  TCI timeout with {method} {url}')
                    continue
                except requests.exceptions.RequestException as e:
                    if debug:
                        print(f'  TCI request error with {method} {url}: {e}')
                    continue
            else:
                # All approaches failed
                if debug:
                    print('  All TCI approaches failed')
                return None

            if get_id.status_code == 200 and len(get_id.history) == 0:
                # get_id.text
                html = BeautifulSoup(get_id.text, 'html.parser')
                # print(html.prettify()); exit(1)

                # Get the token, required for POST request for SDS file name later
                csrf_token = html.find('input', attrs={'name': 'CSRFToken'})['value'] if html.find('input', attrs={'name': 'CSRFToken'}) else None
                # breakpoint()
                if not csrf_token:
                    return
                # print(f'{csrf_token=}')

                region_code = html.find_all(string=re.compile(r'(encodedContextPath[^;]+?;)'))
                # print(region_code[0])
                encodedContextPath = re.search(r'(encodedContextPath[^;]+?\'(\S+)\';)', region_code[0])[2].replace('\\' ,'')
                # print(encodedContextPath)

                product_cat_css = 'div#contentSearchFacet > span.facet__text:first-child > a:first-child'
                product_category = html.select(product_cat_css)[0]
                # print(product_category)

                hit_count = 0
                if product_category.text == 'Products':
                    hit_count = re.search(r'\((\d+)\)',
                                        html.select(f'{product_cat_css} + span.facet__value__count')[0].text)[1]
                # print(f'{hit_count=}')

                # Check to make sure that there is at least 1 hit
                if hit_count:
                    # Find the first hit
                    first_hit_div = html.find('div', class_='prductlist')
                    # print(first_hit_form)

                    # Find the CAS# for the first hit
                    returned_cas = first_hit_div['data-casno']
                    # print(f'{returned_cas=}')

                    # Confirm the first hit has the same CAS# as search chemical
                    if returned_cas == cas_nr:
                        # Get this TCI product number as follow:
                        prd_id = first_hit_div['data-id']
                        # print(f'{prd_id=}')

                        # Check if TCI product number is found:
                        if prd_id:
                            sds_url = ' https://www.tcichemicals.com/US/en/documentSearch/productSDSSearchDoc'

                            data = {
                                'productCode': f'{prd_id}',
                                'langSelector': 'en',
                                'selectedCountry': 'US',
                                'CSRFToken': f'{csrf_token}'
                            }
                            file_name_res = s.post(sds_url, headers=headers, timeout=15, data=data)
                            # print(f'{file_name_res=}')
                            # print(file_name_res.headers)
                            # print(f"{file_name_res.headers.get('content-disposition')=}")

                            # Get the SDS file name using the return header, in "content-disposition"
                            res_file = re.search(r'filename=(\S+)$', file_name_res.headers.get('content-disposition'))[1]
                            # print(f"{res_file=}")

                            # url = f'https://www.tcichemicals.com/US/en/sds/{prd_id.upper()}_US_EN.pdf'
                            # An example of an sds url: 'https://www.tcichemicals.com/US/en/sds/B3296_US_EN.pdf'
                            url = f'https://www.tcichemicals.com{encodedContextPath}/sds/{res_file}'
                            # print(url)

                            return 'TCI', url

    except Exception as error:
        if debug:
            print(f"TCI search failed: {error}")
            # Don't print full traceback for timeouts to reduce noise
            if "timeout" not in str(error).lower():
                traceback.print_exception(error)


if __name__ == '__main__':
    cas_list = [
        '10257-55-3', '106-93-4', '110489-05-9', '111-87-5', '124-73-2',
        '1323-83-7', '139-02-6', '15022-08-9', '18586-22-6', '1859-08-1',
        '2156-97-0', '3687-18-1', '39389-20-3', '558-20-3', '63316-43-8',
        '68441-33-8', '70900-21-9', '7440-06-4', '75-47-8', '75-69-4',
        '853-68-9', '141-78-6', '110-82-7', '67-63-0', '75-09-2', '109-89-7',
        '872-50-4', '68-12-2', '96-47-9', '111-66-0', '110-54-3',
        '491588-98-8',
        '1215071-17-2', '63148-57-2', '128577-47-9', '57395-89-8', '34851-41-7', '732-80-9',
        '00000-00-0',     # invalid CAS number, or unknown CAS
    ]
    download_path = 'SDS'
    find_sds(cas_list=cas_list, download_path=download_path, pool_size=10)

    # find_sds(cas_list=cas_list, pool_size=10)
