# Data Directory

This directory contains all parameter files and data sources used by the UAE Preventive Health Investment Framework.

## 📁 File Structure

### Core Parameter Files
- **`uae_epidemiological_parameters.json`** - Disease prevalence, incidence, and progression parameters
- **`cost_parameters_aed_2025.json`** - Intervention and treatment costs in AED 2025 values  
- **`calculator_defaults.json`** - Default parameters for web calculator interface
- **`core_parameters.json`** - Core replication parameters for validation

### Generated Files (Created by Scripts)
- **`processed_calculator_config.json`** - Processed parameters ready for calculator
- **`intervention_summary.csv`** - Intervention overview in CSV format
- **`cost_summary.csv`** - Cost breakdown in CSV format  
- **`population_summary.csv`** - Population demographics in CSV format

## 📊 Data Sources

All parameters derived exclusively from **publicly available sources**:

### Clinical & Epidemiological Data
- UAE health statistics and national health surveys
- Published peer-reviewed research on UAE/MENA populations
- International clinical trial data adapted for UAE context
- WHO/UNDP reports on UAE health status

### Cost Data
- Dubai Health Authority expenditure reports
- Published health economics studies with PPP adjustments
- International prevention program cost benchmarks
- Healthcare fee schedules from public sources

### Quality of Life Data
- UAE-specific EQ-5D-5L value set (Papadimitropoulos et al., 2024)
- Disease-specific utility decrements from literature
- No individual-level preference data utilized

## 🔄 Data Updates

### Update Schedule
- **Annual**: Cost inflation adjustments, epidemiological updates
- **Biannual**: Parameter validation and stakeholder review
- **As needed**: New evidence integration, policy changes

### Version Control
Each file includes metadata with:
- Version number (v2025.08 format)
- Last update timestamp
- Source attribution
- Validation status

## 📈 Usage Instructions

### For Researchers
```bash
# Load core parameters for analysis
python -c "import json; data=json.load(open('core_parameters.json')); print(data['portfolio_summary'])"

# Validate parameter consistency
python ../scripts/parameter_validation.py --data-dir .

# Update inflation adjustments
python ../scripts/data_preprocessing.py --update-inflation
```

### For Policy Users
- Use `calculator_defaults.json` to understand baseline assumptions
- Review `intervention_summary.csv` for quick intervention comparison
- Check `population_summary.csv` for demographic context

### For Technical Integration
- All JSON files follow consistent structure with metadata
- Cost values in AED with explicit base year
- Population counts as integers, rates as decimals 0-1
- Quality indicators and confidence intervals provided where available

## ⚠️ Data Limitations

### Known Constraints
- Some international costs adjusted for UAE using PPP where local data unavailable
- Expatriate vs. Emirati population differences averaged in many parameters
- Private sector utilization patterns may differ from public estimates
- Temporal variations in disease prevalence not fully captured

### Uncertainty Ranges
- **Prevalence estimates**: ±10-15% typical variation
- **Cost estimates**: ±20-25% variation due to provider differences
- **Effectiveness estimates**: ±15-20% based on population heterogeneity
- **Utility estimates**: ±10% based on cultural adaptation

## 🔒 Data Ethics & Privacy

### Compliance Standards
- **No individual-level data**: All parameters are population aggregates
- **Public sources only**: No proprietary healthcare data utilized
- **Anonymized statistics**: No identifiable health information
- **Transparent methodology**: All data sources documented and citable

### Research Ethics
- Framework designed for population health policy, not individual diagnosis
- Results intended for decision-making support, not medical advice
- Appropriate disclaimers included in all applications

## 🔍 Validation & Quality Assurance

### Validation Process
1. **Technical validation**: JSON structure, value ranges, consistency
2. **Clinical validation**: Parameter reasonableness against literature
3. **Economic validation**: Cost relationships and inflation adjustments
4. **Cross-validation**: Consistency across parameter files

### Quality Indicators
- **Completeness**: Percentage of required parameters available
- **Accuracy**: Alignment with external validation data (R²=0.89)
- **Timeliness**: Recency of underlying data sources
- **Transparency**: Documentation and source attribution quality

Run validation: `python ../scripts/parameter_validation.py`

## 📞 Support & Questions

### Data Questions
- **Parameter interpretation**: See inline documentation in JSON files
- **Source validation**: Check references in metadata sections
- **Update requests**: Submit via repository issues
- **Technical problems**: Run validation scripts for diagnostics

### Research Collaboration
- **Academic partnerships**: Available for methodology validation
- **Institutional adoption**: Parameters can be customized for local contexts
- **Peer review**: Seeking independent validation of methodology

---

**Last Updated**: 2025-08-11  
**Next Review**: 2026-08-11  
**Contact**: Repository issues for technical questions