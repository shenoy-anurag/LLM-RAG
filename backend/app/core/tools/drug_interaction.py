import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel
import os


OPENFDA_API_KEY = os.getenv("FDA_API_KEY", "")

BASE_URL = "https://api.fda.gov/drug/label.json"


def _make_api_request(url: str, params: dict) -> Optional[dict]:
    """Make request to OpenFDA API with optional API key."""
    request_params = params.copy()
    if OPENFDA_API_KEY:
        request_params["api_key"] = OPENFDA_API_KEY
    
    try:
        response = requests.get(url, params=request_params, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def _get_drug_label(drug_name: str) -> List[Dict[str, Any]]:
    """Get drug label information from OpenFDA."""
    search_query = f'openfda.brand_name:"{drug_name}"+OR+openfda.generic_name:"{drug_name}"'
    
    params = {
        "search": search_query,
        "limit": 5,
    }
    
    data = _make_api_request(BASE_URL, params)
    if data and "results" in data:
        return data["results"]
    return []


def _extract_relevant_sections(label: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant interaction-related sections from drug label."""
    sections = {}
    
    relevant_fields = [
        ("drug_interactions", "Drug Interactions"),
        ("contraindications", "Contraindications"),
        ("warnings", "Warnings"),
        ("precautions", "Precautions"),
        ("boxed_warning", "Boxed Warning"),
        ("adverse_reactions", "Adverse Reactions"),
        ("use_in_specific_populations", "Use in Specific Populations"),
    ]
    
    for field, display_name in relevant_fields:
        if field in label and label[field]:
            sections[display_name] = label[field]
    
    return sections


def _check_keyword_interactions(drug1_info: Dict[str, Any], drug2_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check for keyword-based interaction warnings between two drugs."""
    interactions = []
    
    drug1_name = drug1_info.get("name", "").lower()
    drug2_name = drug2_info.get("name", "").lower()
    
    for section_name, content in drug1_info.get("sections", {}).items():
        if isinstance(content, list):
            content_text = " ".join(str(c) for c in content)
        else:
            content_text = str(content)
        
        content_lower = content_text.lower()
        
        if drug2_name in content_lower:
            interactions.append({
                "drugs": [drug1_info["name"], drug2_name.title()],
                "section": section_name,
                "description": content_text[:500],
                "severity": _assess_severity(section_name, content_text)
            })
    
    return interactions


def _assess_severity(section: str, content: str) -> str:
    """Assess the severity based on the section type."""
    content_lower = content.lower()
    
    high_severity_keywords = ["serious", "severe", "life-threatening", "death", "fatal", "major"]
    medium_severity_keywords = ["moderate", "increased", "may increase", "could increase"]
    
    if "boxed warning" in section.lower() or "contraindications" in section.lower():
        return "HIGH - Contraindicated"
    
    if any(kw in content_lower for kw in high_severity_keywords):
        return "HIGH"
    elif any(kw in content_lower for kw in medium_severity_keywords):
        return "MODERATE"
    
    return "LOW"


@tool
def check_drug_interactions(drugs: List[str]) -> str:
    """
    Check for interactions between multiple medications using the OpenFDA Drug Label API.
    
    Use this tool when a user asks about drug interactions, combining medications,
    or safety of taking multiple drugs together.
    
    Args:
        drugs: List of drug names to check for interactions (e.g., ["Aspirin", "Warfarin"])
    
    Returns:
        A formatted string describing any interactions found between the drugs.
    """
    if not drugs or len(drugs) < 2:
        return "Please provide at least two drugs to check for interactions."
    
    results = []
    results.append(f"Drug Interaction Check for: {', '.join(drugs)}")
    results.append("=" * 60)
    results.append("Source: FDA Drug Labeling Database (openFDA)")
    results.append("")
    
    drug_labels = {}
    
    for drug in drugs:
        labels = _get_drug_label(drug)
        if labels:
            drug_labels[drug] = {
                "name": drug,
                "labels": labels,
                "sections": _extract_relevant_sections(labels[0])
            }
        else:
            drug_labels[drug] = {
                "name": drug,
                "labels": [],
                "sections": {}
            }
    
    all_interactions = []
    
    for i, drug1 in enumerate(drugs):
        for drug2 in drugs[i+1:]:
            if drug_labels[drug1]["sections"] or drug_labels[drug2]["sections"]:
                interactions = _check_keyword_interactions(
                    drug_labels[drug1],
                    drug_labels[drug2]
                )
                all_interactions.extend(interactions)
                
                reverse_interactions = _check_keyword_interactions(
                    drug_labels[drug2],
                    drug_labels[drug1]
                )
                all_interactions.extend(reverse_interactions)
    
    if all_interactions:
        results.append(f"\n⚠️  Found {len(all_interactions)} potential interaction(s):\n")
        
        seen = set()
        for interaction in all_interactions:
            key = (interaction["drugs"][0].lower(), interaction["drugs"][1].lower(), interaction["section"])
            if key in seen:
                continue
            seen.add(key)
            
            results.append(f"Drugs: {' + '.join(interaction['drugs'])}")
            results.append(f"Section: {interaction['section']}")
            results.append(f"Severity: {interaction['severity']}")
            
            desc = interaction["description"]
            if len(desc) > 300:
                desc = desc[:300] + "..."
            results.append(f"Details: {desc}")
            results.append("-" * 50)
    else:
        results.append("\nNo specific interactions found in FDA labeling.")
        results.append("\nNote: Always consult a healthcare provider for medication safety.")
    
    results.append("\n" + "=" * 60)
    results.append("DISCLAIMER: This information is from FDA labeling and may not be")
    results.append("comprehensive. Consult a healthcare professional before combining medications.")
    
    return "\n".join(results)


@tool
def get_drug_info(drug_name: str) -> str:
    """
    Get detailed information about a single drug using the OpenFDA Drug Label API.
    
    Use this tool when a user asks for information about a specific medication,
    such as what a drug is used for, its side effects, or general details.
    
    Args:
        drug_name: The name of the drug (e.g., "Aspirin", "Warfarin")
    
    Returns:
        Formatted information about the drug.
    """
    if not drug_name:
        return "Please provide a drug name."
    
    labels = _get_drug_label(drug_name)
    
    if not labels:
        return f"No FDA labeling information found for: {drug_name}"
    
    results = []
    results.append(f"Drug Information: {drug_name}")
    results.append("=" * 50)
    results.append("Source: FDA Drug Labeling Database (openFDA)")
    results.append("")
    
    for i, label in enumerate(labels[:3]):
        if i > 0:
            results.append("-" * 30)
        
        openfda = label.get("openfda", {})
        
        if openfda.get("brand_name"):
            results.append(f"Brand Name(s): {', '.join(openfda['brand_name'][:5])}")
        
        if openfda.get("generic_name"):
            results.append(f"Generic Name(s): {', '.join(openfda['generic_name'][:5])}")
        
        if openfda.get("manufacturer_name"):
            results.append(f"Manufacturer: {openfda['manufacturer_name'][0]}")
        
        if openfda.get("product_type"):
            results.append(f"Product Type: {', '.join(openfda['product_type'][:3])}")
        
        sections = _extract_relevant_sections(label)
        
        if sections:
            results.append("")
            results.append("Key Label Information:")
            
            if "Indications and Usage" in sections:
                usage = sections["Indications and Usage"]
                if isinstance(usage, list) and usage:
                    results.append(f"  Uses: {usage[0][:300]}...")
            
            if "Drug Interactions" in sections:
                interactions = sections["Drug Interactions"]
                if isinstance(interactions, list) and interactions:
                    results.append(f"  Drug Interactions: {interactions[0][:300]}...")
            
            if "Contraindications" in sections:
                contraindications = sections["Contraindications"]
                if isinstance(contraindications, list) and contraindications:
                    results.append(f"  Contraindications: {contraindications[0][:300]}...")
            
            if "Warnings" in sections:
                warnings = sections["Warnings"]
                if isinstance(warnings, list) and warnings:
                    results.append(f"  Warnings: {warnings[0][:300]}...")
            
            if "Adverse Reactions" in sections:
                adverse = sections["Adverse Reactions"]
                if isinstance(adverse, list) and adverse:
                    results.append(f"  Side Effects: {adverse[0][:300]}...")
        
        results.append("")
    
    results.append("=" * 50)
    results.append("DISCLAIMER: This is FDA labeling information. Consult a healthcare")
    results.append("professional for medical advice.")
    
    return "\n".join(results)


DRUG_TOOLS = [check_drug_interactions, get_drug_info]
