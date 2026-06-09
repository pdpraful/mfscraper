import os
import re
import tempfile
import requests
import pdfplumber
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class PDFExtractorMixin:
    """Mixin for downloading and extracting data from AMC Factsheet PDFs."""
    
    def download_pdf(self, url: str, prefix: str = "amc_") -> Optional[str]:
        """Downloads a PDF securely and returns the local temp path."""
        try:
            logger.info(f"Downloading PDF from {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
            }
            # Append domain if relative
            if url.startswith('/'):
                url = f"https://www.motilaloswalmf.com{url}"
                
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".pdf")
            with os.fdopen(fd, 'wb') as f:
                f.write(response.content)
            
            return temp_path
        except Exception as e:
            logger.error(f"Failed to download PDF {url}: {e}")
            return None

    def extract_aum_for_fund(self, pdf_path: str, fund_keywords: list[str]) -> Optional[float]:
        """
        Scans the PDF pages for the fund keywords, and attempts to extract AUM.
        Returns the AUM as a float (in Crores).
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return None
            
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    # Check if all keywords are on this page
                    if all(kw.lower() in text.lower() for kw in fund_keywords):
                        # Simple regex to find AUM: e.g. "AUM: ₹ 5,432.10 Crores" or "AUM (Rs. in Crores) 5432.10"
                        # This is highly specific to the AMC, but we make a best-effort generic guess
                        aum_matches = re.findall(r'AUM[^\d]{1,20}([\d,]+\.\d{2})', text, re.IGNORECASE)
                        if aum_matches:
                            aum_str = aum_matches[0].replace(',', '')
                            try:
                                return float(aum_str)
                            except ValueError:
                                pass
            logger.warning(f"Could not find AUM for keywords {fund_keywords} in PDF.")
        except Exception as e:
            logger.error(f"Error extracting AUM from {pdf_path}: {e}")
        finally:
            # Cleanup temp file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                
        return None
