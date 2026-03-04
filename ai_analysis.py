"""
STEP 2: AI Patent Analysis using Claude
Built to extract scientific insights from patents

This module:
1. Takes parsed patent data (title, abstract, company)
2. Sends to Claude for analysis
3. Extracts structured insights:
   - Biology: targets, mechanisms, indications
   - Chemistry: compound series, novelty
   - Confidence levels
"""

import json
import os
from typing import Dict


def analyze_patent_with_claude(patent_data: Dict, api_key: str) -> Dict:
    """
    Analyze patent using Claude AI
    
    Args:
        patent_data: Dict with 'title', 'abstract', 'description', 'company', 'patent_id'
        api_key: Your Anthropic API key
        
    Returns:
        Dict with structured AI analysis
    """
    
    print("\n" + "="*60)
    print("🤖 AI ANALYSIS STARTING")
    print("="*60)
    
    try:
        # Import anthropic library
        try:
            import anthropic
        except ImportError:
            print("✗ Error: anthropic library not installed")
            print("\nPlease install it:")
            print("  pip install anthropic")
            return create_empty_analysis()
        
        # Initialize Claude client
        print("  Connecting to Claude API...")
        client = anthropic.Anthropic(api_key=api_key)
        
        # Prepare the context
        context = prepare_patent_context(patent_data)
        
        # Create the prompt
        prompt = create_analysis_prompt(context, patent_data)
        
        # Call Claude
        print("  Sending patent to Claude for analysis...")
        print(f"  (This will cost ~$0.02-0.05)")
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Latest Claude Sonnet
            max_tokens=4000,
            temperature=0.3,  # Lower = more focused/factual
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract response
        response_text = message.content[0].text
        print("  ✓ Received analysis from Claude")
        
        # Parse the structured response
        analysis = parse_claude_response(response_text)
        
        print("  ✓ Analysis complete!")
        print("="*60)
        
        return analysis
        
    except Exception as e:
        print(f"✗ Error during AI analysis: {e}")
        import traceback
        traceback.print_exc()
        return create_empty_analysis()


def prepare_patent_context(patent_data: Dict) -> str:
    """Prepare patent information as context for Claude"""
    
    parts = []
    
    # Patent ID
    if patent_data.get('patent_id'):
        parts.append(f"Patent: {patent_data['patent_id']}")
    
    # Company
    if patent_data.get('company'):
        parts.append(f"Company: {patent_data['company']}")
    
    # Title
    if patent_data.get('title'):
        parts.append(f"\nTitle:\n{patent_data['title']}")
    
    # Abstract
    if patent_data.get('abstract'):
        parts.append(f"\nAbstract:\n{patent_data['abstract']}")
    
    # Description (if available)
    if patent_data.get('description'):
        desc = patent_data['description']
        # Limit to 5000 chars to avoid token limits
        if len(desc) > 5000:
            desc = desc[:5000] + "...[truncated]"
        parts.append(f"\nDescription:\n{desc}")
    
    return '\n'.join(parts)


def create_analysis_prompt(context: str, patent_data: Dict) -> str:
    """Create the analysis prompt for Claude"""
    
    prompt = f"""You are an expert patent analyst specializing in pharmaceutical and biotech patents.

Analyze the following patent and provide a structured scientific analysis.

{context}

Please provide your analysis in the following JSON format. Be precise and only extract information that is EXPLICITLY stated in the patent. Do not infer or speculate.
{{
  "biology": {{
    "targets": "Primary biological targets (e.g., PI4K, mTOR, EGFR)",
    "mechanism": "Mechanism of action description",
    "indications": "Diseases or conditions targeted (e.g., malaria, cancer, diabetes)",
    "confidence": "HIGH/MEDIUM/LOW"
  }},
  "medicinal_chemistry": {{
    "series_description": "Description of the chemical series or compound class",
    "key_features": "Key structural features or modifications",
    "novelty": "What makes this chemistry novel or different",
    "confidence": "HIGH/MEDIUM/LOW"
  }},
  "therapeutic_area": "Primary therapeutic area (e.g., Infectious Diseases, Oncology, CNS)",
  "innovation_level": "BREAKTHROUGH/INCREMENTAL/DEFENSIVE",
  "key_insights": [
    "List 3-5 key insights",
    "Include competitive advantages",
    "Note potential commercial value"
  ],
  "summary": "One paragraph executive summary",
  "compounds": [
    {{
      "id": "Compound identifier (e.g., Compound 23, Example 5)",
      "in_vitro_ic50": "IC50 value in nM (number only)",
      "in_vivo_ed50": "ED50 value in mg/kg (number only)",
      "half_life": "Half-life in hours (number only)",
      "bioavailability": "Oral bioavailability % (number only)",
      "therapeutic_index": "Therapeutic index (number only)",
      "notes": "Brief note about this compound"
    }}
  ]
}}

COMPOUND DATA EXTRACTION RULES:
- Look for compound profiling data in tables, examples, or experimental sections
- Extract IC50, EC50, Ki values (convert to nM)
- Extract in vivo data: ED50, efficacy at doses (in mg/kg)
- Extract PK data: half-life (hrs), Cmax, AUC, bioavailability (%)
- Extract safety data: TD50, therapeutic index, cytotoxicity
- Only include compounds with at least 2 parameters available
- If no compound data exists in the patent, return empty array: "compounds": []

IMPORTANT: 
- Only extract information explicitly stated in the patent
- If information is unclear or not stated, say "Not specified"
- Set confidence to LOW if you're uncertain
- Respond with ONLY the JSON object, no additional text

JSON Response:"""
    
    return prompt


def parse_claude_response(response_text: str) -> Dict:
    """Parse Claude's JSON response into structured data"""
    
    try:
        # Try to extract JSON from response
        # Sometimes Claude adds explanation, so find the JSON block
        
        # Find JSON start and end
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            analysis = json.loads(json_str)
            
            # Validate structure
            if 'biology' in analysis and 'medicinal_chemistry' in analysis:
                return analysis
            else:
                print("  ⚠ Warning: Response missing expected fields")
                return analysis
        else:
            print("  ✗ Could not find JSON in response")
            return {
                'raw_response': response_text,
                'error': 'Could not parse JSON'
            }
            
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parsing error: {e}")
        return {
            'raw_response': response_text,
            'error': 'Invalid JSON'
        }


def create_empty_analysis() -> Dict:
    """Return empty analysis structure if analysis fails"""
    return {
        'biology': {
            'targets': 'Analysis failed',
            'mechanism': 'Analysis failed',
            'indications': 'Analysis failed',
            'confidence': 'LOW'
        },
        'medicinal_chemistry': {
            'series_description': 'Analysis failed',
            'key_features': 'Analysis failed',
            'novelty': 'Analysis failed',
            'confidence': 'LOW'
        },
        'therapeutic_area': 'Unknown',
        'innovation_level': 'UNKNOWN',
        'key_insights': ['Analysis could not be completed'],
        'summary': 'Analysis failed'
    }


# ==============================================================================
# TEST CODE
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("AI PATENT ANALYSIS - TEST MODE")
    print("="*70)
    
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("\n⚠️  No API key found!")
        print("\nTo test this module, you need a Claude API key.")
        print("\nTwo ways to provide it:")
        print("\n1. Set environment variable:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("\n2. Pass as command line argument:")
        print("   python ai_analysis.py your-api-key-here")
        
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
            print(f"\n✓ Using API key from command line")
        else:
            print("\n❌ Cannot test without API key")
            sys.exit(1)
    else:
        print(f"\n✓ Found API key in environment")
    
    # Load the parser module
    print("\n📄 Loading patent parser...")
    try:
        from xml_parser_FIXED import parse_patent_xml
    except ImportError:
        print("✗ Could not import xml_parser_FIXED.py")
        print("  Make sure xml_parser_FIXED.py is in the same folder")
        sys.exit(1)
    
    # Load test patent
    print("📄 Loading test patent...")
    try:
        with open('example_patent.xml', 'rb') as f:
            xml_bytes = f.read()
        print(f"✓ Loaded example_patent.xml")
    except FileNotFoundError:
        print("✗ example_patent.xml not found")
        print("  Make sure example_patent.xml is in the same folder")
        sys.exit(1)
    
    # Parse the patent
    print("\n🔍 Parsing patent...")
    patent_data = parse_patent_xml(xml_bytes)
    print(f"✓ Parsed: {patent_data['patent_id']}")
    print(f"  Company: {patent_data['company']}")
    
    # Analyze with AI
    print("\n🤖 Starting AI analysis...")
    print("(This will use your Claude API - costs ~$0.02-0.05)")
    
    analysis = analyze_patent_with_claude(patent_data, api_key)
    
    # Display results
    print("\n" + "="*70)
    print("AI ANALYSIS RESULTS")
    print("="*70)
    
    if 'biology' in analysis:
        print("\n🧬 BIOLOGY")
        print(f"  Targets: {analysis['biology'].get('targets', 'N/A')}")
        print(f"  Mechanism: {analysis['biology'].get('mechanism', 'N/A')}")
        print(f"  Indications: {analysis['biology'].get('indications', 'N/A')}")
        print(f"  Confidence: {analysis['biology'].get('confidence', 'N/A')}")
    
    if 'medicinal_chemistry' in analysis:
        print("\n⚗️  MEDICINAL CHEMISTRY")
        print(f"  Series: {analysis['medicinal_chemistry'].get('series_description', 'N/A')}")
        print(f"  Key Features: {analysis['medicinal_chemistry'].get('key_features', 'N/A')}")
        print(f"  Novelty: {analysis['medicinal_chemistry'].get('novelty', 'N/A')}")
        print(f"  Confidence: {analysis['medicinal_chemistry'].get('confidence', 'N/A')}")
    
    if 'therapeutic_area' in analysis:
        print(f"\n🏥 THERAPEUTIC AREA: {analysis['therapeutic_area']}")
    
    if 'innovation_level' in analysis:
        print(f"💡 INNOVATION LEVEL: {analysis['innovation_level']}")
    
    if 'key_insights' in analysis:
        print("\n🔑 KEY INSIGHTS:")
        for i, insight in enumerate(analysis['key_insights'], 1):
            print(f"  {i}. {insight}")
    
    if 'summary' in analysis:
        print(f"\n📝 SUMMARY:")
        print(f"  {analysis['summary']}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
