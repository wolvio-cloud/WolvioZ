#!/usr/bin/env python3
"""
Seed 3 demo products with full specification tables for the India Pharma Expo 2026 demo.

Products:
  1. Paracetamol IP
  2. Microcrystalline Cellulose (MCC) PH102
  3. Gelatin (Pharma Grade)

Usage:
  cd backend
  python scripts/seed_specs.py

Requires .env with SUPABASE_URL and SUPABASE_SERVICE_KEY set.
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import json

BASE_URL = os.getenv("COA_API_URL", "http://localhost:8000")


DEMO_PRODUCTS = [
    {
        "product_name": "Paracetamol IP",
        "product_grade": "IP",
        "product_description": "Paracetamol as per Indian Pharmacopoeia",
        "spec_version": "IP-2022",
        "effective_date": "2022-01-01",
        "parameters": [
            {
                "parameter_name": "Description",
                "specification_limit": "White crystalline powder",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Solubility",
                "specification_limit": "Slightly soluble in water, freely soluble in ethanol",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Identification (IR)",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Melting Point",
                "method_reference": "IP 2.4.21",
                "specification_limit": "168 - 172",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Loss on Drying",
                "method_reference": "IP 2.4.19",
                "specification_limit": "NMT 0.5%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Residue on Ignition",
                "method_reference": "IP 2.3.19",
                "specification_limit": "NMT 0.1%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Heavy Metals",
                "method_reference": "IP 2.3.13",
                "specification_limit": "NMT 20 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Clarity of Solution",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Colour of Solution",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
            {
                "parameter_name": "pH (1% w/v solution)",
                "method_reference": "IP 2.4.24",
                "specification_limit": "5.3 - 6.5",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Assay (on dried basis)",
                "method_reference": "IP 2.4.5",
                "specification_limit": "98.0 - 102.0%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "4-Aminophenol",
                "method_reference": "IP HPLC",
                "specification_limit": "NMT 50 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Chloride",
                "specification_limit": "NMT 100 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Sulfate",
                "specification_limit": "NMT 200 ppm",
                "is_quantitative": True,
            },
        ],
    },
    {
        "product_name": "Microcrystalline Cellulose PH102",
        "product_grade": "PH102",
        "product_description": "Microcrystalline Cellulose as per NF/EP — PH102 grade",
        "spec_version": "NF-2023",
        "effective_date": "2023-01-01",
        "parameters": [
            {
                "parameter_name": "Description",
                "specification_limit": "White or almost white, fine or granular powder",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Identification",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
            {
                "parameter_name": "pH (2% w/v suspension)",
                "method_reference": "NF pH",
                "specification_limit": "5.0 - 7.5",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Loss on Drying",
                "method_reference": "NF 731",
                "specification_limit": "NMT 7.0%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Residue on Ignition",
                "specification_limit": "NMT 0.1%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Heavy Metals",
                "specification_limit": "NMT 10 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Water-Soluble Substances",
                "specification_limit": "NMT 0.24%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Ether-Soluble Substances",
                "specification_limit": "NMT 0.05%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Conductivity",
                "specification_limit": "NMT 75 μS/cm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Particle Size (d50)",
                "method_reference": "Laser diffraction",
                "specification_limit": "90 - 150 μm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Bulk Density",
                "specification_limit": "0.26 - 0.35 g/mL",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Tapped Density",
                "specification_limit": "0.33 - 0.46 g/mL",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Starch",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
        ],
    },
    {
        "product_name": "Gelatin Pharma Grade",
        "product_grade": "Pharma",
        "product_description": "Gelatin for pharmaceutical capsule manufacturing",
        "spec_version": "BP-2023",
        "effective_date": "2023-01-01",
        "parameters": [
            {
                "parameter_name": "Description",
                "specification_limit": "Light amber to amber, hard, vitreous fragments",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Identification",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Colour",
                "specification_limit": "Passes test",
                "is_quantitative": False,
            },
            {
                "parameter_name": "pH (1% w/v solution, 35°C)",
                "method_reference": "BP pH",
                "specification_limit": "3.8 - 7.6",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Loss on Drying",
                "method_reference": "BP 2.2.32",
                "specification_limit": "NMT 15.0%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Sulfur Dioxide",
                "specification_limit": "NMT 50 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Arsenic",
                "specification_limit": "NMT 1 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Lead",
                "specification_limit": "NMT 5 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Chromium",
                "specification_limit": "NMT 10 ppm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Gel Strength (Bloom)",
                "method_reference": "BP Gel strength",
                "specification_limit": "NLT 250 g",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Viscosity (6.67% w/w, 60°C)",
                "method_reference": "BP Viscometry",
                "specification_limit": "2.0 - 7.5 mPa.s",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Conductivity",
                "specification_limit": "NMT 1.0 mS/cm",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Residue on Ignition",
                "specification_limit": "NMT 2.0%",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Total Aerobic Microbial Count",
                "specification_limit": "NMT 1000 CFU/g",
                "is_quantitative": True,
            },
            {
                "parameter_name": "Total Yeast and Mould Count",
                "specification_limit": "NMT 100 CFU/g",
                "is_quantitative": True,
            },
            {
                "parameter_name": "E. coli",
                "specification_limit": "Absent in 10 g",
                "is_quantitative": False,
            },
            {
                "parameter_name": "Salmonella",
                "specification_limit": "Absent in 25 g",
                "is_quantitative": False,
            },
        ],
    },
]


async def seed():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        for product in DEMO_PRODUCTS:
            print(f"Seeding: {product['product_name']} ({product['spec_version']})...")
            response = await client.post("/api/specs/parameters", json=product)

            if response.status_code == 201:
                data = response.json()["data"]
                print(
                    f"  ✓ {data['parameters_inserted']} parameters seeded "
                    f"(product: {data['product_id'][:8]}...)"
                )
            else:
                print(f"  ✗ Failed: {response.status_code} — {response.text}")


if __name__ == "__main__":
    asyncio.run(seed())
