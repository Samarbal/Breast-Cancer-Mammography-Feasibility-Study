# TASK-01 — permissions and attribution

Audit date: 2026-11-05. This is a source-based permissions summary, not institutional legal or ethics approval.

## VERIFIED

- The [official CBIS-DDSM access table](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) labels both DICOM images and the mass CSVs **Creative Commons Attribution 3.0 Unported (CC BY 3.0)**, Version 1 updated 2017-09-14. The page requires a data citation with DOI:

  > Sawyer-Lee, R., Gimenez, F., Hoogi, A., & Rubin, D. (2016). *Curated Breast Imaging Subset of Digital Database for Screening Mammography (CBIS-DDSM)* [Data set]. The Cancer Imaging Archive. https://doi.org/10.7937/K9/TCIA.2016.7O02S9CY

- [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) permits copying, sharing, and adaptation, including commercial use, with appropriate credit, a license link, and notice of adaptations where applicable. The license does not imply endorsement or provide a warranty.
- [TCIA's data usage policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions) requires users not to try to identify or contact participants, and to acknowledge the specific dataset and repository in oral/written presentations and publications. It directs investigators doing human-subjects research to applicable review requirements. For a manuscript, it asks for the collection citation plus the [TCIA repository paper](https://doi.org/10.1007/s10278-013-9622-7). The [collection page](https://www.cancerimagingarchive.net/collection/cbis-ddsm/) also lists the [dataset authors' paper](https://doi.org/10.1038/sdata.2017.177) as recommended reading/citation.
- TCIA says mirroring public datasets or offering direct access through another tool/site involves its [Data Analysis Centers policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions). A public prototype should avoid hosting or redistributing original images until that route and local policy are reviewed.

## INFERRED — working permissions plan

- Academic research use and local read-only processing of an official TCIA download appear compatible with CC BY 3.0 and the posted TCIA policy, subject to institutional rules. Keep original DICOM/CSV immutable; label derived masks, thumbnails, and figures as transformed CBIS-DDSM material, with provenance and attribution.
- A prototype can display predictions on locally held research images as a technical demonstration only after access controls and consent/privacy handling are reviewed. License permission alone does not authorize a clinical service or validate medical decisions.

## UNVERIFIED — obtain local decisions before public release

- Whether the university requires an ethics/IRB determination for this student project, even with publicly released de-identified data.
- Whether a deployed demo will expose patient images, derivative thumbnails, DICOM metadata, or re-identification risk; its hosting location and audience are not specified.
- Whether any additional current TCIA site terms or institution-specific security requirements apply at download time; review the live acceptance screen when acquiring the smoke-test cases.

## Required attribution checklist

1. Cite the full CBIS-DDSM dataset citation and DOI in reports, slides, and any repository README using data.
2. Link the [CC BY 3.0 license](https://creativecommons.org/licenses/by/3.0/) and identify any modified/derived material.
3. Credit TCIA as the access repository; cite its repository paper in a manuscript per [TCIA policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions).
4. Do not seek identities, contact participants, or redistribute images via a mirror without reviewing TCIA's applicable policy.

## Evidence links

- [CBIS-DDSM license and citation](https://www.cancerimagingarchive.net/collection/cbis-ddsm/)
- [TCIA usage policy](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions)
- [CC BY 3.0 deed](https://creativecommons.org/licenses/by/3.0/)
