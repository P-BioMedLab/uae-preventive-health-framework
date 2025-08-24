#!/usr/bin/env python3
"""
Minimal validation script for UAE Preventive Health Investment Framework
Validates core ROI calculations and parameter ranges for reproducibility

Usage: python minimal_validation.py
Dependencies: None (uses only Python standard library)
"""

import json
import math

def validate_core_roi_calculation():
    """Validate the headline 257% ROI calculation"""
    
    # Core portfolio parameters (from white paper)
    total_investment = 20.4  # AED billions
    total_benefits = 52.4    # AED billions
    expected_roi = 257       # percentage
    
    # Calculate ROI
    calculated_roi = round(((total_benefits - total_investment) / total_investment) * 100)
    
    print("=== Core ROI Validation ===")
    print(f"Investment: AED {total_investment}B")
    print(f"Benefits: AED {total_benefits}B")
    print(f"Expected ROI: {expected_roi}%")
    print(f"Calculated ROI: {calculated_roi}%")
    print(f"Validation: {'✓ PASS' if calculated_roi == expected_roi else '✗ FAIL'}")
    
    return calculated_roi == expected_roi

def validate_intervention_parameters():
    """Validate individual intervention ROI calculations"""
    
    # Intervention data from framework
    interventions = {
        'cvd': {'investment': 0.71, 'benefits': 1.99, 'expected_roi': 280},
        'diabetes': {'investment': 1.13, 'benefits': 2.37, 'expected_roi': 210},
        'cancer': {'investment': 1.18, 'benefits': 2.18, 'expected_roi': 185},
        'osteoporosis': {'investment': 0.211, 'benefits': 0.389, 'expected_roi': 184},
        'alzheimer': {'investment': 0.068, 'benefits': 0.108, 'expected_roi': 160}
    }
    
    print("\n=== Individual Intervention Validation ===")
    all_valid = True
    
    for name, data in interventions.items():
        calculated_roi = round(((data['benefits'] - data['investment']) / data['investment']) * 100)
        is_valid = abs(calculated_roi - data['expected_roi']) <= 5  # 5% tolerance
        
        print(f"{name.upper()}: {calculated_roi}% (expected {data['expected_roi']}%) {'✓' if is_valid else '✗'}")
        
        if not is_valid:
            all_valid = False
    
    return all_valid

def validate_cost_effectiveness():
    """Validate cost per QALY calculation"""
    
    # Parameters from framework
    total_investment = 20.4e9  # Convert to AED
    total_qalys = 326280
    expected_cost_per_qaly = 62600
    
    calculated_cost_per_qaly = round(total_investment / total_qalys)
    
    print("\n=== Cost-Effectiveness Validation ===")
    print(f"Total Investment: AED {total_investment/1e9:.1f}B")
    print(f"Total QALYs: {total_qalys:,}")
    print(f"Expected Cost/QALY: AED {expected_cost_per_qaly:,}")
    print(f"Calculated Cost/QALY: AED {calculated_cost_per_qaly:,}")
    
    # Allow 5% tolerance
    tolerance = 0.05
    is_valid = abs(calculated_cost_per_qaly - expected_cost_per_qaly) / expected_cost_per_qaly <= tolerance
    
    print(f"Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    
    return is_valid

def validate_health_outcomes():
    """Validate aggregated health outcome calculations"""
    
    # Individual intervention outcomes (CORRECTED to match white paper)
    outcomes = {
        'cvd': {'events': 12450, 'deaths_averted': 4500},
        'diabetes': {'events': 124000, 'deaths_averted': 5500}, 
        'cancer': {'events': 8400, 'deaths_averted': 4125},
        'osteoporosis': {'events': 10530, 'deaths_averted': 1400},
        'alzheimer': {'events': 2700, 'deaths_averted': 800}
    }
    
    total_events = sum(data['events'] for data in outcomes.values())
    total_deaths_averted = sum(data['deaths_averted'] for data in outcomes.values())
    
    expected_events = 158080
    expected_deaths_averted = 16325
    
    print("\n=== Health Outcomes Validation ===")
    print(f"Events Prevented: {total_events:,} (expected {expected_events:,}) {'✓' if total_events == expected_events else '✗'}")
    print(f"Deaths Averted: {total_deaths_averted:,} (expected {expected_deaths_averted:,}) {'✓' if total_deaths_averted == expected_deaths_averted else '✗'}")
    
    events_valid = total_events == expected_events
    deaths_valid = total_deaths_averted == expected_deaths_averted
    
    return events_valid and deaths_valid

def main():
    """Run all validation tests"""
    
    print("UAE Preventive Health Investment Framework - Validation Report")
    print("=" * 65)
    
    tests = [
        ("Core ROI Calculation", validate_core_roi_calculation),
        ("Individual Interventions", validate_intervention_parameters),
        ("Cost-Effectiveness", validate_cost_effectiveness),
        ("Health Outcomes", validate_health_outcomes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
    
    print("\n" + "=" * 65)
    print(f"SUMMARY: {passed}/{total} validation tests passed")
    
    if passed == total:
        print("✓ All validations PASSED - Framework calculations are consistent")
        return 0
    else:
        print("✗ Some validations FAILED - Review calculations and parameters")
        return 1

if __name__ == "__main__":
    exit(main())