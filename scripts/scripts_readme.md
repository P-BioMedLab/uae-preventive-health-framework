# Scripts Directory

This directory contains utility scripts for data preprocessing, validation, and maintenance of the UAE Preventive Health Investment Framework.

## 📁 Script Inventory

### Core Validation Scripts
- **`parameter_validation.py`** - Comprehensive parameter validation and consistency checking
- **`minimal_validation.py`** - Lightweight validation for quick reproducibility checks
- **`data_preprocessing.py`** - Data processing, inflation updates, and export utilities

## 🔧 Script Usage Guide

### `parameter_validation.py`
**Purpose**: Comprehensive validation of all framework parameters

```bash
# Basic validation
python parameter_validation.py

# Custom data directory
python parameter_validation.py --data-dir /path/to/data

# Save validation results
python parameter_validation.py --output validation_results.json

# Verbose output
python parameter_validation.py --verbose
```

**What it validates**:
- ✅ File structure and JSON validity
- ✅ Epidemiological parameter ranges
- ✅ Cost parameter consistency
- ✅ Calculator default values
- ✅ Cross-file consistency
- ✅ Logical relationships between parameters

**Output**: Detailed validation report with warnings and errors

### `minimal_validation.py`
**Purpose**: Quick validation for reproducibility verification

```bash
# Run core calculations validation
python minimal_validation.py
```

**What it validates**:
- ✅ Core ROI calculations (257% target)
- ✅ Individual intervention ROIs
- ✅ Cost-effectiveness calculations
- ✅ Health outcome aggregations

**Output**: Pass/fail validation with summary metrics

### `data_preprocessing.py`
**Purpose**: Data processing and maintenance operations

```bash
# Update costs for inflation
python data_preprocessing.py --update-inflation

# Export to CSV format
python data_preprocessing.py --export-csv

# Run validation after processing
python data_preprocessing.py --validate

# Generate processing report
python data_preprocessing.py --report processing_report.json

# All operations
python data_preprocessing.py --update-inflation --export-csv --validate --report full_report.json
```

**Operations**:
- 🔄 Inflation adjustment for cost parameters
- 📊 CSV export for external analysis
- 🎯 Calculator parameter optimization
- 📈 Population target calculations
- 📋 Processing reports and recommendations

## 🚀 Quick Start Workflows

### New User Setup
```bash
# 1. Validate framework integrity
python parameter_validation.py

# 2. Check core calculations
python minimal_validation.py

# 3. Export data for review
python data_preprocessing.py --export-csv
```

### Annual Maintenance
```bash
# 1. Update costs for inflation
python data_preprocessing.py --update-inflation

# 2. Validate updated parameters
python parameter_validation.py --output annual_validation.json

# 3. Generate maintenance report
python data_preprocessing.py --report annual_maintenance.json
```

### Research Validation
```bash
# 1. Comprehensive validation with detailed output
python parameter_validation.py --verbose --output research_validation.json

# 2. Core calculation verification
python minimal_validation.py

# 3. Data quality assessment
python data_preprocessing.py --report data_quality_report.json
```

## 🔍 Troubleshooting Guide

### Common Issues

#### Import Errors
```
ModuleNotFoundError: No module named 'parameter_validation'
```
**Solution**: Run scripts from the `/scripts/` directory or adjust Python path

#### File Not Found Errors
```
Parameter file not found: uae_epidemiological_parameters.json
```
**Solutions**:
- Ensure `/data/` directory exists with required files
- Use `--data-dir` parameter to specify correct path
- Check file permissions

#### JSON Parsing Errors
```
Invalid JSON in cost_parameters_aed_2025.json: Expecting ',' delimiter
```
**Solutions**:
- Validate JSON syntax using online validator
- Check for trailing commas or missing quotes
- Restore from backup if available

#### Validation Failures
```
CVD prevalence 0.45 outside typical range 15-50%
```
**Solutions**:
- Review parameter sources and calculations
- Check if warnings are acceptable for UAE context
- Update validation ranges if justified by evidence

### Performance Issues

#### Slow Processing
- **Cause**: Large parameter files or complex validation
- **Solution**: Run scripts on dedicated system, close other applications

#### Memory Issues  
- **Cause**: Loading large datasets
- **Solution**: Process in smaller batches, increase system memory

## 📊 Output File Guide

### Validation Reports (`validation_results.json`)
```json
{
  "timestamp": "2025-08-11T10:30:00",
  "overall_valid": true,
  "warnings": ["Parameter outside typical range..."],
  "errors": [],
  "file_validations": {
    "epidemiological": true,
    "cost_parameters": true
  }
}
```

### Processing Reports (`processing_report.json`)
```json
{
  "processing_summary": {
    "operations": [{"operation": "inflation_update", "details": "..."}],
    "warnings": [],
    "errors": []
  },
  "data_quality_assessment": {
    "overall_quality_score": 0.94,
    "completeness_check": "passed"
  }
}
```

### CSV Exports
- **`intervention_summary.csv`**: Key intervention parameters
- **`cost_summary.csv`**: Detailed cost breakdowns  
- **`population_summary.csv`**: Demographics by age group

## 🔄 Automation & Integration

### Scheduled Tasks
```bash
# Weekly validation check
0 2 * * 1 cd /path/to/scripts && python parameter_validation.py --output weekly_check.json

# Monthly data processing
0 3 1 * * cd /path/to/scripts && python data_preprocessing.py --report monthly_report.json

# Annual inflation update
0 4 1 1 * cd /path/to/scripts && python data_preprocessing.py --update-inflation --validate
```

### CI/CD Integration
```yaml
# GitHub Actions workflow example
- name: Validate Parameters
  run: |
    cd scripts
    python parameter_validation.py --output validation.json
    python minimal_validation.py
```

## 📈 Development Guidelines

### Adding New Scripts
1. **Follow naming convention**: `purpose_action.py`
2. **Include comprehensive docstring** with usage examples
3. **Add command-line argument parsing** for flexibility
4. **Implement error handling** and logging
5. **Update this README** with usage instructions

### Script Standards
- **Python 3.7+** compatibility
- **No external dependencies** for core functionality
- **UTF-8 encoding** for all file operations
- **Consistent error reporting** format
- **Progress indicators** for long operations

### Testing New Scripts
```bash
# Syntax check
python -m py_compile script_name.py

# Basic functionality test
python script_name.py --help

# Integration test
python script_name.py --validate
```

## 🔒 Security & Privacy

### Data Handling
- Scripts process only **aggregated, non-personal data**
- **No network connections** required for core functionality
- **Local file system only** - no cloud uploads
- **Transparent operations** - no hidden data modifications

### Best Practices
- **Review output** before sharing validation reports
- **Backup data** before running modification scripts
- **Use version control** for parameter changes
- **Document modifications** in processing reports

## 📞 Support & Contribution

### Getting Help
- **Script errors**: Check troubleshooting section above
- **Parameter questions**: See `/data/README.md`
- **Feature requests**: Submit via repository issues
- **Bug reports**: Include full error output and system info

### Contributing
- **Code review**: All scripts undergo peer review
- **Testing**: New features require validation tests
- **Documentation**: Update README for any changes
- **Standards**: Follow existing code patterns and style

### Contact Information
- **Technical Issues**: Repository issues
- **Research Questions**: Academic collaboration via discussions
- **Institutional Support**: Contact framework maintainers

---

**Dependencies**: Python 3.7+ (standard library only)  
**Compatibility**: Windows, macOS, Linux  
**Last Updated**: 2025-08-11