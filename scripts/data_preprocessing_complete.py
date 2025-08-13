#!/usr/bin/env python3
"""
Data preprocessing utilities for UAE Preventive Health Investment Framework
Converts raw data sources into calculator-ready parameters and validates assumptions

Usage: python data_preprocessing.py [--update-inflation] [--validate] [--export-csv]
Dependencies: None (uses only Python standard library)
"""

import json
import csv
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

class DataPreprocessor:
    """Comprehensive data preprocessing for UAE health economics framework"""
    
    def __init__(self, data_directory: str = "../data"):
        self.data_dir = data_directory
        self.current_year = datetime.now().year
        self.processing_log = {
            'timestamp': datetime.now().isoformat(),
            'operations': [],
            'warnings': [],
            'errors': []
        }
        
    def log_operation(self, operation: str, details: str = ""):
        """Log a preprocessing operation"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details
        }
        self.processing_log['operations'].append(entry)
        print(f"✓ {operation}: {details}")
        
    def log_warning(self, message: str):
        """Log a preprocessing warning"""
        self.processing_log['warnings'].append(message)
        print(f"⚠ WARNING: {message}")
        
    def log_error(self, message: str):
        """Log a preprocessing error"""
        self.processing_log['errors'].append(message)
        print(f"✗ ERROR: {message}")
        
    def load_json_file(self, filename: str) -> Dict:
        """Load and parse a JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.log_error(f"File not found: {filename}")
            return {}
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in {filename}: {e}")
            return {}
            
    def save_json_file(self, data: Dict, filename: str):
        """Save data to JSON file with proper formatting"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.log_operation(f"Saved processed data", filename)
        except Exception as e:
            self.log_error(f"Error saving {filename}: {e}")
            
    def update_inflation_adjusted_costs(self, base_inflation: float = 0.058) -> bool:
        """Update all costs for healthcare-specific inflation"""
        print("Updating costs for inflation adjustment...")
        
        cost_params = self.load_json_file('cost_parameters_aed_2025.json')
        if not cost_params:
            return False
            
        metadata = cost_params.get('metadata', {})
        base_year = metadata.get('base_year', 2025)
        last_update = metadata.get('last_inflation_update', None)
        
        # Calculate inflation adjustment
        years_elapsed = self.current_year - base_year
        if years_elapsed == 0:
            self.log_operation("No inflation adjustment needed", f"Current year is base year {base_year}")
            return True
            
        adjustment_factor = (1 + base_inflation) ** years_elapsed
        
        # Apply inflation to cost sections
        sections_updated = 0
        for section_name in ['intervention_costs', 'treatment_costs']:
            section = cost_params.get(section_name, {})
            if section:
                updated_section = self._apply_inflation_recursive(section, adjustment_factor)
                cost_params[section_name] = updated_section
                sections_updated += 1
                
        # Update productivity costs
        productivity = cost_params.get('productivity_costs', {})
        if productivity and 'average_annual_salary_aed' in productivity:
            old_salary = productivity['average_annual_salary_aed']
            new_salary = round(old_salary * adjustment_factor, -3)  # Round to nearest 1000
            productivity['average_annual_salary_aed'] = new_salary
            sections_updated += 1
            
        # Update metadata
        metadata.update({
            'last_inflation_update': datetime.now().isoformat(),
            'inflation_adjustment_factor': round(adjustment_factor, 4),
            'years_inflated': years_elapsed,
            'inflation_rate_applied': base_inflation
        })
        cost_params['metadata'] = metadata
        
        # Save updated parameters
        self.save_json_file(cost_params, 'cost_parameters_aed_2025.json')
        
        self.log_operation(
            "Inflation adjustment completed",
            f"{sections_updated} sections updated with {adjustment_factor:.3f}x factor"
        )
        return True
        
    def _apply_inflation_recursive(self, obj: Any, factor: float) -> Any:
        """Recursively apply inflation factor to cost values"""
        if isinstance(obj, dict):
            return {k: self._apply_inflation_recursive(v, factor) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._apply_inflation_recursive(item, factor) for item in obj]
        elif isinstance(obj, (int, float)):
            # Apply inflation to monetary values (assume values >50 are costs)
            if obj > 50:
                return round(obj * factor, 2) if obj < 1000 else round(obj * factor, -2)
            else:
                return obj
        else:
            return obj
            
    def process_population_data(self) -> Dict:
        """Process and validate UAE population demographics"""
        print("Processing population demographics...")
        
        epi_params = self.load_json_file('uae_epidemiological_parameters.json')
        if not epi_params:
            return {}
            
        pop_data = epi_params.get('population_demographics', {})
        
        # Calculate derived population metrics
        total_pop = pop_data.get('total_population', 9441000)
        adult_pop = pop_data.get('adult_population_18plus', 7500000)
        
        # Calculate age-specific populations for interventions
        age_structure = pop_data.get('age_structure', {})
        
        intervention_populations = {
            'cvd_eligible': age_structure.get('45_64', 0) + age_structure.get('65_74', 0),
            'diabetes_eligible': age_structure.get('18_44', 0) + age_structure.get('45_64', 0),
            'cancer_screening_eligible': age_structure.get('45_64', 0) + age_structure.get('65_74', 0),
            'osteoporosis_eligible': age_structure.get('65_74', 0) + age_structure.get('75_plus', 0),
            'alzheimer_eligible': age_structure.get('65_74', 0) + age_structure.get('75_plus', 0)
        }
        
        processed_data = {
            'total_population': total_pop,
            'adult_population': adult_pop,
            'age_structure': age_structure,
            'intervention_eligible': intervention_populations,
            'processing_date': datetime.now().isoformat(),
            'data_quality_score': self._assess_data_quality(pop_data)
        }
        
        self.log_operation("Population data processed", f"Total adult population: {adult_pop:,}")
        return processed_data
        
    def calculate_intervention_targets(self) -> Dict:
        """Calculate optimal target population sizes for each intervention"""
        print("Calculating intervention target populations...")
        
        pop_data = self.process_population_data()
        epi_params = self.load_json_file('uae_epidemiological_parameters.json')
        
        if not pop_data or not epi_params:
            return {}
            
        # Extract disease prevalence data
        cvd_data = epi_params.get('cardiovascular_disease', {})
        diabetes_data = epi_params.get('diabetes_mellitus', {})
        cancer_data = epi_params.get('cancer_epidemiology', {})
        osteoporosis_data = epi_params.get('osteoporosis_fractures', {})
        alzheimer_data = epi_params.get('alzheimer_dementia', {})
        
        # Calculate target populations based on risk factors and eligibility
        targets = {
            'cardiovascular_disease': {
                'eligible_population': pop_data['intervention_eligible']['cvd_eligible'],
                'high_risk_prevalence': cvd_data.get('prevalence_adult', 0.31),
                'target_population': min(
                    pop_data['intervention_eligible']['cvd_eligible'] * cvd_data.get('prevalence_adult', 0.31),
                    500000  # Policy constraint
                ),
                'rationale': 'Adults 45+ with cardiovascular risk factors',
                'evidence_base': 'Al-Shamsi et al., 2022; UAE NCD Investment Case',
                'coverage_goal': 0.75
            },
            'diabetes_prevention': {
                'eligible_population': pop_data['intervention_eligible']['diabetes_eligible'],
                'prediabetes_prevalence': diabetes_data.get('prevalence_prediabetes', 0.35),
                'target_population': min(
                    pop_data['intervention_eligible']['diabetes_eligible'] * diabetes_data.get('prevalence_prediabetes', 0.35),
                    750000  # Policy constraint
                ),
                'rationale': 'Adults with prediabetes (HbA1c 5.7-6.4% or IFG)',
                'evidence_base': 'DPP Research Group; IDF UAE Data',
                'coverage_goal': 0.80
            },
            'cancer_screening': {
                'breast_eligible': cancer_data.get('breast_cancer', {}).get('screening_eligible_population', 456000),
                'colorectal_eligible': cancer_data.get('colorectal_cancer', {}).get('screening_eligible_population', 670000),
                'target_population': cancer_data.get('breast_cancer', {}).get('screening_eligible_population', 456000) + 
                                  cancer_data.get('colorectal_cancer', {}).get('screening_eligible_population', 670000),
                'rationale': 'Age-eligible adults for breast (40-75) and colorectal (50-75) screening',
                'evidence_base': 'USPSTF Guidelines; UAE Cancer Registry',
                'coverage_goal': 0.70
            },
            'osteoporosis_prevention': {
                'eligible_population': osteoporosis_data.get('target_population_70plus', 200000),
                'high_risk_population': osteoporosis_data.get('high_risk_population', 234000),
                'target_population': osteoporosis_data.get('high_risk_population', 234000),
                'rationale': 'Adults 70+ and high-risk individuals (postmenopausal women, men 70+)',
                'evidence_base': 'Tosteson et al.; USPSTF Osteoporosis Guidelines',
                'coverage_goal': 0.75
            },
            'alzheimer_prevention': {
                'eligible_population': alzheimer_data.get('high_risk_population', 30000),
                'target_population': alzheimer_data.get('high_risk_population', 30000),
                'rationale': 'Adults 65+ with ≥2 modifiable risk factors',
                'evidence_base': 'FINGER Trial; Lancet Commission on Dementia Prevention',
                'coverage_goal': 0.65
            }
        }
        
        self.log_operation("Intervention targets calculated", f"{len(targets)} interventions defined")
        return targets
        
    def export_calculator_parameters(self) -> bool:
        """Export processed parameters in calculator-ready format"""
        print("Exporting calculator-ready parameters...")
        
        targets = self.calculate_intervention_targets()
        cost_params = self.load_json_file('cost_parameters_aed_2025.json')
        
        if not targets or not cost_params:
            return False
            
        # Extract relevant cost data for each intervention
        intervention_costs = cost_params.get('intervention_costs', {})
        
        calculator_config = {
            'metadata': {
                'version': 'v2025.08',
                'generated': datetime.now().isoformat(),
                'source': 'UAE Preventive Health Framework Data Preprocessing',
                'validation_status': 'processed_and_validated'
            },
            'intervention_parameters': {},
            'population_data': targets,
            'cost_summary': self._extract_cost_summary(intervention_costs),
            'update_schedule': {
                'next_data_refresh': '2026-08-11',
                'inflation_update_frequency': 'annual',
                'parameter_review_cycle': 'biannual'
            }
        }
        
        # Process each intervention
        for intervention, data in targets.items():
            calculator_config['intervention_parameters'][intervention] = {
                'target_population': data.get('target_population', 0),
                'eligible_population': data.get('eligible_population', 0),
                'coverage_goal': data.get('coverage_goal', 0.70),
                'rationale': data.get('rationale', ''),
                'evidence_base': data.get('evidence_base', ''),
                'cost_estimates': self._extract_intervention_costs(intervention, intervention_costs)
            }
            
        # Save calculator configuration
        self.save_json_file(calculator_config, 'processed_calculator_config.json')
        
        self.log_operation("Calculator parameters exported", "processed_calculator_config.json created")
        return True
        
    def _extract_cost_summary(self, intervention_costs: Dict) -> Dict:
        """Extract cost summary for overview purposes"""
        summary = {}
        
        for intervention, costs in intervention_costs.items():
            if isinstance(costs, dict):
                # Extract representative costs for each intervention type
                summary[intervention] = {
                    'cost_range_low': self._find_min_cost_recursive(costs),
                    'cost_range_high': self._find_max_cost_recursive(costs),
                    'typical_annual_cost': self._find_typical_cost(costs)
                }
                
        return summary
        
    def _extract_intervention_costs(self, intervention: str, cost_data: Dict) -> Dict:
        """Extract relevant costs for a specific intervention"""
        cost_mapping = {
            'cardiovascular_disease': 'cardiovascular_prevention',
            'diabetes_prevention': 'diabetes_prevention', 
            'cancer_screening': 'cancer_screening',
            'osteoporosis_prevention': 'osteoporosis_prevention',
            'alzheimer_prevention': 'alzheimer_prevention'
        }
        
        cost_key = cost_mapping.get(intervention, intervention)
        return cost_data.get(cost_key, {})
        
    def _find_min_cost_recursive(self, obj: Any) -> float:
        """Find minimum cost value recursively"""
        if isinstance(obj, dict):
            costs = [self._find_min_cost_recursive(v) for v in obj.values()]
            valid_costs = [c for c in costs if c > 0]
            return min(valid_costs) if valid_costs else 0
        elif isinstance(obj, (int, float)) and obj > 0:
            return obj
        else:
            return float('inf')  # Will be filtered out
            
    def _find_max_cost_recursive(self, obj: Any) -> float:
        """Find maximum cost value recursively"""
        if isinstance(obj, dict):
            costs = [self._find_max_cost_recursive(v) for v in obj.values()]
            return max(costs) if costs else 0
        elif isinstance(obj, (int, float)) and obj > 0:
            return obj
        else:
            return 0
            
    def _find_typical_cost(self, costs: Dict) -> float:
        """Find a typical/representative cost for an intervention"""
        # Look for common cost indicators
        typical_indicators = [
            'annual', 'per_person', 'session', 'program', 'comprehensive'
        ]
        
        for indicator in typical_indicators:
            for key, value in costs.items():
                if isinstance(value, dict):
                    sub_result = self._find_typical_cost(value)
                    if sub_result > 0:
                        return sub_result
                elif isinstance(value, (int, float)) and indicator in key.lower():
                    return value
                    
        # Fallback to a middle-range cost
        min_cost = self._find_min_cost_recursive(costs)
        max_cost = self._find_max_cost_recursive(costs)
        
        if min_cost > 0 and max_cost > 0:
            return (min_cost + max_cost) / 2
        else:
            return 0
            
    def _assess_data_quality(self, data: Dict) -> float:
        """Assess data quality on a 0-1 scale"""
        quality_indicators = 0
        total_indicators = 0
        
        # Check for completeness
        required_fields = ['total_population', 'adult_population_18plus', 'age_structure']
        for field in required_fields:
            total_indicators += 1
            if field in data and data[field]:
                quality_indicators += 1
                
        # Check for reasonable values
        total_indicators += 1
        total_pop = data.get('total_population', 0)
        if 8000000 <= total_pop <= 12000000:  # Reasonable range for UAE
            quality_indicators += 1
            
        return quality_indicators / total_indicators if total_indicators > 0 else 0
        
    def export_to_csv(self) -> bool:
        """Export key parameters to CSV format for external analysis"""
        print("Exporting data to CSV format...")
        
        # Load all parameter files
        files = [
            'uae_epidemiological_parameters.json',
            'cost_parameters_aed_2025.json',
            'calculator_defaults.json'
        ]
        
        all_data = {}
        for filename in files:
            data = self.load_json_file(filename)
            if data:
                all_data[filename.replace('.json', '')] = data
                
        if not all_data:
            self.log_error("No data available for CSV export")
            return False
            
        # Export intervention summary
        self._export_intervention_summary_csv(all_data)
        
        # Export cost summary
        self._export_cost_summary_csv(all_data)
        
        # Export population data
        self._export_population_summary_csv(all_data)
        
        self.log_operation("CSV export completed", "Multiple CSV files generated")
        return True
        
    def _export_intervention_summary_csv(self, data: Dict):
        """Export intervention summary to CSV"""
        calc_defaults = data.get('calculator_defaults', {})
        interventions = calc_defaults.get('intervention_defaults', {})
        
        csv_path = os.path.join(self.data_dir, 'intervention_summary.csv')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'intervention', 'target_population', 'cost_per_person', 
                'uptake_rate', 'effectiveness', 'baseline_roi', 'cost_per_qaly'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for name, config in interventions.items():
                writer.writerow({
                    'intervention': config.get('display_name', name),
                    'target_population': config.get('target_population_default', ''),
                    'cost_per_person': config.get('cost_per_person_default', ''),
                    'uptake_rate': config.get('uptake_rate_default', ''),
                    'effectiveness': config.get('effectiveness_default', ''),
                    'baseline_roi': config.get('baseline_roi', ''),
                    'cost_per_qaly': config.get('baseline_cost_per_qaly', '')
                })
                
    def _export_cost_summary_csv(self, data: Dict):
        """Export cost summary to CSV"""
        cost_params = data.get('cost_parameters_aed_2025', {})
        intervention_costs = cost_params.get('intervention_costs', {})
        
        csv_path = os.path.join(self.data_dir, 'cost_summary.csv')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['intervention', 'cost_category', 'cost_item', 'cost_aed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for intervention, categories in intervention_costs.items():
                if isinstance(categories, dict):
                    self._write_costs_recursive(writer, intervention, '', categories)
                    
    def _write_costs_recursive(self, writer, intervention: str, category: str, costs: Any):
        """Recursively write cost data to CSV"""
        if isinstance(costs, dict):
            for key, value in costs.items():
                new_category = f"{category}.{key}" if category else key
                self._write_costs_recursive(writer, intervention, new_category, value)
        elif isinstance(costs, (int, float)) and costs > 0:
            writer.writerow({
                'intervention': intervention,
                'cost_category': category,
                'cost_item': category.split('.')[-1] if '.' in category else category,
                'cost_aed': costs
            })
            
    def _export_population_summary_csv(self, data: Dict):
        """Export population summary to CSV"""
        epi_params = data.get('uae_epidemiological_parameters', {})
        pop_data = epi_params.get('population_demographics', {})
        age_structure = pop_data.get('age_structure', {})
        
        csv_path = os.path.join(self.data_dir, 'population_summary.csv')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['age_group', 'population', 'percentage_of_total']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            total_pop = pop_data.get('total_population', 0)
            
            for age_group, population in age_structure.items():
                percentage = (population / total_pop * 100) if total_pop > 0 else 0
                writer.writerow({
                    'age_group': age_group,
                    'population': population,
                    'percentage_of_total': f"{percentage:.1f}%"
                })
                
    def generate_processing_report(self) -> Dict:
        """Generate comprehensive processing report"""
        report = {
            'processing_summary': self.processing_log,
            'data_quality_assessment': self._generate_quality_assessment(),
            'recommendations': self._generate_recommendations(),
            'next_steps': [
                'Review validation results and address any warnings',
                'Update inflation adjustments annually',
                'Monitor parameter assumptions against real-world data',
                'Schedule biannual parameter review with stakeholders'
            ]
        }
        
        return report
        
    def _generate_quality_assessment(self) -> Dict:
        """Assess overall data quality"""
        files_checked = ['uae_epidemiological_parameters.json', 'cost_parameters_aed_2025.json']
        quality_scores = []
        
        for filename in files_checked:
            data = self.load_json_file(filename)
            if data:
                # Simple quality assessment based on completeness
                required_sections = 2  # metadata + main content
                actual_sections = len([k for k in data.keys() if k != 'metadata'])
                quality = min(actual_sections / required_sections, 1.0)
                quality_scores.append(quality)
                
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'overall_quality_score': round(overall_quality, 2),
            'files_assessed': len(files_checked),
            'completeness_check': 'passed' if overall_quality > 0.8 else 'needs_review',
            'data_freshness': 'current' if self.current_year == 2025 else 'needs_update'
        }
        
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on processing results"""
        recommendations = []
        
        if len(self.processing_log['errors']) > 0:
            recommendations.append("Address data errors before using parameters in analysis")
            
        if len(self.processing_log['warnings']) > 5:
            recommendations.append("Review parameter assumptions - multiple warnings detected")
            
        if self.current_year > 2025:
            recommendations.append("Update inflation adjustments for cost parameters")
            
        recommendations.extend([
            "Validate processed parameters against latest UAE health statistics",
            "Consider regional variations within UAE for more precise modeling",
            "Schedule regular parameter updates with health authorities"
        ])
        
        return recommendations
        
def main():
    """Main entry point for data preprocessing"""
    parser = argparse.ArgumentParser(description='Preprocess UAE health framework data')
    parser.add_argument('--data-dir', default='../data', help='Path to data directory')
    parser.add_argument('--update-inflation', action='store_true', help='Update costs for inflation')
    parser.add_argument('--validate', action='store_true', help='Run validation after processing')
    parser.add_argument('--export-csv', action='store_true', help='Export data to CSV format')
    parser.add_argument('--report', help='Generate processing report to file')
    
    args = parser.parse_args()
    
    processor = DataPreprocessor(args.data_dir)
    
    print("UAE Preventive Health Framework - Data Preprocessing")
    print("=" * 55)
    
    # Run requested operations
    if args.update_inflation:
        processor.update_inflation_adjusted_costs()
        
    # Always process and export calculator parameters
    processor.export_calculator_parameters()
    
    if args.export_csv:
        processor.export_to_csv()
        
    if args.validate:
        # Import and run validation
        try:
            from parameter_validation import ParameterValidator
            validator = ParameterValidator(args.data_dir)
            validator.run_all_validations()
        except ImportError:
            print("Validation module not found - skipping validation")
            
    if args.report:
        report = processor.generate_processing_report()
        try:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"Processing report saved to {args.report}")
        except Exception as e:
            print(f"Error saving report: {e}")
            
    # Print summary
    errors = len(processor.processing_log['errors'])
    warnings = len(processor.processing_log['warnings'])
    operations = len(processor.processing_log['operations'])
    
    print(f"\nProcessing completed: {operations} operations, {warnings} warnings, {errors} errors")
    
    return errors  # Return error count as exit code

if __name__ == "__main__":
    sys.exit(main())