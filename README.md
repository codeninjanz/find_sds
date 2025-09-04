[![Python 3](https://pyup.io/repos/github/khoivan88/find_sds/python-3-shield.svg)](https://pyup.io/repos/github/khoivan88/find_sds/)
[![Updates](https://pyup.io/repos/github/khoivan88/find_sds/shield.svg)](https://pyup.io/repos/github/khoivan88/find_sds/)
[![codecov](https://codecov.io/gh/khoivan88/find_sds/branch/master/graph/badge.svg)](https://codecov.io/gh/khoivan88/find_sds)
[![python version](https://img.shields.io/badge/python-v3.10%2B-blue)]()
[![tested platforms](https://img.shields.io/badge/tested%20platform-win%20%7C%20osx%20%7C%20ubuntu-lightgrey)]()


# SDS FINDER API

**Enhanced safety data sheet finder with REST API support**

This program is designed to find and download safety data sheets (SDS) using either **CAS numbers** or **product names**. The enhanced version includes a RESTful API for easy integration with other applications.

<br/>


## CONTENTS

- [FIND MISSING SAFETY DATA SHEET (SDS)](#find-missing-safety-data-sheet-sds)
  - [CONTENTS](#contents)
  - [DETAILS](#details)
  - [REQUIREMENTS](#requirements)
  - [USAGE](#usage)
  - [VERSIONS](#versions)


## DETAILS

### Core Features
- **Multi-format search**: Search by CAS numbers OR product names
- **RESTful API**: Easy integration with web applications and other services  
- **Multithreading**: Fast concurrent downloads with configurable thread pool
- **Multiple databases**: Searches across 6 different chemical databases
- **Flexible deployment**: Can be used as Python library or deployed as web API

### Search Capabilities
- **CAS Number Search**: Traditional search using Chemical Abstracts Service numbers
- **Product Name Search**: NEW! Search using common chemical names and product names
- **Mixed Search**: Combine both CAS numbers and product names in a single request
- **Batch Processing**: Handle multiple chemicals in one API call

### Supported Databases
- [ChemBlink](https://www.chemblink.com/) - CAS and product name search
- [VWR](https://us.vwr.com/store/search/searchMSDS.jsp) - CAS and product name search
- [Fisher Scientific](https://www.fishersci.com/us/en/catalog/search/sdshome.html) - CAS and product name search
- [TCI Chemicals](www.tcichemicals.com) - CAS and product name search
- [ChemicalSafety](https://chemicalsafety.com/sds-search/) - CAS and product name search
- [Fluorochem](http://www.fluorochem.co.uk/) - CAS and product name search

### Output Options
- **URL only**: Get direct links to SDS files without downloading
- **Download files**: Automatically download SDS files as PDFs
- **JSON responses**: Structured data for API integration



## REQUIREMENTS

- Python 3.10+
- [Dependencies](requirements.txt)

<br/>

## USAGE

### Quick Start

1. **Clone this repository:**

   ```bash
   git clone https://github.com/khoivan88/find_sds.git
   cd find_sds
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the API server:**

   ```bash
   python run_server.py
   ```

   The API will be available at `http://localhost:5000`

### API Usage

#### 1. Search by CAS Number

```bash
curl -X POST http://localhost:5000/search/cas \
  -H "Content-Type: application/json" \
  -d '{"cas_numbers": ["67-63-0", "75-09-2"], "download": false}'
```

#### 2. Search by Product Name

```bash
curl -X POST http://localhost:5000/search/product \
  -H "Content-Type: application/json" \
  -d '{"product_names": ["Isopropanol", "Acetone"], "download": false}'
```

#### 3. Mixed Search (CAS + Product Names)

```bash
curl -X POST http://localhost:5000/search/mixed \
  -H "Content-Type: application/json" \
  -d '{
    "cas_numbers": ["67-63-0"], 
    "product_names": ["Acetone"], 
    "download": false
  }'
```

#### 4. Download SDS Files

Set `"download": true` in any request to automatically download PDF files:

```bash
curl -X POST http://localhost:5000/search/cas \
  -H "Content-Type: application/json" \
  -d '{"cas_numbers": ["67-63-0"], "download": true}'
```

### Python Library Usage

The original functionality is still available as a Python library:

```python
from find_sds.find_sds import find_sds

# Search by CAS numbers
cas_list = ['67-63-0', '75-09-2', '96-47-9']
find_sds(cas_list=cas_list, download_path='SDS', pool_size=10)
```

### API Response Format

```json
{
  "request_id": "uuid-string",
  "results": [
    {
      "cas_number": "67-63-0",
      "found": true,
      "source": "ChemicalSafety",
      "url": "https://example.com/sds.pdf",
      "download_url": "/download/uuid/67-63-0-SDS.pdf"
    }
  ],
  "total_searched": 1,
  "found_count": 1
}
```

### Testing

Run the test suite:

```bash
python test_api.py
```

For deployed API:

```bash
python test_api.py https://yourapp.pythonanywhere.com
```

### Deployment to PythonAnywhere

1. **Upload files** to your PythonAnywhere account
2. **Install dependencies**: `pip3.10 install --user -r requirements.txt`  
3. **Configure web app** using the provided `flask_app.py` as your WSGI file
4. **Update paths** in `flask_app.py` to match your directory structure

See [deployment_instructions.md](deployment_instructions.md) for detailed setup instructions.

<br/>


## NEW FEATURES (v2.0)

- ✅ **Product Name Search**: Search by chemical names like "Acetone", "Isopropanol"
- ✅ **REST API**: Complete Flask-based API with JSON responses
- ✅ **Mixed Search**: Combine CAS numbers and product names in one request
- ✅ **URL-only Mode**: Get download links without actually downloading files
- ✅ **Batch Processing**: Handle multiple chemicals in a single API call
- ✅ **Enhanced Error Handling**: Proper HTTP status codes and error messages
- ✅ **PythonAnywhere Ready**: Easy deployment configuration included

## VERSIONS
See [here](VERSION.md) for the most up-to-date
