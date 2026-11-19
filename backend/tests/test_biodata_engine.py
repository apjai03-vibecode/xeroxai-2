import pytest
from app.biodata_engine import _heuristic_parse, extract_biodata_with_gemma, generate_biodata_pdf
from app.models import BiodataSchema

SAMPLE_CUSTOMER_NOTES = """
Name: Senthil Kumar R
DOB: 12/04/1997
Passed B.Com in Loyola College with 75%
Phone: 9840123456
Email: senthil.kumar97@gmail.com
Address: Plot 22, 4th Main Road, T.Nagar, Chennai - 600017
Skills: Tally ERP 9, MS Excel, English Typing 50 WPM, GST Filing
Languages: Tamil, English, Hindi
"""

def test_heuristic_biodata_extraction():
    """Verify offline fallback parser extracts key candidate fields correctly."""
    data = _heuristic_parse(SAMPLE_CUSTOMER_NOTES)
    assert isinstance(data, BiodataSchema)
    assert "Senthil" in data.full_name
    assert "12/04/1997" in data.dob
    assert "B.Com" in data.qualification
    assert "9840123456" in data.contact
    assert "senthil.kumar97@gmail.com" in data.email
    assert len(data.skills) >= 2
    assert "Tamil" in data.languages or "English" in data.languages

def test_extract_biodata_fallback_stability():
    """extract_biodata_with_gemma should never raise an exception even if Ollama is unreachable."""
    data, is_fallback, model_used = extract_biodata_with_gemma(SAMPLE_CUSTOMER_NOTES)
    assert isinstance(data, BiodataSchema)
    assert data.full_name != ""
    assert isinstance(is_fallback, bool)

def test_generate_biodata_pdf_validity():
    """ReportLab must generate a valid single-page PDF with standard %PDF signature."""
    schema = BiodataSchema(
        full_name="Priya Dharshini",
        dob="05/11/1999",
        qualification="B.E Computer Science & Engineering",
        contact="9876543210",
        email="priya.d@example.com",
        address="12 Anna Salai, Guindy, Chennai - 600032",
        skills=["Python", "Web Development", "MS Office", "Data Analysis"],
        languages=["English", "Tamil"]
    )
    pdf_bytes = generate_biodata_pdf(schema)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-"), "Generated file is missing standard PDF magic bytes"
