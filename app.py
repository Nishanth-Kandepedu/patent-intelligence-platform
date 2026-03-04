"""
Patent Research Platform
AI-Powered Patent Analysis for Competitive Intelligence
Target Users: R&D Scientists, Competitive Intelligence Analysts, Business Development
"""

import streamlit as st
import os
import time
from datetime import datetime
from typing import List, Dict
from xml_parser_FIXED import parse_patent_xml
from ai_analysis import analyze_patent_with_claude
from wordcloud import WordCloud

# Pharma relevance checker


def is_pharma_relevant(patent_data: dict) -> tuple[bool, str]:
    """
    Quick check if patent is pharmaceutical/drug discovery related
    
    Returns:
        (is_relevant: bool, reason: str)
    """
    
    # Combine searchable text
    title = patent_data.get('title', '').lower()
    abstract = patent_data.get('abstract', '').lower()
    ipc_codes = patent_data.get('ipc_codes', [])
    
    combined_text = f"{title} {abstract}"
    
    # Pharma-relevant IPC codes
    PHARMA_IPC_CODES = {
        'A61K',  # Preparations for medical, dental, or toilet purposes
        'A61P',  # Therapeutic activity of chemical compounds
        'C07',   # Organic chemistry (all subcodes)
        'C12',   # Biochemistry; Beer; Spirits; Wine; Vinegar; Microbiology; Enzymology
    }
    
    # Check IPC codes first (most reliable)
    if ipc_codes:
        for code in ipc_codes:
            # Check if any pharma IPC code matches
            if any(code.startswith(pharma_code) for pharma_code in PHARMA_IPC_CODES):
                return True, f"Relevant IPC code found: {code}"
    
    # Pharma-related keywords (strong signals)
    STRONG_PHARMA_KEYWORDS = [
        # Drug-related
        'pharmaceutical', 'drug', 'therapeutic', 'medicament', 'medicine',
        'therapy', 'treatment of disease', 'treatment of cancer',
        
        # Chemistry
        'compound', 'molecule', 'inhibitor', 'antagonist', 'agonist',
        'small molecule', 'chemical entity',
        
        # Biology
        'biological target', 'receptor', 'enzyme', 'kinase', 'protease',
        'antibody', 'protein', 'peptide', 'nucleic acid',
        
        # Disease
        'cancer', 'tumor', 'carcinoma', 'oncology', 'diabetes',
        'infectious disease', 'viral infection', 'bacterial infection',
        
        # Pharmacology
        'pharmacological', 'pharmacokinetic', 'bioavailability',
        'efficacy', 'toxicity', 'dosage', 'administration'
    ]
    
    # Count strong keyword matches
    strong_matches = sum(1 for keyword in STRONG_PHARMA_KEYWORDS if keyword in combined_text)
    
    if strong_matches >= 3:
        return True, f"Pharmaceutical keywords found ({strong_matches} matches)"
    
    # Non-pharma keywords (exclusions)
    NON_PHARMA_KEYWORDS = [
        # Engineering/mechanical
        'engine', 'motor', 'vehicle', 'automotive', 'mechanical',
        'welding', 'cutting', 'drilling', 'machining',
        
        # Electronics/electrical
        'circuit', 'semiconductor', 'transistor', 'integrated circuit',
        'display panel', 'led', 'oled', 'battery', 'solar cell',
        
        # Materials/construction
        'concrete', 'cement', 'steel', 'aluminum', 'alloy',
        'building', 'construction', 'structural',
        
        # Software/IT
        'software', 'algorithm', 'computer program', 'data processing',
        'neural network', 'machine learning', 'artificial intelligence',
        
        # Telecommunications
        'antenna', 'wireless', 'telecommunications', 'network protocol',
        '5g', 'wifi', 'bluetooth'
    ]
    
    # Check for non-pharma keywords
    non_pharma_matches = sum(1 for keyword in NON_PHARMA_KEYWORDS if keyword in combined_text)
    
    if non_pharma_matches >= 2:
        return False, "Non-pharmaceutical patent (engineering/electronics/IT)"
    
    # If weak pharma signals or unclear, be conservative
    if strong_matches >= 1:
        return True, f"Possibly pharmaceutical (weak signal: {strong_matches} keyword matches)"
    
    return False, "Not pharmaceutical - no relevant keywords or IPC codes found"



import matplotlib.pyplot as plt


# ==============================================================================
# DISPLAY FUNCTION - CLEAN SCIENTIFIC RESULTS
# ==============================================================================
def display_results(patent_data, analysis):
    """Display analysis results with reorganized logical flow"""
    
    st.markdown("---")
    
    
    # =============================
    # PATENT DISCLOSURE DETAILS
    # =============================
    st.markdown("### 📄 Patent Disclosure Details")
    
    st.markdown(f"**Patent Number:** `{patent_data['patent_id']}`")
    
    if patent_data.get('company'):
        st.markdown(f"**Assignee:** {patent_data['company']}")
    
    st.markdown(f"**Title:** {patent_data.get('title', 'Not available')}")
    
    if patent_data.get('filing_date'):
        st.markdown(f"**Filing Date:** {patent_data['filing_date']}")
    
    if patent_data.get('abstract'):
        st.markdown("**Abstract:**")
        st.write(patent_data['abstract'])
    
    st.markdown("---")
    
    
    # =============================
    # HELP SECTION
    # PATENT SUMMARY TABLE - SIMPLE APPROACH
    # =============================
    st.markdown("### 📊 Patent Summary")
    
    # Get biology and chemistry
    bio = analysis.get('biology', {})
    chem = analysis.get('medicinal_chemistry', {})
    
    # Build table using simple markdown - ALWAYS WORKS
    table_rows = []
    
    # Target - FULL TEXT
    if bio.get('targets'):
        target = bio['targets']  # Show all targets
        table_rows.append(f"| **Target** | {target} |")
    
    # Mechanism - FULL TEXT
    if bio.get('mechanism'):
        mechanism = bio['mechanism']  # Show complete mechanism
        table_rows.append(f"| **Mechanism** | {mechanism} |")
    
    # Chemical Class
    if chem.get('series_description'):
        chem_class = chem['series_description'].split('as')[0].strip()
        if 'compound' in chem_class.lower():
            chem_class = chem_class.replace('compounds', '').replace('compound', '').strip()
        table_rows.append(f"| **Chemical Class** | {chem_class} |")
    
    # Indication - FULL TEXT
    if bio.get('indications'):
        indication = bio['indications']  # Show all indications
        table_rows.append(f"| **Indication** | {indication} |")
    
    # Therapeutic Area
    therapeutic_area = analysis.get('therapeutic_area', 'Not specified')
    table_rows.append(f"| **Therapeutic Area** | {therapeutic_area} |")
    
    # Innovation
    innovation = analysis.get('innovation_level', 'Not assessed')
    table_rows.append(f"| **Innovation** | {innovation.title()} |")
    
    # Display as markdown table
    if table_rows:
        table_md = "| Field | Details |\n|:------|:--------|\n" + "\n".join(table_rows)
        st.markdown(table_md)
    
    st.markdown("")
    # =============================
    # WORD CLOUD VISUALIZATION
    # =============================
    st.markdown("---")
    st.markdown("### ☁️ Patent Focus Visualization")
    
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        word_text = []
        bio = analysis.get('biology', {})
        chem = analysis.get('medicinal_chemistry', {})
        
        if bio.get('targets'): word_text.append(bio['targets'])
        if bio.get('mechanism'): word_text.append(bio['mechanism'])
        if bio.get('indications'): word_text.append(bio['indications'])
        if chem.get('series_description'): word_text.append(chem['series_description'])
        if chem.get('novelty'): word_text.append(chem['novelty'])
        if analysis.get('therapeutic_area'): word_text.append(analysis['therapeutic_area'])
        
        combined_text = ' '.join(word_text)
        
        if combined_text:
            stopwords = {
                'compound', 'compounds', 'treatment', 'method', 'methods', 'use', 'uses', 'used',
                'comprising', 'include', 'includes', 'including', 'said', 'wherein', 'thereof',
                'invention', 'present', 'disclosed', 'described', 'provide', 'provides', 'provided',
                'composition', 'pharmaceutical', 'selected', 'group', 'consisting', 'example',
                'the', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from',
                'that', 'which', 'this', 'these', 'those', 'such', 'be', 'are', 'is', 'was', 'were',
                'has', 'have', 'had', 'may', 'can', 'will', 'would', 'could', 'should', 'also',
                'like', 'through', 'over', 'under', 'between', 'into', 'during', 'before', 'after',
                'specific', 'general', 'suitable', 'appropriate', 'further', 'preferably', 'particularly'
            }
            
            wc = WordCloud(width=1000, height=500, background_color='white',
                          colormap='viridis', relative_scaling=0.5, min_font_size=10,
                          max_words=40, collocations=True, stopwords=stopwords).generate(combined_text)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            plt.close()
            
            st.caption("💡 Larger words indicate key focus areas")
    except: pass
    
    st.markdown("")
    
    # EXECUTIVE SUMMARY
    # =============================
    if 'summary' in analysis and analysis['summary']:
        st.markdown("### 📝 Executive Summary")
        st.info(analysis['summary'])
        st.markdown("")
    
    # =============================
    # KEY INSIGHTS
    # =============================
    if 'key_insights' in analysis and analysis['key_insights']:
        st.markdown("### 🔑 Key Research Findings")
        for i, insight in enumerate(analysis['key_insights'], 1):
            st.markdown(f"**{i}.** {insight}")
        st.markdown("")
    
    # =============================
    # =============================
    # SCIENTIFIC SUMMARY
    # =============================
    st.markdown("### 🔬 Scientific Analysis")
    
    # Build narrative
    narrative_parts = []
    
    # Target and mechanism
    if bio.get('targets') and bio.get('mechanism'):
        target_text = bio['targets']
        mech_text = bio['mechanism']
        if mech_text.strip().endswith('.'):
            mech_text = mech_text.strip()[:-1]
        
        narrative_parts.append(
            f"This patent describes inhibitors targeting {target_text}. "
            f"The mechanism of action involves {mech_text.lower()}"
        )
    elif bio.get('targets'):
        narrative_parts.append(f"The disclosed compounds target {bio['targets']}")
    
    # Chemistry
    if chem.get('series_description') and chem.get('novelty'):
        series_text = chem['series_description']
        novelty_text = chem['novelty']
        
        if series_text.endswith('.'):
            series_text = series_text[:-1]
        if novelty_text.endswith('.'):
            novelty_text = novelty_text[:-1]
        
        narrative_parts.append(
            f"The chemical matter comprises {series_text.lower()}. "
            f"The novelty of this work lies in {novelty_text.lower()}"
        )
    
    # Therapeutic context
    if bio.get('indications'):
        therapeutic_area = analysis.get('therapeutic_area', '')
        indication_text = bio['indications']
        
        if therapeutic_area:
            narrative_parts.append(
                f"The therapeutic application is focused on {indication_text.lower()}, "
                f"positioned within the {therapeutic_area.lower()} domain"
            )
        else:
            narrative_parts.append(f"These compounds are being developed for {indication_text.lower()}")
    
    # Innovation
    innovation = analysis.get('innovation_level', '')
    if innovation == 'BREAKTHROUGH':
        narrative_parts.append(
            "This represents a potentially breakthrough innovation with novel mechanism of action "
            "and significant differentiation from existing therapeutic options"
        )
    elif innovation == 'INCREMENTAL':
        narrative_parts.append(
            "From an innovation standpoint, this work represents an incremental advancement, "
            "building upon and optimizing existing therapeutic modalities"
        )
    
    # Display
    if narrative_parts:
        full_narrative = ". ".join(narrative_parts)
        if not full_narrative.endswith('.'):
            full_narrative += "."
        
        st.info(full_narrative)
        
        # Confidence
        bio_conf = bio.get('confidence', 'LOW')
        chem_conf = chem.get('confidence', 'LOW')
        
        if bio_conf != 'HIGH' or chem_conf != 'HIGH':
            conf_text = []
            if bio_conf != 'HIGH':
                conf_text.append(f"Biology: {bio_conf}")
            if chem_conf != 'HIGH':
                conf_text.append(f"Chemistry: {chem_conf}")
            
            st.caption(f"Assessment Confidence: {', '.join(conf_text)}")
    
    st.markdown("")
    
    # =============================
    # EXPORT FUNCTIONALITY - Direct download links
    # =============================
    st.markdown("---")
    
    st.markdown("### 📥 Export Analysis")
    st.caption("💡 Click to download file directly")
    
    # Generate all export formats
    export_md = generate_export_report_markdown(patent_data, analysis)
    export_html = generate_export_report_html(patent_data, analysis)
    export_csv = generate_export_data_csv(patent_data, analysis)
    
    # Create data URLs with download attribute
    import base64
    
    # Base64 encode for data URLs
    md_b64 = base64.b64encode(export_md.encode()).decode()
    html_b64 = base64.b64encode(export_html.encode()).decode()
    csv_b64 = base64.b64encode(export_csv.encode()).decode()
    
    patent_id = patent_data['patent_id']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'''
        <a href="data:text/markdown;base64,{md_b64}" 
           download="{patent_id}_report.md"
           style="display: inline-block; width: 100%; padding: 0.5rem 1rem; background-color: #FF4B4B; color: white; text-align: center; text-decoration: none; border-radius: 0.25rem; font-weight: 500;">
            📄 Markdown
        </a>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <a href="data:text/html;base64,{html_b64}" 
           download="{patent_id}_report.html"
           style="display: inline-block; width: 100%; padding: 0.5rem 1rem; background-color: #FF4B4B; color: white; text-align: center; text-decoration: none; border-radius: 0.25rem; font-weight: 500;">
            📄 HTML/PDF
        </a>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <a href="data:text/csv;base64,{csv_b64}" 
           download="{patent_id}_data.csv"
           style="display: inline-block; width: 100%; padding: 0.5rem 1rem; background-color: #FF4B4B; color: white; text-align: center; text-decoration: none; border-radius: 0.25rem; font-weight: 500;">
            📊 CSV Data
        </a>
        ''', unsafe_allow_html=True)
    
    st.caption("📌 **Files download directly** | Open HTML in browser, then Print → Save as PDF for professional reports")


def generate_export_report_markdown(patent_data: Dict, analysis: Dict) -> str:
    """Generate markdown report matching display order and format"""
    
    bio = analysis.get('biology', {})
    chem = analysis.get('medicinal_chemistry', {})
    
    report = f"""# Patent Analysis Report

---

## 📄 Patent Disclosure Details

**Patent Number:** `{patent_data['patent_id']}`

**Assignee:** {patent_data.get('company', 'Not available')}

**Title:** {patent_data.get('title', 'Not available')}

**Filing Date:** {patent_data.get('filing_date', 'Not available')}

**Abstract:**

{patent_data.get('abstract', 'Not available')}

---

## 📊 Patent Summary

| Field | Details |
|:------|:--------|
| **Target** | {bio.get('targets', 'Not specified')} |
| **Mechanism** | {bio.get('mechanism', 'Not specified')} |
| **Chemical Class** | {chem.get('series_description', 'Not specified').split('as')[0].strip()} |
| **Indication** | {bio.get('indications', 'Not specified')} |
| **Therapeutic Area** | {analysis.get('therapeutic_area', 'Not specified')} |
| **Innovation** | {analysis.get('innovation_level', 'Not specified').title()} |

---

## 📝 Executive Summary

{analysis.get('summary', 'Not available')}

---

## 🔑 Key Research Findings

"""
    
    # Add key insights
    if 'key_insights' in analysis and analysis['key_insights']:
        for i, insight in enumerate(analysis['key_insights'], 1):
            report += f"{i}. {insight}\n"
    else:
        report += "Not available\n"
    
    report += "\n---\n\n## 🔬 Scientific Analysis\n\n"
    
    # Build the narrative like display
    narrative_parts = []
    
    if bio.get('targets') and bio.get('mechanism'):
        mech_text = bio['mechanism']
        if mech_text.strip().endswith('.'):
            mech_text = mech_text.strip()[:-1]
        narrative_parts.append(
            f"This patent describes inhibitors targeting {bio['targets']}. "
            f"The mechanism of action involves {mech_text.lower()}"
        )
    
    if chem.get('series_description') and chem.get('novelty'):
        series_text = chem['series_description']
        novelty_text = chem['novelty']
        if series_text.endswith('.'): series_text = series_text[:-1]
        if novelty_text.endswith('.'): novelty_text = novelty_text[:-1]
        narrative_parts.append(
            f"The chemical matter comprises {series_text.lower()}. "
            f"The novelty of this work lies in {novelty_text.lower()}"
        )
    
    if bio.get('indications'):
        therapeutic_area = analysis.get('therapeutic_area', '')
        if therapeutic_area:
            narrative_parts.append(
                f"The therapeutic application is focused on {bio['indications'].lower()}, "
                f"positioned within the {therapeutic_area.lower()} domain"
            )
    
    innovation = analysis.get('innovation_level', '')
    if innovation == 'INCREMENTAL':
        narrative_parts.append(
            "From an innovation standpoint, this work represents an incremental advancement, "
            "building upon and optimizing existing therapeutic modalities"
        )
    elif innovation == 'BREAKTHROUGH':
        narrative_parts.append(
            "This represents a potentially breakthrough innovation with novel mechanism of action "
            "and significant differentiation from existing therapeutic options"
        )
    
    if narrative_parts:
        report += ". ".join(narrative_parts)
        if not report.endswith('.'):
            report += "."
    
    # Add confidence if needed
    bio_conf = bio.get('confidence', 'LOW')
    chem_conf = chem.get('confidence', 'LOW')
    if bio_conf != 'HIGH' or chem_conf != 'HIGH':
        conf_parts = []
        if bio_conf != 'HIGH': conf_parts.append(f"Biology: {bio_conf}")
        if chem_conf != 'HIGH': conf_parts.append(f"Chemistry: {chem_conf}")
        report += f"\n\n*Assessment Confidence: {', '.join(conf_parts)}*"
    
    report += "\n\n---\n\n## 📥 Competitive Intelligence Recommendations\n\n"
    
    # Add recommendations based on innovation level
    if innovation == 'BREAKTHROUGH':
        report += """**Strategic Priority:** HIGH ⚠️

**Recommended Actions:**
- Conduct immediate freedom-to-operate (FTO) analysis
- Assess potential licensing or partnership opportunities
- Monitor for subsequent filings in this series
- Evaluate impact on your development pipeline
- High priority for detailed claim analysis
"""
    elif innovation == 'INCREMENTAL':
        report += """**Strategic Priority:** MEDIUM

**Recommended Actions:**
- Monitor for market entry timelines
- Track clinical development progress
- Assess differentiation vs. existing therapies
- Evaluate commercial threat level
- Medium priority for detailed analysis
"""
    else:
        report += """**Strategic Priority:** LOW

**Recommended Actions:**
- Track as part of routine surveillance
- Low immediate competitive threat
- Review during periodic portfolio updates
"""
    
    report += f"""
---

**Generated:** {datetime.now().strftime("%B %d, %Y at %H:%M")}  
**Platform:** Patent Research Platform (AI-Powered by Claude)

*This report was generated using AI analysis. Please verify critical details with the original patent document.*
"""
    
    return report



def generate_export_report_html(patent_data: Dict, analysis: Dict) -> str:
    """Generate HTML report matching display order and format"""
    
    bio = analysis.get('biology', {})
    chem = analysis.get('medicinal_chemistry', {})
    innovation = analysis.get('innovation_level', '')
    
    # Build narrative like display
    narrative_parts = []
    if bio.get('targets') and bio.get('mechanism'):
        mech_text = bio['mechanism']
        if mech_text.strip().endswith('.'): mech_text = mech_text.strip()[:-1]
        narrative_parts.append(
            f"This patent describes inhibitors targeting {bio['targets']}. "
            f"The mechanism of action involves {mech_text.lower()}"
        )
    
    if chem.get('series_description') and chem.get('novelty'):
        series = chem['series_description']
        novelty = chem['novelty']
        if series.endswith('.'): series = series[:-1]
        if novelty.endswith('.'): novelty = novelty[:-1]
        narrative_parts.append(
            f"The chemical matter comprises {series.lower()}. "
            f"The novelty of this work lies in {novelty.lower()}"
        )
    
    if bio.get('indications'):
        therapeutic_area = analysis.get('therapeutic_area', '')
        if therapeutic_area:
            narrative_parts.append(
                f"The therapeutic application is focused on {bio['indications'].lower()}, "
                f"positioned within the {therapeutic_area.lower()} domain"
            )
    
    if innovation == 'INCREMENTAL':
        narrative_parts.append(
            "From an innovation standpoint, this work represents an incremental advancement"
        )
    elif innovation == 'BREAKTHROUGH':
        narrative_parts.append(
            "This represents a potentially breakthrough innovation"
        )
    
    narrative = ". ".join(narrative_parts)
    if narrative and not narrative.endswith('.'):
        narrative += "."
    
    # Confidence
    bio_conf = bio.get('confidence', 'LOW')
    chem_conf = chem.get('confidence', 'LOW')
    conf_html = ""
    if bio_conf != 'HIGH' or chem_conf != 'HIGH':
        conf_parts = []
        if bio_conf != 'HIGH': conf_parts.append(f"Biology: {bio_conf}")
        if chem_conf != 'HIGH': conf_parts.append(f"Chemistry: {chem_conf}")
        conf_html = f"<p><em>Assessment Confidence: {', '.join(conf_parts)}</em></p>"
    
    priority_class = 'priority-high' if innovation == 'BREAKTHROUGH' else ('priority-medium' if innovation == 'INCREMENTAL' else 'priority-low')
    

    # Generate word cloud for HTML export
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        import io
        import base64
        
        # Collect text
        word_text = []
        if bio.get('targets'): word_text.append(bio['targets'])
        if bio.get('mechanism'): word_text.append(bio['mechanism'])
        if bio.get('indications'): word_text.append(bio['indications'])
        if chem.get('series_description'): word_text.append(chem['series_description'])
        if chem.get('novelty'): word_text.append(chem['novelty'])
        if analysis.get('therapeutic_area'): word_text.append(analysis['therapeutic_area'])
        
        combined_text = ' '.join(word_text)
        
        if combined_text:
            # Stopwords
            stopwords = {
                'compound', 'compounds', 'treatment', 'method', 'methods', 'use', 'uses', 'used',
                'comprising', 'include', 'includes', 'including', 'said', 'wherein', 'thereof',
                'invention', 'present', 'disclosed', 'described', 'provide', 'provides', 'provided',
                'composition', 'pharmaceutical', 'selected', 'group', 'consisting', 'example',
                'the', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from',
                'that', 'which', 'this', 'these', 'those', 'such', 'be', 'are', 'is', 'was', 'were',
                'has', 'have', 'had', 'may', 'can', 'will', 'would', 'could', 'should', 'also',
                'like', 'through', 'over', 'under', 'between', 'into', 'during', 'before', 'after',
                'specific', 'general', 'suitable', 'appropriate', 'further', 'preferably', 'particularly'
            }
            
            # Generate word cloud
            wc = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='viridis', 
                relative_scaling=0.5, 
                min_font_size=10,
                max_words=40, 
                collocations=True, 
                stopwords=stopwords
            ).generate(combined_text)
            
            # Convert to image
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            
            # Save to base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close()
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode()
            
            wordcloud_html = f"""
    <h2>☁️ Patent Focus Visualization</h2>
    <div class="section">
        <img src="data:image/png;base64,{img_base64}" alt="Word Cloud" style="width: 100%; max-width: 800px; height: auto;">
        <p style="text-align: center; color: #666; font-size: 12px; margin-top: 10px;">
            💡 Larger words indicate key focus areas of the patent
        </p>
    </div>
    """
        else:
            wordcloud_html = ""
    except:
        wordcloud_html = ""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #1f77b4;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c5aa0;
            margin-top: 30px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }}
        .header {{
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid #1f77b4;
        }}
        .highlight {{
            background-color: #fff9e6;
            padding: 10px;
            border-radius: 3px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f0f2f6;
            font-weight: 600;
        }}
        .priority-high {{ color: #d32f2f; font-weight: bold; }}
        .priority-medium {{ color: #f57c00; font-weight: bold; }}
        .priority-low {{ color: #388e3c; font-weight: bold; }}
        ul {{ line-height: 1.8; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <h1>Patent Analysis Report</h1>
    <div class="header">
        <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
        <p><strong>Platform:</strong> Patent Research Platform (AI-Powered by Claude)</p>
    </div>
    
    <h2>📄 Patent Disclosure Details</h2>
    <div class="section">
        <p><strong>Patent Number:</strong> <code>{patent_data['patent_id']}</code></p>
        <p><strong>Assignee:</strong> {patent_data.get('company', 'Not available')}</p>
        <p><strong>Title:</strong> {patent_data.get('title', 'Not available')}</p>
        <p><strong>Filing Date:</strong> {patent_data.get('filing_date', 'Not available')}</p>
        <p><strong>Abstract:</strong><br>{patent_data.get('abstract', 'Not available')}</p>
    </div>
    
    <h2>📊 Patent Summary</h2>
    <div class="section">
        <table>
            <tr><th>Field</th><th>Details</th></tr>
            <tr><td><strong>Target</strong></td><td>{bio.get('targets', 'Not specified')}</td></tr>
            <tr><td><strong>Mechanism</strong></td><td>{bio.get('mechanism', 'Not specified')}</td></tr>
            <tr><td><strong>Chemical Class</strong></td><td>{chem.get('series_description', 'Not specified').split('as')[0].strip()}</td></tr>
            <tr><td><strong>Indication</strong></td><td>{bio.get('indications', 'Not specified')}</td></tr>
            <tr><td><strong>Therapeutic Area</strong></td><td>{analysis.get('therapeutic_area', 'Not specified')}</td></tr>
            <tr><td><strong>Innovation</strong></td><td><span class='{priority_class}'>{innovation.title()}</span></td></tr>
        </table>
    </div>
    
{wordcloud_html}
        <h2>📝 Executive Summary</h2>
    <div class="section highlight">
        <p>{analysis.get('summary', 'Not available')}</p>
    </div>
    
    <h2>🔑 Key Research Findings</h2>
    <div class="section">
        <ul>
"""
    
    if 'key_insights' in analysis and analysis['key_insights']:
        for insight in analysis['key_insights']:
            html += f"            <li>{insight}</li>\n"
    else:
        html += "            <li>Not available</li>\n"
    
    html += f"""        </ul>
    </div>
    
    <h2>🔬 Scientific Analysis</h2>
    <div class="section">
        <p>{narrative}</p>
        {conf_html}
    </div>
    
    <div style="page-break-before: always;"></div>
    
    <h2>📥 Competitive Intelligence Recommendations</h2>
    <div class="section highlight">
"""
    
    if innovation == 'BREAKTHROUGH':
        html += """        <p><strong>Strategic Priority:</strong> <span class="priority-high">HIGH ⚠️</span></p>
        <p><strong>Recommended Actions:</strong></p>
        <ul>
            <li>Conduct immediate freedom-to-operate (FTO) analysis</li>
            <li>Assess potential licensing or partnership opportunities</li>
            <li>Monitor for subsequent filings in this series</li>
            <li>Evaluate impact on your development pipeline</li>
            <li>High priority for detailed claim analysis</li>
        </ul>
"""
    elif innovation == 'INCREMENTAL':
        html += """        <p><strong>Strategic Priority:</strong> <span class="priority-medium">MEDIUM</span></p>
        <p><strong>Recommended Actions:</strong></p>
        <ul>
            <li>Monitor for market entry timelines</li>
            <li>Track clinical development progress</li>
            <li>Assess differentiation vs. existing therapies</li>
            <li>Evaluate commercial threat level</li>
            <li>Medium priority for detailed analysis</li>
        </ul>
"""
    else:
        html += """        <p><strong>Strategic Priority:</strong> <span class="priority-low">LOW</span></p>
        <p><strong>Recommended Actions:</strong></p>
        <ul>
            <li>Track as part of routine surveillance</li>
            <li>Low immediate competitive threat</li>
            <li>Review during periodic portfolio updates</li>
        </ul>
"""
    
    html += f"""    </div>
    
    <hr style="margin-top: 40px;">
    <p style="text-align: center; color: #666; font-size: 12px;">
        Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")} | 
        Patent Research Platform | 
        AI-Powered by Claude
    </p>
    <p style="text-align: center; color: #999; font-size: 11px; margin-top: 10px;">
        💡 To convert to PDF: Open this file in your browser → Print → Save as PDF
    </p>
</body>
</html>"""
    
    return html



def generate_export_data_csv(patent_data: Dict, analysis: Dict) -> str:
    """Generate a CSV with structured data for spreadsheet analysis"""
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Patent Analysis Data Export'])
    writer.writerow(['Generated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    # Patent Information Section
    writer.writerow(['PATENT INFORMATION'])
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Patent Number', patent_data['patent_id']])
    writer.writerow(['Title', patent_data.get('title', 'Not available')])
    writer.writerow(['Assignee', patent_data.get('company', 'Not available')])
    writer.writerow(['Abstract', patent_data.get('abstract', 'Not available')])
    writer.writerow([])
    
    # Executive Summary
    writer.writerow(['EXECUTIVE SUMMARY'])
    writer.writerow(['Summary', analysis.get('summary', 'Not available')])
    writer.writerow([])
    
    # Key Insights
    writer.writerow(['KEY RESEARCH FINDINGS'])
    writer.writerow(['#', 'Finding'])
    if 'key_insights' in analysis and analysis['key_insights']:
        for i, insight in enumerate(analysis['key_insights'], 1):
            writer.writerow([i, insight])
    else:
        writer.writerow([1, 'Not available'])
    writer.writerow([])
    
    # Biology Section
    writer.writerow(['BIOLOGICAL ANALYSIS'])
    writer.writerow(['Field', 'Value'])
    if 'biology' in analysis:
        bio = analysis['biology']
        writer.writerow(['Molecular Targets', bio.get('targets', 'Not specified')])
        writer.writerow(['Mechanism of Action', bio.get('mechanism', 'Not specified')])
        writer.writerow(['Therapeutic Indications', bio.get('indications', 'Not specified')])
        writer.writerow(['Assessment Confidence', bio.get('confidence', 'Not specified')])
    else:
        writer.writerow(['Status', 'Not available'])
    writer.writerow([])
    
    # Chemistry Section
    writer.writerow(['CHEMICAL ANALYSIS'])
    writer.writerow(['Field', 'Value'])
    if 'medicinal_chemistry' in analysis:
        chem = analysis['medicinal_chemistry']
        writer.writerow(['Chemical Series', chem.get('series_description', 'Not specified')])
        writer.writerow(['Structural Features', chem.get('key_features', 'Not specified')])
        if chem.get('novelty') and 'not specified' not in chem.get('novelty', '').lower():
            writer.writerow(['Novelty Assessment', chem.get('novelty', 'Not specified')])
        writer.writerow(['Assessment Confidence', chem.get('confidence', 'Not specified')])
    else:
        writer.writerow(['Status', 'Not available'])
    writer.writerow([])
    
    # Strategic Assessment
    writer.writerow(['STRATEGIC ASSESSMENT'])
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Therapeutic Area', analysis.get('therapeutic_area', 'Not specified')])
    writer.writerow(['Innovation Assessment', analysis.get('innovation_level', 'Not specified')])
    
    # Map innovation level to priority
    innovation = analysis.get('innovation_level', '')
    if innovation == 'BREAKTHROUGH':
        writer.writerow(['Strategic Priority', 'HIGH'])
        writer.writerow(['Recommended Action', 'Immediate FTO analysis and partnership assessment'])
    elif innovation == 'INCREMENTAL':
        writer.writerow(['Strategic Priority', 'MEDIUM'])
        writer.writerow(['Recommended Action', 'Monitor market entry and track development'])
    else:
        writer.writerow(['Strategic Priority', 'LOW'])
        writer.writerow(['Recommended Action', 'Routine surveillance and tracking'])
    
    writer.writerow([])
    writer.writerow(['METADATA'])
    writer.writerow(['Analysis Date', datetime.now().strftime("%Y-%m-%d")])
    writer.writerow(['Analysis Time', datetime.now().strftime("%H:%M:%S")])
    writer.writerow(['Platform', 'Patent Research Platform'])
    writer.writerow(['AI Model', 'Claude (Anthropic)'])
    
    return output.getvalue()


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Patent Intelligence Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    h1 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    h3 {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🔬 Patent Intelligence Platform")
st.caption("Pharmaceutical Competitive Intelligence | AI-Powered Analysis")
st.markdown("---")

# ==============================================================================
# SIDEBAR: UNIFIED TRACKED PATENTS
# ==============================================================================

with st.sidebar:
    st.markdown("# 🔬 Patent Intelligence")
    st.caption("AI-powered competitive intelligence")
    
    st.markdown("---")
    
    st.markdown("### 📚 Quick Resources")
    st.markdown("[🔍 Google Patents](https://patents.google.com)")
    st.caption("Search patent database")
    st.markdown("[🌍 WIPO Patentscope](https://patentscope.wipo.int)")
    st.caption("International patents")
    st.markdown("[🇪🇺 Espacenet](https://worldwide.espacenet.com)")
    st.caption("European patent office")
    st.markdown("[🇺🇸 USPTO](https://www.uspto.gov)")
    st.caption("US patent office")
    
    st.markdown("---")
    
    st.markdown("### 💡 Quick Tips")
    st.caption("• Enter WO patent numbers for instant analysis")
    st.caption("• Upload XML for older patents")
    st.caption("• Analysis takes ~30 seconds")
    
    st.markdown("---")
    st.caption("💰 **Cost:** ~$0.02-0.05 per analysis")


tab1, tab2 = st.tabs(["🔍 Analyze Patent", "📤 Upload Document"])

# =============================
# TAB 1: ANALYZE PATENT
# =============================
with tab1:
    st.markdown("### Patent Analysis")
    st.caption("Enter WO patent number for instant AI-powered analysis")
    st.caption("⚠️ **Note:** Direct analysis works best for WO patents from 2010 onwards. For other patent types (US, EP) or older patents, use 'Upload Document' tab.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        default_value = st.session_state.get('patent_to_analyze', '')
        
        patent_number = st.text_input(
            "Patent Number",
            value=default_value,
            placeholder="e.g., WO2024033280, WO2025128873",
            help="Enter WO patent publication number",
            key="patent_input",
            label_visibility="collapsed"
        )
    
    with col2:
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True, key="fetch_btn")
    
    # Auto-analyze if triggered from sidebar
    auto_analyze = st.session_state.get('auto_analyze', False)
    
    # Check if we have cached results for this patent
    has_cached_results = False
    if patent_number and 'last_patent_data' in st.session_state and 'last_analysis' in st.session_state:
        if patent_number.upper() == st.session_state.last_patent_data.get('patent_id', '').upper():
            has_cached_results = True
    
    # Show cached results if available (prevents re-analysis on download button clicks)
    if has_cached_results and not analyze_button and not auto_analyze:
        display_results(st.session_state.last_patent_data, st.session_state.last_analysis)
    
    # Only run analysis if button clicked or auto-analyze triggered
    elif analyze_button or auto_analyze:
        # Clear auto-analyze flag
        if auto_analyze:
            st.session_state.auto_analyze = False
        
        if not patent_number:
            st.error("⚠️ Please enter a patent number")
            st.stop()
        
        if not patent_number.upper().startswith('WO'):
            st.error("⚠️ Please enter a **WO patent number** (e.g., WO2024033280)")
            st.stop()
        
        # Get API key from environment only
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        if not api_key:
            st.error("⚠️ **API Key Required**")
            st.info("**For deployment:** Set `ANTHROPIC_API_KEY` in Streamlit Cloud secrets.\n\n**For local use:** Set environment variable:\n```bash\nexport ANTHROPIC_API_KEY='your-key-here'\n```")
            st.stop()
        
        # Fetch patent
        from google_patents_fetcher import fetch_patent_from_google
        
        with st.spinner(f"🌐 Retrieving patent data for {patent_number}..."):
            patent_data = fetch_patent_from_google(patent_number)
        
        # Error handling AFTER spinner
        if not patent_data:
            st.error(f"❌ Unable to retrieve patent {patent_number}")
            
            # Extract year from patent number to give better guidance
            try:
                year = int(patent_number[2:6])  # WO2006... -> 2006
                if year < 2010:
                    st.warning(f"⚠️ **Older Patent Detected (Year: {year})**\n\nPatents before 2010 may have limited data availability on Google Patents. Try the 'Upload Document' tab instead.")
                else:
                    st.info("💡 **Troubleshooting:**\n- Check patent number format (e.g., WO2024033280)\n- Try the 'Upload Document' tab to upload XML from WIPO\n- Some patents may have restricted access")
            except:
                st.info("💡 **Alternative:** Use the 'Upload Document' tab to upload patent XML file from WIPO")
            
            # Add link to WIPO
            st.markdown(f"🔗 **Search on WIPO:** [Open {patent_number} on WIPO Patentscope](https://patentscope.wipo.int/search/en/detail.jsf?docId={patent_number})")
            st.stop()
        
        st.success(f"✅ Patent data retrieved successfully")
        
        # Check if patent is pharmaceutical/drug discovery related
        is_relevant, relevance_reason = is_pharma_relevant(patent_data)
        
        if not is_relevant:
            st.warning(f"⚠️ **Non-Pharmaceutical Patent Detected**")
            st.info(f"**Reason:** {relevance_reason}\n\nThis platform is optimized for pharmaceutical and drug discovery patents. This patent appears to be outside that domain.")
            
            # Show only basic patent details
            st.markdown("---")
            st.markdown("### 📄 Patent Disclosure Details")
            st.markdown(f"**Patent Number:** `{patent_data['patent_id']}`")
            
            if patent_data.get('company'):
                st.markdown(f"**Assignee:** {patent_data['company']}")
            
            st.markdown(f"**Title:** {patent_data.get('title', 'Not available')}")
            
            if patent_data.get('filing_date'):
                st.markdown(f"**Filing Date:** {patent_data['filing_date']}")
            
            if patent_data.get('abstract'):
                st.markdown("**Abstract:**")
                st.write(patent_data['abstract'])
            
            if patent_data.get('ipc_codes'):
                st.markdown(f"**IPC Codes:** {', '.join(patent_data['ipc_codes'])}")
            
            st.markdown("---")
            st.info("💡 **Tip:** This tool works best with patents related to:\n- Small molecule drugs\n- Biologics (antibodies, peptides)\n- Drug targets and mechanisms\n- Pharmaceutical formulations\n- Medicinal chemistry")
            
            st.stop()  # Don't proceed with AI analysis
        
        # If relevant, show confirmation
        st.success(f"✅ Pharmaceutical patent confirmed: {relevance_reason}")
        
        
        # Analyze with AI
        with st.spinner("🤖 Performing AI analysis..."):
            analysis = analyze_patent_with_claude(patent_data, api_key)
        
        st.success("✅ Analysis complete")
        
        # Store results in session state to persist across reruns (for export buttons)
        st.session_state.last_patent_data = patent_data
        st.session_state.last_analysis = analysis
        
        # Display results
        display_results(patent_data, analysis)

# =============================
# TAB 2: UPLOAD DOCUMENT
# =============================
with tab2:
    st.markdown("### Document Upload Analysis")
    st.caption("Upload patent XML file for comprehensive analysis - supports WO, US, EP, and all other patent types")

    uploaded_file = st.file_uploader(
        "Select Patent XML File",
        type=['xml'],
        help="Download XML from WIPO Patentscope"
    )

    if uploaded_file is not None:
        st.success(f"✅ File loaded: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        # Get API key from environment only
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        if not api_key:
            st.error("⚠️ **API Key Required**")
            st.info("**For deployment:** Set `ANTHROPIC_API_KEY` in Streamlit Cloud secrets.\n\n**For local use:** Set environment variable:\n```bash\nexport ANTHROPIC_API_KEY='your-key-here'\n```")
            st.stop()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button("🤖 Analyze Document", type="primary", use_container_width=True, key="upload_btn")
        
        # Check if we have cached results
        has_cached_results = 'last_patent_data' in st.session_state and 'last_analysis' in st.session_state
        
        # Show cached results if available (prevents re-analysis on download)
        if has_cached_results and not analyze_button:
            display_results(st.session_state.last_patent_data, st.session_state.last_analysis)
        
        # Only analyze if button clicked
        elif analyze_button:
            xml_bytes = uploaded_file.read()
            
            with st.spinner("🔍 Parsing document..."):
                patent_data = parse_patent_xml(xml_bytes)
                
                if patent_data.get('patent_id') == 'Not available':
                    st.error("❌ Unable to parse XML file")
                    st.stop()
            
            st.success("✅ Document parsed successfully")
            
            with st.spinner("🤖 Performing AI analysis..."):
                analysis = analyze_patent_with_claude(patent_data, api_key)
            
            st.success("✅ Analysis complete")
            
            # Store in session state
            st.session_state.last_patent_data = patent_data
            st.session_state.last_analysis = analysis
            
            display_results(patent_data, analysis)
    else:
        st.info("👆 Upload a patent XML file to begin analysis")
        st.caption("Download XML files from [WIPO Patentscope](https://patentscope.wipo.int/)")

# Footer
st.markdown("---")
st.caption("🔬 Patent Intelligence Platform | AI-Powered by Claude | Pharmaceutical Competitive Intelligence")
