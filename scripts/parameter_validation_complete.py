#!/usr/bin/env python3
"""
Comprehensive parameter validation script for UAE Preventive Health Framework
Validates all model parameters against acceptable ranges, sources, and consistency

Usage: python parameter_validation.py [--verbose] [--output results.json]
Dependencies: None (uses only Python standard library)
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Any

class ParameterValidator:
    """Comprehensive validation of UAE health economics model parameters"""
    
    def __init__(self, data_directory: str = "../data"):
        self.data_dir = data_directory
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_valid': True,
            'warnings': [],
            'errors': [],
            'file_validations': {}
        }
        
    def load_parameter_file(self, filename: str) -> Dict:
        """Load and parse a parameter JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.add_error(f"Parameter file not found: {filename}")
            return {}
        except json.JSONDecodeError as e:
            self.add_error(f"Invalid JSON in {filename}: {e}")
            return {}
            
    def add_warning(self, message: str):
        """Add a validation warning"""
        self.validation_results['warnings'].append(message)
        
    def add_error(self, message: str):
        """Add a validation error"""
        self.validation_results['errors'].append(message)
        self.validation_results['overall_valid'] = False
        
    def validate_epidemiological_parameters(self) -> bool:
        """Validate epidemiological parameters against known ranges"""
        print("Validating epidemiological parameters...")
        
        params = self.load_parameter_file('uae_epidemiological_parameters.json')
        if not params:
            return False
            
        file_valid = True
        
        # Validate population demographics
        pop_data = params.get('population_demographics', {})
        total_pop = pop_data.get('total_population', 0)
        adult_pop = pop_data.get('adult_population_18plus', 0)
        
        if total_pop < 9000000 or total_pop > 12000000:
            self.add_warning(f"Total population {total_pop:,} outside expected range 9-12M")
            
        if adult_pop > total_pop:
            self.add_error("Adult population cannot exceed total population")
            file_valid = False
            
        # Validate CVD parameters
        cvd = params.get('cardiovascular_disease', {})
        cvd_prevalence = cvd.get('prevalence_adult', 0)
        cvd_onset = cvd.get('onset_age_mean', 0)
        
        if cvd_prevalence < 0.15 or cvd_prevalence > 0.50:
            self.add_warning(f"CVD prevalence {cvd_prevalence:.1%} outside typical range 15-50%")
            
        if cvd_onset < 40 or cvd_onset > 65:
            self.add_warning(f"CVD onset age {cvd_onset} outside typical range 40-65 years")
            
        # Validate diabetes parameters
        diabetes = params.get('diabetes_mellitus', {})
        dm_prevalence_low = diabetes.get('prevalence_adult_low', 0)
        dm_prevalence_high = diabetes.get('prevalence_adult_high', 0)
        
        if dm_prevalence_high > 0.30:
            self.add_warning(f"Diabetes prevalence {dm_prevalence_high:.1%} exceptionally high (>30%)")
            
        if dm_prevalence_low > dm_prevalence_high:
            self.add_error("Low diabetes prevalence cannot exceed high estimate")
            file_valid = False
            
        # Validate utility values
        utilities = params.get('quality_of_life_utilities', {})
        for state, utility in utilities.items():
            if isinstance(utility, (int, float)):
                if utility < 0 or utility > 1:
                    self.add_error(f"Invalid utility value for {state}: {utility} (must be 0-1)")
                    file_valid = False
                    
        self.validation_results['file_validations']['epidemiological'] = file_valid
        return file_valid
        
    def validate_cost_parameters(self) -> bool:
        """Validate cost parameters for consistency and reasonableness"""
        print("Validating cost parameters...")
        
        params = self.load_parameter_file('cost_parameters_aed_2025.json')
        if not params:
            return False
            
        file_valid = True
        
        # Check metadata
        metadata = params.get('metadata', {})
        currency = metadata.get('currency', '')
        base_year = metadata.get('base_year', 0)
        
        if currency != 'AED':
            self.add_error(f"Expected currency AED, got {currency}")
            file_valid = False
            
        if base_year != 2025:
            self.add_warning(f"Base year {base_year} may need inflation adjustment")
            
        # Validate intervention costs
        interventions = params.get('intervention_costs', {})
        for intervention, costs in interventions.items():
            if isinstance(costs, dict):
                self._validate_cost_section(costs, f"intervention_{intervention}")
                
        # Validate treatment costs
        treatments = params.get('treatment_costs', {})
        for treatment, costs in treatments.items():
            if isinstance(costs, dict):
                self._validate_cost_section(costs, f"treatment_{treatment}")
                
        # Check for logical cost relationships
        self._validate_cost_relationships(params)
        
        self.validation_results['file_validations']['cost_parameters'] = file_valid
        return file_valid
        
    def _validate_cost_section(self, costs: Dict, section_name: str):
        """Validate individual cost section for reasonable values"""
        for item, cost in costs.items():
            if isinstance(cost, (int, float)):
                if cost < 0:
                    self.add_error(f"Negative cost in {section_name}.{item}: {cost}")
                elif cost > 1000000:  # 1M AED threshold for very high costs
                    self.add_warning(f"Very high cost in {section_name}.{item}: AED {cost:,}")
            elif isinstance(cost, dict):
                # Recursive validation for nested cost structures
                self._validate_cost_section(cost, f"{section_name}.{item}")
                
    def _validate_cost_relationships(self, params: Dict):
        """Validate logical relationships between different costs"""
        # Check if prevention costs are generally lower than treatment costs
        interventions = params.get('intervention_costs', {})
        treatments = params.get('treatment_costs', {})
        
        # Example: CVD prevention vs treatment
        cvd_prevention = interventions.get('cardiovascular_prevention', {})
        cvd_treatment = treatments.get('cardiovascular_disease', {})
        
        if cvd_prevention and cvd_treatment:
            # Get sample prevention cost (statin)
            statin_cost = cvd_prevention.get('pharmacological', {}).get('generic_atorvastatin_annual', 0)
            # Get sample treatment cost (MI)
            mi_cost = cvd_treatment.get('acute_care', {}).get('acute_myocardial_infarction', 0)
            
            if statin_cost > 0 and mi_cost > 0:
                ratio = mi_cost / statin_cost
                if ratio < 10:  # Treatment should be much more expensive than prevention
                    self.add_warning(f"Low treatment/prevention cost ratio: {ratio:.1f}x")
                    
    def validate_calculator_defaults(self) -> bool:
        """Validate calculator default parameters"""
        print("Validating calculator defaults...")
        
        params = self.load_parameter_file('calculator_defaults.json')
        if not params:
            return False
            
        file_valid = True
        
        # Validate intervention defaults
        interventions = params.get('intervention_defaults', {})
        for name, config in interventions.items():
            # Check required fields
            required_fields = [
                'target_population_default', 'cost_per_person_default',
                'uptake_rate_default', 'effectiveness_default',
                'baseline_roi', 'baseline_cost_per_qaly'
            ]
            
            for field in required_fields:
                if field not in config:
                    self.add_error(f"Missing required field {field} in {name}")
                    file_valid = False
                    
            # Validate ranges
            if 'uptake_rate_default' in config:
                uptake = config['uptake_rate_default']
                if uptake < 0 or uptake > 1:
                    self.add_error(f"Invalid uptake rate {uptake} for {name} (must be 0-1)")
                    file_valid = False
                    
            if 'effectiveness_default' in config:
                effectiveness = config['effectiveness_default']
                if effectiveness < 0 or effectiveness > 1:
                    self.add_error(f"Invalid effectiveness {effectiveness} for {name} (must be 0-1)")
                    file_valid = False
                    
        # Validate portfolio totals (CORRECTED TARGETS)
        portfolio = params.get('portfolio_defaults', {})
        investment = portfolio.get('total_investment_billions', 0)
        benefits = portfolio.get('total_benefits_billions', 0)
        roi = portfolio.get('portfolio_roi', 0)
        events_prevented = portfolio.get('total_events_prevented', 0)
        deaths_averted = portfolio.get('total_deaths_averted', 0)
        
        # Validate ROI calculation
        if investment > 0 and benefits > 0:
            calculated_roi = round(((benefits - investment) / investment) * 100)
            if abs(calculated_roi - roi) > 5:  # Allow 5% tolerance
                self.add_warning(f"Portfolio ROI inconsistency: calculated {calculated_roi}%, stated {roi}%")
                
        # Validate health outcome targets
        expected_events = 158080
        expected_deaths = 16325
        
        if events_prevented != expected_events:
            self.add_error(f"Events prevented mismatch: {events_prevented:,} vs expected {expected_events:,}")
            file_valid = False
            
        if deaths_averted != expected_deaths:
            self.add_error(f"Deaths averted mismatch: {deaths_averted:,} vs expected {expected_deaths:,}")
            file_valid = False
                
        self.validation_results['file_validations']['calculator_defaults'] = file_valid
        return file_valid
        
    def validate_cross_file_consistency(self) -> bool:
        """Validate consistency between different parameter files"""
        print("Validating cross-file consistency...")
        
        # Load all files
        epi_params = self.load_parameter_file('uae_epidemiological_parameters.json')
        cost_params = self.load_parameter_file('cost_parameters_aed_2025.json')
        calc_defaults = self.load_parameter_file('calculator_defaults.json')
        core_params = self.load_parameter_file('core_parameters.json')
        
        if not all([epi_params, cost_params, calc_defaults]):
            return False
            
        consistency_valid = True
        
        # Check population consistency
        epi_adult_pop = epi_params.get('population_demographics', {}).get('adult_population_18plus', 0)
        interventions = calc_defaults.get('intervention_defaults', {})
        
        total_target_pop = sum(
            config.get('target_population_default', 0) 
            for config in interventions.values()
        )
        
        if total_target_pop > epi_adult_pop * 1.5:  # Allow for overlap
            self.add_warning(f"Total intervention targets ({total_target_pop:,}) may exceed available population")
            
        # Validate core parameters consistency if available
        if core_params:
            portfolio_summary = core_params.get('portfolio_summary', {})
            calc_portfolio = calc_defaults.get('portfolio_defaults', {})
            
            # Check key metrics
            core_events = portfolio_summary.get('events_prevented', 0)
            calc_events = calc_portfolio.get('total_events_prevented', 0)
            
            if core_events != calc_events:
                self.add_error(f"Events prevented inconsistent between core ({core_events:,}) and calculator ({calc_events:,})")
                consistency_valid = False
                
            core_deaths = portfolio_summary.get('deaths_averted', 0)  
            calc_deaths = calc_portfolio.get('total_deaths_averted', 0)
            
            if core_deaths != calc_deaths:
                self.add_error(f"Deaths averted inconsistent between core ({core_deaths:,}) and calculator ({calc_deaths:,})")
                consistency_valid = False
                
        self.validation_results['file_validations']['cross_file_consistency'] = consistency_valid
        return consistency_valid
        
    def validate_file_structure(self) -> bool:
        """Validate that all required files exist and are properly structured"""
        print("Validating file structure...")
        
        required_files = [
            'uae_epidemiological_parameters.json',
            'cost_parameters_aed_2025.json',
            'calculator_defaults.json'
        ]
        
        optional_files = [
            'core_parameters.json'
        ]
        
        structure_valid = True
        
        for filename in required_files:
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                self.add_error(f"Required file missing: {filename}")
                structure_valid = False
                continue
                
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        self.add_error(f"File {filename} does not contain a JSON object")
                        structure_valid = False
                    elif 'metadata' not in data:
                        self.add_warning(f"File {filename} missing metadata section")
                        
            except Exception as e:
                self.add_error(f"Error reading {filename}: {e}")
                structure_valid = False
                
        # Check optional files
        for filename in optional_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                print(f"Found optional file: {filename}")
                
        self.validation_results['file_validations']['file_structure'] = structure_valid
        return structure_valid
        
    def run_all_validations(self) -> Dict:
        """Run all validation tests and return comprehensive results"""
        print("=" * 60)
        print("UAE Preventive Health Framework - Parameter Validation")
        print("=" * 60)
        
        validations = [
            ("File Structure", self.validate_file_structure),
            ("Epidemiological Parameters", self.validate_epidemiological_parameters),
            ("Cost Parameters", self.validate_cost_parameters),
            ("Calculator Defaults", self.validate_calculator_defaults),
            ("Cross-File Consistency", self.validate_cross_file_consistency),
        ]
        
        passed = 0
        total = len(validations)
        
        for test_name, test_func in validations:
            try:
                result = test_func()
                print(f"{test_name}: {'✓ PASS' if result else '✗ FAIL'}")
                if result:
                    passed += 1
            except Exception as e:
                print(f"{test_name}: ✗ ERROR - {e}")
                self.add_error(f"Exception in {test_name}: {e}")
                
        print("\n" + "=" * 60)
        print(f"VALIDATION SUMMARY: {passed}/{total} tests passed")
        
        if self.validation_results['warnings']:
            print(f"\nWARNINGS ({len(self.validation_results['warnings'])}):")
            for warning in self.validation_results['warnings']:
                print(f"  ⚠  {warning}")
                
        if self.validation_results['errors']:
            print(f"\nERRORS ({len(self.validation_results['errors'])}):")
            for error in self.validation_results['errors']:
                print(f"  ✗ {error}")
                
        if passed == total and not self.validation_results['errors']:
            print("\n✓ All validations PASSED - Parameters are consistent and valid")
        else:
            print("\n✗ Some validations FAILED - Review parameters before use")
            
        return self.validation_results
        
def main():
    """Main entry point for parameter validation"""
    parser = argparse.ArgumentParser(description='Validate UAE health framework parameters')
    parser.add_argument('--data-dir', default='../data', help='Path to data directory')
    parser.add_argument('--output', help='Output validation results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    validator = ParameterValidator(args.data_dir)
    results = validator.run_all_validations()
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nValidation results written to {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            
    return 0 if results['overall_valid'] else 1

if __name__ == "__main__":
    sys.exit(main())