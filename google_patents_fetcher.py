"""
Google Patents Fetcher
Fetches patent data from patents.google.com

Advantages:
- No API key needed
- Works for WO, US, EP, and all patent offices
- Very reliable (Google's infrastructure)
- Fast and simple
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import re


def fetch_patent_from_google(patent_number: str) -> Optional[Dict]:
    """
    Fetch patent data from Google Patents
    
    Args:
        patent_number: Patent number (e.g., WO2024033280A1, US20240123456A1)
        
    Returns:
        Dictionary with patent data if successful, None otherwise
    """
    
    print("\n" + "="*60)
    print("🌐 FETCHING FROM GOOGLE PATENTS")
    print("="*60)
    
    try:
        # Normalize patent number (remove spaces, make uppercase)
        patent_number = normalize_patent_number(patent_number)
        
        print(f"\n  Patent: {patent_number}")
        
        # Google Patents URL
        url = f"https://patents.google.com/patent/{patent_number}/en"
        
        print(f"  URL: {url}")
        
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        print(f"  Fetching page...")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ✗ Failed to fetch (HTTP {response.status_code})")
            return None
        
        print(f"  ✓ Page fetched ({len(response.text):,} bytes)")
        
        # Parse HTML
        print(f"  Parsing HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract patent data
        patent_data = {
            'patent_id': patent_number,
            'title': extract_title(soup),
            'abstract': extract_abstract(soup),
            'company': extract_assignee(soup),
            'claims': extract_claims(soup),
            'description': extract_description(soup),
            'inventors': extract_inventors(soup),
            'filing_date': extract_filing_date(soup),
            'publication_date': extract_publication_date(soup),
            'images': extract_structure_images(soup, patent_number),
        }
        
        print(f"\n  ✓ Extracted:")
        print(f"    - Title: {patent_data['title'][:50]}...")
        print(f"    - Company: {patent_data['company']}")
        print(f"    - Abstract: {len(patent_data['abstract'])} chars")
        print(f"    - Claims: {len(patent_data['claims'])} chars")
        print(f"    - Images: {len(patent_data['images'])} found")
        
        print("="*60)
        
        return patent_data
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Network error: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def normalize_patent_number(patent_input: str) -> str:
    """
    Normalize patent number for Google Patents
    
    Examples:
        "WO2024033280" -> "WO2024033280A1"
        "US19060264" -> "US20190060264A1"
        "US20190060264A1" -> "US20190060264A1"
        "EP4123456" -> "EP4123456A1"
    """
    # Remove spaces and slashes
    patent_input = patent_input.strip().upper().replace(" ", "").replace("/", "")
    
    print(f"  Input: {patent_input}")
    
    # Handle US patents with shortened year format
    # US19060264 should become US20190060264
    if patent_input.startswith("US"):
        # Extract the number part
        num_part = patent_input[2:]
        
        # Remove any existing kind code
        kind_codes = ['A1', 'A2', 'B1', 'B2', 'B3', 'C1', 'C2']
        for kind_code in kind_codes:
            if num_part.endswith(kind_code):
                num_part = num_part[:-2]
                break
        
        # Check if it's a short format (e.g., 19060264 instead of 20190060264)
        # US patents after 2000 are typically 11 digits: YYYY + 7 digits
        if len(num_part) == 8 and num_part[0:2] in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                                                       '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                                                       '20', '21', '22', '23', '24', '25']:
            # It's a shortened year format - add '20' prefix
            num_part = '20' + num_part
            print(f"  Expanded US year: {num_part}")
        
        normalized = f"US{num_part}A1"
        print(f"  Normalized: {normalized}")
        return normalized
    
    # Handle WO patents
    elif patent_input.startswith("WO"):
        num_part = patent_input[2:]
        # Remove any existing kind code
        kind_codes = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2']
        for kind_code in kind_codes:
            if num_part.endswith(kind_code):
                num_part = num_part[:-2]
                break
        normalized = f"WO{num_part}A1"
        print(f"  Normalized: {normalized}")
        return normalized
    
    # Handle EP patents
    elif patent_input.startswith("EP"):
        num_part = patent_input[2:]
        # Remove any existing kind code
        kind_codes = ['A1', 'A2', 'A3', 'B1', 'B2']
        for kind_code in kind_codes:
            if num_part.endswith(kind_code):
                num_part = num_part[:-2]
                break
        normalized = f"EP{num_part}A1"
        print(f"  Normalized: {normalized}")
        return normalized
    
    # Default: assume it already has kind code or add A1
    else:
        if not any(patent_input.endswith(code) for code in ['A1', 'A2', 'B1', 'B2']):
            patent_input += 'A1'
        print(f"  Normalized: {patent_input}")
        return patent_input


def extract_title(soup) -> str:
    """Extract patent title from Google Patents page"""
    
    # Try different selectors
    selectors = [
        'meta[name="DC.title"]',
        'meta[property="og:title"]',
        'invention-title',
        'h1[itemprop="title"]',
    ]
    
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get('content') or elem.get_text()
            if title:
                # Clean up title
                title = title.strip()
                # Remove " - Google Patents" suffix
                title = re.sub(r'\s*-\s*Google Patents\s*$', '', title, flags=re.IGNORECASE)
                return title
    
    return 'Not available'


def extract_abstract(soup) -> str:
    """Extract patent abstract"""
    
    # Look for abstract section
    abstract_div = soup.find('div', {'class': 'abstract'}) or soup.find('section', {'itemprop': 'abstract'})
    
    if abstract_div:
        # Get text, cleaning up whitespace
        text = abstract_div.get_text(separator=' ', strip=True)
        return text
    
    # Try meta description
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc['content'].strip()
    
    return 'Not available'


def extract_assignee(soup) -> str:
    """Extract assignee/applicant (company name)"""
    
    # Look for assignee information
    assignee_elem = soup.find('dd', {'itemprop': 'assigneeCurrent'}) or soup.find('dd', {'itemprop': 'assigneeOriginal'})
    
    if assignee_elem:
        return assignee_elem.get_text(strip=True)
    
    # Try meta tag
    meta_assignee = soup.find('meta', {'name': 'DC.contributor'})
    if meta_assignee and meta_assignee.get('content'):
        return meta_assignee['content'].strip()
    
    return None


def extract_inventors(soup) -> List[str]:
    """Extract inventor names"""
    
    inventors = []
    
    # Find all inventor elements
    inventor_elems = soup.find_all('dd', {'itemprop': 'inventor'})
    
    for elem in inventor_elems:
        name = elem.get_text(strip=True)
        if name:
            inventors.append(name)
    
    return inventors


def extract_claims(soup) -> str:
    """Extract patent claims"""
    
    # Look for claims section
    claims_div = soup.find('section', {'itemprop': 'claims'}) or soup.find('div', {'class': 'claims'})
    
    if claims_div:
        # Get all claim text
        text = claims_div.get_text(separator='\n', strip=True)
        # Limit to first 5000 chars for AI analysis
        if len(text) > 5000:
            text = text[:5000] + "...[truncated]"
        return text
    
    return ''


def extract_description(soup) -> str:
    """Extract patent description"""
    
    # Look for description section
    desc_div = soup.find('section', {'itemprop': 'description'}) or soup.find('div', {'class': 'description'})
    
    if desc_div:
        # Get text
        text = desc_div.get_text(separator=' ', strip=True)
        # Limit to first 10000 chars for AI analysis
        if len(text) > 10000:
            text = text[:10000] + "...[truncated]"
        return text
    
    return ''


def extract_filing_date(soup) -> str:
    """Extract filing date"""
    
    date_elem = soup.find('time', {'itemprop': 'filingDate'})
    if date_elem:
        return date_elem.get_text(strip=True)
    
    return 'Not available'


def extract_publication_date(soup) -> str:
    """Extract publication date"""
    
    date_elem = soup.find('time', {'itemprop': 'publicationDate'})
    if date_elem:
        return date_elem.get_text(strip=True)
    
    return 'Not available'


def extract_structure_images(soup, patent_number: str) -> List[Dict]:
    """
    Extract chemical structure images from the patent
    Returns list of image URLs with metadata
    """
    
    images = []
    
    # Find all figure images
    figure_imgs = soup.find_all('img', {'class': 'figures'}) or soup.find_all('img', {'itemprop': 'image'})
    
    for img in figure_imgs[:5]:  # Limit to first 5 images
        src = img.get('src')
        if src:
            # Get alt text or figure number
            alt = img.get('alt', '')
            
            # Check if it's likely a chemical structure
            is_structure = any(keyword in alt.lower() for keyword in ['formula', 'structure', 'compound', 'fig'])
            
            images.append({
                'url': src,
                'alt': alt,
                'is_structure': is_structure,
            })
    
    print(f"    Found {len(images)} images")
    
    return images


# ==============================================================================
# TEST CODE
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("GOOGLE PATENTS FETCHER - TEST MODE")
    print("="*70)
    
    # Get patent number from command line or use default
    if len(sys.argv) > 1:
        test_patent = sys.argv[1]
    else:
        # Default: your patent!
        test_patent = "WO2024033280A1"
    
    print(f"\nTest patent: {test_patent}")
    
    # Fetch it
    patent_data = fetch_patent_from_google(test_patent)
    
    if patent_data:
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"\nPatent ID: {patent_data['patent_id']}")
        print(f"Company: {patent_data['company']}")
        print(f"Title: {patent_data['title']}")
        print(f"\nAbstract:\n{patent_data['abstract'][:200]}...")
        print(f"\nClaims: {len(patent_data['claims'])} chars")
        print(f"Images: {len(patent_data['images'])}")
        
        if patent_data['images']:
            print("\nImages found:")
            for i, img in enumerate(patent_data['images'], 1):
                print(f"  {i}. {img['alt']} - Structure: {img['is_structure']}")
        
        print("\n" + "="*70)
    else:
        print("\n" + "="*70)
        print("❌ FAILED TO FETCH PATENT")
        print("="*70)
        print(f"\nTry visiting manually:")
        print(f"https://patents.google.com/patent/{test_patent}")
        print("="*70)
