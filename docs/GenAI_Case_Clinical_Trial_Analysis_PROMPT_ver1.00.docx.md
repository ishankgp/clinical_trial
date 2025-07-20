# Clinical Trial Analysis Automation Prompt 

**Objective:** For each provided **NCT ID**, analyze the full clinical trial record from [ClinicalTrials.gov](https://clinicaltrials.gov) and extract structured data fields to generate a standardized, valuable and human intelligent **Analysis-Ready Dataset (ARD)**. This dataset will be used for downstream data analysis and dashboard visualization.

**Clinical trial analysis data fields** 

| Fields to Extract | Source  | Notes |
| :---- | :---- | :---- |
| Primary Drug | Analysis  | Requires analysis and standardization (below rules for data analysis and extraction) |
| Primary Drug MoA | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Primary Drug Target | Analysis | Based on the MoA |
| Primary Drug Modality | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Indication | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Primary Drug ROA | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Mono/Combo | Analysis | Classification based on the combination partner |
| Combination Partner | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| MoA of Combination | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Experimental Regimen | Analysis | Primary drug \+ combination partner (s) |
| MoA of Experimental Regimen | Analysis | Primary Drug MoA \+ MoA of Combination |
| Trial Name  | Analysis | Requires analysis; standardization **not required** (below rules for data analysis and extraction) |
| Trial ID | ClinicalTrials.gov  | Directly from clinical trial record |
| Trial Phase | ClinicalTrials.gov | Directly from clinical trial record; Use exact phrase as listed, example Phase 1, phase ½, Phase ¾, Phase 2/3, Phase 2, Phase 3, Phase 4, NA |
| Line of Therapy | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Biomarker (Mutations) | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Biomarker stratification | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Biomarker (Wildtype) | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Histology | Analysis | Requires analysis; standardization **not required** (below rules for data analysis and extraction) |
| Prior Treatment | Analysis | Requires analysis; standardization **not required** (below rules for data analysis and extraction) |
| Stage of Disease | Analysis | Requires analysis and standardization (below rules for data analysis and extraction) |
| Trial Status | ClinicalTrials.gov | Directly from clinical trial record |
| Patient Enrollment/Accrual | ClinicalTrials.gov | Directly from clinical trial record |
| Sponsor Type | Analysis | Based on the sponsor and collaborator information, classify the trial as "Industry Only," "Industry–Academic Collaboration," or "Academic Only. |
| Sponsor | ClinicalTrials.gov | Directly from clinical trial record, standardize the data (example *“Roche”*, *“F. Hoffmann-La Roche”*, *“Roche Pharma AG- to be tagged as “Roche)* |
| Collaborator | ClinicalTrials.gov | Directly from clinical trial record, standardize the data (example *“Roche”*, *“F. Hoffmann-La Roche”*, *“Roche Pharma AG- to be tagged as “Roche)* |
| Developer | Analysis | Based on the sponsor and collaborator information |
| Start Date (YY-MM-DD) | ClinicalTrials.gov | Directly from clinical trial record |
| Primary Completion Date (YY-MM-DD) | ClinicalTrials.gov | Directly from clinical trial record |
| Study completion date (YY-MM-DD) | ClinicalTrials.gov | Directly from clinical trial record |
| Primary Endpoints | ClinicalTrials.gov | Directly from clinical trial record |
| Secondary Endpoints | ClinicalTrials.gov | Directly from clinical trial record |
| Patient Population | Analysis | Requires analysis; standardization **not required** (below rules for data analysis and extraction) |
| Inclusion Criteria | ClinicalTrials.gov | Directly from clinical trial record |
| Exclusion Criteria | ClinicalTrials.gov | Directly from clinical trial record |
| Trial Countries | ClinicalTrials.gov | Directly from clinical trial record |
| Geography | Analysis | Requires standard grouping based on the trial countries |
| Investigators name | ClinicalTrials.gov | Directly from clinical trial record |
| Investigator designation | ClinicalTrials.gov | Directly from clinical trial record |
| Investigators qualification | ClinicalTrials.gov | Directly from clinical trial record |
| Investigator location | ClinicalTrials.gov | Directly from clinical trial record |
| History of changes  | ClinicalTrials.gov | Directly from clinical trial record; requires standardization  |

| Criteria for splitting | Conditions |
| ----- | ----- |
| Based on Combination Partners | Separate rows to be created for mono and combo regimens (Row 1- Mono; Row 2: with combination If there are multiple combination regimens evaluated in different arms, each arm to be profiled in a separate row with the respective combination partners of that particular arm |
| Based on LOT | Separation of rows based on previous treatments for same indication  Separate rows to be created for each Line of therapy within the same trial  In the same trial, If the patients evaluated are previously untreated/Newly diagnosed (1L); treated with no more than one therapy (2L); treated with at least one therapy/Exhausted all therapies/2 or more lines/multiple treatment lines (2L+) |
| Based on Patient Subgroup (subjective-specific to requirement) | If there are different sub indications of a broad therapy condition evaluated withing same trial, separate rows to be created for each sub indication cohort (for e.g if trial is a bladder cancer trial evaluating NMIBC and MIBC cohorts, separate row to be created for each cohort) |
| Based on ROA | If the same drug has been evaluated for different routes of administration, separate rows to be created for each route Row 1: IV; Row 2: Oral         |

**\*Note:**  when the rows are duplicated based on the above conditions; changes will apply to only those particular columns, whereas for the remaining columns, the information to be duplicated as the primary row (Except for patient population)

1. **Field: Primary Drug**  
* Trial source section: Brief Title, Brief Summary, Description, Official Title, Intervention  
* Objective: The primary investigational drug being tested in the clinical trial  
* Instructions for data analysis:   
* Identify the primary drug by analysing the trial's main objective and focus of the trial evaluation, as described in the **Brief Title**, **Brief Summary**, **Official Title**, **Description and Intervention section**.  
* *Secondary reference*: Cross-reference the sponsor’s drug pipeline or development focus to validate the primary agent   
* Exclude any drugs used as active comparators (e.g., chemotherapy listed as "vs chemo" or "Active Comparator: Chemo"). (*Example, Input 1*)  
* Do **not** consider background therapies or standard-of-care agents as primary unless they are part of a novel investigational combination.  
* In trials evaluating **novel combinations** of two investigational agents, consider **both drugs as primary**, and list them in **separate rows (2 different rows)**, each treated as a distinct entry   
* Standardize the primary drug (example *pembrolizumab and Keytruda-\> Tag as pembrolizumab; imatinib” vs. “imatinib mesylate-\> tag as imatinib*  
* Same drug can be listed as: Generic Name/ Brand Name; Code Name / Development Name; Different Salt Forms or Derivatives; Format Variations (case difference or hyphenation)  
* Use the generic drug name (e.g., “pembrolizumab”), regardless of brand name or code name mentioned; If generic name is not available use the Code Name

**Input 1**: 

* NCT06592326 (Title: **9MW2821** in Combination with Toripalimab vs Standard Chemotherapy in Locally Advanced or Metastatic Urothelial Cancer)  
* **Primary drug output:** 9MW2821 *(Justification: Toripalimab is a combination partner; standard chemo is a comparator)*

**Input 2:** 

* NCT06225596 (Title: Study **BT8009-230** in Participants with Locally Advanced or Metastatic Urothelial Cancer (Duravelo-2)  
* Primary drug output: BT8009-230 (*Justification:* *The drug is evaluated in mono arm and is primary focus. In the intervention, Pembrolizumab is the combination partner, and the trial is also sponsored by BicycleTx Limited (developer of* BT8009-230*))*

1. **Field: Mechanism of action (MoA) of primary drug**  
* Trial source section: Brief Title, Brief Summary, Detailed Description, Arms and Interventions.  
* Objective: Capture the mechanism of action (MoA) of the primary drug being tested in the trial.  
* Instructions for data analysis:  
  * Extract the MoA only for the primary drug, not for combination agents or active comparators. *(Example, Input 1)*  
  * *Secondary reference*: If the mechanism is not clearly stated within the trial record, Include from credible secondary sources, including (NCI drug dictionary([https://www.cancer.gov/publications/dictionaries/cancer-drug/](https://www.cancer.gov/publications/dictionaries/cancer-drug/)) *(Example, Input 2)*  
* Standardize the MoA (e.g., *“PD-1 inhibitor”* regardless of the specific drug name or formulation)   
* If no category can be inferred, tag as “Not Available**”** and retain any available description  
* Use consistent tags.  
  * For example:  
    * Same MoA can be listed as *“PARP inhibitor”, “PARPi”, “Poly (ADP-ribose) polymerase inhibitor”-\>* *Tag as: PARP inhibitor*  
    * “Nectin-4-directed ADC”, “Nectin-4 Inhibitor”, and “Anti-Nectin-4” should all be tagged as: Anti-Nectin-4  
    * Use the naming pattern: "Anti-\[Target\]", or "Anti-\[Target\] × \[Target\]" for bispecifics/trispecific


  **Examples for Reference:**

| Drug | Standardized MoA Tag |
| :---- | :---- |
| 9MW2821 | Anti-Nectin-4 |
| Balstilimab | Anti-PD-1 |
| HC010 | Anti-PD-1 × CTLA-4 × VEGF trispecific |
| NWY001 | Anti-PD-1 × CD40 bispecific |

    

    

| Term | Descriptions | Example Drug |
| :---- | :---- | :---- |
| Anti- | Used for antibodies (mAbs, ADCs) that bind to a specific target, usually on the cell surface. Monoclonal antibodies, ADCs, CART | Anti-HER2 (Trastuzumab) Anti-CD22 (TAC-001) Anti-CD19 CAR-T (Axicabtagene ciloleucel) |
| Inhibitor | Small molecules that block enzyme or receptor activity. Enzymes, kinases, intracellular targets | PARP Inhibitor (e.g., olaparib) EGFR inhibitor (e.g., osimertinib) CDK4/6 inhibitor (e.g., palbociclib) |
| Agonist | A molecule that activates a receptor/pathway (turns it on). | TLR9 agonist (e.g., TAC-001) CD28 agonist OX40 agonist  |
| Antagonist | A molecule that blocks a receptor, preventing it from being activated (turns it *off*). | CCR4 antagonist Estrogen receptor antagonist (e.g., fulvestrant)  |

    

  **Input 1:**

* NCT ID: NCT05827614  
* Brief Summary: **BBI-355** is an oral, potent, **selective checkpoint kinase 1 (or CHK1)** small molecule inhibitor in development as an ecDNA (extrachromosomal DNA) directed therapy (ecDTx). This is a first-in-human, open-label, 3-part, Phase 1/2 study to determine the safety profile and identify the maximum tolerated dose and recommended Phase 2 dose of BBI-355 administered as a single agent or in combination with select therapies   
* **MoA Output**: Anti-CHK1 (*Justification*: *BBI-355 is the primary drug and its mechanism given in the summary)* 


  

 **Input 2:**

* NCT ID: NCT03557918  
* Title: Trial of Tremelimumab in Patients With Previously Treated Metastatic Urothelial Cancer (*Tremelimumab is the primary drug)*  
* **MoA Output from *Secondary reference***: Anti- CTLA-4 ([https://www.cancer.gov/publications/dictionaries/cancer-terms/def/tremelimumab](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/tremelimumab))  
    
2. **Field: Target of Primary Drug**  
* Trial source section: Brief Title, Brief Summary, Detailed Description, Arms and Interventions Table  
* Objective: Capture the molecular or biological target of the primary drug being evaluated in the trial.  
* Instructions for data analysis:  
  * Identify the target only for the primary drug, excluding combination agents and active comparators. *(Example, Input 1)*  
  * Align the target with the corresponding mechanism of action (MoA) (e.g., MoA: Anti-Nectin-4 → Target: Nectin-4).  
  * Standardization- Use the target name only (e.g., Nectin-4, PD-1, c-MET). Do not include prefixes like "Anti-" or suffixes like "-inhibitor" in this field.  
* *Secondary reference* If not explicitly mentioned in the trial record, infer the target using secondary sources: ), NCI drug dictionary([https://www.cancer.gov/publications/dictionaries/cancer-drug/](https://www.cancer.gov/publications/dictionaries/cancer-drug/)) *(Example, Input 2)*


  **Input 1**

* NCT ID: NCT05827614  
* Brief Summary: **BBI-355** is an oral, potent, selective checkpoint kinase 1 (or **CHK1**) small molecule inhibitor in development as an ecDNA (extrachromosomal DNA) directed therapy (ecDTx). This is a first-in-human, open-label, 3-part, Phase 1/2 study to determine the safety profile and identify the maximum tolerated dose and recommended Phase 2 dose of BBI-355 administered as a single agent or in combination with select therapies.  
* **Target Output**: CHK1 (*Justification*: *BBI-355 is the primary drug and its mechanism given in the summary; Target is derived from MoA)* 


  **Input 2**

* NCT ID: NCT06592326  
* Title: 9MW2821 in Combination With Toripalimab vs Standard Chemotherapy in Locally Advanced or Metastatic Urothelial Cancer  
* **Target Output (from secondary):** Nectin-4  
    
    
3. **Field: Modality of primary drug**   
* Trial source section: Brief Title, Brief Summary, Detailed Description, Arms and Interventions Table  
* Objective: Identify the drug modality of the primary drug only being tested in the clinical trial. Do not consider the modality of combination drugs or active comparators.  
* Instructions for data analysis:  
  * Standardize terminology across trials. For example:  
    * “Antibody-drug conjugate” → ADC *(Example, Input 1)*  
    * “T-cell redirecting bispecific” → T-cell engager  
    * “Chimeric antigen receptor T cell” → CAR-T  
  * Tagging Rules:  
    * Drugs ending in \-mab → Monoclonal antibody  
    * Drugs ending in \-tinib → Small molecule  
    * Gene-altering/encoding drugs (e.g., VNX-203) → Gene therapy  
    * Radiolabeled ligands → Radiopharmaceutical  
    * Cell-based therapies (e.g., NK, T-cell) → Cell therapy  
  * *Secondary reference*: If the modality is not explicitly mentioned in the trial record, use trusted secondary sources, such as: sources (AACR journal ([https://aacrjournals.org/mct/article/22/8/913/727923/Preclinical-Evaluation-of-9MW2821-a-Site-Specific](https://aacrjournals.org/mct/article/22/8/913/727923/Preclinical-Evaluation-of-9MW2821-a-Site-Specific) ), NCI drug dictionary([https://www.cancer.gov/publications/dictionaries/cancer-drug/](https://www.cancer.gov/publications/dictionaries/cancer-drug/)) company website(example, [https://mabwell.com/en/rd.html](https://mabwell.com/en/rd.html))  *(Example, Input 2)*

    

  Some common examples.

| Drug | Modality |
| :---- | :---- |
| 9MW2821 | ADC |
| Aflibercept | Fusion protein |
| A2B694 | CAR-T |
| Acasunlimab | Monoclonal antibody |
| Adebelimumab | Monoclonal antibody |
| Allogenic NK cell therapy | Cell therapy |
| Belvarafenib | Small molecule |
| AdAPT-001 | Oncolytic virus |
| BA-3182 | T-cell Engager |


  
**Input 1**: 

* NCT07012031  
* Brief Summary:  **Trastuzumab deruxtecan** is in a class of medications called **antibody-drug conjugates**. It is composed of a monoclonal antibody, called trastuzumab, linked to a chemotherapy drug, called deruxtecan.  
* **Modality output**: ADC (Justification: *Trastuzumab deruxtecan is the primary drug and its modality given in the summary)*

**Input 2**: 

* NCT06592326   
* **Title**: 9MW2821 in Combination With Toripalimab vs Standard Chemotherapy in Locally Advanced or Metastatic Urothelial Cancer  
* **Modality from secondary**: ADC

4. **Field: Indication**  
* Trial source section: Title, official title, brief summary, detailed description, conditions, Inclusion criteria  
  * Objective: For each clinical trial (using its NCT ID), review the relevant sections of the record (Title, Official Title, Brief Summary, Detailed Description, Conditions, and Inclusion Criteria) to:  
  * Extract all disease indications studied in the clinical trial.  
* Classify the indications into:  
  * \[Indication 1\]: The primary disease of interest/scope (e.g., Bladder Cancer)  
  * \[Indication 2\]: All other disease indications studied in the trial if the scope of interest is Bladder Cancer (e.g., Advanced Solid Tumors, Cholangiocarcinoma, Biliary Tract Cancer, HER2-negative Breast Cancer, Triple Negative Breast Cancer, Small-cell Lung Cancer, Prostate Cancer, Thyroid Cancer, Gastric Cancer, Gallbladder Cancer) \-\>  Solid tumors \+ Bladder cancer  
* Instructions for Data Extraction and Grouping:  
  * Use exact or closely mapped disease names as described in the trial record  
  * Group and deduplicate disease names logically (e.g., “HER2-negative Breast Cancer” and “Triple Negative Breast Cancer” are distinct, not duplicates).  
  * If general terms like **“advanced solid tumors”** are listed, extract all specific disease names mentioned in the eligibility criteria or other relevant sections.  
  * Final Output should clearly list the primary indication and the grouped set of other indications


  **Input**: 


* NCT05253053 (*Justification: For a trial with focus indication \= Bladder Cancer, and listing other tumors*)  
* Conditions : Advanced Solid Tumor, Cholangiocarcinoma, Biliary Tract Cancer, HER2-negative Breast Cancer, Triple Negative Breast Cancer, Small-cell Lung Cancer, **Bladder Cancer**, Prostate Cancer, Thyroid Cancer, Gastric Cancer, Gallbladder Cancer  
* Inclusion Criteria:  
1. ≥ 18 years of age  
2. Arm A：Histopathological or cytologically documented locally advanced or metastatic and **solid tumors** (including but not limited to advanced cholangiocarcinoma, small cell lung cancer, HER2-negative breast cancer including TNBC, **bladder cancer**, prostate cancer, thyroid cancer, gastric cancer, gallbladder cancer and other advanced solid tumors.

   Arm B：Histopathological or cytologically documented locally advanced or metastatic and Unresectable advanced biliary tract malignant tumors (except ampullary carcinoma).

   Arm C：Histopathological invasive advanced TNBC with triple-negative receptor status that meets the institution standards was proved ER or PR by IHC (positive tumor nucleus\<10% ); HER2-negative (ASCO-CAP guideline \[Wolff A C, 2018\] )

**Output (for bladder landscape)**: \[Bladder Cancer\] \[Advanced Solid Tumor, Cholangiocarcinoma, Biliary Tract Cancer, HER2-negative Breast Cancer, Triple Negative Breast Cancer, Small-cell Lung Cancer, Prostate Cancer, Thyroid Cancer, Gastric Cancer, Gallbladder Cancer\] \-\> **Bladder Cancer \+ Solid tumors**  (*Justification: Arm A is evaluating the indication of interest, bladder cancer along with other solid tumours. Also, other arms evaluating other solid tumours*) 

5. **Field: ROA (Route of Administration) – Primary Drug**  
* Trial source section: Official title, brief summary, Detailed description, Arms and Interventions table  
* Objective: Identify the route of administration (ROA) of the primary drug being tested in the clinical trial. Do not extract or include the ROA of combination drugs, background therapies, or active comparators.  
* Instructions for data analysis:  
  * Output should be in a standardized format, e.g.:  
    * Intravenous (IV)   
    * Subcutaneous (SC)  
    * Oral  
    * Intratumoral  (IT)  
* Do not infer or assume ROA unless clearly stated in the trial or supported by secondary reference (e.g., sponsor website).  
* In case of multiple ROAs for the same primary drug, profile each separately in two rows (example Row 1as IV and Row 2 as SC)  
    
  **Input**: NCT06592326


| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: 9MW2821+Toripalimab 9MW2821+Toripalimab | Drug:** 9MW2821** 9MW2821, 1.25mg/kg, **intravenous (IV) infusion** Drug: Toripalimab Toripalimab, 240mg, intravenous (IV) infusion Other Names: Toripalimab injection |


   **ROA output**: intravenous (IV) (*Justification: Primary drug is 9MW2821 and ROA is intravenous***)**

6. **Field: Mono/ Combo**  
* Trial source section: Arms and intervention, brief title, official title, summary, detailed description  
* Objective: Classify interventions into "Mono" or "Combo" based on their evaluation context in clinical studies. Do not include active comparators or drugs used in the background without relevance to trial assessment as combo.

* Instructions for data analysis:  
  * **Mono**: If the intervention is being evaluated alone (not in combination with any other drug or without any additional therapy), tag it as **Mono**.  
  * **Combo:** If the drug is being evaluated **in combination** with one or more drugs, tag it as **Combo**.  
  * **Special Cases:**  
  * If both mono and combo drug treatment are evaluated within the same trial, profile each separately in two rows: one as **Mono** and one as **Combo** (example-input 2).  
  * If interventions are studied across multiple indication cohorts, consider only the **indication-specific cohort** (the indication of interest) for Mono-Combo classification (example input 3\) or consider all the indications cohort in separate based on the objective of the scope or indications   
  * If indication cohorts are **not specified and indication of interest mentioned only under conditions**, consider all combinations and classify accordingly (example input 4\)

    

**Input 1**: NCT06592326 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: **9MW2821+Toripalimab** 9MW2821+Toripalimab | Drug: 9MW2821 9MW2821, 1.25mg/kg, intravenous (IV) infusion Drug: Toripalimab Toripalimab, 240mg, intravenous (IV) infusion Other Names: Toripalimab injection |
| Active Comparator: Gemcitabine+Cisplatin/Carboplatin Gemcitabine+Cisplatin/Carboplatin   | Drug: Gemcitabine Gemcitabine: 1000mg/m2, intravenous (IV) infusion Other Names: Gemcitabine Hydrochloride for Injection Drug: Cisplatin/Carboplatin Cisplatin: 70mg/m2 or Carboplatin: AUC=4.5/5, intravenous (IV) infusion. Other Names: Cisplatin for injection/Carboplatin Injection |

**Expected output**: Combo *(Justification: Do **not** classify an active comparator as a combination therapy)*

**Input 2**: NCT05253053 (To Evaluate Efficacy and Safety of TT-00420 (Tinengotinib) as Monotherapy and Combination Therapy in Patients With Advanced Solid Tumors)

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Arm A: **TT-00420 Tablet Monotherapy** TT-00420 tablets will be administered once daily in 21-day cycles. Dose escalation will be guided by a 3+3 design in Phase Ib to determine the recommended phase 2 dose (RP2D). | Drug: TT-00420 TT-00420 tablet will be administered orally once daily per protocol defined schedule. |
| Experimental: Arm B: **TT-00420 tablet in combination with Atezolizumab** Injection (Tecentriq ®) TT-00420 tablets will be administered once daily in 21-day cycles. Atezolizumab(1200 mg/20 mL) will be administered intravenously on Day 1 of each 21-day cycle. Dose escalation will be guided by a 3+3 design in Phase Ib to determine the recommended phase 2 dose (RP2D). | Drug: TT-00420 TT-00420 tablet will be administered orally once daily per protocol defined schedule. Drug: Combination Product: Atezolizumab Atezolizumab would be administered via infusion on Day 1 of 21-day cycle |
| Experimental: Arm C: **TT-00420 tablet in combination with nab-paclitaxel (Abraxane®)** TT-00420 tablets will be administered once daily in 21-day cycles. Nab-paclitaxel 125 mg/m^2 will be administered intravenously on Day 1 and 8 of each 21-day cycle. Dose escalation will be guided by a 3+3 design in Phase Ib to determine the recommended phase 2 dose (RP2D). | Drug: TT-00420 TT-00420 tablet will be administered orally once daily per protocol defined schedule. Drug: Combination Product: Nab-Paclitaxel Nab-Paclitaxel would be administered via infusion on Day 1 and 8 of 21-day cycle |

**Expected output**: Row 1: Mono ( TT-00420); Row 2: combo ( T-00420 \+ Atezolizumab); Row 3 combo (T-00420 \+ Abraxane)  *(Justification: TT-00420 is evaluated in different arms with multiple combination regimens)* 

**Input 3**: NCT05489211 (Study of Dato-Dxd as Monotherapy and in Combination With Anti-cancer Agents in Patients With Advanced Solid Tumours (TROPION-PanTumor03)

**Interventional Model Description:**  
Within each substudy, Dato-DXd will be evaluated as monotherapy (all except \#2 Gastric Cancer) and in combination with approved or novel anticancer agents that may be active in the tumour type being evaluated (all except \#1 Endometrial Cancer and \#7 Biliary Tract Cancer). All substudies will be treatment assigned.  
Substudy 1 (Endometrial): MONO: Dato-DXd  
Substudy 2 (Gastric): COMBO: Dato-DXd \+ capecitabine, Dato-DXd \+ 5-FU  
Substudy 3 (mCRPC): MONO: Dato-DXd; COMBO: Dato-DXd \+ prednisone/prednisolone  
Substudy 4 (Ovarian): MONO: Dato-DXd; COMBO: Dato-DXd \+ carboplatin \+ bevacizumab \--\> Dato-DXd \+ bevacizumab  
Substudy 5 (CRC): MONO: Dato-DXd; COMBO: Dato-DXd \+ 5-FU \+ leucovorin \+ bevacizumab or Dato-DXd \+ capecitabine \+ bevacizumab  
**Substudy 6 (Urothelial): MONO: Dato-DXd; COMBO: Dato-DXd \+ volrustomig, Dato-DXd \+ rilvegostomig, Dato-DXd \+ carboplatin or cisplatin**  
Substudy 7 (BTC): MONO: Dato-DXd

**Expected output (bladder)**: **only substudy 6**\- Row 1: Mono ( Dato-DXd); Row 2: combo ( Dato-DXd \+ volrustomig); Row 3: combo (Dato-DXd \+ rilvegostomig); Row 4: combo (Dato-DXd \+ carboplatin or cisplatin) *(Justification: Dato-DXd is evaluated in multiple combination regimens for the indication of interest in a separate cohort; bladder cancer)* 

**Input 4**: NCT05827614 (Study of the CHK1 Inhibitor BBI-355, an EcDNA-directed Therapy (ecDTx), in Subjects with Tumors with Oncogene Amplifications (POTENTIATE**)**

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Single Agent Dose Escalation **Single agent BBI-355**, administered orally in 28-day cycles | Drug: BBI-355 Oral CHK1 inhibitor |
| Experimental: Single Agent Dose Expansion **Single agent BBI-355**, administered orally in 28-day cycles | Drug: BBI-355 Oral CHK1 inhibitor |
| Experimental: Dose Escalation in Combination with EGFR Inhibitor Combination therapy of **BBI-355 and EGFR inhibitor erlotinib**, administered orally in 28-day cycles. | Drug: BBI-355 Oral CHK1 inhibitor Drug: Erlotinib EGFR Inhibitor |
| Experimental: Dose Escalation in Combination with FGFR Inhibitor Combination therapy of **BBI-355 and FGFR1-4 inhibitor futibatinib**, administered orally in 28-day cycles. | Drug: BBI-355 Oral CHK1 inhibitor Drug: Futibatinib FGFR1-4 Inhibitor |

**Expected output**: \- Row 1: Mono ( BBI-355); Row 2: combo ( BBI-355 \+ erlotinib); Row 3: combo (BBI-355 \+ futibatinib) *(Justification: Dato-DXd is evaluated in multiple combination regimens)* 

7. **Field: Combination Partner**   
* Trial source section: Arms and intervention, title, brief summary, detailed description  
* Objective: Extract the combination partners that have been evaluated with the primary drug in each arm. DO not consider active comparators (eg those given as V/S chemo or Active comparator: chemo) as combination   
* Standardised format of primary drug is applicable here  
* Instructions for data analysis:  
* If combination therapy is being evaluated for an intervention  
* Tag the combination (Example: Input 1)  
  * If both monotherapy and combination therapy are being evaluated for an intervention:

* Profile them in two separate rows.  
* The combo-tagged row should document the combination partner.  
* The mono-tagged row should have "NA" in the combination partner field. (Example: Input 2)

* If interventions are targeted toward different indication cohorts:

  * Consider only the cohort relevant to the indication of interest for mono/combo analysis.  
  * Tag the combination partner for that specific cohort. (Example: Input 3)

* If no indication specific cohort is specified separately in arms and interventions but the indication of interest is just mentioned in “Conditions”

* Consider all combos for analysis.  
* Tag the combination partners for each row. (Example: Input 4)

* If there are multiple combination partners in a single arm:  
  * Separate all drugs using a plus sign ("+"). (Example: Input 5)

**Input 1**: NCT06592326 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: 9MW2821+Toripalimab 9MW2821\+**Toripalimab** | Drug: 9MW2821 9MW2821, 1.25mg/kg, intravenous (IV) infusion Drug: Toripalimab Toripalimab, 240mg, intravenous (IV) infusion Other Names: Toripalimab injection |
| Active Comparator: Gemcitabine+Cisplatin/Carboplatin Gemcitabine+Cisplatin/Carboplatin | Drug: Gemcitabine Gemcitabine: 1000mg/m2, intravenous (IV) infusion Other Names: Gemcitabine Hydrochloride for Injection Drug: Cisplatin/Carboplatin Cisplatin: 70mg/m2 or Carboplatin: AUC=4.5/5, intravenous (IV) infusion. Other Names: Cisplatin for injection/Carboplatin Injection |

**Expected output**: Toripalimab  *(Justification: 9MW2821 is the primary drug of evaluation; Gemcitabine+Cisplatin/Carboplatin and Gemcitabine+Cisplatin/Carboplatin are active comparators)*

**Input 2**: NCT05253053 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Arm A: **TT-00420 Tablet Monotherapy** TT-00420 tablets will be administered once daily in 21-day cycles. Dose escalation will be guided by a 3+3 design in Phase Ib to determine the recommended phase 2 dose (RP2D). | Drug: TT-00420 TT-00420 tablet will be administered orally once daily per protocol defined schedule. |
| Experimental: Arm B: TT-00420 tablet in **combination with Atezolizumab** Injection (Tecentriq ®) TT-00420 tablets will be administered once daily in 21-day cycles. Atezolizumab(1200 mg/20 mL) will be administered intravenously on Day 1 of each 21-day cycle. Dose escalation will be guided by a 3+3 design in Phase Ib to determine the recommended phase 2 dose (RP2D). | Drug: TT-00420 TT-00420 tablet will be administered orally once daily per protocol defined schedule. Drug: Combination Product: Atezolizumab Atezolizumab would be administered via infusion on Day 1 of 21-day cycle |
| Experimental: Arm C: TT-00420 tablet **in combination with nab-paclitaxel (Abraxane®)** TT-00420 tablets will be administered once daily in 21-day cycles. Nab-paclitaxel 125 mg/m^2 will be administered intravenously on Day 1 and 8 of each 21-day cycle. Dose escalation will be guided by a 3+3 design in Phase Ib to determine the recommended phase 2 dose (RP2D). | Drug: TT-00420 TT-00420 tablet will be administered orally once daily per protocol defined schedule. Drug: Combination Product: Nab-Paclitaxel Nab-Paclitaxel would be administered via infusion on Day 1 and 8 of 21-day cycle |

**Expected output**: NA (row1); Atezolizumab (row2); Nab-Paclitaxel (row 3\)   
(Justification: primary drug tested with 3 different combination partners separated in 3 different rows)

**Input 3**: NCT05489211 

**Interventional Model Description:**  
Within each substudy, Dato-DXd will be evaluated as monotherapy (all except \#2 Gastric Cancer) and in combination with approved or novel anticancer agents that may be active in the tumour type being evaluated (all except \#1 Endometrial Cancer and \#7 Biliary Tract Cancer). All substudies will be treatment assigned.  
Substudy 1 (Endometrial): MONO: Dato-DXd  
Substudy 2 (Gastric): COMBO: Dato-DXd \+ capecitabine, Dato-DXd \+ 5-FU  
Substudy 3 (mCRPC): MONO: Dato-DXd; COMBO: Dato-DXd \+ prednisone/prednisolone  
Substudy 4 (Ovarian): MONO: Dato-DXd; COMBO: Dato-DXd \+ carboplatin \+ bevacizumab \--\> Dato-DXd \+ bevacizumab  
Substudy 5 (CRC): MONO: Dato-DXd; COMBO: Dato-DXd \+ 5-FU \+ leucovorin \+ bevacizumab or Dato-DXd \+ capecitabine \+ bevacizumab  
**Substudy 6 (Urothelial): MONO: Dato-DXd; COMBO: Dato-DXd \+ volrustomig, Dato-DXd \+ rilvegostomig, Dato-DXd \+ carboplatin or cisplatin**  
Substudy 7 (BTC): MONO: Dato-DXd

**Expected output (bladder)**: **only substudy 6**\-NA (row1); volrustomig (row2); rilvegostomig (row 3); carboplatin or cisplatin (row 4\) (Justification: Only substudy 6 is bladder specific hence only 3 combos specific to indication of interest profiled in 3 rows)

**Input 4**: NCT05827614 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Single Agent Dose Escalation Single agent BBI-355, administered orally in 28-day cycles | Drug: BBI-355 Oral CHK1 inhibitor |
| Experimental: Single Agent Dose Expansion Single agent BBI-355, administered orally in 28-day cycles | Drug: BBI-355 Oral CHK1 inhibitor |
| Experimental: Dose Escalation in Combination with EGFR Inhibitor Combination therapy of BBI-355 and **EGFR inhibitor erlotinib**, administered orally in 28-day cycles. | Drug: BBI-355 Oral CHK1 inhibitor Drug: Erlotinib EGFR Inhibitor |
| Experimental: Dose Escalation in Combination with FGFR Inhibitor Combination therapy of BBI-355 and **FGFR1-4 inhibitor futibatinib**, administered orally in 28-day cycles. | Drug: BBI-355 Oral CHK1 inhibitor Drug: Futibatinib FGFR1-4 Inhibitor |

**Expected output**: NA (row1); Erlotinib (row2); Futibatinib (row3)

**Input 5**: NCT03964233 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Dose Escalation \- BI 907828 \+ ezabenlimab All neoplasms | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 |
| Experimental: Dose Expansion \- Cohort 1 BI 907828 \+ ezabenlimab | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 |
| Experimental: Dose Expansion \- Cohort 2 \- BI 907828 \+ ezabenlimab | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 |
| Experimental: Dose Escalation \- BI 907828 \+ ezabenlimab \+ BI 754111 All neoplasms | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 Drug: BI 754111 Solution for infusion |

**Expected output**: ezabenlimab (row1); ezabenlimab \+ BI 754111 (row2) (Justification: both the combinations with primary drugs are placed in 2 different rows)

8. **Field: MoA of Combination**  
   

Trial source section: Brief Title, Brief Summary, Detailed Description, Arms and Interventions Table  
Objective: Extract MOAs for all the combos where combination partners exist

* Instructions for data analysis:  
  * Extract the MoA only for combination agents, not for Primary drug or active comparators.  
  * Standadized format of primary drug MoA is applicable here  
  * Secondary reference If the mechanism is not clearly stated within the trial record, consult credible secondary sources, including: Drug mechanisms if not in trial to be captured by scanning secondary sources : NCI drug dictionary([https://www.cancer.gov/publications/dictionaries/cancer-terms/def/erlotinib-hydrochloride](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/erlotinib-hydrochloride) )  
  * Ensure standardization of MoA terminology across trials. Use consistent tags.  
  * For example:  
    * “Nectin-4-directed ADC”, “Nectin-4 Inhibitor”, and “Anti-Nectin-4” should all be tagged as: Anti-Nectin-4  
    * Use the naming pattern: "Anti-\[Target\]", or "Anti-\[Target\] × \[Target\]" for bispecifics/trispecifics.  
* In case of multiple combination partners in a single arm, the MoA of all drugs to be tagged separated by a plus sign 

**Input 1**: NCT05827614 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Single Agent Dose Escalation Single agent BBI-355, administered orally in 28-day cycles | Drug: BBI-355 Oral CHK1 inhibitor |
| Experimental: Single Agent Dose Expansion Single agent BBI-355, administered orally in 28-day cycles | Drug: BBI-355 Oral CHK1 inhibitor |
| Experimental: Dose Escalation in Combination with EGFR Inhibitor Combination therapy of BBI-355 and EGFR inhibitor erlotinib, administered orally in 28-day cycles. | Drug: BBI-355 Oral CHK1 inhibitor Drug: Erlotinib **EGFR Inhibitor** |
| Experimental: Dose Escalation in Combination with FGFR Inhibitor Combination therapy of BBI-355 and FGFR1-4 inhibitor futibatinib, administered orally in 28-day cycles. | Drug: BBI-355 Oral CHK1 inhibitor Drug: Futibatinib **FGFR1-4 Inhibitor** |

**Expected output**: NA (row1); Anti-EGFR (row2); Anti-FGFR1-4 (row3)  
(Justification: MOA of combination partners captured in correlation to combination drugs placed in different rows)

**Input 2**: NCT03964233 

| Participant Group/Arm  | Intervention/Treatment  |
| :---- | :---- |
| Experimental: Dose Escalation \- BI 907828 \+ ezabenlimab All neoplasms | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 |
| Experimental: Dose Expansion \- Cohort 1 BI 907828 \+ ezabenlimab | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 |
| Experimental: Dose Expansion \- Cohort 2 \- BI 907828 \+ ezabenlimab | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 |
| Experimental: Dose Escalation \- BI 907828 \+ ezabenlimab \+ BI 754111 All neoplasms | Drug: BI 907828 Film-coated tablets Other Names: Brigimadlin Drug: ezabenlimab Solution for infusion Other Names: BI 754091 Drug: BI 754111 Solution for infusion |

**Expected output (from secondary MOA search)**: Anti-PD-1 (row1); Anti-PD-1 \+ Anti-LAG-3 (row2)  
(Justification: MOA of combination partners captured in correlation to combination drugs placed in different rows based on secondary search)

9. **Field: Experimental regimen**  
* Objective: Capture experimental regimen in each row as names of Primary drug \+ combination partners  
* Instructions for data analysis:  
  * Experimental regimen for mono tagged entries will be the name of primary drug  
  * Experimental regimen for combo tagged entries will be the names of primary drug \+ combination partners

**Input 1**: NCT05827614   
**Expected output**: BBI-355 (row1); BBI-355 \+ Erlotinib (row2); BBI-355 \+ Futibatinib(row3) (Justification: Primary drug \+ Combination partner)

**Input 2**: NCT03964233   
**Expected output**: BI 907828 \+ ezabenlimab (row1); BI 907828 \+ ezabenlimab \+ BI 754111 (row2) (Justification: Primary drug \+ Combination partner)

10. **Field: MOA for experimental regimen**  
* Objective: Capture experimental regimen in each row as names of Primary drug \+ combination partners   
* Instructions for data analysis:  
  * Experimental regimen for mono tagged entries will be the name of primary drug  
  * Experimental regimen for combo tagged entries will be the names of primary drug \+ combination partners

**Input 1**: NCT05827614   
**Expected output**: CHK1 Inh(row1); CHK1 Inh+ Anti-EGFR (row2); CHK1 Inh+ Anti-FGFR 1-4 (row3)  
(Justification: MOA of Primary drug \+ MOA of Combination partner)

**11\. Field: Trial Name**

* Trial source section: trial title, official title, or other “Other Study ID Numbers”  
* Objective: Capture the trial acronym  
* Instructions for data analysis:  
* Capture only the names from Other Study ID Numbers and NOT the study codes

**Input:** NCT05243550   
Title: A Phase 3 Single-Arm Study of UGN-102 for Treatment of Low-Grade Intermediate-Risk Non-Muscle Invasive Bladder Cancer (**ENVISION**)  
**Expected Trial Name Output**: ENVISION (Justification: Trial acronym from the title)

**12\. Field: Line of treatment**

Trial source section**:** Brief summary, study description, official title, inclusion Criteria, study title

**Objective:** Identify and tag the Line of Treatment (LOT) at which the investigational drug is being evaluated in a clinical trial.

Instruction for data analysis:

* Create additional rows if the drugs are tested in the multiple LOT’s   
* Rules to map line of treatment follows  
  * 1L: Treatment-naive or previously untreated patients or Newly diagnosed  
  * 2L: Patients treated with no more than 1 prior therapy.  
  * 2L+: Patients treated with ≥1 prior therapy, or who have no standard of care (SOC) options left, or are refractory/intolerant to SOC; No available standard of care therapy or participant is ineligible for standard of care therapy; who have exhausted all standard therapy available or are intolerant of the same; Resistant/refractory to or intolerant of existing standard therapies known to provide clinical benefit  
  * Adjuvant: Treatment given **after the primary therapy** (typically surgery) ;(Other terms for adjuvant include post-operative therapy, post-surgical therapy, Consolidation therapy)  
  * Neoadjuvant: Treatment given **before the primary therapy**  
    (Other terms for neoadjuvant include preoperative, pre-surgical therapy)  
  * Adjuvant/Neoadjuvant: in and around the surgery (pre and post)  
  * Maintenance: Ongoing treatment given **after initial successful therapy**   
  * 1L-Maintenance: If given after 1st\-line treatment  
  * 2L-Maintenance: If given after completing 2nd line treatment  
* Standardized format to follow is 1L, 2L, 2L+, adjuvant, neoadjuvant, maintenance   
* If the trial is specific to adjuvant, neoadjuvant and maintenance then same terms have to be tagged in LOT  
*  Look for the keywords to identify the line of treatment which is not limited to "patients must have received at least X prior lines of therapy", "second-line treatment", “Adjuvant”, “Neoadjuvant”, “Maintenance”, “Relapse or refractory”, “≥2 prior lines”

**Input 1:** NCT02451423 (Title: **Neoadjuvant** Atezolizumab in Localized Bladder Cancer)

**LOT output expected:** Neoadjuvant (justification: Neoadjuvant therapy as denoted by title itself)

**Input 2:** NCT06592326 

**Inclusion criteria:** 

**Previously untreated with local advanced or metastatic urothelial cancer**

**LOT output expected:** 1L (Justification: Previously untreated as per definition is 1L)

Input 3: NCT05239624 (Enfortumab Vedotin and Pembrolizumab in People with Bladder Cancer)

Official title: Enfortumab Vedotin in Combination with Pembrolizumab for Locally Advanced And/or Node Positive Urothelial Carcinoma Prior to Surgery (EV-ECLIPSE)

**Inclusion criteria:**

* Deemed medically appropriate for radical cystectomy with treatment response achieved, as per MSK or participating site Attending Urologic Oncologist

* Platinum eligible and ineligible patients are permitted on study

* No prior treatments for muscle invasive or metastatic urothelial carcinoma

LOT output expected: Neoadjuvant (Justification: treatment given prior to surgery and has not received any treatment before)

**Input 4**: NCT03697850 (Official title: Phase II Study of Maintenance Anti-PD-L1 Treatment With Atezolizumab After Chemo-radiotherapy for Muscle-infiltrating Bladder Cancer Patients Not Eligible for Radical Cystectomy: Bladder Sparing)

LOT output expected: 1L-Maintenance (Justification: Maintenance after first line treatment)

**13\. Field: Biomarkers**

Trial source section: Official title, brief summary, Study description, Inclusion criteria, outcome measures

**Objective:** Extract all biomarkers mentioned in each clinical trial

Instruction for data analysis:

* Identify the biomarkers mentioned in the clinical trial  
* Look for the keywords to identify the biomarkers which is not limited to mutation, amplification, expression, fusion, biomarkers, actionable molecular alteration, Gene deletion, Expressing (XXX) antigen, Gene/Target positive (E.g. HER2-positive, FAP-positive, PD-L1-positive), Inclusion allele  
* Do Not consider the biomarkers mentioned in the Background or exclusion criteria  
* Most common Biomarkers include (HER2, PD-L1, EGFR, HLA-A\*02:0, PIK3Ca, TROP2, HER2, MAGE-A4, MSI-H/dMMR, ALK, ROS1, BRAF, RET, MET, KRAS, dMMR/MSI, Nectin-4, TP53, 5T4, MTAP, CD39, CD103, CD8+, B&-H3)  
* Standardized format   
  * HER2 ➔ HER2 (no alternatives like “ErbB2”)  
  * PD-L1 ➔ PD-L1 (instead of “PDL1” or “PD L1”)  
  * EGFR ➔ EGFR (instead of “Epidermal Growth Factor Receptor”)  
  * Maintain consistency with symbols, punctuation, and numbering: e.g., HLA-A\*02:01 ➔ HLA-A\*02:01 (retain asterisk and colon)  
  * Group synonymous or highly related variations into one standardized term:e.g., dMMR and MSI-H ➔ Maintain both as dMMR/MSI-H if referring to the same context  
  * When unclear or unavailable: Tag as **“**Not Available” and retain any available description.


**Input 1:** NCT06319820

Official title: A Phase 3, Randomized Study Evaluating the Efficacy and Safety of TAR-210 Erdafitinib Intravesical Delivery System Versus Single Agent Intravesical Chemotherapy in Participants With Intermediate-risk Non-muscle Invasive Bladder Cancer (IR-NMIBC) and Susceptible **FGFR Alterations** 

**Biomarker output expected:** FGFR (Justification: patients with FGFR mutations as specified in title)

**Input 2:** NCT05203913

| Outcome Measure | Measure Description | Time Frame |
| :---- | :---- | :---- |
| Median Disease Free Survival by **PD-L1 expression.** | Patients with or without PD-L1 expression evaluated by Combined Positive Score (CPS) will be compared in terms of median disease free survival. Patients with CPS ≥ 10 will considered positive, the others negative. | From the start of therapy up to 5 years. |
| Median Disease Free Survival by **PI3KCA mutations** | Patients with or without PI3KCA mutation will be compared in terms of median disease free survival. | From the start of therapy up to 5 years. |

**Biomarker output expected:** PI3KCA, PD-L1 (Justification: patients with PI3KCA mutations and PD-L1 expression comparisons as mentioned in outcome measures)

Input 3: NCT03132922 (Official title: Phase 1 Dose Escalation, Multi-tumor Study to Assess the Safety, Tolerability and Antitumor Activity of Genetically Engineered MAGE-A4ᶜ¹º³²T in HLA-A2+ Subjects With MAGE-A4 Positive Tumors)

Inclusion criteria: 

1. Subject is HLA-A\*02 positive. (This determination will be made under screening protocol ADP-0000-001).

2. Subject's tumor shows expression of the MAGE-A4 RNA or protein. (This determination will be made under screening protocol ADP-0000-001).

**Biomarker output expected:** HLA-A\*02, MAGE-A4 (Justification: HLA-A\*02 positive, MAGE-A4 expression patients included in the inclusion criteria)

**14\. Field: Biomarker Stratification**

Trial source section: Study description, Inclusion criteria

**Objective:** Extract all biomarkers stratification numbers, expression levels  mentioned in each clinical trial

Instructions for data analysis:

* Identify the biomarkers expression levels mentioned in the inclusion criteria  
* Capture the levels as mentioned in the trial (commonly given as CPS-Combined positive score or immunohistochemistry (IHC) test scores 0, 1+, 2+, and 3+ or TPS (Tumor Proportion Score))  
* Eg include PD-L1 CPS ≥ 10; HER-2 expression (including IHC3+, IHC2+/FISH+ and IHC2+/FISH-)

**Input 1**: NCT05940896 (Title: RC48-ADC Combined With Radiotherapy in the Treatment of Locally Advanced Solid Tumors With HER2 Expression)

**Inclusion criteria:** 

HER2 expression is confirmed by the site: IHC 1+, 2+ or 3+

**Expected stratification output**: IHC 1+, 2+or 3+ (Justification:The expression levels for HER biomarker as given in inclusion criteria include IHC 1+, 2+or 3+)

**Input 2**: NCT02256436 (Title: A Study of Pembrolizumab (MK-3475) Versus Paclitaxel, Docetaxel, or Vinflunine for Participants With Advanced Urothelial Cancer (MK-3475-045/​KEYNOTE-045)

**Detailed Description**

For the purposes of this study, participants with a programmed cell death-ligand 1 (PD-L1) combined positive score (CPS) ≥10% were considered to have a strongly PD-L1 positive tumor status and participants with PD-L1 CPS ≥1% were considered to have a PD-L1 positive tumor status.

**Expected stratification output**: CPS ≥1% or CPS ≥10% (Justification: The expression levels for PD-L1 biomarker as given in the trial description as PD-L1 positive score)

**14\. Field:** Biomarkers wildtype

Trial source section: Official title, brief summary, Study description, Inclusion criteria, outcome measures

**Objective:** Extract all wild type biomarkers mentioned in each clinical trial

Instruction for data analysis:

* Extract the wildtype biomarkers mentioned in the clinical trial (brief summary, official title, and Inclusion Criteria, outcome measures)  
* Look for the keywords to identify the wildtype biomarkers which is not limited to “Wild type” *(e.g., KRAS wild-type, BRAF wild-type)*; “non mutated”; “Mutation-negative”, **Negative for \[specific mutation\]**  
  *(e.g., EGFR T790M-negative); “Genomically unaltered”; “**Lacking \[specific mutation\]** (e.g., lacking BRAF V600E mutation)”; **\[Gene\] negative by NGS/IHC/FISH/PCR** (e.g., ALK-negative by FISH), “WT” mutation, Biomarker-negative*  
* **Standardized Format:** Always use the **gene name** followed by the status, e.g.: KRAS wild-type, EGFR T790M-negative, BRAF V600E-negative, ALK-negative Biomarker-negative (if generic)

| Status  | Standardized Format |
| :---- | :---- |
| KRAS wild-type / KRAS WT / WT KRAS | KRAS wild-type |
| KRAS G12C-negative / Non-mutated KRAS | KRAS G12C-negative |
| EGFR T790M-negative / Negative for EGFR T790M | EGFR T790M-negative |
| EGFR exon 19/21 wild-type | EGFR exon 19/21 wild-type |
| BRAF V600E-negative / Lacking BRAF V600E | BRAF V600E-negative |
| ALK-negative by FISH / ALK not detected | ALK-negative |
| ROS1-negative / No ROS1 alteration | ROS1-negative |
| MET wild-type / MET unaltered | MET wild-type |
| PD-L1 low/negative | PD-L1-negative |
| Not mutated / No genomic alterations (general) | Biomarker-negative |

**Input 1:** NCT05512377 

**Official title:** Brightline-2: A Phase IIa/IIb, Open-label, Single-arm, Multi-centre Trial of BI 907828 (Brigimadlin) for Treatment of Patients With Locally Advanced / Metastatic, MDM2 Amplified, **TP53 Wild-type** Biliary Tract Adenocarcinoma, Pancreatic Ductal Adenocarcinoma, or Other Selected Solid Tumours

**Wildtype biomarker output expected:** TP53 (Justification: wild type TP53 biomarker mentioned in title itself)

Input 2: NCT05827614 (Title: Study of the CHK1 Inhibitor BBI-355, an ecDNA-directed Therapy (ecDTx), in Subjects With Tumors With Oncogene Amplifications (POTENTIATE)**)**

Inclusion criteria:

* Single agent arm: Evidence of oncogene amplification,

* BBI-355 combination with erlotinib arm: Evidence of amplification of wildtype EGFR,

* BBI-355 combination with futibatinib arm: Evidence of amplification of wildtype FGFR1, FGFR2, FGFR3, or FGFR4,

Expected biomarker wild type output: EGFR (Row 2), FGFR1, FGFR2, FGFR3, or FGFR4 (Row 3\) (Justification: specific wild type mutations for each combination arm separately mentioned in the inclusion criteria)

**15\.  Field: Histology**

Trial source section**:** Official Title, Brief Summary, Study Description and Inclusion Criteria, intervention 

**Objective:** Determine and extract the disease histology described in a clinical trial

Instruction for data analysis:

* Look for the keywords to identify the histology which is not limited to carcinomas, adenocarcinoma, squamous cell carcinoma, urothelial carcinoma, basal cell carcinoma, Mixed histology types  
* Histology should be co-related with disease if the exact histology is not given in the trial

**Input 1:** NCT05203913

**Inclusion criteria:**  18 years old or older

Histologic diagnosis of predominantly **urothelial carcinoma of the bladder**. Focal differentiation allowed other than small cell histology.

Stage T2-T3 N0M0 (AJCC-TNM version 6\) based on trans-urethral resection of bladder tumor (TURBT), CT or MRI imaging, \+/- bimanual examination under anaesthesia.

**Histology output expected:** Urothelial carcinoma (justification: histology type of the indication of interest mentioned in inclusion criteria)

**16\.  Field: Prior Treatment**

Trial source section**:** Inclusion criteria, Brief Summary, Study Description, Official Title  
**Objective:** Identify and list all therapies that participants must have received prior to enrolling in the clinical trial.

Instruction for data analysis:

* If specific prior therapies are mentioned, list them explicitly.  
* If the trial clearly states that participants have not received any prior therapy tag as treatment naive  
* Mention “NA” if no information is available regarding prior treatment.  
* Look for the keywords to identify the prior treatment which is not limited to “Previously failed”, “Progressed on”, “refractory to”, “previously treated”, “prior treatment” 

**Input 1:** NCT03871036 

**Brief summary**: This trial will include metastatic urothelial carcinoma patients who **progressed during or after treatment with anti-PD(L)1 therapy and have been treated by a platinum-containing regimen** or are cisplatin-ineligible. 

**Prior treatment output expected:** Anti-PD-L1 or Platinum based chemotherapy (Justification: prior therapy progression information given in brief summary)

**Input 2:** NCT04165317 (A Study of Sasanlimab in People With Non-muscle Invasive Bladder Cancer (CREST))

**Inclusion criteria:** (Cohorts B1 and B2 only): Histological confirmed diagnosis of **BCG-unresponsive high-risk**, non-muscle invasive TCC of the urothelium within 12 months (CIS only) or 6 months (recurrent Ta/T1 disease) of completion of adequate BCG therapy.

**Prior treatment output expected:** BCG (Justification: prior therapy progression information given in Inclusion criteria)

**17\.  Field: Stage**

Trial source section: Official Title, Brief Summary, Detailed Description, Eligibility Criteria  
**Objective:** Identify and tag the stage of disease being studied in each clinical trial using textual cues from the trial record.

Instruction for data analysis:

* Tag as Stage 4 if the trial mentions "metastatic" or "advanced cancer."  
* Tag as Stage 3/Stage 4 if the trial mentions "locally advanced" or "locally advanced/metastatic."  
* Tag as Stage 1/2 if the trial refers to early-stage disease.  
* If the trial stage is not evident from the trial, any elaborative information on tumour TNM staging such as (\[MIBC\] (cT2-T4aN0M0 or T1-T4aN1M0) can be captured

**Input 1:** NCT05911295 

**Official title:** An Open-label, Randomized, Controlled Phase 3 Study of Disitamab Vedotin in Combination With Pembrolizumab Versus Chemotherapy in Subjects With Previously Untreated **Locally Advanced or Metastatic Urothelial Carcinoma** That Expresses HER2 (IHC 1+ and Greater)

**Stage output expected:** Stage 3/4 (Justification: As per defined definitions above)

**Input 2**: NCT04486781

**Brief summary:**  sEphB-HSA may prevent tumor cells from multiplying and blocks several compounds that promote the growth of blood vessels that bring nutrients to the tumor. The purpose of this study is to evaluate the combination of Pembrolizumab \+ sEphB4-HSA in the population of patients with previously untreated **advanced (metastatic or recurrent) urothelial carcinoma** who are chemotherapy ineligible or who refuse chemotherapy.

**Stage output expected:** Stage 4 (Justification: As per defined definitions above)

**18\. Field: Sponsor type**

* Trial source section: Collaborators and Investigators  
  * Objective: Classify the type of collaboration based on analysis of sponsors and collaborators  
  * Instruction for data analysis:  
* If the sponsor is a pharmaceutical company or if the sponsor and collaborator both are pharmaceutical companies, the sponsor type is ‘Industry’  
* If the sponsor is an academic institution, university, non-profit organisation, or other centers, and the collaborator is also similar the sponsor type is ‘Academic’  
* If either of the sponsor or collaborator either of them is a pharma company and the other is an academic institution, university, non-profit organisation, or other centers, then the sponsor type is ‘Industry-Academic collaboration.

**Input**: NCT06279130   
Sponsor:  The Netherlands Cancer Institute  
Collaborators: Agenus Inc.  
**Expected output**: Industry \- Academic collaboration (justification: Sponsor is academic institute, and collaborator is a pharma company, hence sponsor type will be Industry \- Academic collaboration) 

**19\. Field: Developer**

Trial source section**:** Sponsor and collaborator

Objective: Capture the developer of the primary drug being tested in each clinical trial

Instructions for data analysis

* The trial sponsor or collaborator is the developer of the primary drug in the majority of the cases (Only Pharma companies to be captured; no universities, non-profit organisations, Hospitals to be listed).   
    
  Secondary search requirements  
* If the company is not tagged in the trial, a brief secondary to be done to identify the primary developer of the molecule, searching for company websites and pipeline  
* If the primary drug was developed by another company that has now been acquired, the company that acquired the entity is to be listed (not the original developer)  
  \*Note: The Trial might still mention the old primary developer’s name in the sponsor (e.g., sponsor might be Mirati Therapeutics in the trial, but the Developer should be tagged as BMS because the entity is acquired by BMS)  
    
  List of some common acquisitions

| Original company | Acquired by |
| :---- | :---- |
| Seagen | Pfizer |
| Mirati Therapeutics, BioNTech SE | BMS |
| Fusion Pharma | AstraZeneca |

**Input 1:** NCT03682068 (Title: Study of Durvalumab Given with Chemotherapy, Durvalumab in Combination with Tremelimumab Given with Chemotherapy, or Chemotherapy in Patients with Unresectable Urothelial Cancer (NILE))

Sponsor: AstraZeneca

**Developer output expected:** AstraZeneca (Justification: The trial is sponsored by AstraZeneca; Durvalumab and Tremelimumab are molecules from the AstraZeneca pipeline)

**Input 2:** NCT03289962 (Title: A Study of Autogene Cevumeran (RO7198457) as a Single Agent and in combination With Atezolizumab in Participants with Locally Advanced or Metastatic Tumors)  
Sponsor & Collaborator: Genentech, Inc. & BioNTech SE

**Developer output expected:** Roche/BMS (Justification: Genentech is the sponsor and BioNTech SE is the collaborator; however, both are acquired companies, i.e, Genentech by Roche and BioNTech by BMS)

**20\. Field: Patient Population**

* Trial source section**:** brief summary, official title, and inclusion criteria  
* Objective: Extract Patient population being evaluated from the trial.   
* Instructions for data analysis  
* Patient population captured considering disease stage, type of disease, mutations, if any, and the number of prior therapies experienced  
* Patient population to be tagged for each arm; specific to that particular cohort (eg input 1)

**Input 1**: NCT05614739 

Inclusion Criteria:

* Have solid tumor cancer with an FGFR3 pathway alteration on molecular testing in tumor or blood sample that is deemed as actionable  
  * Cohort A1: Presence of an alteration in FGFR3 or its ligands  
  * Cohort A2, B2, B3, and B5: Histological diagnosis of urothelial cancer (UC) that is locally advanced or metastatic with a qualifying FGFR3 genetic alteration  
  * Cohorts B1 and B4: Histological diagnosis of urothelial cancer that is locally advanced or metastatic  
  * Cohort C1: Must have histological diagnosis of a non-urothelial solid tumor malignancy that is locally advanced or metastatic with a qualifying FGFR3 genetic alteration  
* Prior Systemic Therapy Criteria:  
  * Cohort A1/C1: Participant has received all standard therapies for which the participant was deemed to be an appropriate candidate by the treating Investigator; OR the participant is refusing the remaining most appropriate standard of care treatment; OR there is no standard therapy available for the disease. There is no restriction on number of prior therapies.  
  * Cohort A2, B2, B3 participants must have received at least one prior regimen, and cohorts B1 and B4 participants at least 2 prior regimens, in the locally advanced or metastatic setting  
  * There is no restriction on number of prior therapies  
* Cohort B5: Participants have not received prior systemic therapy for locally advanced or metastatic UC  
* FGFR inhibitor specific requirements:  
  * Cohort A1/A2/B3: Prior FGFR inhibitor treatment is permitted but not required  
  * Cohort B1/B4: Participants must have been previously treated with erdafitinib  
  * Cohort B2, B5, and C1: Participants must be FGFR inhibitor naïve  
  * 

**Expected output** (Justification: patient population for each cohort tagged in separate rows based on its genetic alteration and prior treatment)

* **cohort A1/A2/B1/B2/B4/C1: mono (ROW 1\)**\- Locally advanced or metastatic cancer with FGFR3 genetic alteration who have received at least one prior therapy, or 2 prior therapies, or exhausted all standard therapies.   
* **B3: combo pembrolizumab (Row 2):** Locally advanced or metastatic cancer with FGFR3 genetic alteration who have received at least one prior therapy  
* **B5: combo Enfortumab Vedotin (Row 3):** Locally advanced or metastatic cancer with FGFR3 genetic alteration who have not received prior systemic therapy

**Input 2**: NCT06592326 

Inclusion Criteria:

* Sign the informed consent form approved by IEC.  
* Male or female subjects aged 18 to 80 years.  
* ECOG status: 0 or 1\.  
* Histologically confirmed local advanced or metastatic urothelial cancer  
* Previously untreated with local advanced or metastatic urothelial cancer  
* At least one measurable lesion, according to RECIST V1.1.  
* Adequate tumor tissues submitted for test  
* Suitable for cisplatin/carboplatin-based chemotherapy assessed by investigator  
* Life expectancy for more than 12 weeks.  
* Adequate organ functions.  
* Proper contraception methods.  
* Willingness to follow the study procedures.

**Expected output**: Previously untreated local advanced or metastatic urothelial cancer suitable for cisplatin/carboplatin-based chemotherapy (Justification: Patient population specified from inclusion criteria considering type of cancer and previous treatment)

**21\. Field: Geography**

Trial source section**:** Contacts and Locations

**Objective**: Identify the **trial geography** for each clinical trial using data from the **"Contacts and Locations"** section of the trial record.

Instructions for data analysis

* Extract all trial site countries listed under the "Locations" section of each trial  
* Determine the trial geography using the following classification rules  
  * Tag the trial as Global if it includes all 4 locations (United States, at least one EU country, Japan and China)  
  * Tag the trial as international if the trial location contains Europe with/without JP, China and other countries  
  * Tag the trial as China only, if the trial location includes only China or China and Taiwan location

**Input 1:** NCT04736394 

* **Location Countries: China**

**Geography output expected**: China only (Justification: Only China specific trial)

 **Input 2:** NCT03682068 

* **Location countries:** Argentina, Australia, Brazil, Bulgaria, Canada, China, Czechia, Hungary, India, Israel, Italy, Japan, Korea, Republic of, Philippines, Poland, Russian Federation, Spain, Taiwan, Thailand, Turkey, United States, Vietnam

**Geography output expected**: Global (All 4 regions US, EU, JP, CH present)

**21\. Investigators and co-investigator (Names and Address)**

Trial source**:** “**Collaborators and Investigators section”**

Objective: Capture the information of investigators and co-investigators (Designation, Name, address, and other details present)

Instructions for data analysis:

* Extract the information of all the investigators along with the details mentioned above from the “**Collaborators and Investigators section”**

**Input**: NCT03799835 (Title: Atezolizumab Plus One-year BCG Bladder Instillation in BCG-naive High-risk Non-muscle Invasive Bladder Cancer Patients (ALBAN))

Collaborators and Investigators:

This is where you will find people and organizations involved with this study.

Investigators 

* Principal Investigator:Morgan Roupret, MD-PHD, Hôpital Pitié-Salpétrière

* **Expected Output:** (Justification: All details of investigators or co-investigators captured as is from the investigators section)  
  * Investigator name: Morgan Roupret  
    Investigator designation: Principal Investigator  
  * Investigator qualification: MD-PHD  
  * Investigator Location: Hôpital Pitié-Salpétrière

**History of changes** 

* Trial source section  
* Changes made pre- vs. post-first patient enrolment  
* Change in patient population  
* Change in primary drug or combination   
* **Protocol Changes**  
  * Primary and secondary outcome measure modifications.  
  * Changes in inclusion/exclusion criteria.  
  * Intervention changes (e.g., dosage, arms, timeframe added/removed).  
* Recruitment and Location Updates   
  * Changes in recruitment status (e.g., from “Not Yet Recruiting” to “Active”).  
  * Start/primary completion date/study completion date extensions or early closure  
  * Site location additions or removals.  
* Sponsorship and Role Changes  
  * New collaborators, funders, or PIs added.  
  * Change in sponsor type (industry to academic, or vice versa).

