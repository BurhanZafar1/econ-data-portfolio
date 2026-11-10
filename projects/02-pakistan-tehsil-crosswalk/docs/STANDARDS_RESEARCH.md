# Standards for data papers and replication packages: what the sources say, and a checklist

Compiled 2026-11-09 from primary sources (each opened and read; URL given). Where a source was only partly accessible, that is stated. Items in the checklist cite the section number of the source that states them; nothing in the checklist is invented beyond what a cited source states, except where marked "(project-specific application)".

Scope: the Pakistan district/tehsil crosswalk 1951–2023 (population and area weights, event register, lineage tables) and the night-time lights panel on 2023 units.

---

## Part A. What the standards say

### A1. AEA Data and Code Availability Policy

Source: https://www.aeaweb.org/journals/data/data-code-policy (read in full).

What must be deposited:
- Materials "sufficient to permit replication": data, code and computation details, in an open trusted repository (AEA Data and Code Repository at openICPSR strongly encouraged). Unzipped; "Zipped deposits will be returned."
- Raw data unless non-public-data exceptions apply, or the exact extract is in a FAIR repository with a permanent identifier (DOI).
- Analysis data, unless reproducible from accessible data.
- "All programs used to generate the analysis data from raw data must be included," even when raw data are withheld; plus all programs producing results.
- A master script is "strongly encouraged"; otherwise step-by-step instructions. A setup program that installs required packages.
- Notify the Data Editor if unusual or costly software is required.

Data Availability Statement (DAS):
- Required even when all data are deposited. Must describe provenance: how, where and under what conditions a researcher can access the original data, "any limitations and the expected monetary and time cost of data access."
- "Upon request" from the authors is "generally not acceptable" as an access route.
- For non-public data: preserve data and code "no less than five years following publication," make code public, document the source with contact information.

README (must be a PDF in the top-level directory) must include:
1. the DAS (or a reference to it), plus statements that authors had legitimate access and the right to redistribute included data;
2. a description of package contents;
3. software and hardware used, "expected running time," specific versions and libraries;
4. step-by-step instructions to run the code and reproduce results;
5. a mapping of programs to outputs and to the paper's exhibits;
6. data citations not already in the paper;
7. "The README must clearly indicate any omission."

Other: all data must be cited in AEA reference style; software citations encouraged. Authors keep copyright but must license files for replication use (default licence provided; other licences reviewed by the Data Editor). The Data Editor "will assess compliance with this policy," including reproducibility checks.

### A2. Template README for Social Science Replication Packages (Social Science Data Editors)

Sources: https://social-science-data-editors.github.io/template_README (overview page) and https://social-science-data-editors.github.io/template_README/template-README.html (full template), both read. Markdown template: https://github.com/social-science-data-editors/template_README/blob/release-candidate/templates/README.md. Releases: https://github.com/social-science-data-editors/template_README/releases.

Section structure and required contents:

- **Overview**: brief overview of the material and a start-to-finish guide to reproducing results.
- **Data Availability and Provenance Statements**: where all data came from, where located, how accessed, for every source, "including data not included in the archive." Citations must be augmented with access details (registration, cost, procedure), not just a URL.
  - *Statement about Rights* (checkboxes): "I certify that the author(s) of the manuscript have legitimate access to and permission to use the data"; "documented permission to redistribute/publish the data contained within this replication package."
  - *License for Data* (optional, recommended): separate LICENSE.txt; note that data may carry inherited licence terms from the provider.
  - *Summary of Availability* (checkboxes): all / some / no data publicly available; confidential-data preservation period.
  - *Details on each Data Source*: for each source the data files, format, data dictionary or codebook, whether provided, and bibliographic reference. Summary table columns: `Data.Name | Data.Files | Location | Provided | Citation`.
  - *Dataset list*: every file described; labelled variables; table columns `Data file | Source | Notes | Provided`.
- **Computational requirements**:
  - *Software Requirements*: all software with exact versions, OS requirements, package versions; checkbox (highly recommended): package "contains one or more programs to install all dependencies and set up the necessary directory structure."
  - *Controlled Randomness*: "Random seed is set at line ___ of program __" or "No Pseudo random generator is used."
  - *Memory, Runtime, Storage Requirements*: runtime bands (<10 min … >14 days), storage bands (<25 MB … >250 GB), and the hardware/OS used, per stage of processing.
  - *Description of programs/code*: high-level overview of each program and purpose; "remove obsolete files."
  - *License for Code* (optional, recommended): e.g. MIT, BSD, GPL in LICENSE.txt.
- **Instructions to Replicators**: a strict linear list of steps; if more than 4–5 manual steps, wrap them in a main program or Makefile; describe run order, runtime, and any manual steps "such as GIS procedures."
- **List of tables and programs**: checkbox whether all numbers in text / all tables and figures / selected ones are reproduced; table columns `Figure/Table # | Program | Line Number | Output file | Note`.
- **References**: full bibliographic references in journal style, consistent with manuscript and data citations.
- **Acknowledgements**.

Overview page adds: wall-clock run time on the stated hardware; "no manual interventions required unless absolutely unavoidable"; the template itself is CC-BY-NC.

### A3. Gentzkow and Shapiro, "Code and Data for the Social Sciences: A Practitioner's Guide" (2014)

Source: https://economic-analysis-with-stata.uni-goettingen.de/material/Replication%20&%20transparency/Further%20reading/Gentzkow_Shapiro_2014_Guide.pdf (read; the canonical copy is at web.stanford.edu/~gentzkow/research/CodeAndData.pdf, not fetched).

Rules, verbatim:
- Automation: "Automate everything that can be automated." "Write a single script that executes all code from beginning to end."
- Version control: "Store code and data under version control." "Run the whole directory before checking it back in."
- Directories: "Separate directories by function." "Separate files into inputs and outputs." "Make directories portable."
- Keys: "Store cleaned data in tables with unique, non-missing keys." "Keep data normalized as far into your code pipeline as you can."
- Abstraction: "Abstract to eliminate redundancy." "Abstract to improve clarity." "Otherwise, don't abstract."
- Documentation: "Don't write documentation you will not maintain." "Code should be self-documenting."
- Management: "Manage tasks with a task management system." "E-mail is not a task management system."

### A4. Crosswalk and geographic-harmonisation precedents

#### A4.1 Eckert, Gvirtz, Liang and Peters (2020), NBER WP 26770

Source: https://www.nber.org/system/files/working_papers/w26770/w26770.pdf (read). Landing page: https://www.nber.org/papers/w26770.

- Weights: reporting map intersected with reference map in GIS (Python/GeoPandas); each weight is the sub-unit's share of the reporting unit's land area. Stock variables are "distributed proportionally to area size across the subunits." For averages, weights must be built from reference-unit shares (their footnote 6). Where possible they recommend an observed weighting variable (e.g. workers) rather than area.
- Validation: crosswalked population compared with Census totals by decade (their Table E.1); "The largest discrepancy occurs in 1790, where we can only map 99.1% of the US population." A before/after map (Figure 5) as a qualitative check. No confidence intervals or formal error bounds.
- Uncertainty reporting: shapefile imprecision means "it is difficult to determine which intersections identify actual county boundary changes"; intersections under 10 m² dropped as slivers. Table 2 reports the share of weights in (0.2, 0.8) and (0.4, 0.6) by decade, i.e. how much of the crosswalk is non-trivial splits.
- Release: three CSV crosswalks with variable descriptions (Tables C.1–C.3), Python code for general crosswalks, replication code, shapefiles, a worked example, step-by-step instructions (Appendix B). Output format: reporting ID, reference ID, weight.
- User guidance: "researchers should always use the most disaggregated maps for which data are reported"; stock weights for stocks; one-to-many merge, multiply by weight, sum to reference units; watch code systems (FIPS vs ICPSR).

#### A4.2 Ferrara, Testa and Zhou (2024), NBER WP 32206; published in Journal of Economic Geography

Source: https://nber.org/system/files/working_papers/w32206/w32206.pdf (read). Data: https://doi.org/10.3886/E150101 (openICPSR project 150101; listing at https://www.openicpsr.org/openicpsr/project/150101/version/V4/view).

- Six weighting models: M1 area-based (equivalent to existing area crosswalks); M2–M4 population-based using 1 km gridded historical population (Fang and Jawitz 2018) with urban/rural split, uninhabitable-area exclusion and elevation; M5–M6 using 250 m built-up/property-record grids (HISDAC-US).
- Validation: harmonised values compared with official tabulations for 1960–1990 on six variables; metrics are correlation, RMSE and MAE (their Table 1) and a replication of a published balance test (Table 2). "population-based weights outperform area-based ones in terms of similarity to official data." Correlation ≈0.91 (population weights) vs ≈0.76 (area weights).
- Error statements: "Error in harmonized data stems largely from the act of disaggregating the already-aggregated 'origin' data"; "any disaggregation into smaller units can introduce error in harmonized data, regardless of the weights used." Error is largest for variables distributed more unevenly than population (their Black-population example, correlation 0.62–0.75). They report the share of weights undefined by year (≈25% for 1810 vs ≈5% for 2010) when ancillary grids are sparse.
- Recommendations to users: "we ultimately recommend reporting estimates based on all six weighting models"; "we recommend using M2–M4 for boundary harmonization involving very early census periods and M6 for more recent ones"; use the range across models as a sensitivity check; harmonise only stock variables (transform shares/averages first); state how missing weights are treated (e.g. as zero). The paper does not use the term "modifiable areal unit problem"; its closest statement is that crosswalking to the largest extent "may generate some loss of spatial precision due to sample aggregation."

#### A4.3 Hornbeck county boundary adjustment

Source: Hornbeck (2012), "The Enduring Impact of the American Dust Bowl," AER, copy at https://brianhwpark.github.io/files/teaching-resources/monmouthcollege-econ-380/econ-380-papers/econ-380-intro-causality/Hornbeck-EnduringImpactAmerican-2012.pdf (read). Replication files: openICPSR project 112528 (https://www.openicpsr.org/openicpsr/project/112528/version/V1/view, listing only).

- The paper states only: "To account for county border changes, census data are adjusted in later periods to maintain the 1910 county definitions (Hornbeck 2010)"; county acres "held fixed at 1910 borders"; balanced panel of 779 counties 1910–1997. The method itself is deferred to Hornbeck (2010, AER, "The Enduring Impact of the American Dust Bowl" data appendix / Hornbeck 2010 QJE), which was not fetched. Takeaway for documentation: a fixed base-year geography, a balanced panel, and an explicit statement of which year's borders are held fixed.

#### A4.4 SHRUG (Asher, Lunt, Matsuura, Novosad 2021, World Bank Economic Review)

Source: https://ryumatsuura.github.io/files/almn_2021_shrug.pdf (read; first ~100k characters). Project site: https://www.devdatalab.org/shrug (not fetched).

- Stable identifier design: a `shrid` "describes a geographical unit that can be mapped consistently across all rounds"; merged/split locations are aggregated into one shrid (the lowest common denominator), with the consequence that some shrids are very large (whole city-states).
- Matching provenance: digital keys plus narrative district handbooks, hierarchical matching (district → subdistrict → village), fuzzy matching with a documented tool ("masala-merge").
- Match rates reported per census and per state: "the match rate is 98 percent or higher for all but two small states in 1991"; lower match rate for 1990 Economic Census stated explicitly.
- Imputation thresholds and flags: fields set to missing where more than 25% of population would be imputed; ~10% of locations georeferenced only by points, assigned Thiessen polygons "and flagged."
- Uncertainty: "Some degree of incorrect matches is inevitable"; a simulation dropping up to 25% of shrids to show robustness of aggregates; bootstrap for first-stage estimation error; warnings that some outliers are "almost surely incorrect."
- Night lights in SHRUG: NOAA grid (DN 0–63, 1 km) aggregated to polygons; they use log of average luminosity per polygon, control for polygon area (cell count), add 1 before logging to keep zeros, and report IHS gives "virtually identical" results; they caution against applying cross-sectional light-GDP elasticities to time-series changes.
- Licensing and versioning: ODbL-style copyleft for non-commercial users; version numbers (v1.5 at publication); "all prior versions will be archived on the Harvard Dataverse"; codebook and metadata table on the website; data "regularly updated."

#### A4.5 IPUMS International geographic harmonisation

Sources: https://international.ipums.org/international/geography_variables.shtml (read); MPC working paper 2016-03, https://assets.ipums.org/_files/mpc/wp2016-03.pdf (read); Pakistan variable https://international.ipums.org/international-action/variables/GEO2_PK (read).

- Two variable families: harmonised ("consistent geographic units for a country across sample years") and year-specific ("retain all of the original detail from each sample, but they are usually not fully consistent over time"). Recommendation: use both; "Year-specific geography provides greater detail and should be used in conjunction with spatially harmonized maps."
- Harmonisation rule: aggregate rather than split; "the harmonized unit will have the boundaries of the largest version of the unit"; where territory is redistributed "the units are combined." Explicit statement of loss: "Some geographic detail is typically lost in the construction of the harmonized units." Where changes are too extensive, consistent units only for limited periods.
- Regionalisation to a 20,000-population threshold (confidentiality), with contiguity and nesting enforced (REDCAP).
- Documentation: GIS shapefiles with unique identifiers for harmonised and year-specific units at levels 1 and 2; "The website provides extensive documentation about how units have been harmonized and regionalized"; per-variable comparability notes.
- Pakistan precedent: GEO2_PK covers 1973, 1981, 1998; "spatially harmonized to account for political boundary changes across census years"; "Boundary changes for GEO2_PK are too numerous to list here, but users should be aware that there were changes over time"; "All Pakistan samples exclude the Federally Administered Tribal Areas, Northern Areas (Gilgit-Baltistan) and Kashmir"; shapefile downloadable. Note: this is the weakest part of the IPUMS documentation (no event list), which is a gap the present project's event register fills. No PIDE or Data Darbar harmonisation document was found within the search budget; none should be cited.

### A5. Night-lights practice

#### A5.1 Henderson, Storeygard and Weil (2012), AER 102(2): 994–1028

Sources: https://www.nber.org/papers/w15199 (abstract page, read) and https://researchonline.lse.ac.uk/id/eprint/52095 (abstract, read). Full-text PDF not fetched within budget; the data-handling details below are therefore taken only from what the Remote Sensing review (A5.4) attributes to this literature, and the paper DOI is https://doi.org/10.1257/aer.102.2.994.
- Framework: lights growth augments official income growth, assuming measurement error in lights is uncorrelated with error in national accounts; lights matter most where statistical capacity is weakest; "composite with roughly equal weights" for the worst national accounts.
- The widespread economics practice derived from this paper, as characterised by the review in A5.4, is to rely on year (or satellite-year) fixed effects to absorb inter-satellite differences in DMSP digital numbers; the review argues this only works if satellite effects are random.

#### A5.2 Chen and Nordhaus (2011), PNAS

Source attempted: https://pmc.ncbi.nlm.nih.gov/articles/PMC3102367 (blocked by a browser check; not read). NBER WP 16317 listing at https://econpapers.repec.org/RePEc:nbr:nberwo:16317. Not summarised here beyond the fact of its existence; do not cite specific claims from it on the basis of this document.

#### A5.3 Gibson, Olivia and Boe-Gibson (2020/2021), "Which night lights data should we use in economics, and where?", JDE 149

Source: MPRA working-paper version, https://mpra.ub.uni-muenchen.de/97582/1/MPRA_paper_97582.pdf (read). Journal record: https://ideas.repec.org/a/eee/deveco/v149y2021ics0304387820301772.html. (Author list is three names; "Li" is not a coauthor.)
- DMSP defects: "'blurring' is an inherent feature of DMSP data" (off-nadir viewing, 5×5 pixel aggregation, geolocation error; lit area overstated by ~77% on average across 15 big cities); top-coding at DN 63; "the dynamic range of the DMSP sensor is less than two orders of magnitude"; 6-bit DN vs VIIRS 14-bit; "there is no on-board calibration."
- VIIRS advantages: ~0.7 km constant resolution, in-flight calibration, ~7 orders of magnitude dynamic range; in Indonesia the lights–GDP relation is "twice as noisy" with DMSP (unexplained variation 64% vs 32% for urban units).
- Rural areas: "neither DMSP nor VIIRS seem to provide a good proxy for rural economic activity"; "economists should look elsewhere for studying rural areas remotely."
- Transformation: IHS, which "lets us use zeros without resorting to transformations like adding one to all values before logging."
- Sensor transition: not analysed; they note DMSP ends 2013, monthly VIIRS starts April 2012, and recommend moving to VIIRS (continuity via NOAA-20).

#### A5.4 Critical review of economics use of night lights (Remote Sensing 2025, 17(7): 1130, "Lost in Translation?")

Source: https://mdpi.com/2072-4292/17/7/1130 (read in two parts).
- Top-coding: DN ≥ 55 is "a threshold used by some for identifying pixels subject to top-coded pixels on at least some nights of the year."
- Bottom-coding "creates 'false zeros'"; in their Nigeria example 57% of children lived in clusters that DMSP showed as unlit, mostly false zeros.
- Transformation: IHS is "equivalent to logging non-zero values while allowing zeros to be included"; dropping zeros before logging removes many pixels.
- Intercalibration: few economics studies use intercalibrated DMSP; year fixed effects absorb satellite effects only if those are random, and their tests suggest they are not.
- Overpass-time drift of DMSP satellites affects temporal consistency; VIIRS annual composites built from masked monthly data to rule out ephemeral lights.
- Resolution: DMSP footprint is far coarser than the 30 arc-second output grid; authors should state the sensor's ground field of view, not just grid size (citing Elvidge et al. 2013).
- Recommendations: use VIIRS or at least check robustness with it, especially for fine spatial units; test whether satellite effects are random; weigh long/less-accurate vs short/more-accurate series; state how zeros are handled.

#### A5.5 Harmonised DMSP–VIIRS series

Li, Zhou, Zhao and Zhao (2020), "A harmonized global nighttime light dataset 1992–2018," Scientific Data. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7272434 (read). GEE community listing: https://gee-community-catalog.org/projects/hntl/.
- Method: stepwise intercalibrated DMSP stable lights (F10–F18) for 1992–2013; VIIRS monthly vcm radiance averaged to annual composites weighted by cloud-free observations; noise masks (μ+3σ above 45° latitude; empirical threshold 0.3 nW elsewhere for fires/boats; bright pixels outside urban clusters removed); Gaussian point-spread resampling to DMSP resolution; ln(V+1) then a four-parameter sigmoid fitted on 2013 to produce DMSP-like DN for 2014–2018.
- Validation: histogram comparison 2012/2013 (DN ≤ 10 excluded); temporal trend of sum of lights and lit-pixel counts at DN thresholds 7, 20 and 30, with VIIRS-derived series "more reliable at higher thresholds"; visual comparisons; no quantitative correlation reported.
- Caveats: sigmoid fitted only on 2013 overlap; 2012 VIIRS partial (from April); plateau/compression above DN ~60; series "more fluctuated during the period from 2015 to 2018" at low thresholds; "users should be cautious when applying the data in rural areas due to the uncertainty in low luminance regions"; overpass time differs (VIIRS ~1:30 am vs DMSP ~9 pm); residual aurora/greenhouse lights.

Chen, Yu, Yang, Li and Jia (2021), "An extended time series (2000–2018) of global NPP-VIIRS-like nighttime light data from a cross-sensor calibration," ESSD 13: 889–906. Source: https://essd.copernicus.org/articles/13/889/2021/ (read). Data DOI https://doi.org/10.7910/DVN/YGIVCD; code DOI https://doi.org/10.7910/DVN/JRM2XE.
- Method: VIIRS-like (not DMSP-like) series; EANTLI input (stepwise-calibrated DMSP × MODIS EVI); convolutional auto-encoder trained on 2013; annual VIIRS composites from monthly data by median; postprocessing masks dark background, zeroes values below 1 nW cm⁻² sr⁻¹, smooths year-to-year change against the DMSP trend; 15 arc-second grid.
- Validation: pixel-level 2012 R² 0.87, RMSE 2.96 nW; city-level R² 0.94–0.95; country-level R² 0.70–0.86; against official 2015 annual VIIRS R² 0.85; total NTL vs population R² 0.84; "no sudden jump" reported at the 2012/2013 join.
- Caveats stated: 2000–2012 values are simulated, not observed; the model targets statistical rather than physical radiance, so absolute values need care; ocean mask removes boats; urban peripheries may be underestimated; users should be aware of the 2012/2013 join.

### A6. Software, citation and licensing mechanics

- CITATION.cff: GitHub docs, https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files (read). Root-level `CITATION.cff` with `cff-version`, `message`, `authors` (family-names, given-names, orcid), `title`, `version`, `doi`, `date-released`, `url`; GitHub shows "Cite this repository" with APA and BibTeX; `type: dataset` at top level produces a data citation; `preferred-citation` can point to the paper. Schema guide: https://github.com/citation-file-format/citation-file-format/blob/1.2.0/schema-guide.md (not fetched).
- Zenodo and CITATION.cff: https://help.zenodo.org/docs/github/describe-software/citation-file/ (read). "Currently Zenodo implements a subset of the CITATION.cff schema" (title, version, license, type, abstract, message, authors with affiliation/orcid, keywords). If `.zenodo.json` exists Zenodo "will only use the .zenodo.json metadata and ignore the CITATION.cff entirely." Validate with cff-convert. Releases are archived through the GitHub integration (separate page, not fetched; the per-release DOI / concept DOI mechanics are therefore not documented here from a primary source).
- Open licences (CC BY 4.0 for data, MIT for code): the Template README (A2) recommends a separate LICENSE.txt for data and for code and names MIT/BSD/GPL for code; the AEA policy (A1) requires that files be usable for replication and that non-default licences be reviewed. Neither source mandates CC BY 4.0; SHRUG uses an ODbL-style copyleft licence. The licence texts themselves were not fetched.
- Checksums, pinned dependency files, CHANGELOG, automated tests: none of the fetched primary sources require these by name. The nearest statements are the AEA requirement for a setup program and exact versions (A1, A2), Gentzkow–Shapiro "Run the whole directory before checking it back in" (A3), and SHRUG's versioning and archived prior versions (A4.4). Items of this kind in the checklist below are marked as project-specific applications of those statements.

### A7. What reviewers criticise in crosswalk-based work, and how the sources pre-empt it

From the sources above (no separate referee-report corpus was found):
- Uniform-density assumption of area weights: stated explicitly as an assumption by Eckert et al. and Ferrara et al.; Ferrara et al. show it is dominated by population-based weights (correlation 0.76 vs 0.91) and that the error is largest for unevenly distributed variables. Pre-emption: provide population-based weights alongside area weights; report results under all weight sets; "use the most disaggregated maps for which data are reported."
- Disaggregation error: "any disaggregation into smaller units can introduce error in harmonized data, regardless of the weights used" (Ferrara et al.). Pre-emption: harmonise to the coarsest geography that answers the question; harmonise stocks only; report the share of weights that are non-trivial (Eckert et al. Table 2) and the share of population that cannot be mapped (99.1% mapped in 1790).
- Low-confidence or undefined weights: Ferrara et al. report the share of undefined weights by year and state how missing weights are treated; SHRUG sets fields to missing above a 25% imputation share and flags point-georeferenced units.
- Loss of detail from aggregation (the IPUMS alternative): "Some geographic detail is typically lost"; pre-empted by offering both harmonised and year-specific geographies.
- Match-rate transparency: SHRUG reports match rates per census and per state and simulates the effect of dropping up to 25% of matched units.
- Night lights: sensor mixing without intercalibration, false zeros, top-coding, rural-area invalidity, and reliance on year fixed effects are the criticisms documented in A5.3–A5.4; pre-empted by using a harmonised series with a stated join year, IHS or log(1+x) with the choice reported, DN-threshold sensitivity, and an explicit rural caveat.
- "Modifiable areal unit problem" as a phrase is not used by Ferrara et al.; the substantive point (results depend on the aggregation chosen) is covered by their sample-aggregation statement.

---

## Part B. Consolidated checklist (46 items)

Each item names the source section (Part A) that states the requirement. "Applied" marks a project-specific application of a more general statement.

### README (top-level, also exported to PDF for a deposit)

1. [ ] Overview paragraph plus a start-to-finish guide to running the package. (A2)
2. [ ] Data Availability Statement covering every input, including inputs not redistributed: how, where and under what conditions each can be obtained, with expected monetary and time cost and any limitations. (A1, A2)
3. [ ] Statement of rights: authors had legitimate access and have documented permission to redistribute each file in the package. (A1, A2)
4. [ ] Summary of availability (all / some / none public) and, for anything withheld, the reason and the preservation period (≥5 years). (A1, A2)
5. [ ] Details on each data source table: `Data.Name | Data.Files | Location | Provided | Citation`, covering every census volume, gazette notification, shapefile and lights product used. (A2)
6. [ ] Dataset list of every file in the package: `Data file | Source | Notes | Provided`. (A2)
7. [ ] Computational requirements: OS, exact Python/R/Stata versions, every package with version; hardware (CPU, memory, disk); wall-clock run time per stage in the template's bands. (A1, A2)
8. [ ] Controlled randomness: state the seed location or state that no PRNG is used. (A2)
9. [ ] Description of each program and its purpose; obsolete files removed. (A2)
10. [ ] Instructions to replicators as a strict linear list; any manual GIS step named explicitly or eliminated. (A2)
11. [ ] Mapping of programs to outputs: a table `Output (table/figure/CSV) | Program | Line | Output file | Note`, covering every published CSV and every validation-report table. (A1, A2)
12. [ ] Full data citations in journal style for every source, and software citations for key packages. (A1, A2)
13. [ ] Any omission from the package stated explicitly. (A1)

### Data

14. [ ] Every cleaned table has a unique, non-missing key (unit ID × census year, or event ID). (A3)
15. [ ] Crosswalk tables follow the `source ID | target ID | weight` layout with weights summing to 1 within each source unit (where the source is fully covered), and a variable-description table for each file. (A4.1)
16. [ ] Both area-based and population-based weights are published, with the ancillary population grid or census-block source named, and users told which to prefer for which period. (A4.2)
17. [ ] Harmonised ("lowest common denominator") units are published alongside year-specific units, and the loss of detail is stated. (A4.5)
18. [ ] Stable identifiers are documented: how an ID persists across merges and splits, and which units became very large as a result. (A4.4)
19. [ ] Excluded territories and periods are stated (e.g. FATA, Gilgit-Baltistan, AJK, 1951 and 1961 coverage). (A4.5 Pakistan note)
20. [ ] A machine-readable data dictionary (CSV) with variable, type, units and source for every column; labelled variables in Stata/R outputs. (A2 "data dictionary or codebook"; CSV form is Applied)
21. [ ] Data kept normalised (event register, lineage, weights as separate tables) until the final apply step. (A3)
22. [ ] Deposited copy is unzipped files, not an archive. (A1)

### Code

23. [ ] One master script runs the whole pipeline from raw inputs to all outputs. (A1, A2, A3)
24. [ ] A setup program installs all dependencies with pinned versions (requirements/lock file; R and Stata package versions listed). (A1, A2; lock file is Applied)
25. [ ] Directories separated by function, with inputs and outputs separated and all paths relative/portable. (A3)
26. [ ] Code and data under version control; whole pipeline re-run before each tagged release. (A3)
27. [ ] Apply functions in R and Stata implement the documented one-to-many merge → multiply by weight → sum procedure and warn on non-stock variables. (A4.1, A4.2)
28. [ ] Automated asserts in the build (weights sum to 1, no duplicate keys, crosswalked totals match census totals within stated tolerance) and output checksums recorded per release. (Applied from A3 and A4.1/A4.2 validation practice)

### Validation (published in the validation reports)

29. [ ] Share of census population and area successfully mapped per census year, with the largest discrepancy named. (A4.1)
30. [ ] Crosswalked totals compared with official totals for years where both exist, with correlation, RMSE and MAE per variable. (A4.2)
31. [ ] Distribution of weights: share of non-trivial weights (e.g. in (0.2, 0.8) and (0.4, 0.6)) per census pair. (A4.1)
32. [ ] Share of undefined or missing weights per year and the rule applied to them. (A4.2)
33. [ ] Match rates for name/ID linkage per census and per province, with unmatched units listed. (A4.4)
34. [ ] Sliver handling rule stated (minimum intersection area dropped) and shapefile precision noted. (A4.1)
35. [ ] Robustness check that drops low-confidence rows or a random share of matched units and reports the effect on aggregates. (A4.4)
36. [ ] Before/after map or figure for at least one census pair as a qualitative check. (A4.1)

### Documentation of uncertainty and assumptions

37. [ ] Uniform-density (and any ancillary-grid) assumption stated formally, with the statement that error is larger for variables distributed more unevenly than population. (A4.1, A4.2)
38. [ ] Guidance that only stock variables should be crosswalked and that shares/averages must be converted first. (A4.1, A4.2)
39. [ ] Recommendation to report results under all published weight sets and use the range as a sensitivity bound; use the most disaggregated source geography available. (A4.1, A4.2)
40. [ ] Confidence or quality flag on each event/row (e.g. point-georeferenced, imputed, source gazette missing) and a threshold above which fields are set missing. (A4.4)
41. [ ] Explicit note that aggregation to large units loses spatial precision and that some incorrect matches are inevitable. (A4.2, A4.4)

### Licensing, citation and versioning

42. [ ] Separate LICENSE files for data and code, with inherited terms from source providers noted (open licence such as CC BY 4.0 for data and MIT for code is consistent with, but not mandated by, the sources). (A1, A2, A6)
43. [ ] Root `CITATION.cff` (`cff-version`, `message`, `authors` with ORCID, `title`, `version`, `doi`, `date-released`, `url`, `type: dataset` or `preferred-citation`), validated with cff-convert; no conflicting `.zenodo.json` unless intended. (A6)
44. [ ] Each release tagged with a version number, archived with a DOI (Zenodo GitHub integration or openICPSR), prior versions remain retrievable, and a CHANGELOG records what changed. (A4.4; CHANGELOG is Applied)

### Night lights panel

45. [ ] Product provenance stated per year: sensor (DMSP-OLS satellite ID or VIIRS DNB), product and version, annual-composite method (stable lights, vcm/vcmsl, median or weighted mean of monthly), intercalibration applied, noise/threshold masks, grid cell size and sensor footprint, zonal-statistic method (sum, mean, per km², per capita) and polygon area used. (A5.3, A5.4, A5.5)
46. [ ] The DMSP–VIIRS join is documented: which harmonised series (Li et al. 2020 DMSP-like DN or Chen et al. 2021 VIIRS-like radiance) or raw products are used, the join year(s) (2012/2013 or 2013/2014), the known caveats (sigmoid plateau above DN ~60; simulated pre-2013 values; low-light instability; overpass time), and a sensor indicator supplied so users can include sensor-period effects; the transformation used (log(1+x) vs IHS) with zeros handled explicitly and the alternative reported; DN-threshold sensitivity (e.g. 7/20/30); and an explicit caveat that lights are a poor proxy for rural and low-density tehsils. (A5.3, A5.4, A5.5, A4.4)

---

## Sources (all URLs opened unless marked)

- AEA Data and Code Availability Policy: https://www.aeaweb.org/journals/data/data-code-policy
- Template README (overview): https://social-science-data-editors.github.io/template_README
- Template README (full): https://social-science-data-editors.github.io/template_README/template-README.html
- Template README markdown and releases: https://github.com/social-science-data-editors/template_README/blob/release-candidate/templates/README.md ; https://github.com/social-science-data-editors/template_README/releases (not opened)
- Gentzkow and Shapiro (2014): https://economic-analysis-with-stata.uni-goettingen.de/material/Replication%20&%20transparency/Further%20reading/Gentzkow_Shapiro_2014_Guide.pdf
- Eckert, Gvirtz, Liang, Peters (2020): https://www.nber.org/system/files/working_papers/w26770/w26770.pdf
- Ferrara, Testa, Zhou (2024): https://nber.org/system/files/working_papers/w32206/w32206.pdf ; data https://doi.org/10.3886/E150101
- Hornbeck (2012) AER copy: https://brianhwpark.github.io/files/teaching-resources/monmouthcollege-econ-380/econ-380-papers/econ-380-intro-causality/Hornbeck-EnduringImpactAmerican-2012.pdf ; replication listing https://www.openicpsr.org/openicpsr/project/112528/version/V1/view (not opened)
- SHRUG paper: https://ryumatsuura.github.io/files/almn_2021_shrug.pdf
- IPUMS International geography: https://international.ipums.org/international/geography_variables.shtml ; MPC WP 2016-03 https://assets.ipums.org/_files/mpc/wp2016-03.pdf ; GEO2_PK https://international.ipums.org/international-action/variables/GEO2_PK
- Henderson, Storeygard, Weil (2012): https://www.nber.org/papers/w15199 (abstract) ; https://doi.org/10.1257/aer.102.2.994 (not opened)
- Chen and Nordhaus (2011): https://pmc.ncbi.nlm.nih.gov/articles/PMC3102367 (blocked, not read)
- Gibson, Olivia, Boe-Gibson (2021): https://mpra.ub.uni-muenchen.de/97582/1/MPRA_paper_97582.pdf
- Remote Sensing 2025 critical review: https://mdpi.com/2072-4292/17/7/1130
- Li et al. (2020) harmonised NTL: https://pmc.ncbi.nlm.nih.gov/articles/PMC7272434
- Chen et al. (2021) VIIRS-like NTL: https://essd.copernicus.org/articles/13/889/2021/
- CITATION.cff on GitHub: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files
- Zenodo and CITATION.cff: https://help.zenodo.org/docs/github/describe-software/citation-file/
