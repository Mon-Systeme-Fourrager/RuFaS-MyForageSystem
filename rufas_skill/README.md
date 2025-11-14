# RuFaS Claude AI Skill

A comprehensive Claude AI skill for working with the RuFaS (Ruminant Farm Systems) codebase.

---

## What is This?

This skill package provides Claude AI with deep knowledge of the RuFaS project, enabling intelligent assistance with:
- Understanding the RuFaS architecture and codebase
- Writing code that follows RuFaS conventions
- Debugging simulations and interpreting results
- Configuring farm models and running analyses
- Contributing to the RuFaS project

---

## Skill Contents

### Core Documentation

1. **SKILL.md** - Main reference document
   - Project overview and architecture
   - Core technologies and components
   - Data flow and design patterns
   - Development standards
   - Testing strategy
   - Performance optimization

2. **API.md** - API reference
   - TaskManager, SimulationEngine, InputManager, OutputManager
   - DataValidator, HerdManager, ManureManager
   - FeedManager, FieldManager
   - Utility functions and enums
   - Complete function signatures and examples

3. **GUIDES.md** - Practical guides
   - Installation and setup
   - Running simulations
   - Input configuration
   - Using the Data Collection App
   - Interpreting results
   - Sensitivity analysis
   - Debugging workflows
   - Contributing to RuFaS

### Domain-Specific References

4. **references/ANIMAL_MODULE.md**
   - Animal modeling components
   - Milk production and lactation curves
   - Growth and body weight
   - Reproduction and breeding
   - Nutrition (NASEM requirements)
   - Enteric methane and manure production
   - Health and disease
   - Genetics and breeding values

5. **references/MANURE_MODULE.md**
   - Manure collection systems
   - Treatment and separation
   - Storage (lagoons, tanks, composting)
   - Greenhouse gas emissions (CH4, N2O, NH3)
   - Nutrient transformations
   - Land application methods
   - Nutrient credits

6. **references/FIELD_CROP_MODULE.md**
   - Crop growth and development
   - Soil processes (water, nutrients, carbon)
   - Nutrient cycling (N, P, C)
   - Field management operations
   - Harvest scheduling and yields
   - Environmental impacts (erosion, leaching)

7. **references/FEED_STORAGE_MODULE.md**
   - Feed inventory management
   - Storage types (silage, hay, grain, baleage)
   - Storage degradation and losses
   - Nutritional composition changes
   - Feed purchasing and planning
   - Distribution to animals

---

## About RuFaS

**RuFaS (Ruminant Farm Systems)** is an open-source whole-farm modeling environment for dairy farms.

### Key Features

- **Comprehensive Modeling**: Animals, manure, crops, feed storage
- **Scientific Rigor**: Based on NASEM, NRC, IPCC standards
- **Environmental Impact**: GHG emissions, water quality, soil health
- **Sensitivity Analysis**: Sobol, Morris, Fractional Factorial methods
- **High Quality**: 95% test coverage, strict type checking
- **Open Source**: GPLv3 license

### Technical Stack

- **Language**: Python 3.12+
- **Scientific**: NumPy, SciPy, Pandas, SALib
- **Testing**: Pytest (95% coverage)
- **Quality**: Black, Flake8, Mypy (strict)
- **Frontend**: HTML5/JavaScript Data Collection App

### Version

- **Current Version**: 0.9.2
- **Repository**: https://github.com/RuminantFarmSystems/RuFaS
- **Documentation**: https://ruminantfarmsystems.github.io/RuFaS/
- **Website**: https://rufas.org

---

## How to Use This Skill with Claude

### Installation in Claude

1. Download the `rufas_skill.zip` file
2. Extract to a local directory
3. Upload to Claude Code or Claude.ai as a project knowledge base

### Example Queries

**Understanding the Codebase**:
```
"Explain how the simulation engine coordinates daily routines"
"What's the data flow from InputManager to OutputManager?"
"How does RuFaS calculate enteric methane emissions?"
```

**Writing Code**:
```
"Create a new lactation curve model for Jersey cows"
"Add validation for minimum protein requirements in rations"
"Write tests for the manure separator class"
```

**Configuration Help**:
```
"Help me configure a 200-cow dairy farm with anaerobic digestion"
"What crop rotation should I use for maximum milk production?"
"How do I set up seasonal breeding in the animal config?"
```

**Debugging**:
```
"Why is my simulation showing feed shortages on day 245?"
"Interpret this error: 'Ration violates minimum NDF constraint'"
"My milk production is 30% lower than expected - what to check?"
```

**Analysis**:
```
"Run a Sobol sensitivity analysis on feed protein and corn yield"
"Compare GHG emissions between covered lagoon and digester"
"Calculate the economic value of manure nutrients"
```

---

## Skill Structure

```
rufas_skill/
├── README.md                          # This file
├── SKILL.md                           # Main reference (core architecture)
├── API.md                             # API documentation (classes & functions)
├── GUIDES.md                          # Practical tutorials
└── references/
    ├── ANIMAL_MODULE.md               # Animal modeling reference
    ├── MANURE_MODULE.md               # Manure management reference
    ├── FIELD_CROP_MODULE.md           # Field & crop modeling reference
    └── FEED_STORAGE_MODULE.md         # Feed storage reference
```

---

## What Claude Can Help You With

### For Developers

- **Code Navigation**: "Where is milk production calculated?"
- **Implementation**: "Add a new crop type to the system"
- **Testing**: "Write E2E tests for sensitivity analysis"
- **Refactoring**: "Improve performance of daily animal routines"
- **Documentation**: "Generate docstrings for InputManager methods"

### For Researchers

- **Model Understanding**: "Explain the NASEM energy partitioning equations"
- **Sensitivity Analysis**: "Which parameters most affect GHG emissions?"
- **Result Interpretation**: "Why did conception rate drop in summer?"
- **Comparison**: "Compare Wood's vs Dijkstra lactation curves"

### For Farm Consultants

- **Configuration**: "Set up a seasonal calving system"
- **Optimization**: "Maximize milk per unit of feed cost"
- **Scenario Testing**: "Compare corn silage vs alfalfa-based rations"
- **Reporting**: "Generate economic and environmental reports"

---

## Key Capabilities

### Domain Knowledge

- ✅ Dairy cattle biology and management
- ✅ Manure handling and emissions
- ✅ Crop production and nutrient cycling
- ✅ Feed storage and quality
- ✅ Greenhouse gas accounting (IPCC)
- ✅ Economic optimization

### Technical Expertise

- ✅ Python 3.12+ development
- ✅ Scientific computing (NumPy, SciPy)
- ✅ Testing strategies (Pytest, E2E)
- ✅ Type checking (Mypy strict)
- ✅ Design patterns (Singleton, Factory, etc.)
- ✅ Performance optimization (Numba, multiprocessing)

### RuFaS-Specific

- ✅ TaskManager configuration
- ✅ Input/Output data structures
- ✅ Simulation engine workflow
- ✅ Validation and error handling
- ✅ Report and graph generation
- ✅ Data Collection App schemas

---

## Skill Coverage

### Completeness

| Module | Coverage | Details |
|--------|----------|---------|
| Core Architecture | ✅ Complete | TaskManager, SimulationEngine, I/O |
| Animal Module | ✅ Complete | All submodules documented |
| Manure Module | ✅ Complete | Collection, storage, emissions |
| Field/Crop Module | ✅ Complete | Growth, soil, nutrients, harvest |
| Feed Storage Module | ✅ Complete | All storage types, degradation, purchasing |
| Testing | ✅ Complete | Unit, integration, E2E testing |
| Contribution Guide | ✅ Complete | Workflow, style, PR process |

---

## Related Resources

### Official Documentation
- [GitHub Repository](https://github.com/RuminantFarmSystems/RuFaS)
- [Online Documentation](https://ruminantfarmsystems.github.io/RuFaS/)
- [Project Website](https://rufas.org)

### Scientific References
- NASEM (2021) - Nutrient Requirements of Dairy Cattle
- IPCC (2019) - Refinement to 2006 IPCC Guidelines
- NRC - National Research Council standards

### Community
- [GitHub Issues](https://github.com/RuminantFarmSystems/RuFaS/issues)
- [Contributing Guide](https://github.com/RuminantFarmSystems/RuFaS/blob/dev/CONTRIBUTING.md)
- Email: contact@rufas.org

---

## Skill Maintenance

### Version Compatibility

This skill is based on:
- **RuFaS Version**: 0.9.2
- **Snapshot Date**: November 2024
- **Python**: 3.12-3.13

### Updates

To update this skill:
1. Pull latest RuFaS code: `git pull origin dev`
2. Review changelog.md for major changes
3. Update skill documentation as needed
4. Regenerate using Skill_Seekers (optional)

### Known Limitations

- Field/Crop module documentation is partial (rapidly evolving)
- Mypy type checking still in progress (3,275 errors being resolved)
- Some advanced features may not be fully documented

---

## Credits

### RuFaS Team

RuFaS is developed by a collaborative community of researchers, developers, and stakeholders. See [contributors](https://github.com/RuminantFarmSystems/RuFaS/graphs/contributors).

### Skill Creation

This skill was created using the [Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) framework for converting repositories into Claude AI skills.

**Skill Generator**: Skill_Seekers v1.0+
**Generation Date**: November 2024
**License**: GPLv3 (same as RuFaS)

---

## License

This skill documentation is licensed under **GPLv3**, consistent with the RuFaS project.

### What This Means

- ✅ You can use this skill freely
- ✅ You can modify and share the skill
- ✅ Modifications must also be GPLv3
- ❌ No warranty provided
- ❌ No liability accepted

See [COPYING.txt](https://github.com/RuminantFarmSystems/RuFaS/blob/dev/COPYING.txt) for full license text.

---

## Support

### For RuFaS Questions
- Open an [issue](https://github.com/RuminantFarmSystems/RuFaS/issues)
- Email: contact@rufas.org
- Check [documentation](https://ruminantfarmsystems.github.io/RuFaS/)

### For Skill Issues
- Verify skill is loaded correctly in Claude
- Check that queries reference RuFaS context
- Consult GUIDES.md for usage examples

---

## Quick Start

### 1. Install RuFaS

```bash
git clone https://github.com/RuminantFarmSystems/RuFaS.git
cd RuFaS
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Run Example Simulation

```bash
python main.py -p input/task_manager_metadata.json -v logs
```

### 3. Ask Claude for Help

```
"Claude, using the RuFaS skill, explain what just happened in the simulation"
"How can I increase milk production in my model?"
"What's causing the high methane emissions?"
```

---

## Feedback

Help improve this skill:
- Report inaccuracies or gaps
- Suggest additional documentation
- Share use cases and examples

Contact: Use RuFaS GitHub issues or email contact@rufas.org

---

**Happy Modeling! 🐄🌱**

*This skill enables Claude to be your intelligent assistant for sustainable dairy farm modeling with RuFaS.*
