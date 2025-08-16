#!/usr/bin/env python3
"""
UAE Preventive Health Framework - Monte Carlo Analysis Runner
Generates 95% confidence intervals for the 5 key metrics

This script implements the complete Monte Carlo analysis with:
- 10,000 iterations
- Full parameter uncertainty
- Proper economic modeling with discounting
- UAE-specific parameters

Run this script to get the 95% confidence intervals for:
1. Major Disease Events Prevented
2. Premature Deaths Prevented  
3. Quality-Adjusted Life Years (QALYs) Gained
4. Direct Healthcare Savings
5. Return on Investment (ROI)

Author: UAE Preventive Health Framework Project
Date: August 2025
"""

import numpy as np
import pandas as pd
import json
import warnings
warnings.filterwarnings('ignore')

class UAEMonteCarloAnalysis:
    """Complete Monte Carlo Analysis for UAE Preventive Health Framework"""
    
    def __init__(self, n_iterations=10000):
        self.n_iterations = n_iterations
        self.discount_rate = 0.03
        self.time_horizon = 10
        
        # Target populations (from UAE data)
        self.target_populations = {
            'cvd': 500000,
            'diabetes': 750000, 
            'cancer': 1126000,
            'osteoporosis': 234000,
            'alzheimer': 30000
        }
        
        # Set random seed for reproducibility
        np.random.seed(42)
    
    def sample_parameters(self):
        """Sample all parameters for Monte Carlo iterations"""
        n = self.n_iterations
        
        # CVD Parameters (using beta and gamma distributions)
        cvd_effectiveness = np.random.beta(15, 5, n)  # Mean ~0.75
        cvd_baseline_risk = np.random.beta(12, 88, n)  # Mean ~0.12
        cvd_mortality_rate = np.random.beta(9, 21, n)  # Mean ~0.30
        cvd_intervention_cost = np.random.gamma(9, 210)  # Mean ~1890
        cvd_event_cost = np.random.gamma(16, 2812.5)  # Mean ~45000
        cvd_care_cost = np.random.gamma(9, 1667)  # Mean ~15000
        
        # Diabetes Parameters  
        diabetes_effectiveness = np.random.beta(15, 10, n)  # Mean ~0.60
        diabetes_progression = np.random.beta(11, 89, n)  # Mean ~0.11
        diabetes_mortality = np.random.beta(3, 27, n)  # Mean ~0.10
        diabetes_intervention_cost = np.random.gamma(16, 117.7)  # Mean ~1883
        diabetes_care_cost = np.random.gamma(9, 1022)  # Mean ~9200
        diabetes_complication_cost = np.random.gamma(4, 13833)  # Mean ~55333
        
        # Cancer Parameters
        cancer_effectiveness = np.random.beta(11, 9, n)  # Mean ~0.55
        cancer_detection_rate = np.random.beta(3, 97, n)  # Mean ~0.03
        cancer_mortality_reduction = np.random.beta(4, 16, n)  # Mean ~0.20
        cancer_screening_cost = np.random.gamma(9, 166.3)  # Mean ~1497
        cancer_treatment_cost = np.random.gamma(4, 18750)  # Mean ~75000
        
        # Osteoporosis Parameters
        osteo_effectiveness = np.random.beta(13, 7, n)  # Mean ~0.65
        fracture_risk = np.random.beta(18, 182, n)  # Mean ~0.09
        fracture_mortality = np.random.beta(3, 17, n)  # Mean ~0.15
        osteo_intervention_cost = np.random.gamma(16, 75.1)  # Mean ~1202
        fracture_treatment_cost = np.random.gamma(4, 21250)  # Mean ~85000
        
        # Alzheimer Parameters
        alzheimer_effectiveness = np.random.beta(10, 10, n)  # Mean ~0.50
        alzheimer_risk = np.random.beta(5, 95, n)  # Mean ~0.05
        alzheimer_mortality = np.random.beta(8, 2, n)  # Mean ~0.80
        alzheimer_intervention_cost = np.random.gamma(16, 217.9)  # Mean ~3487
        alzheimer_care_cost = np.random.gamma(4, 80000)  # Mean ~320000
        
        # Quality of Life Parameters
        healthy_utility = np.random.beta(19, 1, n)  # Mean ~0.95
        cvd_utility = np.random.beta(15, 5, n)  # Mean ~0.75
        diabetes_utility = np.random.beta(16, 4, n)  # Mean ~0.80
        cancer_utility = np.random.beta(13, 7, n)  # Mean ~0.65
        fracture_utility = np.random.beta(12, 8, n)  # Mean ~0.60
        alzheimer_utility = np.random.beta(8, 12, n)  # Mean ~0.40
        
        return {
            'cvd_effectiveness': cvd_effectiveness,
            'cvd_baseline_risk': cvd_baseline_risk,
            'cvd_mortality_rate': cvd_mortality_rate,
            'cvd_intervention_cost': cvd_intervention_cost,
            'cvd_event_cost': cvd_event_cost,
            'cvd_care_cost': cvd_care_cost,
            
            'diabetes_effectiveness': diabetes_effectiveness,
            'diabetes_progression': diabetes_progression,
            'diabetes_mortality': diabetes_mortality,
            'diabetes_intervention_cost': diabetes_intervention_cost,
            'diabetes_care_cost': diabetes_care_cost,
            'diabetes_complication_cost': diabetes_complication_cost,
            
            'cancer_effectiveness': cancer_effectiveness,
            'cancer_detection_rate': cancer_detection_rate,
            'cancer_mortality_reduction': cancer_mortality_reduction,
            'cancer_screening_cost': cancer_screening_cost,
            'cancer_treatment_cost': cancer_treatment_cost,
            
            'osteo_effectiveness': osteo_effectiveness,
            'fracture_risk': fracture_risk,
            'fracture_mortality': fracture_mortality,
            'osteo_intervention_cost': osteo_intervention_cost,
            'fracture_treatment_cost': fracture_treatment_cost,
            
            'alzheimer_effectiveness': alzheimer_effectiveness,
            'alzheimer_risk': alzheimer_risk,
            'alzheimer_mortality': alzheimer_mortality,
            'alzheimer_intervention_cost': alzheimer_intervention_cost,
            'alzheimer_care_cost': alzheimer_care_cost,
            
            'healthy_utility': healthy_utility,
            'cvd_utility': cvd_utility,
            'diabetes_utility': diabetes_utility,
            'cancer_utility': cancer_utility,
            'fracture_utility': fracture_utility,
            'alzheimer_utility': alzheimer_utility
        }
    
    def calculate_discounted_value(self, annual_value, duration_years=None):
        """Calculate present value with discounting"""
        if duration_years is None:
            duration_years = self.time_horizon
            
        total_pv = 0
        for year in range(duration_years):
            discount_factor = (1 + self.discount_rate) ** (-year)
            total_pv += annual_value * discount_factor
        return total_pv
    
    def run_comprehensive_model(self, params):
        """Run comprehensive prevention model for all interventions"""
        
        # Initialize totals
        total_events = np.zeros(self.n_iterations)
        total_deaths = np.zeros(self.n_iterations)
        total_qalys = np.zeros(self.n_iterations)
        total_savings = np.zeros(self.n_iterations)
        total_costs = np.zeros(self.n_iterations)
        
        # 1. CVD PREVENTION
        cvd_pop = self.target_populations['cvd']
        cvd_events = cvd_pop * params['cvd_baseline_risk'] * self.time_horizon
        cvd_prevented = cvd_events * params['cvd_effectiveness']
        cvd_deaths_prevented = cvd_prevented * params['cvd_mortality_rate']
        
        # CVD costs and savings (discounted)
        cvd_intervention_cost = cvd_pop * params['cvd_intervention_cost'] * self.time_horizon
        cvd_savings = cvd_prevented * (params['cvd_event_cost'] + params['cvd_care_cost'] * 3)
        cvd_savings = self.calculate_discounted_value(cvd_savings / self.time_horizon)
        
        # CVD QALYs (discounted)
        cvd_life_years = cvd_deaths_prevented * 10  # 10 years life extension
        cvd_quality_years = cvd_prevented * 2.5 * params['cvd_utility']
        cvd_qalys = self.calculate_discounted_value((cvd_life_years + cvd_quality_years) / self.time_horizon) * params['healthy_utility']
        
        total_events += cvd_prevented
        total_deaths += cvd_deaths_prevented
        total_qalys += cvd_qalys
        total_savings += cvd_savings
        total_costs += cvd_intervention_cost
        
        # 2. DIABETES PREVENTION
        diabetes_pop = self.target_populations['diabetes']
        diabetes_progression = diabetes_pop * params['diabetes_progression'] * self.time_horizon
        diabetes_prevented = diabetes_progression * params['diabetes_effectiveness']
        diabetes_deaths_prevented = diabetes_prevented * params['diabetes_mortality'] * 0.6
        
        # Diabetes costs and savings (discounted)
        diabetes_intervention_cost = diabetes_pop * params['diabetes_intervention_cost'] * self.time_horizon
        diabetes_savings = diabetes_prevented * (params['diabetes_care_cost'] + params['diabetes_complication_cost'] * 0.3)
        diabetes_savings = self.calculate_discounted_value(diabetes_savings / self.time_horizon)
        
        # Diabetes QALYs (discounted)
        diabetes_life_years = diabetes_deaths_prevented * 8
        diabetes_quality_years = diabetes_prevented * 3.0 * params['diabetes_utility']
        diabetes_qalys = self.calculate_discounted_value((diabetes_life_years + diabetes_quality_years) / self.time_horizon) * params['healthy_utility']
        
        total_events += diabetes_prevented
        total_deaths += diabetes_deaths_prevented
        total_qalys += diabetes_qalys
        total_savings += diabetes_savings
        total_costs += diabetes_intervention_cost
        
        # 3. CANCER SCREENING
        cancer_pop = self.target_populations['cancer']
        cancer_detected = cancer_pop * params['cancer_detection_rate'] * self.time_horizon
        cancer_deaths_prevented = cancer_detected * params['cancer_mortality_reduction']
        
        # Cancer costs and savings (discounted)
        cancer_intervention_cost = cancer_pop * params['cancer_screening_cost'] * self.time_horizon
        cancer_savings = cancer_deaths_prevented * params['cancer_treatment_cost'] * 2
        cancer_savings = self.calculate_discounted_value(cancer_savings / self.time_horizon)
        
        # Cancer QALYs (discounted)
        cancer_life_years = cancer_deaths_prevented * 12
        cancer_quality_years = cancer_detected * 2.5 * params['cancer_utility']
        cancer_qalys = self.calculate_discounted_value((cancer_life_years + cancer_quality_years) / self.time_horizon) * params['healthy_utility']
        
        total_events += cancer_detected
        total_deaths += cancer_deaths_prevented
        total_qalys += cancer_qalys
        total_savings += cancer_savings
        total_costs += cancer_intervention_cost
        
        # 4. OSTEOPOROSIS PREVENTION
        osteo_pop = self.target_populations['osteoporosis']
        fractures = osteo_pop * params['fracture_risk'] * self.time_horizon
        fractures_prevented = fractures * params['osteo_effectiveness']
        osteo_deaths_prevented = fractures_prevented * params['fracture_mortality']
        
        # Osteoporosis costs and savings (discounted)
        osteo_intervention_cost = osteo_pop * params['osteo_intervention_cost'] * self.time_horizon
        osteo_savings = fractures_prevented * params['fracture_treatment_cost']
        osteo_savings = self.calculate_discounted_value(osteo_savings / self.time_horizon)
        
        # Osteoporosis QALYs (discounted)
        osteo_life_years = osteo_deaths_prevented * 5
        osteo_quality_years = fractures_prevented * 1.5 * params['fracture_utility']
        osteo_qalys = self.calculate_discounted_value((osteo_life_years + osteo_quality_years) / self.time_horizon) * params['healthy_utility']
        
        total_events += fractures_prevented
        total_deaths += osteo_deaths_prevented
        total_qalys += osteo_qalys
        total_savings += osteo_savings
        total_costs += osteo_intervention_cost
        
        # 5. ALZHEIMER'S PREVENTION
        alzheimer_pop = self.target_populations['alzheimer']
        alzheimer_cases = alzheimer_pop * params['alzheimer_risk'] * self.time_horizon
        alzheimer_prevented = alzheimer_cases * params['alzheimer_effectiveness']
        alzheimer_deaths_prevented = alzheimer_prevented * params['alzheimer_mortality'] * 0.8
        
        # Alzheimer costs and savings (discounted)
        alzheimer_intervention_cost = alzheimer_pop * params['alzheimer_intervention_cost'] * self.time_horizon
        alzheimer_savings = alzheimer_prevented * params['alzheimer_care_cost'] * 0.7
        alzheimer_savings = self.calculate_discounted_value(alzheimer_savings / self.time_horizon)
        
        # Alzheimer QALYs (discounted, including caregiver benefits)
        alzheimer_life_years = alzheimer_deaths_prevented * 6
        alzheimer_quality_years = alzheimer_prevented * 3.0 * params['alzheimer_utility']
        caregiver_qalys = alzheimer_prevented * 2.0 * 0.8  # Caregiver benefit
        alzheimer_qalys = self.calculate_discounted_value((alzheimer_life_years + alzheimer_quality_years + caregiver_qalys) / self.time_horizon) * params['healthy_utility']
        
        total_events += alzheimer_prevented
        total_deaths += alzheimer_deaths_prevented
        total_qalys += alzheimer_qalys
        total_savings += alzheimer_savings
        total_costs += alzheimer_intervention_cost
        
        # Calculate ROI
        net_benefit = total_savings - total_costs
        roi = (net_benefit / total_costs) * 100
        
        return {
            'major_events_prevented': total_events,
            'premature_deaths_prevented': total_deaths,
            'qalys_gained': total_qalys,
            'direct_healthcare_savings': total_savings,
            'roi': roi,
            'total_investment': total_costs,
            'net_benefit': net_benefit
        }
    
    def run_monte_carlo(self):
        """Run complete Monte Carlo analysis"""
        print(f"🚀 Running {self.n_iterations:,}-iteration Monte Carlo analysis...")
        
        # Sample all parameters
        params = self.sample_parameters()
        
        # Run comprehensive model
        results = self.run_comprehensive_model(params)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Calculate 95% confidence intervals
        confidence_intervals = {}
        key_metrics = [
            'major_events_prevented',
            'premature_deaths_prevented', 
            'qalys_gained',
            'direct_healthcare_savings',
            'roi'
        ]
        
        for metric in key_metrics:
            data = results_df[metric]
            ci_lower = np.percentile(data, 2.5)
            ci_upper = np.percentile(data, 97.5)
            mean_val = np.mean(data)
            
            confidence_intervals[metric] = {
                'mean': float(mean_val),
                'lower_95_ci': float(ci_lower),
                'upper_95_ci': float(ci_upper),
                'std': float(np.std(data)),
                'relative_uncertainty': float((ci_upper - ci_lower) / mean_val) if mean_val > 0 else 0
            }
        
        return confidence_intervals, results_df

def main():
    """Run the complete analysis and print results"""
    print("="*80)
    print("🇦🇪 UAE PREVENTIVE HEALTH FRAMEWORK - MONTE CARLO ANALYSIS")
    print("="*80)
    print("✅ 10,000-iteration probabilistic sensitivity analysis")
    print("📊 Full economic modeling with discounting and uncertainty")
    print("🎯 95% confidence intervals for 5 key metrics")
    print("="*80)
    
    # Initialize and run analysis
    analysis = UAEMonteCarloAnalysis(n_iterations=10000)
    confidence_intervals, results_df = analysis.run_monte_carlo()
    
    # Print detailed results
    print("\n🎯 95% CONFIDENCE INTERVALS FOR UAE PREVENTIVE HEALTH METRICS")
    print("="*70)
    
    for i, (metric, ci) in enumerate(confidence_intervals.items(), 1):
        metric_name = metric.replace('_', ' ').title()
        
        if metric == 'major_events_prevented':
            print(f"\n{i}️⃣  MAJOR DISEASE EVENTS PREVENTED:")
            print(f"     Mean: {ci['mean']:,.0f} events")
            print(f"     95% CI: [{ci['lower_95_ci']:,.0f}, {ci['upper_95_ci']:,.0f}]")
            
        elif metric == 'premature_deaths_prevented':
            print(f"\n{i}️⃣  PREMATURE DEATHS PREVENTED:")
            print(f"     Mean: {ci['mean']:,.0f} deaths")
            print(f"     95% CI: [{ci['lower_95_ci']:,.0f}, {ci['upper_95_ci']:,.0f}]")
            
        elif metric == 'qalys_gained':
            print(f"\n{i}️⃣  QUALITY-ADJUSTED LIFE YEARS (QALYs) GAINED:")
            print(f"     Mean: {ci['mean']:,.0f} QALYs")
            print(f"     95% CI: [{ci['lower_95_ci']:,.0f}, {ci['upper_95_ci']:,.0f}]")
            
        elif metric == 'direct_healthcare_savings':
            print(f"\n{i}️⃣  DIRECT HEALTHCARE SAVINGS:")
            print(f"     Mean: AED {ci['mean']:,.0f}")
            print(f"     95% CI: [AED {ci['lower_95_ci']:,.0f}, AED {ci['upper_95_ci']:,.0f}]")
            
        elif metric == 'roi':
            print(f"\n{i}️⃣  RETURN ON INVESTMENT (ROI):")
            print(f"     Mean: {ci['mean']:,.1f}%")
            print(f"     95% CI: [{ci['lower_95_ci']:,.1f}%, {ci['upper_95_ci']:,.1f}%]")
        
        print(f"     Uncertainty Range: ±{ci['relative_uncertainty']*100:.1f}%")
    
    # Summary statistics
    print(f"\n💰 INVESTMENT SUMMARY:")
    print("-" * 40)
    investment_mean = np.mean(results_df['total_investment'])
    net_benefit_mean = np.mean(results_df['net_benefit'])
    
    print(f"   Total Investment: AED {investment_mean:,.0f}")
    print(f"   Net Benefit: AED {net_benefit_mean:,.0f}")
    
    if net_benefit_mean > 0:
        print(f"   💡 POSITIVE NET BENEFIT: Investment generates savings")
    else:
        print(f"   ⚠️  Investment required (costs exceed immediate savings)")
    
    # Probability analysis
    print(f"\n🎯 PROBABILITY ANALYSIS:")
    print("-" * 40)
    prob_positive_roi = (results_df['roi'] > 0).mean()
    prob_high_roi = (results_df['roi'] > 100).mean()
    prob_cost_saving = (results_df['net_benefit'] > 0).mean()
    
    print(f"   Probability of Positive ROI: {prob_positive_roi:.1%}")
    print(f"   Probability of ROI > 100%: {prob_high_roi:.1%}")
    print(f"   Probability of Cost-Saving: {prob_cost_saving:.1%}")
    
    print("\n" + "="*80)
    print("✅ MONTE CARLO ANALYSIS COMPLETE")
    print("📊 Results based on 10,000 iterations with full uncertainty")
    print("🎯 All 5 key metrics include 95% confidence intervals")
    print("💡 Economic modeling with proper discounting applied")
    print("="*80)
    
    # Save results
    with open('uae_monte_carlo_95ci.json', 'w') as f:
        json.dump(confidence_intervals, f, indent=2)
    
    results_df.to_csv('uae_monte_carlo_full_results.csv', index=False)
    
    print(f"\n📁 Results saved:")
    print(f"   - uae_monte_carlo_95ci.json: 95% confidence intervals")
    print(f"   - uae_monte_carlo_full_results.csv: Full iteration results")
    
    return confidence_intervals, results_df

if __name__ == "__main__":
    confidence_intervals, results_df = main()
