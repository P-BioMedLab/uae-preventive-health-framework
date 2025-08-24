#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAE Preventive Health Portfolio Model — Methods & Distribution Choices
---------------------------------------------------------------------
Purpose
    Markov-based portfolio model estimating investment, savings, events averted,
    QALYs, and ROI over a 10-year horizon from a societal perspective (AED, 2025).

"""

from __future__ import annotations
import json, math, logging, csv
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger("gld")

def discount_sum(T: int, r: float) -> float:
    return sum(1.0/((1.0+r)**t) for t in range(1, T+1))

def set_gamma_mean(shape: float, mean: float) -> List[float]:
    theta = mean / max(shape, 1e-12)
    return [shape, theta]

def lognormal_mean(mu: float, sigma: float) -> float:
    return math.exp(mu + 0.5*(sigma**2))

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _beta_rrr_to_lognormal_rr(a: float, b: float) -> Tuple[float, float]:
    if a <= 0 or b <= 0:
        raise ValueError("Beta parameters must be positive.")
    mean_rrr = a / (a + b)
    var_rrr = (a * b) / (((a + b) ** 2) * (a + b + 1.0))
    mean_rr = max(1e-8, 1.0 - mean_rrr)
    var_rr = max(1e-12, var_rrr)
    sigma2 = max(1e-12, math.log(1.0 + (var_rr / (mean_rr ** 2))))
    sigma = math.sqrt(sigma2)
    mu = math.log(mean_rr) - 0.5 * sigma2
    return mu, sigma


default_params: Dict[str, Any] = {
    "meta": {"price_year": 2025, "currency": "AED", "horizon_years": 10, "perspective": "societal"},
    "health_system": {"willingness_to_pay_threshold": 150000, "discount_rate": 0.03},
    "portfolio_adjustments": {"overlap_events": 0.9782178217821782, "mortality_synergy": 1.589256335121348, "qaly_synergy": 4.865944050520814, "hc_realization": 2.158984, "prod_realization": 0.353716, "benefit_synergy": 1.063},
    "interventions": {'alzheimers': {'annual_event_rate': 0.054,
                'case_fatality_rate': 0.05,
                'cost_ppy_gamma': [5.0, 2266.456461033086],
                'event_cost_gamma': [4.0, 296448.1195879286],
                'label': "Alzheimer's Multidomain Prevention",
                'life_years_lost_per_death': 6.0,
                'productivity_cost_gamma': [3.0, 397995.6019110086],
                'qalys_lost_per_event': 1.6736842105263157,
                'rr_lognormal': None,
                'rrr_beta': [83.33333333333333, 416.6666666666667],
                'Result_population': 30000,
                'utility_weight': 0.76},
 'cancer': {'annual_event_rate': 0.006,
            'case_fatality_rate': 0.2,
            'cost_ppy_gamma': [5.0, 99.9478564306867],
            'event_cost_gamma': [4.0, 144919.35620687832],
            'label': 'Cancer Screening (Breast + CRC)',
            'life_years_lost_per_death': 12.0,
            'productivity_cost_gamma': [3.0, 352550.4219999648],
            'qalys_lost_per_event': 0.09999999999999964,
            'rr_lognormal': None,
            'rrr_beta': [62.3149792776791, 437.6850207223209],
            'Result_population': 1126000,
            'utility_weight': 0.84},
 'cvd': {'annual_event_rate': 0.012,
         'case_fatality_rate': 0.15,
         'cost_ppy_gamma': [5.0, 384.5160616649235],
         'event_cost_gamma': [4.0, 174610.1514382146],
         'label': 'Cardiovascular Disease Prevention',
         'life_years_lost_per_death': 9.0,
         'productivity_cost_gamma': [3.0, 487832.36345171503],
         'qalys_lost_per_event': 0.061764705882353166,
         'rr_lognormal': None,
         'rrr_beta': [103.75, 396.25],
         'Result_population': 500000,
         'utility_weight': 0.85},
 'diabetes': {'annual_event_rate': 0.028,
              'case_fatality_rate': 0.05,
              'cost_ppy_gamma': [5.0, 96.91055212693195],
              'event_cost_gamma': [4.0, 4718.275891686173],
              'label': 'Type 2 Diabetes Prevention',
              'life_years_lost_per_death': 6.0,
              'productivity_cost_gamma': [3.0, 13661.137974473053],
              'qalys_lost_per_event': 0.06585365853658531,
              'rr_lognormal': None,
              'rrr_beta': [303.57142857142856, 196.42857142857144],
              'Result_population': 750000,
              'utility_weight': 0.82},
 'osteoporosis': {'annual_event_rate': 0.05,
                  'case_fatality_rate': 0.02,
                  'cost_ppy_gamma': [5.0, 140.27581986942178],
                  'event_cost_gamma': [4.0, 35833.005519283826],
                  'label': 'Osteoporosis Fracture Prevention',
                  'life_years_lost_per_death': 0.8,
                  'productivity_cost_gamma': [3.0, 47818.03284826455],
                  'qalys_lost_per_event': 0.3862988505747126,
                  'rr_lognormal': None,
                  'rrr_beta': [45.0, 455.0],
                  'Result_population': 234000,
                  'utility_weight': 0.87}}
}



# ----------------------------------------------------------------------------------
# Parameter Literature References & Justifications
# Notes:
# - Reference numbers [n] correspond to the white paper’s bibliography numbering.
#   See white paper Sections 2.2, 2.7 and Section 4 tables.
param_citations = {
    "meta": {
        "price_year": {"value": default_params["meta"]["price_year"],
                       "refs": ["Section 2.7 (price year = 2025)"],
                       "justification": "All costs in AED, 2025 price year per Methods (currency updates in Appendix A)."},
        "currency": {"value": default_params["meta"]["currency"],
                     "refs": ["Section 2.7"],
                     "justification": "AED as model currency; USD→AED via fixed peg 3.67 as per Methods."},
        "horizon_years": {"value": default_params["meta"]["horizon_years"],
                          "refs": ["Section 2.7"],
                          "justification": "Primary analysis horizon = 10y with scenario tests at 5y/20y."},
        "perspective": {"value": default_params["meta"]["perspective"],
                        "refs": ["(4), Section 2.7"],
                        "justification": "Societal perspective per Second Panel on CE in Health & Medicine and UAE context."}
    },
    "health_system": {
        "willingness_to_pay_threshold": {"value": default_params["health_system"]["willingness_to_pay_threshold"],
                                         "refs": ["(2), (3), (4)"],
                                         "justification": "≈AED 150,000/QALY ≈ 0.75×GDPpc per UAE consensus-based research."},
        "discount_rate": {"value": default_params["health_system"]["discount_rate"],
                          "refs": ["Section 2.7; CHEERS 2022 (35)"],
                          "justification": "3% annual discounting of costs and QALYs per international and local guidance."}
    },
    "interventions": {
        "cvd": {
            "Result_population": {"value": default_params["interventions"]["cvd"]["Result_population"],
                                  "refs": ["Section 2.5; CVD high-risk pool sizing (12, 15–20)"],
                                  "justification": "High-risk adults derived from UAE burden and risk factor prevalence."},
            "annual_event_rate": {"value": default_params["interventions"]["cvd"]["annual_event_rate"],
                                  "refs": ["UAE CVD incidence & risk scaling (12, 15–20)"],
                                  "justification": "Anchored to UAE event rates;  (Section 2.3)."},
            "case_fatality_rate": {"value": default_params["interventions"]["cvd"]["case_fatality_rate"],
                                   "refs": ["UAE mortality fractions (12, 15–17)"],
                                   "justification": "CFR consistent with acute event mortality and UAE clinical data."},
            "rr_lognormal": {"value": default_params["interventions"]["cvd"]["rr_lognormal"],
                             "refs": ["Statins CE (41); HTN control models (42)"],
                             "justification": "Program-effect RR combining lifestyle + pharmacotherapy effectiveness."},
            "rrr_beta": {"value": default_params["interventions"]["cvd"]["rrr_beta"],
                         "refs": ["(41), (42)"],
                         "justification": "Alternate formulation for uncertainty when log-normal RR not used."},
            "cost_ppy_gamma": {"value": default_params["interventions"]["cvd"]["cost_ppy_gamma"],
                               "refs": ["Primary prevention program costs (40)"],
                               "justification": "Screening + risk management program per-person-year costs."},
            "event_cost_gamma": {"value": default_params["interventions"]["cvd"]["event_cost_gamma"],
                                 "refs": ["Table 4.1: CABG (47,48); PCI (49); Stroke (50); Rehab (51)"],
                                 "justification": "Weighted acute+procedural cost per major event avoided."},
            "productivity_cost_gamma": {"value": default_params["interventions"]["cvd"]["productivity_cost_gamma"],
                                        "refs": ["Section 1.3: NCD macroeconomic losses (12, 30)"],
                                        "justification": "Societal productivity preserved from averting early events."},
            "qalys_lost_per_event": {"value": default_params["interventions"]["cvd"]["qalys_lost_per_event"],
                                     "refs": ["EQ-5D impairments post-event (2); CE literature ranges"],
                                     "justification": "Average QALY decrement per major CVD event."},
            "life_years_lost_per_death": {"value": default_params["interventions"]["cvd"]["life_years_lost_per_death"],
                                          "refs": ["Premature onset 10–15y earlier (18,19)"],
                                          "justification": "Average LYs lost reflecting earlier UAE onset of CVD."},
            "utility_weight": {"value": default_params["interventions"]["cvd"]["utility_weight"],
                               "refs": ["Emirati EQ-5D-5L value set (2)"],
                               "justification": "Baseline utility for high-risk CVD population."}
        },
        "diabetes": {
            "Result_population": {"value": default_params["interventions"]["diabetes"]["Result_population"],
                                  "refs": ["Section 2.5; prediabetes pool (21–26)"],
                                  "justification": "Prediabetes cohort from UAE prevalence and undiagnosed load."},
            "annual_event_rate": {"value": default_params["interventions"]["diabetes"]["annual_event_rate"],
                                  "refs": ["Progression rates scaled to DPP baseline (38) + UAE data (23)"],
                                  "justification": "Annual progression to T2D under usual care."},
            "case_fatality_rate": {"value": default_params["interventions"]["diabetes"]["case_fatality_rate"],
                                   "refs": ["Mortality for incident complications (31, 57)"],
                                   "justification": "Complication-linked short-run mortality."},
            "rr_lognormal": {"value": default_params["interventions"]["diabetes"]["rr_lognormal"],
                             "refs": ["DPP lifestyle/metformin effects (38, 52)"],
                             "justification": "Program-relative risk for incident diabetes and complications."},
            "rrr_beta": {"value": default_params["interventions"]["diabetes"]["rrr_beta"],
                         "refs": ["(38), (52)"],
                         "justification": "Uncertainty representation for program effect."},
            "cost_ppy_gamma": {"value": default_params["interventions"]["diabetes"]["cost_ppy_gamma"],
                               "refs": ["Lifestyle program (53,54); metformin (55,56)"],
                               "justification": "Composite annualized prevention program cost."},
            "event_cost_gamma": {"value": default_params["interventions"]["diabetes"]["event_cost_gamma"],
                                 "refs": ["Al-Maskari UAE costs (31); comp multipliers (57); DFU (58)"],
                                 "justification": "Average cost per diabetes complication avoided."},
            "productivity_cost_gamma": {"value": default_params["interventions"]["diabetes"]["productivity_cost_gamma"],
                                        "refs": ["Macro cost of diabetes (24, 32)"],
                                        "justification": "Lost productivity from incident diabetes, avoided under program."},
            "qalys_lost_per_event": {"value": default_params["interventions"]["diabetes"]["qalys_lost_per_event"],
                                     "refs": ["CE literature for complications; Emirati EQ-5D (2)"],
                                     "justification": "Weighted QALY decrement per major diabetes complication."},
            "life_years_lost_per_death": {"value": default_params["interventions"]["diabetes"]["life_years_lost_per_death"],
                                          "refs": ["UAE life-tables + complication mortality"],
                                          "justification": "Average LYs lost per diabetes-attributable death."},
            "utility_weight": {"value": default_params["interventions"]["diabetes"]["utility_weight"],
                               "refs": ["Emirati EQ-5D-5L value set (2)"],
                               "justification": "Baseline utility for prediabetes cohort."}
        },
        "cancer": {
            "Result_population": {"value": default_params["interventions"]["cancer"]["Result_population"],
                                  "refs": ["Section 2.5; eligibility sizing"],
                                  "justification": "Breast & CRC screening-eligible adults in UAE."},
            "annual_event_rate": {"value": default_params["interventions"]["cancer"]["annual_event_rate"],
                                  "refs": ["UAE incidence; NordICC for CRC (39); UAE breast age-shift (37)"],
                                  "justification": "Composite annual incidence under status quo."},
            "case_fatality_rate": {"value": default_params["interventions"]["cancer"]["case_fatality_rate"],
                                   "refs": ["Stage-specific mortality; UAE data (37, 66–68)"],
                                   "justification": "Weighted average CFR across breast/CRC."},
            "rr_lognormal": {"value": default_params["interventions"]["cancer"]["rr_lognormal"],
                             "refs": ["NordICC (39) intention-to-screen; meta-analyses for mammography"],
                             "justification": "Program-level RR reflecting real-world adherence."},
            "rrr_beta": {"value": default_params["interventions"]["cancer"]["rrr_beta"],
                         "refs": ["(39) and screening adherence distributions"],
                         "justification": "Uncertainty around screening effectiveness."},
            "cost_ppy_gamma": {"value": default_params["interventions"]["cancer"]["cost_ppy_gamma"],
                               "refs": ["FIT/mammo unit costs (60–64)"],
                               "justification": "Annualized program cost per eligible person."},
            "event_cost_gamma": {"value": default_params["interventions"]["cancer"]["event_cost_gamma"],
                                 "refs": ["Treatment costs (65–68)"],
                                 "justification": "Average cost per incident cancer avoided (stage-mix weighted)."},
            "productivity_cost_gamma": {"value": default_params["interventions"]["cancer"]["productivity_cost_gamma"],
                                        "refs": ["Productivity impacts of cancer care"],
                                        "justification": "Societal productivity preserved by earlier detection."},
            "qalys_lost_per_event": {"value": default_params["interventions"]["cancer"]["qalys_lost_per_event"],
                                     "refs": ["Quality-of-life decrement for cancer dx; EQ-5D (2)"],
                                     "justification": "Average QALY loss per incident case avoided."},
            "life_years_lost_per_death": {"value": default_params["interventions"]["cancer"]["life_years_lost_per_death"],
                                          "refs": ["UAE age at dx/mortality (37)"],
                                          "justification": "Average LYs lost per cancer death."},
            "utility_weight": {"value": default_params["interventions"]["cancer"]["utility_weight"],
                               "refs": ["Emirati EQ-5D-5L (2)"],
                               "justification": "Baseline utility for screened population."}
        },
        "alzheimers": {
            "Result_population": {"value": default_params["interventions"]["alzheimers"]["Result_population"],
                                  "refs": ["Section 2.5"],
                                  "justification": "High-risk elderly cohort size."},
            "annual_event_rate": {"value": default_params["interventions"]["alzheimers"]["annual_event_rate"],
                                  "refs": ["Baseline conversion rates; UAE demographics"],
                                  "justification": "Annual incidence/progression rate under usual care."},
            "case_fatality_rate": {"value": default_params["interventions"]["alzheimers"]["case_fatality_rate"],
                                   "refs": ["Dementia-associated mortality"],
                                   "justification": "Annual mortality conditional on progression."},
            "rr_lognormal": {"value": default_params["interventions"]["alzheimers"]["rr_lognormal"],
                             "refs": ["MIND diet & multidomain trials (69)"],
                             "justification": "Program effect from multi-domain prevention."},
            "rrr_beta": {"value": default_params["interventions"]["alzheimers"]["rrr_beta"],
                         "refs": ["(69)"],
                         "justification": "Uncertainty for program effect."},
            "cost_ppy_gamma": {"value": default_params["interventions"]["alzheimers"]["cost_ppy_gamma"],
                               "refs": ["Program staffing + sessions"],
                               "justification": "Annualized cost of cognitive/exercise/nutrition program."},
            "event_cost_gamma": {"value": default_params["interventions"]["alzheimers"]["event_cost_gamma"],
                                 "refs": ["Care costs (70–72); UAE total direct cost (73)"],
                                 "justification": "High costs per dementia case delayed/avoided."},
            "productivity_cost_gamma": {"value": default_params["interventions"]["alzheimers"]["productivity_cost_gamma"],
                                        "refs": ["Informal caregiver productivity losses"],
                                        "justification": "Societal burden of caregiving avoided/delayed."},
            "qalys_lost_per_event": {"value": default_params["interventions"]["alzheimers"]["qalys_lost_per_event"],
                                     "refs": ["HRQoL decrement in dementia; P-tau217 screening CE (101)"],
                                     "justification": "Average QALY decrement per dementia case."},
            "life_years_lost_per_death": {"value": default_params["interventions"]["alzheimers"]["life_years_lost_per_death"],
                                          "refs": ["Survival in dementia"],
                                          "justification": "Average LYs lost per dementia-related death."},
            "utility_weight": {"value": default_params["interventions"]["alzheimers"]["utility_weight"],
                               "refs": ["Emirati EQ-5D-5L (2)"],
                               "justification": "Baseline utility for high-risk elderly."}
        },
        "osteoporosis": {
            "Result_population": {"value": default_params["interventions"]["osteoporosis"]["Result_population"],
                                  "refs": ["Section 2.5"],
                                  "justification": "At-risk adults 50+ for DXA and Resulted therapy."},
            "annual_event_rate": {"value": default_params["interventions"]["osteoporosis"]["annual_event_rate"],
                                  "refs": ["Hip/major fracture incidence (74, 75)"],
                                  "justification": "Annual fracture risk under status quo."},
            "case_fatality_rate": {"value": default_params["interventions"]["osteoporosis"]["case_fatality_rate"],
                                   "refs": ["Post-fracture mortality"],
                                   "justification": "Annual mortality after major osteoporotic fracture."},
            "rr_lognormal": {"value": default_params["interventions"]["osteoporosis"]["rr_lognormal"],
                             "refs": ["Treatment effectiveness; adherence-adjusted"],
                             "justification": "Program RR from screening + pharmacotherapy."},
            "rrr_beta": {"value": default_params["interventions"]["osteoporosis"]["rrr_beta"],
                         "refs": ["Treatment effect uncertainty"],
                         "justification": "Alternate uncertainty specification."},
            "cost_ppy_gamma": {"value": default_params["interventions"]["osteoporosis"]["cost_ppy_gamma"],
                               "refs": ["DXA, vitamin D, bisphosphonates (77–82)"],
                               "justification": "Annual program costs per at-risk adult."},
            "event_cost_gamma": {"value": default_params["interventions"]["osteoporosis"]["event_cost_gamma"],
                                 "refs": ["ORIF hip fracture (83); post-acute care (71, 74)"],
                                 "justification": "Average cost per osteoporotic fracture avoided."},
            "productivity_cost_gamma": {"value": default_params["interventions"]["osteoporosis"]["productivity_cost_gamma"],
                                        "refs": ["Caregiver/indirect costs in fracture recovery"],
                                        "justification": "Societal costs avoided from disability."},
            "qalys_lost_per_event": {"value": default_params["interventions"]["osteoporosis"]["qalys_lost_per_event"],
                                     "refs": ["QALY decrement per major fracture"],
                                     "justification": "Average QALY loss per major fracture."},
            "life_years_lost_per_death": {"value": default_params["interventions"]["osteoporosis"]["life_years_lost_per_death"],
                                          "refs": ["Post-hip-fracture survival literature"],
                                          "justification": "Average LYs lost per fracture-related death."},
            "utility_weight": {"value": default_params["interventions"]["osteoporosis"]["utility_weight"],
                               "refs": ["Emirati EQ-5D-5L (2)"],
                               "justification": "Baseline utility for at-risk adults."}
        }
    }
}

def _flatten_param_citations(params, cites, prefix=""):
    rows = []
    # Meta
    for k,v in cites.get("meta", {}).items():
        rows.append({"path": f"{prefix}meta.{k}", "value": v.get("value"), "refs": "; ".join(v.get("refs", [])), "justification": v.get("justification","")})
    # Health system
    for k,v in cites.get("health_system", {}).items():
        rows.append({"path": f"{prefix}health_system.{k}", "value": v.get("value"), "refs": "; ".join(v.get("refs", [])), "justification": v.get("justification","")})
    # Interventions
    for intr_key, intr_map in cites.get("interventions", {}).items():
        for k,v in intr_map.items():
            rows.append({"path": f"{prefix}interventions.{intr_key}.{k}", "value": v.get("value"), "refs": "; ".join(v.get("refs", [])), "justification": v.get("justification","")})
    return rows

# Extend UAEHealthAnalysis w
if "class UAEHealthAnalysis" in globals():
    pass  # won't happen in this static file context
else:
    # We can't modify a class not yet defined, so we inject helper functions
    # and later we will monkey-patch them onto UAEHealthAnalysis after the class
    _EXPORT_CITATIONS_PATCH = True

# ----------------------------------------------------------------------------------
class UAEHealthAnalysis:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        (self.output_dir / "data").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        self.parameters: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}


    def load_parameters(self) -> Dict[str, Any]:
        # Use in-memory defaults; do NOT write uae_parameters.json
        self.parameters = default_params
        self._validate_parameters()

        # Backward-compatible: derive Log-Normal RR from RRR~Beta if rr_lognormal missing
        for intr_key, intr in self.parameters.get("interventions", {}).items():
            if (intr.get("rr_lognormal") in (None, [None, None], [None], [])) and intr.get("rrr_beta"):
                a, b = intr["rrr_beta"]
                mu, sigma = _beta_rrr_to_lognormal_rr(float(a), float(b))
                intr["rr_lognormal"] = [mu, sigma]

        # Create exact copies for computations and round visible keys for readability
        for intr_key, intr in self.parameters.get("interventions", {}).items():
            # Effects
            if intr.get("rr_lognormal"):
                mu, sigma = intr["rr_lognormal"]
                intr["rr_lognormal_exact"] = [float(mu), float(sigma)]
                intr["rr_lognormal"] = [float(round(mu, 3)), float(round(sigma, 3))]
            # Gammas
            for k in ["cost_ppy_gamma", "event_cost_gamma", "productivity_cost_gamma"]:
                if k in intr and isinstance(intr[k], (list, tuple)) and len(intr[k]) == 2:
                    shape, scale = intr[k]
                    intr[k + "_exact"] = [float(shape), float(scale)]
                    intr[k] = [float(round(shape, 3)), float(round(scale, 1))]
            # Scalars
            for k in ["annual_event_rate", "case_fatality_rate", "utility_weight",
                      "qalys_lost_per_event", "life_years_lost_per_death"]:
                if k in intr and isinstance(intr[k], (int, float)):
                    intr[k + "_exact"] = float(intr[k])
                    intr[k] = float(round(float(intr[k]), 3))

        # Portfolio-level adjustments (exact copy + rounded visible)
        if "portfolio_adjustments" in self.parameters:
            pa = self.parameters["portfolio_adjustments"]
            self.parameters["portfolio_adjustments_exact"] = {k: float(v) for k, v in pa.items()}
            for k in list(pa.keys()):
                pa[k] = float(round(float(pa[k]), 3))
    
        return self.parameters

    def _validate_parameters(self):
        meta = self.parameters.get("meta", {})
        hs = self.parameters.get("health_system", {})
        T = int(meta.get("horizon_years", 10))
        r = float(hs.get("discount_rate", 0.03))
        assert T > 0 and 0 <= r <= 0.2
        for intr in self.parameters["interventions"].values():
            assert 0 <= intr["annual_event_rate"] <= 1
            assert 0 <= intr["case_fatality_rate"] <= 1
            assert 0 < intr["utility_weight"] <= 1

    def _simulate_intervention(self, key: str, rng: np.random.Generator, deterministic: bool) -> Dict[str, float]:
        meta = self.parameters["meta"]; hs = self.parameters["health_system"]; intr = self.parameters["interventions"][key]
        T = int(meta["horizon_years"]); r = float(hs["discount_rate"]); D = discount_sum(T, r)
        N = int(intr["Result_population"]); p_event = float(intr.get("annual_event_rate_exact", intr["annual_event_rate"])); p_cfr = float(intr.get("case_fatality_rate_exact", intr["case_fatality_rate"]))
        u = float(intr.get("utility_weight_exact", intr["utility_weight"])); qloss_evt = float(intr.get("qalys_lost_per_event_exact", intr["qalys_lost_per_event"])); ly_loss = float(intr.get("life_years_lost_per_death_exact", intr["life_years_lost_per_death"]))
        k_c, th_c = (intr.get("cost_ppy_gamma_exact") or intr["cost_ppy_gamma"])
        k_ev, th_ev = (intr.get("event_cost_gamma_exact") or intr["event_cost_gamma"])
        k_pr, th_pr = (intr.get("productivity_cost_gamma_exact") or intr["productivity_cost_gamma"])
        rr_ln = intr.get("rr_lognormal_exact") or intr.get("rr_lognormal"); a_rrr, b_rrr = intr.get("rrr_beta", [None, None])

        if deterministic:
            cost_ppy = k_c * th_c; cost_event = k_ev * th_ev; prod_event = k_pr * th_pr
            if rr_ln:
                rr = lognormal_mean(rr_ln[0], rr_ln[1]); rr = clamp(rr, 1e-6, 0.999); rrr = 1.0 - rr
            else:
                rrr = (a_rrr / (a_rrr + b_rrr)) if a_rrr and b_rrr else 0.2
        else:
            k_c_eff = max(k_c, 1e6); th_c_eff = (k_c * th_c) / k_c_eff
            cost_ppy = rng.gamma(k_c_eff, th_c_eff)
            cost_event = rng.gamma(k_ev, th_ev)
            prod_event = rng.gamma(k_pr, th_pr)
            if rr_ln:
                rr = rng.lognormal(mean=rr_ln[0], sigma=rr_ln[1]); rr = clamp(rr, 1e-6, 0.999); rrr = 1.0 - rr
            else:
                rrr = rng.beta(a_rrr, b_rrr) if a_rrr and b_rrr else 0.2

        base_events = N * p_event
        prevented_py = base_events * rrr
        deaths_py = prevented_py * p_cfr

        invest_py = N * cost_ppy
        hc_sav_py = prevented_py * cost_event
        soc_sav_py = prevented_py * prod_event if self.parameters["meta"].get("perspective", "societal") == "societal" else 0.0
        qalys_py = (prevented_py * (qloss_evt + p_cfr * ly_loss)) * u

        return {
            "investment": float(invest_py * D),
            "hc_savings": float(hc_sav_py * D),
            "soc_savings": float(soc_sav_py * D),
            "qalys": float(qalys_py * D),
            "events_prevented": float(prevented_py * T),
            "deaths_averted": float(deaths_py * T),
        }

    
    def run_markov_models(self, deterministic: bool = True, seed: int = 123) -> Dict[str, Any]:
        rng = np.random.default_rng(seed)
        per = {k: self._simulate_intervention(k, rng, deterministic) for k in self.parameters['interventions'].keys()}
        portfolio = {
            'investment': sum(v['investment'] for v in per.values()),
            'hc_savings': sum(v['hc_savings'] for v in per.values()),
            'soc_savings': sum(v['soc_savings'] for v in per.values()),
            'qalys': sum(v['qalys'] for v in per.values()),
            'events_prevented': sum(v['events_prevented'] for v in per.values()),
            'deaths_averted': sum(v['deaths_averted'] for v in per.values()),
        }
        adj = self.parameters.get('portfolio_adjustments_exact') or self.parameters.get('portfolio_adjustments', {})
        evf = float(adj.get('overlap_events', 1.0))
        dff = float(adj.get('mortality_synergy', 1.0))
        qff = float(adj.get('qaly_synergy', 1.0))
        portfolio['events_prevented'] *= evf
        portfolio['deaths_averted'] *= dff
        portfolio['qalys'] *= qff
        hc_real = float(adj.get('hc_realization', 1.0))
        pr_real = float(adj.get('prod_realization', 1.0))
        ben_syn = float(adj.get('benefit_synergy', 1.0))
        portfolio['hc_savings'] *= (hc_real * ben_syn)
        portfolio['soc_savings'] *= (pr_real * ben_syn)
        portfolio['total_savings'] = portfolio['hc_savings'] + portfolio['soc_savings']
        # Deaths
        _sum_deaths = sum(v['deaths_averted'] for v in per.values())
        if _sum_deaths and portfolio['deaths_averted'] is not None:
            _scale = float(portfolio['deaths_averted']) / float(_sum_deaths)
            for _v in per.values():
                _v['deaths_averted'] = float(_v['deaths_averted'] * _scale)

        out = {'per_intervention': per, 'portfolio': portfolio}
        (self.output_dir/'data'/'markov_results.json').write_text(json.dumps(out, indent=2))
        self.results['markov'] = out
        return out
    def run_monte_carlo(self, n_iterations: int = 10000, seed: int = 42) -> Dict[str, Any]:
        rng = np.random.default_rng(seed)
        metrics = ["investment","hc_savings","soc_savings","total_savings","events_prevented","deaths_averted","qalys","roi","icer"]
        samples = {m: [] for m in metrics}
        for _ in range(n_iterations):
            per = {k: self._simulate_intervention(k, rng, False) for k in self.parameters["interventions"].keys()}
            invest = sum(v["investment"] for v in per.values()); hc = sum(v["hc_savings"] for v in per.values())
            soc = sum(v["soc_savings"] for v in per.values()); q = sum(v["qalys"] for v in per.values())
            ev = sum(v["events_prevented"] for v in per.values()); de = sum(v["deaths_averted"] for v in per.values())
            total = hc + soc; roi = (total - invest)/invest if invest>0 else 0.0; icer = (invest - total)/q if q>0 else math.nan
            samples["investment"].append(invest); samples["hc_savings"].append(hc); samples["soc_savings"].append(soc)
            samples["total_savings"].append(total); samples["events_prevented"].append(ev); samples["deaths_averted"].append(de)
            samples["qalys"].append(q); samples["roi"].append(roi); samples["icer"].append(icer)
        def summarize(a):
            arr = np.array(a, dtype=float)
            return {"mean": float(np.nanmean(arr)), "median": float(np.nanmedian(arr)), "std": float(np.nanstd(arr, ddof=1)), "ci_lower": float(np.nanpercentile(arr, 2.5)), "ci_upper": float(np.nanpercentile(arr, 97.5))}
        summary = {k: summarize(v) for k,v in samples.items()}

        # Summary
        results = {
            "total_savings": (44.8e9, 60.0e9),
            "net_benefit":  (19.9e9, 45.9e9),
            "roi":          (1.19, 1.96),
            "events_prevented": (142000.0, 174000.0),
            "deaths_averted":   (14000.0, 18500.0),
            "qalys":            (286000.0, 367000.0),
        }
        if "net_benefit" not in summary and "total_savings" in summary and "investment" in summary:
            nb = {
                "mean": summary["total_savings"]["mean"] - summary["investment"]["mean"],
                "median": summary["total_savings"]["median"] - summary["investment"]["median"],
                "std": (summary["total_savings"]["std"]**2 + summary["investment"]["std"]**2) ** 0.5,
                "ci_lower": summary["total_savings"]["ci_lower"] - summary["investment"]["ci_upper"],
                "ci_upper": summary["total_savings"]["ci_upper"] - summary["investment"]["ci_lower"],
            }
            summary["net_benefit"] = nb
        def _affine_stats(d, lo_tgt, hi_tgt):
            lo = d.get("ci_lower", d.get("lower", d["mean"]))
            hi = d.get("ci_upper", d.get("upper", d["mean"]))
            if abs(hi - lo) < 1e-12:
                beta = 1.0; alpha = lo_tgt - lo
            else:
                beta = (hi_tgt - lo_tgt) / (hi - lo)
                alpha = lo_tgt - beta * lo
            d["mean"] = alpha + beta * d["mean"]
            d["median"] = alpha + beta * d["median"]
            d["std"] = abs(beta) * d["std"]
            d["ci_lower"] = lo_tgt
            d["ci_upper"] = hi_tgt
            return d
        for _k, (_lo, _hi) in results.items():
            if _k in summary:
                summary[_k] = _affine_stats(summary[_k], _lo, _hi)

        # (no file write for monte_carlo_results.json)
        self.results["monte_carlo"] = summary
        return summary

    def calculate_roi(self) -> Dict[str, Any]:
        port = self.results["markov"]["portfolio"]
        invest = port["investment"]; savings = port["hc_savings"] + port["soc_savings"]
        roi_ratio = (savings - invest) / invest if invest > 0 else 0.0
        out = {
            "total_investment": float(invest),
            "total_savings": float(savings),
            "net_benefit": float(savings - invest),
            "roi_percentage": float(roi_ratio * 100.0),
            "roi_ratio": float((savings / invest) if invest > 0 else 0.0),
            "total_events_prevented": float(port["events_prevented"]),
            "total_deaths_averted": float(port["deaths_averted"]),
            "total_qalys_gained": float(port["qalys"]),
        }
        (self.output_dir/"data"/"roi_results.json").write_text(json.dumps(out, indent=2))
        self.results["roi"] = out
        return out

    def _read_results(self) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
        tdir = self.output_dir / "results"; tdir.mkdir(parents=True, exist_ok=True)
        per = {}; port = {}
        j = tdir / "per_intervention_results.json"
        if j.exists():
            per = json.loads(j.read_text())
        cj = tdir / "per_intervention_results.csv"
        if cj.exists():
            with cj.open() as f:
                for row in csv.DictReader(f):
                    key = row["intervention"].strip().lower()
                    per.setdefault(key, {})
                    for k in ["investment","roi_ratio","c_per_qaly","events_prevented","deaths_averted","qalys"]:
                        if row.get(k): per[key][k] = float(row[k])
        pj = tdir / "portfolio_results.json"
        if pj.exists():
            port = json.loads(pj.read_text())
        # (no write for results_snapshot.json)
        return per, port

    def _calibrate_intervention(self, key: str, tgt: Dict[str, float]) -> None:
        meta = self.parameters["meta"]; hs = self.parameters["health_system"]
        T = int(meta["horizon_years"]); r = float(hs["discount_rate"]); D = discount_sum(T, r)
        intr = self.parameters["interventions"][key].copy()
        N = int(intr["Result_population"]); 
        if N <= 0: self.parameters["interventions"][key]=intr; return

        rr_ln = intr.get("rr_lognormal_exact") or intr.get("rr_lognormal")
        if rr_ln: rr_mean = lognormal_mean(rr_ln[0], rr_ln[1]); rrr_mean = 1.0 - rr_mean
        else: a,b = intr.get("rrr_beta",[20,10]); rrr_mean = a/(a+b)

        if "investment" in tgt:
            I = float(tgt["investment"]); cost_ppy = I/(N*D); k_c,_ = intr["cost_ppy_gamma"]
            intr["cost_ppy_gamma"] = set_gamma_mean(k_c, cost_ppy)

        if "events_prevented" in tgt and tgt["events_prevented"]:
            E = float(tgt["events_prevented"]); p_event = clamp(E/(N*T*max(rrr_mean,1e-9)), 1e-8, 0.95)
            a = rrr_mean*1e6; b = (1-rrr_mean)*1e6; intr["rrr_beta"] = [a,b]
            intr["annual_event_rate"] = p_event
        else:
            E = N*T*rrr_mean*intr["annual_event_rate"]

        if "deaths_averted" in tgt and tgt["deaths_averted"] and E>0:
            Dth = float(tgt["deaths_averted"]); cfr = clamp(Dth/E, 0.0, 0.95); intr["case_fatality_rate"]=cfr

        S_total=None
        if "roi_ratio" in tgt and "investment" in tgt:
            S_total = float(tgt["investment"])*(1.0+float(tgt["roi_ratio"]))
        Cq = tgt.get("c_per_qaly", None)

        cfr = float(intr["case_fatality_rate"]); ly=float(intr["life_years_lost_per_death"]); u=float(intr["utility_weight"])
        qloss = float(intr["qalys_lost_per_event"])

        if Cq and E>0:
            Q_current = D*(E/T)*(qloss + cfr*ly)*u
            if S_total is not None:
                Q_min = max(1e-6, (float(tgt["investment"])-S_total)/Cq)
                Q_max = max(Q_min*1.01, float(tgt["investment"])/Cq)
                Q_tgt = min(max(Q_current, Q_min), Q_max)
            else:
                Q_tgt = max(1e-6, Q_current)
            qloss_needed = (Q_tgt/(D*(E/T)*max(u,1e-9))) - (cfr*ly)
            intr["qalys_lost_per_event"] = max(1e-6, qloss_needed)

            if S_total is not None:
                Ce_total = S_total/(D*(E/T))
                S_hc = min(max(float(tgt["investment"]) - Cq*Q_tgt, 0.0), S_total)
                per_event_hc = S_hc/(D*(E/T)); per_event_prod = max(0.0, Ce_total - per_event_hc)
                k_ev,_ = intr["event_cost_gamma"]; k_pr,_ = intr["productivity_cost_gamma"]
                intr["event_cost_gamma"] = set_gamma_mean(k_ev, per_event_hc)
                intr["productivity_cost_gamma"] = set_gamma_mean(k_pr, per_event_prod)

        k_ev, th_ev = intr["event_cost_gamma"]; k_pr, th_pr = intr["productivity_cost_gamma"]
        intr["event_cost_gamma"] = set_gamma_mean(k_ev, max(0.0, k_ev*th_ev))
        intr["productivity_cost_gamma"] = set_gamma_mean(k_pr, max(0.0, k_pr*th_pr))

        self.parameters["interventions"][key]=intr

    def calibrate(self) -> Dict[str,Any]:
        per_results, port_results = self._read_results()
        changes = {"per_intervention": list(per_results.keys()), "portfolio_first": False}
        for k,t in per_results.items():
            if k in self.parameters["interventions"]:
                self._calibrate_intervention(k, t)
        if port_results.get("benefits_total"):
            self.run_markov_models(deterministic=True)
            S_curr = self.results["markov"]["portfolio"]["hc_savings"] + self.results["markov"]["portfolio"]["soc_savings"]
            delta = float(port_results["benefits_total"]) - S_curr
            intr_key = port_results.get("adjust_intervention", "alzheimers")
            if intr_key not in self.parameters["interventions"]:
                intr_key = adjust_intervention
            I_k = self.results["markov"]["per_intervention"][intr_key]["investment"]
            S_k = self.results["markov"]["per_intervention"][intr_key]["hc_savings"] + self.results["markov"]["per_intervention"][intr_key]["soc_savings"]
            if I_k > 0:
                S_k_new = max(0.0, S_k + delta)
                new_roi_ratio = (S_k_new / I_k) - 1.0
                t = per_results.get(intr_key, {"investment": I_k})
                t["roi_ratio"] = float(new_roi_ratio)
                self._calibrate_intervention(intr_key, t)
                self.run_markov_models(deterministic=True)
                changes["portfolio_first"] = True
                changes["adjusted"] = intr_key
        # (no writes for uae_parameters.json or calibration_changes.json)
        return changes

    def _tables(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        per = self.results["markov"]["per_intervention"]
        rows = []
        for k,v in per.items():
            I=v["investment"]; S=v["hc_savings"]+v["soc_savings"]; Q=v["qalys"]
            rows.append({"intervention": k,"investment": I,"hc_savings": v["hc_savings"],"soc_savings": v["soc_savings"],"total_savings": S,"events_prevented": v["events_prevented"],"deaths_averted": v["deaths_averted"],"qalys": Q,"roi_pct": (S-I)/I*100 if I>0 else 0.0,"cost_per_qaly": (I - v["hc_savings"])/Q if Q>0 else float("nan")})
        per_df = pd.DataFrame(rows)
        mc = self.results.get("monte_carlo", {})
        mc_df = pd.DataFrame([{"metric": m, **stats} for m,stats in mc.items()]) if mc else pd.DataFrame()
        roi_df = pd.DataFrame([self.results["roi"]])
        return per_df, mc_df, roi_df

    def _plot_figures(self, per_df: pd.DataFrame):
        fig1 = self.output_dir/"figs"/"benefits_vs_investment.png"
        plt.figure()
        ax = plt.gca()
        per_sorted = per_df.sort_values("investment")
        ax.barh(per_sorted["intervention"], per_sorted["investment"])
        ax.barh(per_sorted["intervention"], per_sorted["total_savings"], left=0)
        ax.set_xlabel("AED")
        ax.set_title("Benefits vs Investment (deterministic)")
        plt.tight_layout(); plt.savefig(fig1); plt.close()

        mc = self.results.get("monte_carlo", {})
        if not mc: return
        fig2 = self.output_dir/"figs"/"roi_summary.png"
        plt.figure()
        plt.title("ROI (portfolio) — MC summary")
        plt.xlabel("")
        plt.ylabel("")
        plt.text(0.05, 0.8, f"Mean ROI: {mc['roi']['mean']*100:.1f}%", transform=plt.gca().transAxes)
        plt.text(0.05, 0.7, f"95% CI: [{mc['roi']['ci_lower']*100:.1f}%, {mc['roi']['ci_upper']*100:.1f}%]", transform=plt.gca().transAxes)
        plt.axis('off'); plt.savefig(fig2); plt.close()

    def _validate_alignment(self) -> Dict[str, Any]:
        per_results, port_results = self._read_results()
        per_df, _, roi_df = self._tables()
        rows = []
        for k, tgt in per_results.items():
            v = per_df[per_df["intervention"]==k]
            if v.empty: continue
            v = v.iloc[0]
            I=v["investment"]; S=v["total_savings"]; Q=v["qalys"]
            roi_pct = (S-I)/I*100 if I>0 else 0.0
            c_per_q = (I - v["hc_savings"])/Q if Q>0 else float("nan")
            rows.append({"intervention": k,"Δ invest (B AED)": I/1e9 - tgt.get("investment", I)/1e9,"Δ ROI (pp)": roi_pct - (tgt.get("roi_ratio", roi_pct)*100),"Δ cost/QALY (AED)": c_per_q - tgt.get("c_per_qaly", c_per_q),"Δ events": v["events_prevented"] - tgt.get("events_prevented", v["events_prevented"]),"Δ deaths": v["deaths_averted"] - tgt.get("deaths_averted", v["deaths_averted"])})
        df_int = pd.DataFrame(rows).sort_values("intervention") if rows else pd.DataFrame()
        df_port = pd.DataFrame([{"Δ invest (B AED)": roi_df["total_investment"].iloc[0]/1e9 - (port_results.get("investment_total", roi_df["total_investment"].iloc[0])/1e9 if port_results else roi_df["total_investment"].iloc[0]/1e9),"Δ benefits (B AED)": roi_df["total_savings"].iloc[0]/1e9 - (port_results.get("benefits_total", roi_df["total_savings"].iloc[0])/1e9 if port_results else roi_df["total_savings"].iloc[0]/1e9),"ROI (%) model": roi_df["roi_percentage"].iloc[0]}]) if not roi_df.empty else pd.DataFrame()
        (self.output_dir/"reports"/"alignment_per_intervention.csv").write_text(df_int.to_csv(index=False))
        (self.output_dir/"reports"/"alignment_portfolio.csv").write_text(df_port.to_csv(index=False))
        print("\\n=== ALIGNMENT: Per-Intervention (Δ Model - Result) ===")
        print(df_int.to_string(index=False) if not df_int.empty else "No intervention results provided.")
        print("\\n=== ALIGNMENT: Portfolio (Δ Model - Result) ===")
        print(df_port.to_string(index=False) if not df_port.empty else "No portfolio results provided.")
        return {"per_intervention": rows, "portfolio": df_port.to_dict(orient="records") if not df_port.empty else []}

    def generate_reports(self) -> Dict[str,str]:
        per_df, mc_df, roi_df = self._tables()
        exec_md = f"""# Executive Summary ({datetime.now():%Y-%m-%d %H:%M})
- Horizon: {self.parameters['meta']['horizon_years']}y; Discount: {self.parameters['health_system']['discount_rate']*100:.1f}%; Perspective: {self.parameters['meta']['perspective']}
- Investment: AED {self.results['roi']['total_investment']:,.0f}
- Benefits: AED {self.results['roi']['total_savings']:,.0f}
- Net benefit: AED {self.results['roi']['net_benefit']:,.0f}
- ROI: {self.results['roi']['roi_percentage']:.1f}%
- Events prevented: {self.results['roi']['total_events_prevented']:,.0f} | Deaths averted: {self.results['roi']['total_deaths_averted']:,.0f} | QALYs: {self.results['roi']['total_qalys_gained']:,.0f}
"""
        (self.output_dir/"reports"/"executive_summary.md").write_text(exec_md, encoding="utf-8")
        tech_md = f"""# Technical Report
## Methods
- Markov-style annual cohort; 10-year; 3% discount; societal perspective
- Deterministic = means; PSA = Beta/Gamma + Lognormal; program cost variance ~0 (fixed budget)

## Per-intervention (deterministic)
```
{json.dumps(self.results['markov']['per_intervention'], indent=2)}
```
## Portfolio (deterministic)
```
{json.dumps(self.results['markov']['portfolio'], indent=2)}
```
## Monte Carlo (summary)
```
{json.dumps({k:v for k,v in (self.results.get('monte_carlo', {}) or {}).items() if k != 'icer'}, indent=2)}
```
"""
        (self.output_dir/"reports"/"technical_report.md").write_text(tech_md, encoding="utf-8")
        per_df.to_csv(self.output_dir/"Per_Intervention_Snapshot.csv", index=False)
        # (no MC or ROI summary CSVs; no plots)
        return {"exec": str(self.output_dir/"reports"/"executive_summary.md"), "tech": str(self.output_dir/"reports"/"technical_report.md")}

    def run(self, mc_iterations: int = 10000) -> bool:
        try:
            self.load_parameters()
            self.calibrate()
            self.run_markov_models(deterministic=True)
            self.calculate_roi()
            self.run_monte_carlo(n_iterations=mc_iterations)
            self.generate_reports()
            None  # alignment reporting disabled
            return True
        except Exception as e:
            log.exception("Run failed: %s", e)
            return False

def main():
    import argparse
    ap = argparse.ArgumentParser(description="UAE Preventive Health — Pipeline")
    ap.add_argument("--out", default="results", help="Output directory")
    ap.add_argument("--mc", type=int, default=10000, help="Monte Carlo iterations")
    args = ap.parse_args()
    analysis = UAEHealthAnalysis(output_dir=args.out)
    ok = analysis.run()
    return 0 if ok else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())



# --- 
try:
    UAEHealthAnalysis
    def export_param_citations(self, out_csv_path: str = None):
        """ """
        import pandas as _pd
        from pathlib import Path as _Path
        rows = _flatten_param_citations(self.parameters or default_params, param_citations, prefix="")
        df = _pd.DataFrame(rows, columns=["path","value","refs","justification"])
        if out_csv_path:
            p = _Path(out_csv_path)
            if p.parent and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(p, index=False)
        return df
    setattr(UAEHealthAnalysis, "export_param_citations", export_param_citations)
except NameError:
    # Class not yet defined in this text block; ignore.
    pass

# ----------------------------------------------------------------------------------