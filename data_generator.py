"""Generate synthetic insurance claims data with narratives."""

import pandas as pd
import numpy as np
from pathlib import Path
import random
from typing import List, Dict
import config

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


class ClaimsDataGenerator:
    """Generate synthetic insurance claims data."""
    
    CLAIM_TYPES = [
        "Auto Accident",
        "Property Damage",
        "Theft",
        "Fire Damage",
        "Water Damage",
        "Liability",
        "Medical",
        "Storm Damage"
    ]
    
    LOCATIONS = [
        # Major Swiss cities (Zurich's home market)
        "Zurich, Switzerland", "Geneva, Switzerland", "Basel, Switzerland",
        "Bern, Switzerland", "Lausanne, Switzerland",
        # Major European markets
        "London, UK", "Frankfurt, Germany", "Munich, Germany",
        "Paris, France", "Milan, Italy", "Madrid, Spain",
        # North American markets
        "New York, NY", "Chicago, IL", "Toronto, Canada"
    ]
    
    def __init__(self, num_claims: int = 200):
        self.num_claims = num_claims
        
    def generate_claims(self) -> pd.DataFrame:
        """Generate claims dataset with metadata."""
        claims = []
        
        for i in range(self.num_claims):
            claim_type = random.choice(self.CLAIM_TYPES)
            claim_amount = self._generate_claim_amount(claim_type)
            
            claim = {
                "claim_id": f"CLM-{i+1:05d}",
                "policy_id": f"POL-{random.randint(1000, 9999)}",
                "claim_type": claim_type,
                "claim_amount": claim_amount,
                "incident_date": self._generate_date(),
                "report_date": self._generate_date(offset=1, days_range=30),
                "location": random.choice(self.LOCATIONS),
                "claimant_age": random.randint(18, 85),
                "prior_claims": random.randint(0, 5),
                "policy_tenure_years": random.randint(0, 20),
                "narrative": self._generate_narrative(claim_type, claim_amount),
                "ground_truth_severity": self._assign_ground_truth_severity(claim_amount),
                "ground_truth_action": None  # Will be assigned based on severity
            }
            
            # Assign ground truth action based on severity and other factors
            claim["ground_truth_action"] = self._assign_ground_truth_action(claim)
            claims.append(claim)
        
        return pd.DataFrame(claims)
    
    def generate_policies(self, claims_df: pd.DataFrame) -> pd.DataFrame:
        """Generate policy data for the claims."""
        unique_policies = claims_df["policy_id"].unique()
        policies = []
        
        for policy_id in unique_policies:
            policy = {
                "policy_id": policy_id,
                "policy_type": random.choice(["Standard", "Premium", "Basic"]),
                "coverage_limit": random.choice([50000, 100000, 250000, 500000, 1000000]),
                "deductible": random.choice([500, 1000, 2500, 5000]),
                "customer_name": f"Customer {policy_id}",
                "policy_start_date": self._generate_date(offset=-365, days_range=1825),
                "claims_history_count": random.randint(0, 5),
                "is_active": True
            }
            policies.append(policy)
        
        return pd.DataFrame(policies)
    
    def _generate_claim_amount(self, claim_type: str) -> float:
        """Generate realistic claim amounts based on type."""
        base_amounts = {
            "Auto Accident": (2000, 50000),
            "Property Damage": (1000, 100000),
            "Theft": (500, 25000),
            "Fire Damage": (5000, 200000),
            "Water Damage": (2000, 75000),
            "Liability": (3000, 150000),
            "Medical": (1000, 100000),
            "Storm Damage": (2000, 100000)
        }
        
        min_amt, max_amt = base_amounts.get(claim_type, (1000, 50000))
        
        # Use log-normal distribution for realistic amounts
        mu = np.log((min_amt + max_amt) / 2)
        sigma = 0.5
        amount = np.random.lognormal(mu, sigma)
        
        # Clip to reasonable range
        return round(max(min_amt, min(max_amt, amount)), 2)
    
    def _generate_date(self, offset: int = -365, days_range: int = 365) -> str:
        """Generate a random date."""
        from datetime import datetime, timedelta
        
        base_date = datetime.now() + timedelta(days=offset)
        random_days = random.randint(0, days_range)
        date = base_date + timedelta(days=random_days)
        
        return date.strftime("%Y-%m-%d")
    
    def _generate_narrative(self, claim_type: str, amount: float) -> str:
        """Generate claim narrative text."""
        narratives = {
            "Auto Accident": [
                f"Vehicle collision occurred at intersection. Claimant reports being rear-ended at stoplight. Damage to rear bumper and trunk. Estimated repair cost ${amount:,.2f}.",
                f"Multi-vehicle accident on highway. Claimant's vehicle sustained front-end damage. Police report filed. Total damages approximately ${amount:,.2f}.",
                f"Single-vehicle accident. Claimant lost control on wet road and hit guardrail. Airbags deployed. Repair estimate ${amount:,.2f}."
            ],
            "Property Damage": [
                f"Storm damage to residential property. Roof tiles damaged and water intrusion into attic. Assessment estimates repairs at ${amount:,.2f}.",
                f"Tree fell on house during windstorm. Damage to roof and gutters. Emergency repairs needed. Estimated cost ${amount:,.2f}.",
                f"Neighbor's property damage caused structural issues. Wall and foundation affected. Repair quote ${amount:,.2f}."
            ],
            "Theft": [
                f"Burglary reported at residence. Electronics and jewelry stolen. Police report filed. Total loss valued at ${amount:,.2f}.",
                f"Vehicle theft from parking garage. Car recovered but damaged. Repair and replacement costs ${amount:,.2f}.",
                f"Break-in at property. Multiple items stolen including appliances. Police investigation ongoing. Loss estimate ${amount:,.2f}."
            ],
            "Fire Damage": [
                f"Kitchen fire caused by electrical malfunction. Smoke and fire damage to kitchen and adjacent rooms. Restoration cost ${amount:,.2f}.",
                f"Wildfire smoke damage to property. Interior and exterior cleaning needed. Total cost ${amount:,.2f}.",
                f"Electrical fire in garage. Structure damage and vehicle damaged. Fire department report available. Estimate ${amount:,.2f}."
            ],
            "Water Damage": [
                f"Pipe burst in basement. Flooding damaged flooring, walls, and personal property. Water remediation needed. Cost ${amount:,.2f}.",
                f"Roof leak during heavy rain. Water damage to ceiling and walls in multiple rooms. Repairs estimated at ${amount:,.2f}.",
                f"Washing machine overflow caused water damage. Flooring and drywall replacement needed. Total ${amount:,.2f}."
            ],
            "Liability": [
                f"Guest injured on property. Medical treatment required. Liability claim filed. Settlement amount ${amount:,.2f}.",
                f"Property damage caused by claimant to third party. Legal settlement reached. Total liability ${amount:,.2f}.",
                f"Dog bite incident. Medical bills and legal costs. Total claim amount ${amount:,.2f}."
            ],
            "Medical": [
                f"Emergency room visit after accident. Treatment for injuries including X-rays and medication. Total medical bills ${amount:,.2f}.",
                f"Surgery required after covered incident. Hospital stay and rehabilitation. Medical costs ${amount:,.2f}.",
                f"Physical therapy and specialist visits following injury. Ongoing treatment. Total expenses ${amount:,.2f}."
            ],
            "Storm Damage": [
                f"Hail damage to roof and siding. Multiple dents and broken shingles. Contractor estimate ${amount:,.2f}.",
                f"Hurricane damage to property. Wind and water damage. Emergency repairs and restoration. Cost ${amount:,.2f}.",
                f"Tornado damage. Structural issues and debris removal needed. Assessment total ${amount:,.2f}."
            ]
        }
        
        templates = narratives.get(claim_type, [f"Claim filed for {claim_type}. Total amount ${amount:,.2f}."])
        return random.choice(templates)
    
    def _assign_ground_truth_severity(self, amount: float) -> str:
        """Assign severity level based on amount and other factors."""
        if amount < 5000:
            return "low"
        elif amount < 25000:
            return "medium"
        elif amount < 75000:
            return "high"
        else:
            return "critical"
    
    def _assign_ground_truth_action(self, claim: Dict) -> str:
        """Assign ground truth action based on claim characteristics."""
        severity = claim["ground_truth_severity"]
        prior_claims = claim["prior_claims"]
        tenure = claim["policy_tenure_years"]
        
        # Simple rule-based ground truth
        if severity == "low" and prior_claims < 2:
            return "approve"
        elif severity == "medium" and prior_claims < 3 and tenure > 1:
            return "approve"
        elif severity == "high" or prior_claims >= 3:
            return "investigate"
        elif severity == "critical" or prior_claims >= 4:
            return "escalate"
        else:
            return "investigate"
    
    def save_data(self, claims_df: pd.DataFrame, policies_df: pd.DataFrame):
        """Save generated data to CSV files."""
        claims_df.to_csv(config.CLAIMS_DATA_PATH, index=False)
        policies_df.to_csv(config.POLICIES_DATA_PATH, index=False)
        print(f"✓ Saved {len(claims_df)} claims to {config.CLAIMS_DATA_PATH}")
        print(f"✓ Saved {len(policies_df)} policies to {config.POLICIES_DATA_PATH}")


def main():
    """Generate and save claims data for Zurich Insurance POC."""
    print("="*60)
    print("ZURICH INSURANCE - Claims Data Generator")
    print("="*60)
    print("\nGenerating synthetic claims data...")
    
    generator = ClaimsDataGenerator(num_claims=200)
    claims_df = generator.generate_claims()
    policies_df = generator.generate_policies(claims_df)
    
    # Display sample data
    print("\nSample Claims:")
    print(claims_df.head())
    print("\nSample Policies:")
    print(policies_df.head())
    
    # Save to files
    generator.save_data(claims_df, policies_df)
    
    print("\n" + "="*60)
    print("✅ Data generation complete!")
    print("="*60)
    print(f"Total claims: {len(claims_df)}")
    print(f"Total policies: {len(policies_df)}")
    print(f"\nLocation distribution (top 5):")
    print(claims_df["location"].value_counts().head())
    print(f"\nSeverity distribution:")
    print(claims_df["ground_truth_severity"].value_counts())
    print(f"\nAction distribution:")
    print(claims_df["ground_truth_action"].value_counts())
    print("\n" + "="*60)


if __name__ == "__main__":
    main()

