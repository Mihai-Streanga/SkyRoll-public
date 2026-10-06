"""SkyRoll demo engine: a catalog-driven payroll statement check, on synthetic data.

Simplified on purpose; the full fiscal chain lives in the private product.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "exemple", "catalog_exemplu.json")
PARAMETERS = os.path.join(ROOT, "exemple", "parametri_exemplu.json")

SIMPLIFIED = ("simplified on purpose; the full fiscal chain (deductions, sub-minimum, "
              "medical leave, exemptions, FSH) lives in the private product")
