> CE 492: Undergraduate Thesis Project Open-Source EU ETS Maritime
> Compliance Cost Estimator
>
> Supervisor: Dr. Eyuphan Koc Department of Civil Engineering Bogazici
> University
>
> Email: eyuphan.koc@bogazici.edu.tr Project Duration: 10-12 weeks
>
> Expected Deliverables: Open-source software package + Publishable
> research paper

Project Overview

This undergraduate thesis project aims to develop an open-source EU
Emissions Trading System (ETS) cost estimator for maritime voyages. The
tool will address a critical gap identified in recent research: the
absence of publicly available, policy-accurate, and actively maintained
tools for estimating EU ETS compliance costs in international shipping.

> Students will build a transparent, reproducible system that:
>
> • Ingests port pairs and vessel information (optionally AIS data)
>
> • Estimates voyage emissions using two interchangeable methodologies
>
> • Applies policy-accurate EU ETS coverage rules (100% intra-EEA; 50%
> extra-EEA)
>
> • Accounts for regulatory requirements including CH4 & N2O from 2026
> and phased surren-der schedules (40%/70%/100%)
>
> • Calculates compliance costs by multiplying covered tCO2e by EUA
> (European Union Al-lowance) prices

The project will culminate in both a production-ready software package
and a publishable research paper suitable for journals such as Journal
of Open Source Software (JOSS) or Trans-portation Research Part D.

Background & Motivation

The EU ETS for Maritime Transport

The European Union Emissions Trading System (EU ETS) has been extended
to maritime transport, requiring ship operators to surrender carbon
allowances for covered emissions. Key policy elements include:

> • Coverage: 100% of emissions from intra-EEA voyages and time at berth
> in EEA ports; 50% of emissions from extra-EEA voyage legs (voyages
> between EEA and non-EEA ports)
>
> • Greenhouse gases: CO2 only for 2024-2025; CO2, CH4, and N2O from
> 2026 onward
>
> • Phase-in schedule: 40% of 2024 emissions surrendered by 30 September
> 2025; 70% of 2025 emissions; 100% from 2026 onward
>
> • Special rules: Transshipment ports (Tanger Med, East Port Said) do
> not reset voyage legs for coverage calculation purposes
>
> 1

Current State of Tools

A comprehensive literature review conducted using the Elicit AI research
platform (searching over 126 million academic papers) found no actively
maintained open-source tools for EU ETS maritime compliance cost
estimation. While three proprietary models were identified:

> 1\. Ventikos et al. — Python-based ship air emissions calculator (no
> EU ETS cost calcula-tions, not open-source)
>
> 2\. Sun et al. (2024) — Carbon and cost accounting model explicitly
> modeling EU ETS compliance (most complete methodology but not
> open-source)
>
> 3\. Ji and El-Halwagi (2020) — IMO-focused emission inventory (no EU
> ETS coverage, not open-source)
>
> None of these studies provide:
>
> • OSI-approved or similarly permissive open-source licenses
>
> • Public code repositories
>
> • Evidence of active maintenance (commits/releases since 2023)

This gap creates a significant barrier for researchers, policymakers,
shipping companies, and port authorities seeking transparent, verifiable
tools for compliance cost estimation and scenario analysis.

Project Objectives

Upon successful completion of this project, students will have:

> 1\. Developed a production-ready open-source software package with
> clean architec-ture, comprehensive testing, and clear documentation
>
> 2\. Implemented two complementary emission estimation methods:
>
> • Method A: MRV-intensity approach (using historical verified
> emissions data)
>
> • Method B: Engineering-lite approach (using vessel specifications and
> EPA marine emissions tools)
>
> 3\. Encoded policy-accurate EU ETS coverage rules as testable
> functions, including:
>
> • Intra-EEA / extra-EEA / out-of-scope leg classification •
> Transshipment port special rules
>
> • Phase-in surrender schedules
>
> • Future-ready CH4/N2O accounting framework
>
> 4\. Created a reproducible experimental pipeline validating the tool
> through:
>
> • Accuracy assessment (comparing methods against verified data) •
> Policy sensitivity analysis (transshipment rule impact)
>
> • Price scenario modeling (EUA price uncertainty)
>
> • Uncertainty quantification (Monte Carlo sensitivity)
>
> 5\. Produced publication-ready research outputs:
>
> 2
>
> • Software paper for JOSS or SoftwareX
>
> • Optional method paper for domain journals (Transportation Research
> D, Maritime Policy & Management)
>
> 6\. Established best practices in research software engineering:
>
> • Version control (Git/GitHub)
>
> • Continuous integration and testing
>
> • Data provenance and archival (Zenodo DOI)
>
> • FAIR principles (Findable, Accessible, Interoperable, Reusable)

Technical Approach

Method A: MRV-Intensity Estimator (Fast & Transparent)

This method leverages verified emissions data from the EU’s Monitoring,
Reporting, and Veri-fication (MRV) system:

> 1\. Distance calculation: Compute nautical miles via SeaRoute
> (Eurostat’s open maritime routing engine) from origin to destination
>
> 2\. Emission intensity: Extract from THETIS-MRV public database:
>
> annual CO2 \[kg\] nm annual distance \[nm\]
>
> per IMO number; use ship-type median as fallback for vessels without
> MRV data
>
> 3\. Voyage emissions:
>
> 4\. Coverage application:

leg Inm ×dnm 2 1000

\[tonnes\]

> • 100% for intra-EEA legs and at-berth time in EEA ports • 50% for
> extra-EEA legs (one port in EEA, one outside) • 0% for legs entirely
> outside EEA
>
> • Transshipment rule: stops at Tanger Med or East Port Said do not
> split long extra-EEA legs
>
> 5\. Phase-in multiplication: py = 0.40 (2024), 0.70 (2025), 1.00
> (2026+)
>
> 6\. Cost calculation:
>
> ETS cost = COleg ×coverage×py ×EUA price \[EUR/t\]

Method B: Engineering-Lite Estimator

For vessels lacking MRV data or for forward-looking scenarios:

> 1\. Power & fuel estimation: Use EPA Marine Emissions Tools (R
> package) to estimate main and auxiliary engine power and specific fuel
> oil consumption (SFOC) based on vessel specifications and operational
> speed
>
> 2\. Fuel-to-CO2 conversion: Apply default tank-to-wake emission
> factors:
>
> 3
>
> • Heavy Fuel Oil (HFO): 3.114 g CO2/g fuel • Marine Gas Oil (MGO):
> 3.206 g CO2/g fuel
>
> (IMO/ICCT-aligned values)
>
> 3\. Coverage & cost: Apply identical coverage, phase-in, and pricing
> logic as Method A

Future Extension: CH4 and N2O (2026+)

The architecture will include placeholders for methane and nitrous oxide
accounting, enabling seamless integration when emission factors become
standardized.

Core Building Blocks (Open-Source Tools & Data)

All components of this project leverage open-source tools and publicly
available data:

Routing & Distance

> • SeaRoute (Eurostat): Reference implementation for maritime route
> distance calculation
>
> • Python searoute wrapper: Lightweight Python API interface
>
> • Repository: <https://github.com/eurostat/searoute>

Vessel Activity & Emissions Data

> • THETIS-MRV (EMSA): Public database of verified per-ship annual CO2,
> distance, and hours at berth
>
> • Source: <https://www.emsa.europa.eu/thetis-mrv.html>
>
> • EPA Marine Emissions Tools (R): Engineering models for power curves,
> SFOC, and emission factors
>
> • Repository: <https://github.com/USEPA/Marine_Emissions_Tools>
>
> • Default emission factors: IMO Fourth GHG Study / ICCT well-to-wake
> values

AIS Data Processing (Optional Enhancement)

> • pyais: Decode AIVDM/AIVDO messages from raw AIS streams
>
> • Repository: <https://github.com/M0r13n/pyais>
>
> • AISdb: SQLite/PostgreSQL storage and querying for AIS trajectories
>
> • World Bank Pacific Observatory: Worked examples of AIS → CO2
> pipelines
>
> • Tutorials:
> [https://worldbank.github.io/pacific-observatory/ais/ais_emissions.](https://worldbank.github.io/pacific-observatory/ais/ais_emissions.html)
> [html](https://worldbank.github.io/pacific-observatory/ais/ais_emissions.html)
>
> 4

EU ETS Policy Data

> • Coverage rules & phase-in schedules: Oficial European Commission
> documentation
>
> • Source:
> [https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissio](https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissions-shipping-sector)
>
> • Transshipment port list: Commission Implementing Regulation (EU)
> 2023/2297
>
> • Currently includes: Tanger Med (Morocco), East Port Said (Egypt)
>
> • Legaltext:
> <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202302297>

EUA Price Inputs

> • Sandbag Carbon Price Viewer: Historical EUA price data
>
> • Source: <https://sandbag.be/carbon-price-viewer/>
>
> • TradingEconomics: Indicative current prices
>
> • Source: <https://tradingeconomics.com/commodity/carbon>

Registry Context (Optional)

> • pyeutl: Python interface to EU Transaction Log / Union Registry
>
> • Repository: <https://github.com/jabrell/pyeutl>
>
> • EU ETS Data Viewer: Oficial compliance tracking dashboards

System Architecture

The software package will follow a clean, modular architecture optimized
for testability and extensibility:

eu-ets-estimator/

> data/ ports_eea.csv

\# Seed data files \# EEA port registry

> transshipment_ports.csv
>
> eua_prices.csv mrv_intensities.csv
>
> src/ routing.py
>
> intensity.py coverage.py pricing.py estimator.py io.py
>
> tests/ test_coverage.py test_intensity.py fixtures/

\# Historical/scenario EUA prices \# Preprocessed MRV data

> \# Core source code
>
> \# SeaRoute distance wrapper
>
> \# Method A (MRV) & B (engineering) \# ETS coverage logic (100/50/0)
>
> \# EUA price lookup & scenarios \# Main orchestration
>
> \# CLI + optional API (FastAPI)

\# Unit & integration tests \# Policy rule golden tests

\# Emission calculation tests \# Test data fixtures

> 5
>
> paper/ experiments.py figures/ tables/
>
> docs/ user_guide.md
>
> api_reference.md
>
> Dockerfile CITATION.cff LICENSE README.md

\# Reproducibility & publication \# Experiment scripts

\# Generated plots

> \# Generated result tables
>
> \# Documentation
>
> \# Containerized environment \# Citation metadata
>
> \# Apache-2.0 or MIT \# Project overview

Key Design Principles

> • Modularity: Each module (routing, coverage, intensity, pricing) is
> independently testable
>
> • Transparency: All policy logic (coverage rules, phase-in) encoded as
> functions with unit tests
>
> • Reproducibility: One-command regeneration of all results (make
> reproduce)
>
> • Extensibility: New emission methods or policy updates can be added
> without breaking existing code
>
> 6

Implementation Timeline (10-12 Weeks)

> Week Tasks & Deliverables
>
> 1-2 Scoping & Data Seeding
>
> • Lock policy scope: coverage, phase-in, transshipment, CH4/N2O
> time-line
>
> • Build policy test cases (fixtures for intra-EEA, extra-EEA,
> transship-ment, out-of-scope)
>
> • Seed datasets: EEA port registry, transshipment list, EUA prices,
> MRV export
>
> • Decide target publication venues (JOSS + optional domain journal) •
> Deliverable: Data files, test fixtures, project repository structure
>
> 3-4 Minimum Viable Product (Method A)
>
> • Implement routing.py, coverage.py, pricing.py, intensity.py(A)
>
> • Write unit tests for coverage logic (golden-file approach)
>
> • Build CLI: ingest CSV (port pairs + IMO numbers) → output EUR/leg,
> EUR/voyage
>
> • Deliverable: Working CLI tool with Method A, passing all unit tests
>
> 5-6 Method B & Optional AIS Pipeline
>
> • Implement intensity.py(B) using EPA Marine Emissions Tools
>
> • Document engineering assumptions (power curves, SFOC defaults, fuel
> type)
>
> • (Optional) AIS pipeline: pyais decoding → AISdb storage → voyage
> reconstruction
>
> • Deliverable: Dual-method estimator; AIS case study (if pursued)
>
> 7-8 Experiments & Validation
>
> • Experiment 1 (Accuracy): Compare Method A vs B on ships with MRV
> data
>
> Report MAE/MAPE on tCO2 and EUR/voyage
>
> • Experiment 2 (Policy sensitivity): Cost deltas from transshipment
> rule
>
> on EU ↔ non-EU container routes
>
> • Experiment 3 (Price scenarios): Sensitivity to EUA price (EUR
> 60-100/t)
>
> • Uncertainty analysis: Monte Carlo on intensity (±10-20%), distance
> (±2-3%), price bands; report P50/P90 EUR/voyage
>
> • Deliverable: Experiment scripts, result tables, figures for paper
>
> 9 Reproducibility & Packaging
>
> • One-command reproducibility: make reproduce regenerates all out-puts
>
> • Add CITATION.cff, LICENSE (Apache-2.0 or MIT), data provenance notes
>
> • Policy/version pinning: commit hashes, ETS ruleset version
> documen-tation
>
> • Deliverable: Containerized environment (Docker), archival release
> prep
>
> 10 Software Paper Writing
>
> • Draft JOSS or SoftwareX paper: problem, design, validation,
> docu-mentation
>
> • Create archival release on Zenodo (assign DOI)
>
> • Deliverable: Complete software paper draft, Zenodo release
>
> 11-12 Method Paper & Case Study
>
> • (Optional) Extend results: CH4/N2O-ready design section • Detailed
> case study: Asia ↔ EU route with container ship • Build minimal web
> demo (FastAPI + single-page UI)
>
> • Deliverable: Method paper draft, web demo, final presentation

Note: The timeline is flexible to accommodate student progress. Core
deliverables (Weeks 1-10) are mandatory; Weeks 11-12 focus on optional
enhancements and publication-ready polish.

Project Deliverables

1\. Software Package

> • Clean, well-documented Python codebase with modular architecture
>
> • Comprehensive unit and integration test suite (coverage \> 80%)
>
> • Command-line interface (CLI) for batch processing
>
> • Optional: Web API (FastAPI) and minimal front-end interface
>
> • Open-source license (Apache-2.0 or MIT)
>
> • Public GitHub repository with CI/CD pipeline
>
> • Archived release on Zenodo with persistent DOI

2\. Documentation

> • README with installation, quick start, and examples
>
> • User guide (how to prepare input data, interpret outputs)
>
> • API reference (auto-generated from docstrings)
>
> • Policy documentation (coverage rules, phase-in, assumptions)
>
> • Data provenance (sources, versions, update procedures)

3\. Reproducible Experiments

> • Experiment scripts for all validation analyses
>
> • Generated figures and tables ready for publication
>
> • Single-command reproducibility (make reproduce)
>
> • Documented computational environment (Docker container)

4\. Research Papers

> • Software paper: Submitted to Journal of Open Source Software (JOSS)
> or SoftwareX
>
> – Focus: Tool design, implementation, validation, and community value
> – Length: 2-4 pages + code/documentation review
>
> • Method paper (optional): Target Transportation Research Part D or
> Maritime Policy & Management
>
> – Focus: Emission estimation methodology, policy sensitivity, case
> studies – Length: Full research article format
>
> 8

5\. Final Presentation

> • 20-minute presentation covering motivation, methods, results, and
> impact
>
> • Live demonstration of the tool
>
> • Q&A session with faculty and peers

Evaluation Criteria

The project will be assessed based on the following criteria, which also
serve as validation checks for the research paper:

1\. Policy Conformance (25%)

> • Coverage rules: Correct implementation of 100/50/0 split for
> intra-EEA, extra-EEA, out-of-scope legs
>
> • Transshipment rule: Proper handling of Tanger Med and East Port Said
> stops
>
> • Phase-in schedule: Accurate application of 40%/70%/100% surrender
> ratios by year
>
> • First surrender deadline: Correct accounting for 30 September 2025
> deadline
>
> • Future gases: Architecture supports CH4/N2O from 2026
>
> • Verification: Unit tests with golden-file fixtures pass for all
> policy scenarios

2\. Technical Implementation (25%)

> • Code quality: Clean, modular, well-documented, follows PEP 8 style
> guidelines
>
> • Testing: Comprehensive test coverage (\> 80%), all tests pass
>
> • Distance accuracy: SeaRoute results within ±2-3% of published route
> examples
>
> • Emission plausibility: Method B within ±15-25% of Method A on same
> vessel/year
>
> • Performance: Can process \> 100 voyages per second on standard
> hardware

3\. Experimental Validation (25%)

> • Accuracy assessment: MAE/MAPE reported for both methods against
> held-out MRV data
>
> • Policy sensitivity: Quantified cost impact of transshipment rule on
> representative routes
>
> • Price scenarios: Tornado charts and sensitivity tables for EUA price
> variation
>
> • Uncertainty quantification: Monte Carlo analysis with documented
> assumptions
>
> • Ablation studies: Demonstrate mis-estimation when policy rules are
> incorrectly applied
>
> 9

4\. Reproducibility & Documentation (15%)

> • One-command reproduction: All results regenerable from raw data
>
> • Environment specification: Dockerfile or conda environment with
> pinned versions
>
> • Data provenance: Clear documentation of all data sources, versions,
> access methods
>
> • Archival: Zenodo release with DOI, proper citation metadata
> (CITATION.cff)
>
> • User documentation: Clear installation instructions, usage examples,
> API reference

5\. Research Contribution (10%)

> • Novelty: First open-source, policy-faithful EU ETS maritime cost
> estimator
>
> • Paper quality: Clear writing, proper citations, publication-ready
> figures/tables
>
> • Community value: Tool addresses real need identified in literature
> review
>
> • Open science: Exemplifies FAIR principles and research software best
> practices

Recommended Team Roles

For a group of 3-4 students, we recommend the following division of
responsibilities:

Data Team (1 student)

> • Extract and preprocess THETIS-MRV data (ship-level intensity tables)
>
> • Build EEA/non-EEA port flag registry
>
> • Compile historical EUA price time series from
> Sandbag/TradingEconomics
>
> • Maintain data provenance documentation
>
> • Create test data fixtures for unit tests

Policy Team (1 student)

> • Implement coverage logic (coverage.py)
>
> • Encode transshipment rules and phase-in schedules
>
> • Write comprehensive unit tests for all policy scenarios
>
> • Document regulatory requirements and assumptions
>
> • Track EU policy updates and regulation changes

Engine Team (1-2 students)

> • Implement Method A (MRV-intensity) and Method B (engineering-lite)
>
> • Integrate SeaRoute for distance calculation
>
> • Connect EPA Marine Emissions Tools for Method B
>
> • Design and execute benchmarking experiments
>
> • Conduct sensitivity and uncertainty analyses
>
> 10

UX/Documentation Team (1 student)

> • Build CLI and optional web API (FastAPI)
>
> • Write user guide, API reference, and README
>
> • Create reproducibility pipeline (make reproduce)
>
> • Set up CI/CD (GitHub Actions), Docker container
>
> • Draft software paper and prepare Zenodo release

Note: Students are encouraged to collaborate across roles and contribute
to multiple compo-nents. Regular team meetings (weekly standups) are
recommended to ensure integration and progress tracking.

What Makes This Project Publishable

Novelty

> • First open-source implementation: Addresses gap identified by
> comprehensive litera-ture review (126M papers searched)
>
> • Policy-faithful coverage logic: Includes transshipment rule
> correctly, with testable proofs
>
> • Dual-path emissions engine: MRV-intensity vs. engineering-lite with
> transparent error bounds
>
> • Reproducible pipeline: Closed commercial calculators don’t expose
> code or methodol-ogy

Rigor

> • Comprehensive validation: Accuracy, sensitivity, uncertainty,
> ablation studies
>
> • Unit-tested policy logic: Golden-file fixtures for all coverage
> scenarios
>
> • Documented assumptions: Emission factors, distance methods, price
> sources all cited
>
> • Archival release: Zenodo DOI ensures long-term citability

Community Value

> • Teaching: Universities can use for maritime transport /
> environmental economics courses
>
> • Research: Scenario analysis, policy impact studies, back-testing
> compliance costs
>
> • Policy: Port authorities, regulators can use for impact assessments
>
> • Industry: Shipping companies can use for indicative cost planning
> (with appropriate disclaimers)
>
> 11

Reproducibility & FAIR Principles

> • Findable: GitHub repository, Zenodo DOI, CITATION.cff metadata
>
> • Accessible: Open-source license, containerized environment, public
> data sources
>
> • Interoperable: Standard formats (CSV input/output), documented API
>
> • Reusable: Clear documentation, modular design, comprehensive tests

Ethics, Scope & Disclaimers

Intended Use

This tool is designed for educational, research, and indicative planning
purposes only. It is not intended for:

> • Oficial regulatory compliance reporting
>
> • Financial trading or investment decisions
>
> • Legal or contractual commitments

Data Limitations

> • MRV data lag: THETIS-MRV contains prior-year verified data;
> real-time emissions are not available
>
> • Price feeds: EUA prices from Sandbag/TradingEconomics are historical
> or indicative; actual spot/futures prices may differ
>
> • Coverage simplifications: Tool assumes straightforward port-to-port
> voyages; complex multi-leg journeys may require manual verification

Future Policy Changes

EU ETS regulations are subject to updates and amendments. Students will
document the regulatory version (with effective dates) used in the
implementation and provide mechanisms for future updates.

Academic Integrity

All data sources, code libraries, and prior research must be properly
cited. Students are expected to:

> • Use only openly licensed tools and datasets
>
> • Attribute all external contributions
>
> • Document any modifications or assumptions
>
> • Follow open science best practices
>
> 12

Key References & Data Sources

EU ETS Policy & Regulations

> • European Commission (2024). Reducing emissions from the shipping
> sector.
> [https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissions-ship](https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissions-shipping-sector)
>
> • European Commission (2024). FAQ – Maritime transport in EU Emissions
> Trading Sys-tem (ETS).
>
> [https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-em](https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissions-shipping-sector/faq-maritime-transport-eu-emissions-trading-system-ets)issions-ship
> [faq-maritime-transport-eu-emissions-trading-system-ets](https://climate.ec.europa.eu/eu-action/transport-decarbonisation/reducing-emissions-shipping-sector/faq-maritime-transport-eu-emissions-trading-system-ets)
>
> • Commission Implementing Regulation (EU) 2023/2297 (transshipment
> port list).
> <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202302297>

Emissions Data & Tools

> • EMSA (2024). THETIS MRV – Monitoring, Reporting and Verification.
> <https://www.emsa.europa.eu/thetis-mrv.html>
>
> • US EPA (2024). Marine Emissions Tools (Beta 2).
> <https://github.com/USEPA/Marine_Emissions_Tools>
>
> • ICCT (2021). Accounting for Well-to-Wake Carbon Dioxide Equivalent
> Emissions.
> <https://theicct.org/wp-content/uploads/2021/06/Well-to-wake-co2-mar2021-2.pdf>
>
> • Eurostat. SeaRoute: Compute Shortest Maritime Routes.
> <https://github.com/eurostat/searoute>

AIS Processing (Optional)

> • Römer, L. (2024). pyais: AIS Message Decoding and Encoding.
> <https://github.com/M0r13n/pyais>
>
> • World Bank (2024). Greenhouse Gas Emissions from Maritime Trafic –
> Pacific Observa-tory.
>
> <https://worldbank.github.io/pacific-observatory/ais/ais_emissions.html>

Carbon Pricing

> • Sandbag Climate Campaign (2024). Carbon Price Viewer.
> <https://sandbag.be/carbon-price-viewer/>
>
> • Trading Economics (2024). EU Carbon Permits – Price, Chart,
> Historical Data. <https://tradingeconomics.com/commodity/carbon>

Research Literature

> • Sun, L., Wang, X., Hu, Z., & Ning, Z. (2024). Carbon and Cost
> Accounting for Liner Shipping Under the European Union Emission
> Trading System. Frontiers in Marine Sci-ence.
>
> • Ventikos, N., Stamatopoulou, E., Kalogeropoulos, I., & Louzis, K.
> Development of a Tool for Calculating Ship Air Emissions. Global NEST
> International Conference.
>
> • Ji, C., & El-Halwagi, M. (2020). A Data-Driven Study of IMO
> Compliant Fuel Emissions with Consideration of Black Carbon Aerosols.
>
> 13
>
> • Elicit AI (2024). Estimating EU ETS Compliance Costs for Shipping –
> Literature Review Report.

Software Publishing Venues

> • Journal of Open Source Software (JOSS). <https://joss.theoj.org/>
>
> • SoftwareX. <https://www.sciencedirect.com/journal/softwarex>
>
> • Transportation Research Part D: Transport and Environment.
> [https://www.sciencedirec](https://www.sciencedirect.com/journal/transportation-research-part-d-transport-and-environment)t.
> [com/journal/transportation-research-part-d-transport-and-environment](https://www.sciencedirect.com/journal/transportation-research-part-d-transport-and-environment)
>
> • Maritime Policy & Management.
> <https://www.tandfonline.com/journals/tmpm20>

Support & Resources

Supervision

> • Weekly meetings: 1-hour progress check-ins with supervisor
>
> • Ofice hours: Available by appointment for technical questions
>
> • Code reviews: Regular feedback on implementation and documentation

Computational Resources

> • GitHub repository: Provided and managed by course instructor
>
> • Compute cluster: Available for large-scale data processing (if
> needed)
>
> • Software licenses: All tools are open-source (no licensing costs)

Learning Resources

> • Python packaging and testing best practices tutorials
>
> • Research software engineering guides (e.g., The Turing Way)
>
> • JOSS/SoftwareX author guidelines and example papers
>
> • EU ETS regulatory documents and technical guidance
>
> This project description is subject to refinement. Students will be
> consulted on any modifications.
>
> Questions? Contact: eyuphan.koc@bogazici.edu.tr
>
> 14
