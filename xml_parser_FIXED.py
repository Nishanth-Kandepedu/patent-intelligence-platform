"""
STEP 1: Robust Patent XML Parser
Built from scratch to be foolproof

This parser:
1. Extracts company names (applicants/assignees)
2. Extracts English title (not French/other languages)
3. Extracts English abstract
4. Extracts description text
5. Extracts patent ID
"""

import xml.etree.ElementTree as ET
from typing import Dict, List


def strip_namespace(tag: str) -> str:
    """Remove XML namespace from tag names"""
    return tag.split("}", 1)[1] if "}" in tag else tag


def get_text_safely(element, default="") -> str:
    """Safely get text from an XML element"""
    if element is not None and element.text:
        return element.text.strip()
    return default


def parse_patent_xml(xml_bytes: bytes) -> Dict:
    """
    Parse WIPO patent XML and extract key information
    
    Returns:
        Dict with keys: title, abstract, description, company, patent_id
    """
    
    print("\n" + "="*60)
    print("STARTING XML PARSING")
    print("="*60)
    
    # Parse the XML
    try:
        root = ET.fromstring(xml_bytes)
        print(f"✓ XML parsed successfully")
        print(f"  Root tag: {strip_namespace(root.tag)}")
    except Exception as e:
        print(f"✗ Failed to parse XML: {e}")
        return create_empty_result()
    
    # Initialize result structure
    result = {
        'title': '',
        'abstract': '',
        'description': '',
        'company': None,
        'patent_id': '',
    }
    
    # Extract each field
    result['patent_id'] = extract_patent_id(root)
    result['company'] = extract_company_name(root)
    result['title'] = extract_title(root)
    result['abstract'] = extract_abstract(root)
    result['description'] = extract_description(root)
    
    print("\n" + "="*60)
    print("PARSING COMPLETE")
    print("="*60)
    
    return result


def extract_patent_id(root) -> str:
    """
    Extract patent publication number in proper format
    
    Formats:
    - WO patents: WO2024033280A1
    - US patents: US20240123456A1 or US11234567B2
    - EP patents: EP4123456A1
    - Includes country code, number, and kind code
    """
    print("\n📄 Extracting Patent ID...")
    
    # Look for publication-reference -> document-id
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'publication-reference':
            # Found publication reference, now extract components
            country = ''
            doc_number = ''
            kind = ''
            
            for child in elem.iter():
                child_tag = strip_namespace(child.tag)
                
                if child_tag == 'country' and child.text:
                    country = child.text.strip()
                elif child_tag == 'doc-number' and child.text:
                    doc_number = child.text.strip()
                    # Remove slashes and spaces from doc-number
                    doc_number = doc_number.replace('/', '').replace(' ', '')
                elif child_tag == 'kind' and child.text:
                    kind = child.text.strip()
            
            # Construct the full patent ID
            if country and doc_number:
                patent_id = f"{country}{doc_number}"
                if kind:
                    patent_id += kind
                
                print(f"  ✓ Found patent ID: {patent_id}")
                print(f"    (Country: {country}, Number: {doc_number}, Kind: {kind})")
                return patent_id
    
    print(f"  ✗ Patent ID not found")
    return 'Not available'


def extract_company_name(root) -> str:
    """
    Extract company name from applicants section
    This is the KEY function we need to fix
    """
    print("\n🏢 Extracting Company Name...")
    
    companies = []
    
    # Look for <applicants> section
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'applicants':
            print(f"  ✓ Found 'applicants' section")
            
            # Within applicants, look for each applicant
            for applicant in elem.iter():
                app_tag = strip_namespace(applicant.tag)
                
                if app_tag == 'applicant':
                    # Found an applicant, now look for name
                    company_name = extract_name_from_applicant(applicant)
                    if company_name:
                        companies.append(company_name)
                        print(f"  ✓ Found company: {company_name}")
    
    # Also check for assignees (used in US patents)
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'assignees':
            print(f"  ✓ Found 'assignees' section")
            
            for assignee in elem.iter():
                ass_tag = strip_namespace(assignee.tag)
                
                if ass_tag == 'assignee':
                    company_name = extract_name_from_applicant(assignee)
                    if company_name:
                        companies.append(company_name)
                        print(f"  ✓ Found company: {company_name}")
    
    if companies:
        # Remove duplicates and join
        companies = list(dict.fromkeys(companies))  # Preserve order, remove dupes
        result = ", ".join(companies)
        print(f"  ✓ Final company list: {result}")
        return result
    else:
        print(f"  ✗ No company names found")
        return None


def extract_name_from_applicant(applicant_elem) -> str:
    """Extract company or person name from applicant/assignee element"""
    
    # Look for different name tags in order of preference
    # Different patent offices use different tag names
    
    name_tags = ['name', 'n', 'orgname', 'organization-name']
    
    for elem in applicant_elem.iter():
        tag = strip_namespace(elem.tag)
        
        if tag in name_tags and elem.text:
            name = elem.text.strip()
            print(f"    Found in <{tag}>: {name}")
            return name
    
    return ''


def extract_title(root) -> str:
    """Extract English invention title"""
    print("\n📝 Extracting Title...")
    
    # Look for invention-title with lang="en"
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'invention-title':
            # Check if it's English
            lang = elem.get('lang', '')
            
            if lang == 'en' and elem.text:
                title = elem.text.strip()
                print(f"  ✓ Found English title: {title[:60]}...")
                return title
    
    # If no English title, take first title we find
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'invention-title' and elem.text:
            title = elem.text.strip()
            print(f"  ⚠ Found title (not English): {title[:60]}...")
            return title
    
    print(f"  ✗ Title not found")
    return 'Not available'


def extract_abstract(root) -> str:
    """Extract English abstract"""
    print("\n📋 Extracting Abstract...")
    
    # Look for <abstract lang="en">
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'abstract':
            lang = elem.get('lang', '')
            
            if lang == 'en':
                # Get all paragraph text
                paragraphs = []
                for p in elem.iter():
                    p_tag = strip_namespace(p.tag)
                    if p_tag == 'p' and p.text:
                        paragraphs.append(p.text.strip())
                
                if paragraphs:
                    abstract = '\n\n'.join(paragraphs)
                    print(f"  ✓ Found English abstract: {len(abstract)} chars")
                    return abstract
    
    print(f"  ✗ Abstract not found")
    return 'Not available'


def extract_description(root) -> str:
    """
    Extract description text
    Note: Many WIPO patents have description in image format (TIF files)
    In those cases, we'll use the abstract as a proxy
    """
    print("\n📖 Extracting Description...")
    
    # Look for <description> tag
    description_found = False
    for elem in root.iter():
        tag = strip_namespace(elem.tag)
        
        if tag == 'description':
            description_found = True
            # Get all paragraph text
            paragraphs = []
            for p in elem.iter():
                p_tag = strip_namespace(p.tag)
                if p_tag == 'p' and p.text:
                    paragraphs.append(p.text.strip())
            
            if paragraphs:
                # Limit to first 50 paragraphs to avoid overwhelming the AI
                description = ' '.join(paragraphs[:50])
                print(f"  ✓ Found text description: {len(description)} chars ({len(paragraphs)} paragraphs)")
                return description
    
    if description_found:
        print(f"  ⚠ Description section exists but in image format (TIF files)")
        print(f"    This is normal for many WIPO patents")
        print(f"    We'll use the abstract for AI analysis")
    else:
        print(f"  ✗ No description section found")
    
    return ''


def create_empty_result() -> Dict:
    """Return empty result structure if parsing fails"""
    return {
        'title': 'Not available',
        'abstract': 'Not available',
        'description': '',
        'company': None,
        'patent_id': 'Not available',
    }


# ==============================================================================
# TEST CODE
# ==============================================================================

if __name__ == "__main__":
    import sys
    import os
    
    print("\n" + "="*70)
    print("PATENT XML PARSER - TEST MODE")
    print("="*70)
    
    # Check if a file was provided as argument
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        # Default: look for example_patent.xml in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(script_dir, 'example_patent.xml')
        
        # If example_patent.xml doesn't exist, try the uploads folder
        if not os.path.exists(test_file):
            test_file = '/mnt/user-data/uploads/example_patent.xml'
    
    if not os.path.exists(test_file):
        print(f"\n✗ Error: File not found: {test_file}")
        print("\nUsage:")
        print("  python xml_parser_FIXED.py                    # Uses example_patent.xml in same folder")
        print("  python xml_parser_FIXED.py my_patent.xml      # Uses specified file")
        sys.exit(1)
    
    try:
        with open(test_file, 'rb') as f:
            xml_bytes = f.read()
        
        print(f"\n✓ Loaded file: {os.path.basename(test_file)}")
        print(f"  Size: {len(xml_bytes):,} bytes")
        
        # Parse it
        result = parse_patent_xml(xml_bytes)
        
        # Display results
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"\nPatent ID: {result['patent_id']}")
        print(f"\nCompany: {result['company']}")
        print(f"\nTitle: {result['title'][:80]}...")
        print(f"\nAbstract:\n{result['abstract'][:200]}...")
        print(f"\nDescription: {len(result['description'])} chars")
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
