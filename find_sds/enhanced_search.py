"""
Enhanced search functionality for finding SDS by product name
Extends the existing CAS-based search capabilities
"""

import json
import re
import traceback
from typing import Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

# Global debug flag
debug = False

def extract_download_url_from_chemicalsafety_by_name(product_name: str) -> Optional[Tuple[str, str]]:
    """Search for SDS by product name from ChemicalSafety.com
    
    Parameters
    ----------
    product_name : str
        Product name to search for
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (source_name, url) if found, None otherwise
    """
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36',
        'accept-encoding': 'gzip, deflate, br',
        'content-type': 'application/json',
    }
    
    extract_info_url = 'https://chemicalsafety.com/sds1/sds_retriever.php?action=search'
    
    form1 = {
        "IsContains": "true",  # Enable contains search for product names
        "IncludeSynonyms": "true",  # Include synonyms in search
        "SearchSdsServer": "false",
        "Criteria": [f"common|{product_name}"],  # Search by common/product name
        "HostName": "sfs website",
        "Bee": "stevia",
        "Action": "search",
        "SearchUrl": "",
        "ResultColumns": ["revision_date"]
    }

    if debug:
        print(f'Searching ChemicalSafety for product name: {product_name}')

    try:
        with requests.Session() as s:
            r1 = s.post(extract_info_url, headers=headers,
                        data=json.dumps(form1), timeout=20)

            if r1.status_code == 200 and r1.json():
                response_data = r1.json()
                
                if 'rows' in response_data and response_data['rows']:
                    cols = [row['name'] for row in response_data['cols']]
                    common_col_index = cols.index('COMMON')
                    manufacture_col_index = cols.index('MANUFACT')
                    sds_url_col_index = cols.index('HTTPMSDSREF')
                    
                    # Look for exact or partial matches
                    matching_compounds = []
                    for row in response_data['rows']:
                        common_name = row[common_col_index].lower()
                        search_name = product_name.lower()
                        
                        # Check for exact match or if search term is contained in the product name
                        if (search_name in common_name or common_name in search_name) and \
                           re.search(r'^http.+\.pdf$', row[sds_url_col_index]):
                            matching_compounds.append((row[sds_url_col_index], row[manufacture_col_index]))
                    
                    if matching_compounds:
                        url = matching_compounds[0][0]  # Take first match
                        manufacture = matching_compounds[0][1]
                        return manufacture, url

    except Exception as error:
        if debug:
            traceback.print_exception(error)
    
    return None

def extract_download_url_from_vwr_by_name(product_name: str) -> Optional[Tuple[str, str]]:
    """Search for SDS by product name from VWR
    
    Parameters
    ----------
    product_name : str
        Product name to search for
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (source_name, url) if found, None otherwise
    """
    
    adv_search_url = 'https://us.vwr.com/store/msds'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36',
    }
    params = {
        'keyword': product_name
    }

    if debug:
        print(f'Searching VWR for product name: {product_name}')

    try:
        with requests.Session() as s1:
            get_id = s1.get(adv_search_url, headers=headers, params=params, timeout=10)

            if get_id.status_code == 200 and len(get_id.history) == 0:
                html = BeautifulSoup(get_id.text, 'html.parser')

                result_count_css = '.clearfix .pull-left'
                result_elements = html.select(result_count_css)
                
                if result_elements:
                    result_match = re.search(r'(\d+).*results were found', result_elements[0].text)
                    if result_match:
                        result_count = result_match[1]
                        
                        # Check to make sure that there is at least 1 hit
                        if int(result_count) > 0:
                            # Find first product
                            sds_link_css = 'td[data-title="SDS"] a'
                            sds_links = html.select(sds_link_css)
                            
                            if sds_links:
                                full_url = sds_links[0]['href']

                                sds_manufacturer_css = 'td[data-title="Manufacturer"]'
                                sds_manufacturers = html.select(sds_manufacturer_css)
                                
                                if sds_manufacturers:
                                    sds_source = sds_manufacturers[0].text.strip()
                                    return sds_source, full_url

    except Exception as error:
        if debug:
            traceback.print_exception(error)
    
    return None

def extract_download_url_from_fisher_by_name(product_name: str) -> Optional[Tuple[str, str]]:
    """Search for SDS by product name from Fisher Scientific
    
    Parameters
    ----------
    product_name : str
        Product name to search for
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (source_name, url) if found, None otherwise
    """
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }

    extract_info_url = 'https://www.fishersci.com/us/en/catalog/search/sds'
    payload = {
        'selectLang': '',
        'store': '',
        'msdsKeyword': product_name
    }

    if debug:
        print(f'Searching Fisher Scientific for product name: {product_name}')

    try:
        r = requests.get(extract_info_url, headers=headers, timeout=10, params=payload)
        
        if r.status_code == 200 and len(r.history) == 0:
            html = BeautifulSoup(r.text, 'html.parser')
            
            # Look for the first SDS result
            # Fisher lists products with their names, we'll take the first match
            catalog_items = html.select('.catlog_items')
            
            if catalog_items:
                # Get the first available SDS
                cat_no_items = catalog_items[0].find_all('a')
                
                if cat_no_items:
                    rel_download_url = cat_no_items[0].get('href')
                    if rel_download_url:
                        full_url = 'https://www.fishersci.com' + rel_download_url
                        return 'Fisher', full_url

    except Exception as error:
        if debug:
            traceback.print_exception(error)
    
    return None

def extract_download_url_from_tci_by_name(product_name: str) -> Optional[Tuple[str, str]]:
    """Search for SDS by product name from TCI Chemicals
    
    Parameters
    ----------
    product_name : str
        Product name to search for
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (source_name, url) if found, None otherwise
    """
    
    adv_search_url = 'https://www.tcichemicals.com/US/en/search/'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': adv_search_url,
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }

    if debug:
        print(f'Searching TCI Chemicals for product name: {product_name}')

    try:
        with requests.Session() as s:
            get_id = s.get(adv_search_url, headers=headers, timeout=10, params={'text': product_name})

            if get_id.status_code == 200 and len(get_id.history) == 0:
                html = BeautifulSoup(get_id.text, 'html.parser')

                # Get the token, required for POST request for SDS file name later
                csrf_token = html.find('input', attrs={'name': 'CSRFToken'})
                if not csrf_token:
                    return None
                csrf_token = csrf_token['value']

                region_code = html.find_all(string=re.compile(r'(encodedContextPath[^;]+?;)'))
                if not region_code:
                    return None
                    
                encodedContextPath = re.search(r'(encodedContextPath[^;]+?\'(\S+)\';)', region_code[0])[2].replace('\\', '')

                product_cat_css = 'div#contentSearchFacet > span.facet__text:first-child > a:first-child'
                product_category_elements = html.select(product_cat_css)
                
                if not product_category_elements:
                    return None
                    
                product_category = product_category_elements[0]

                hit_count = 0
                if product_category.text == 'Products':
                    hit_count_elements = html.select(f'{product_cat_css} + span.facet__value__count')
                    if hit_count_elements:
                        hit_count_match = re.search(r'\((\d+)\)', hit_count_elements[0].text)
                        if hit_count_match:
                            hit_count = int(hit_count_match[1])

                # Check to make sure that there is at least 1 hit
                if hit_count > 0:
                    # Find the first hit
                    first_hit_div = html.find('div', class_='prductlist')
                    if not first_hit_div:
                        return None

                    # Get this TCI product number
                    prd_id = first_hit_div.get('data-id')
                    if not prd_id:
                        return None

                    sds_url = 'https://www.tcichemicals.com/US/en/documentSearch/productSDSSearchDoc'

                    data = {
                        'productCode': f'{prd_id}',
                        'langSelector': 'en',
                        'selectedCountry': 'US',
                        'CSRFToken': f'{csrf_token}'
                    }
                    
                    file_name_res = s.post(sds_url, headers=headers, timeout=15, data=data)
                    
                    content_disposition = file_name_res.headers.get('content-disposition')
                    if not content_disposition:
                        return None
                        
                    file_match = re.search(r'filename=(\S+)$', content_disposition)
                    if not file_match:
                        return None
                        
                    res_file = file_match[1]
                    url = f'https://www.tcichemicals.com{encodedContextPath}/sds/{res_file}'
                    
                    return 'TCI', url

    except Exception as error:
        if debug:
            traceback.print_exception(error)
    
    return None

def extract_download_url_from_chemblink_by_name(product_name: str) -> Optional[Tuple[str, str]]:
    """Search for SDS by product name from ChemBlink
    
    Note: ChemBlink primarily searches by CAS, so this searches for 
    product name in their database but may have limited results
    
    Parameters
    ----------
    product_name : str
        Product name to search for
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (source_name, url) if found, None otherwise
    """
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'
    }

    # ChemBlink has a general search that might find product names
    # This is a best-effort implementation
    search_url = f'https://www.chemblink.com/search.htm'
    params = {'q': product_name}

    if debug:
        print(f'Searching ChemBlink for product name: {product_name}')

    try:
        r1 = requests.get(search_url, headers=headers, params=params, timeout=20)
        
        if r1.status_code == 200 and len(r1.history) == 0:
            soup = BeautifulSoup(r1.text, 'html.parser')
            
            # Look for CAS numbers in the search results
            # ChemBlink search results usually show CAS numbers
            cas_pattern = r'\b\d{2,7}-\d{2}-\d\b'
            cas_matches = re.findall(cas_pattern, r1.text)
            
            if cas_matches:
                # Try to get SDS for the first CAS number found
                from find_sds.find_sds import extract_download_url_from_chemblink
                return extract_download_url_from_chemblink(cas_matches[0])

    except Exception as error:
        if debug:
            traceback.print_exception(error)
    
    return None

def extract_download_url_from_fluorochem_by_name(product_name: str) -> Optional[Tuple[str, str]]:
    """Search for SDS by product name from Fluorochem
    
    Parameters
    ----------
    product_name : str
        Product name to search for
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (source_name, url) if found, None otherwise
    """
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36',
        'Content-Type': 'application/json',
    }

    url = 'https://dougdiscovery.com/api/v1/molecules/search'
    payload = {
        "q": product_name, 
        "offset": 0, 
        "limit": 12
    }

    if debug:
        print(f'Searching Fluorochem for product name: {product_name}')

    try:
        r = requests.post(url, headers=headers, timeout=20, data=json.dumps(payload))
        
        if r.status_code == 200 and len(r.history) == 0:
            res = r.json()
            
            if res.get('data') and len(res['data']) > 0:
                # Look through results for matches
                for item in res['data']:
                    molecule = item.get('molecule', {})
                    
                    # Check if product name appears in molecule name or synonyms
                    molecule_name = molecule.get('name', '').lower()
                    search_name = product_name.lower()
                    
                    if search_name in molecule_name or molecule_name in search_name:
                        sds_info = molecule.get('sds')
                        if sds_info:
                            sds_partial_url_en = sds_info.get('custrecord_sdslink_en')
                            if sds_partial_url_en:
                                full_url = f'https://7128445.app.netsuite.com{sds_partial_url_en}'
                                return 'Fluorochem', full_url

    except Exception as error:
        if debug:
            traceback.print_exception(error)
    
    return None
