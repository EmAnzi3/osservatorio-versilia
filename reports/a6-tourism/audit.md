# A6 — audit completo del motore

Catalogo SHA-256 `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `1acf3715892248811f70861147e98c1da7e03fe8b00047ad4b279e16c19b6cad`.

225 indicatori censiti; 175 con adapter e 50 senza adapter. 63 profili fonte.

La presenza di dati A3 ACQUIRED non certifica interrogabilità. Ogni prova conserva la query esatta nel JSON. Le correlazioni richiedono una coppia scelta e motivata.

Una prova può essere rifiutata anche con adapter presente: per esempio un trend con soli due punti non soddisfa il minimo di osservazioni. I conteggi sono derivati e vanno letti insieme alle query.

| Indicatore | Tema | Profilo fonte | Periodo | Adapter / motivo | Dimensioni abilitate | Prove calcolate / rifiutate | Dimensioni A3 acquisite |
|---|---|---|---|---|---|---|---|
| accreditedRsaCount | salute | regione-toscana-rsa | 2025 | adapter_not_implemented | — | 0 / 0 | 1 |
| activeTplAccessPoints | mobilita | regione-toscana-gtfs-scheduled | 26 agosto 2026 | adapter_not_implemented | — | 0 / 0 | 1 |
| activityRate | lavoro | istat-census-annual | 2024 | istat-census-carriers/activityRate/v1 | total, age:15-24\|sex:total, age:15-24\|sex:men, age:15-24\|sex:women, age:25-49\|sex:total, age:25-49\|sex:men, age:25-49\|sex:women, age:50-64\|sex:total, age:50-64\|sex:men, age:50-64\|sex:women, age:65plus\|sex:total, age:65plus\|sex:men, age:65plus\|sex:women, age:25-64\|sex:total, age:25-64\|sex:men, age:25-64\|sex:women, age:15plus\|sex:total, age:15plus\|sex:men, age:15plus\|sex:women | 64 / 90 | 8 |
| ageDistribution | demografia | istat-demography-annual | 2026 | istat-posas-age-band/v1 | age:0-14, age:15-19, age:20-34, age:35-49, age:50-64, age:65-79, age:80-84, age:85+ | 48 / 0 | 7 |
| agriculturalDiversificationAndModernization | ambiente | istat-agriculture-census-2020 | 2020 | agriculture-profiles/agriculturalDiversificationAndModernization/connectedActivities/v1 | total, part:connectedActivities, part:informatization, part:innovation | 12 / 0 | 3 |
| agriculturalFarms | ambiente | istat-agriculture-census-2020 | 2020 | agriculture/agriculturalFarms/v1 | total | 3 / 0 | 2 |
| agriculturalRenewalAndLeadership | ambiente | istat-agriculture-census-2020 | 2020 | agriculture-profiles/agriculturalRenewalAndLeadership/youngManagers/v1 | total, part:youngManagers, part:femaleHolders | 9 / 0 | 3 |
| agriculturalUsedArea | ambiente | istat-agriculture-census-2020 | 2020 | agriculture/agriculturalUsedArea/v1 | total, view:normalized | 7 / 0 | 4 |
| altitudeProfile | ambiente | istat-geografia-comunale-2021 | 31 dicembre 2021 | geography/altitudeProfile/v1 | total, part:0_299, part:300_599, part:600_899, part:900_1199, part:1200_1499, part:1500_1999, part:2000_2499, part:2500_plus, stat:min, stat:mean, stat:max | 36 / 2 | 3 |
| availableAdministrationResultPerResident | bilanci | openbdap-annual | 2025 | rgs-finance/availableAdministrationResultPerResident/v1 | total | 8 / 0 | 3 |
| averageAgriculturalFarmSize | ambiente | istat-agriculture-census-2020 | 2020 | agriculture/averageAgriculturalFarmSize/v1 | total | 6 / 0 | 4 |
| averageGrossRemunerationPerEmployee | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 23 / 0 | 6 |
| bathingNonCompliantSamples | ambiente | arpat-bathing-annual | 2025 | bathing/bathingNonCompliantSamples/share:all:nonCompliant/v1 | total, share:all, share:routine, share:supplementary, nonCompliant:all, nonCompliant:routine, nonCompliant:supplementary, samples:all, samples:routine, samples:supplementary | 24 / 0 | 1 |
| bathingWaterQuality | ambiente | arpat-bathing-annual | 2025 | bathing/bathingWaterQuality/share:areas:excellent/v1 | total, share:areas:excellent, share:areas:good, share:areas:sufficient, share:areas:poor, share:kilometres:excellent, share:kilometres:good, share:kilometres:sufficient, share:kilometres:poor, count:areas:excellent, count:areas:good, count:areas:sufficient, count:areas:poor, count:areas:total, kilometres:excellent, kilometres:good, kilometres:sufficient, kilometres:poor, kilometres:total | 47 / 0 | 3 |
| blueFlagBeaches | ambiente | fee-blue-flag-annual | 2026 | bathing/blueFlagBeaches/count:localities:total/v1 | total | 3 / 0 | 3 |
| businessTurnover | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 23 / 0 | 5 |
| businessValueAdded | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 23 / 0 | 5 |
| capitalExpenditureCommittedPerResident | bilanci | openbdap-annual | 2025 | rgs-finance/capitalExpenditureCommittedPerResident/v1 | total | 8 / 0 | 3 |
| capitalPayments | bilanci | siope-monthly | 2025 | rgs-finance/capitalPayments/v1 | total | 8 / 0 | 3 |
| cashBalancePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/cashBalancePerResident/v1 | total | 8 / 0 | 3 |
| cashReceiptsPerResident | bilanci | openbdap-annual | 2025 | rgs-finance/cashReceiptsPerResident/v1 | total | 8 / 0 | 3 |
| chronicTotal | salute | ars-toscana-mixed | 2025 | ars-275-reviewed/v1 | total | 8 / 0 | 2 |
| civilProtectionMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/civilProtectionMissionExpenditurePerResident/v1 | total | 7 / 0 | 1 |
| climatePrecipitationTrend50y | ambiente | lamma-copernicus-climate | 1975–2025 | climate/precipitation/total/v1 | total, trend:1975-2025, trend_percent:1975-2025 | 7 / 0 | 2 |
| climateTemperatureTrend50y | ambiente | lamma-copernicus-climate | 1975–2025 | climate/temperature/total/v1 | total, trend:1975-2025 | 5 / 0 | 1 |
| climateTmaxTrend | ambiente | lamma-copernicus-climate | 1975–2025 | climate/tmax/total/v1 | total, trend:1975-2025 | 7 / 0 | 1 |
| climateTminTrend | ambiente | lamma-copernicus-climate | 1975–2025 | climate/tmin/total/v1 | total, trend:1975-2025 | 7 / 0 | 1 |
| cohabitingHouseholds | abitare | istat-census-annual | 2023 | istat-census-carriers/cohabitingHouseholds/v1 | total | 6 / 5 | 4 |
| commuterBalance | mobilita | istat-commuting-irregular | 2021 | istat-commuting/commuterBalance/v1 | total | 3 / 0 | 3 |
| commuterBalanceRate | mobilita | istat-commuting-irregular | 2021 | istat-commuting/commuterBalanceRate/v1 | total | 6 / 0 | 4 |
| copdPrevalence | salute | ars-toscana-mixed | 2025 | ars-268-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| cropProfile | ambiente | istat-agriculture-census-2020 | 2020 | agriculture/cropProfile/v1 | total, part:ARLAND, part:OLIVOOILTR, part:OLIVTTR, part:VINEY, part:PGRAPM | 12 / 6 | 1 |
| cultureSportMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/cultureSportMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| currentCollectionCapacity | bilanci | openbdap-annual | 2025 | rgs-finance/currentCollectionCapacity/v1 | total | 9 / 0 | 3 |
| currentExpenditureCommittedPerResident | bilanci | openbdap-annual | 2025 | rgs-finance/currentExpenditureCommittedPerResident/v1 | total | 8 / 0 | 3 |
| currentPaymentCapacity | bilanci | openbdap-annual | 2025 | rgs-finance/currentPaymentCapacity/v1 | total | 9 / 0 | 3 |
| currentPayments | bilanci | siope-monthly | 2025 | rgs-finance/currentPayments/v1 | total | 8 / 0 | 3 |
| currentRevenueAccruedPerResident | bilanci | openbdap-annual | 2025 | rgs-finance/currentRevenueAccruedPerResident/v1 | total | 8 / 0 | 3 |
| dementia | salute | ars-toscana-mixed | 2025 | ars-270-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| dependencyIndices | demografia | istat-demography-annual | 2026 | demography-school/dependencyIndices/total/v1 | total, part:structural, part:elderly, part:structural\|sex:men, part:structural\|sex:women, part:elderly\|sex:men, part:elderly\|sex:women | 46 / 0 | 8 |
| diabetes | salute | ars-toscana-mixed | 2025 | ars-271-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| diagnosticImagingServices | salute | ars-toscana-mixed | 2025 | ars-1325-reviewed/v1 | total, sex:men, sex:women | 19 / 0 | 7 |
| diplomaPlus | istruzione | istat-census-annual | 2024 | istat-census-carriers/diplomaPlus/v1 | total, age:9-24\|sex:total, age:9-24\|sex:men, age:9-24\|sex:women, age:25-49\|sex:total, age:25-49\|sex:men, age:25-49\|sex:women, age:50-64\|sex:total, age:50-64\|sex:men, age:50-64\|sex:women, age:65plus\|sex:total, age:65plus\|sex:men, age:65plus\|sex:women, age:25-64\|sex:total, age:25-64\|sex:men, age:25-64\|sex:women, age:9plus\|sex:total, age:9plus\|sex:men, age:9plus\|sex:women | 64 / 86 | 8 |
| disability064Per1000 | salute | regione-toscana-indicatori-comunali | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| drinkingWaterQuality | ambiente | gaia-quality-semiannual | 2° semestre 2025 | water-quality/locality-parameter/v1 | parameter:0, parameter:1, parameter:2, parameter:3, parameter:4, parameter:5, parameter:6, parameter:7, parameter:8, parameter:9, parameter:10, parameter:11, parameter:12, parameter:13, parameter:14, parameter:15, parameter:16 | 17 / 0 | 0 |
| earlyChildhoodPotentialCapacityRate | istruzione | regione-toscana-early-childhood | 2024/25 | tuscany-child-capacity/v1 | total | 5 / 0 | 3 |
| economicDevelopmentMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/economicDevelopmentMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| economyActivityAtlas | economia | regione-toscana-infocamere-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 6 |
| educationMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/educationMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| elderlyHomeCare | salute | ars-toscana-mixed | 2024 | ars-260-standardized-sex/v1 | sex:total, sex:men, sex:women | 15 / 0 | 7 |
| emergencyAccess | salute | ars-toscana-mixed | 2025 | ars-1657-reviewed/v1 | total, sex:men, sex:women | 19 / 0 | 7 |
| employeesPerLocalUnit | economia | istat-business-annual | 2023 | istat-business/asia/v1 | total | 10 / 0 | 5 |
| employmentGenderGap | lavoro | istat-census-annual | 2023 | istat-census-carriers/employmentGenderGap/v1 | total | 8 / 1 | 5 |
| employmentRate | lavoro | istat-census-annual | 2024 | istat-census-carriers/employmentRate/v1 | total, age:15-24\|sex:total, age:15-24\|sex:men, age:15-24\|sex:women, age:25-49\|sex:total, age:25-49\|sex:men, age:25-49\|sex:women, age:50-64\|sex:total, age:50-64\|sex:men, age:50-64\|sex:women, age:65plus\|sex:total, age:65plus\|sex:men, age:65plus\|sex:women, age:25-64\|sex:total, age:25-64\|sex:men, age:25-64\|sex:women, age:15plus\|sex:total, age:15plus\|sex:men, age:15plus\|sex:women | 64 / 90 | 8 |
| emsResponseTimeP75 | salute | regione-toscana-indicatori-comunali | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| environmentMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/environmentMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| erpArrears | abitare | erp-lucca-annual-balance-sheet | 2024 | adapter_not_implemented | — | 0 / 0 | 3 |
| essentialServicesAccessibility | ambiente | istat-fragility-2022 | 2019 | fragility/essentialServicesAccessibility/v1 | total | 4 / 0 | 2 |
| evPoints | mobilita | pun-continuous | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| extractivePlanning | ambiente | regione-toscana-prc-annual | PRC vigente · variante 2025 | extractive/extractivePlanning/g_ha/v1 | total, view:g_ha, view:g_pct, view:g_n, view:gp_ha, view:gp_pct, view:gp_n, view:acc_ha, view:acc_pct, view:acc_n, view:mos, view:pmos, view:sed, share:g, share:gp, share:acc | 35 / 0 | 1 |
| extractiveProduction | ambiente | regione-toscana-prc-annual | 2025 | extractive/extractiveProduction/total/v1 | total | 2 / 1 | 1 |
| extractiveSites | ambiente | regione-toscana-rtcave-continuous | 2 settembre 2026 | extractive/extractiveSites/total/v1 | total, view:state_active, view:state_inactive, view:state_suspended, view:state_expired, view:state_restoration, view:state_closed, view:state_nd, view:type_ordinary, view:type_restoreworks, view:type_recovery, view:prod_ornamental, view:prod_industrial, view:prod_construction | 28 / 0 | 2 |
| fcdePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/fcdePerResident/v1 | total | 7 / 0 | 1 |
| femaleEmploymentRate | lavoro | istat-census-annual | 2023 | istat-census-femaleEmploymentRate/v1 | total | 10 / 1 | 8 |
| financialDebtProfile | bilanci | openbdap-annual | 2025 | distinct-finance/financialDebtProfile/debtPerResident/v1 | total, part:debtPerResident, part:interestShare, part:debtSustainability | 33 / 0 | 2 |
| fiscalRecoveryActivity | economia | siope-monthly | 2025 | distinct-finance/fiscalRecoveryActivity/recoveryPerResident/v1 | total, part:recoveryPerResident, part:recoveryTotal, part:daitContribution | 18 / 0 | 3 |
| floodExposure | ambiente | ispra-idrogeo-risk | 2020 | hazard/floodExposure/residentsPct/P2/v1 | total, residentsPct:P3, residents:P3, areaPct:P3, areaKm2:P3, residentsPct:P2, residents:P2, areaPct:P2, areaKm2:P2, residentsPct:P1, residents:P1, areaPct:P1, areaKm2:P1 | 46 / 0 | 1 |
| foreignBornSoleProprietorShare | economia | regione-toscana-indicatori-comunali | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| foreignResidentialMobility | demografia | istat-demography-annual | 2024 | demography-school/foreignResidentialMobility/total/v1 | total, part:arrivals, part:departures, part:balance | 40 / 0 | 7 |
| foreignResidents | demografia | istat-demography-annual | 2025 | demography-school/foreignResidents/total/v1 | total, count, sex:men, sex:women | 22 / 2 | 8 |
| foreignTourismShare | economia | regione-toscana-tourism-annual | 2025 | tourism/foreignTourismShare/total/v1 | total, nativeRatio | 8 / 0 | 2 |
| forestCoverIndex | ambiente | pefc-sinfor-foreste-in-comune-2026 | CFI 2020 · aggiornamento 2024 | geography/forestCoverIndex/v1 | total, view:hectares | 7 / 0 | 2 |
| ftthCoverage20m | mobilita | agcom-quarterly | 31 dicembre 2025 | adapter_not_implemented | — | 0 / 0 | 2 |
| ftthCoverageDesi | mobilita | agcom-quarterly | 31 dicembre 2025 | adapter_not_implemented | — | 0 / 0 | 2 |
| ftthReachedHouseholds | mobilita | agcom-quarterly | 31 dicembre 2025 | adapter_not_implemented | — | 0 / 0 | 0 |
| ftthUnreachedHouseholds | mobilita | agcom-quarterly | 31 dicembre 2025 | adapter_not_implemented | — | 0 / 0 | 0 |
| fuelPrices | mobilita | mimit-fuel-daily | 2026-10-03 | adapter_not_implemented | — | 0 / 0 | 3 |
| generalAdministrationMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/generalAdministrationMissionExpenditurePerResident/v1 | total | 7 / 0 | 1 |
| grossOperatingMargin | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 23 / 0 | 5 |
| heartFailurePrevalence | salute | ars-toscana-mixed | 2025 | ars-272-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| hospitalizedAll | salute | ars-toscana-mixed | 2021–2025 | ars-1332-reviewed/v1 | total | 7 / 0 | 2 |
| hospitals | salute | health-ministry-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 1 |
| householdSize | abitare | istat-census-annual | 2023 | istat-census-carriers/householdSize/v1 | total | 3 / 0 | 1 |
| housingStockPer1000 | abitare | istat-census-annual | 2023 | istat-census-housingStockPer1000/v1 | total | 9 / 1 | 5 |
| hydraulicWorksCensusElements | ambiente | regione-toscana-opere-idrauliche-2021 | 2021 | territory/hydraulicWorksCensusElements/total/v1 | total, layer:area, layer:line, layer:point | 12 / 0 | 1 |
| hypertensionPrevalence | salute | ars-toscana-mixed | 2025 | ars-255-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| inboundCommuters | mobilita | istat-commuting-irregular | 2021 | istat-commuting/inboundCommuters/v1 | total | 3 / 0 | 3 |
| inboundCommutersRate | mobilita | istat-commuting-irregular | 2021 | istat-commuting/inboundCommutersRate/v1 | total | 6 / 0 | 4 |
| income | economia | mef-irpef-annual | 2024 | mef-taxable-income/v1 | total | 9 / 0 | 3 |
| incomeDistribution | economia | mef-irpef-annual | 2024 | mef/incomeDistribution/macro:0/v1 | total, macro:0, macro:1, macro:2, macro:3, band:le0, band:0to10k, band:10to15k, band:15to26k, band:26to55k, band:55to75k, band:75to120k, band:over120k | 33 / 6 | 3 |
| incomeSourceProfile | economia | mef-irpef-annual | 2024 | mef/incomeSourceProfile/employment/v1 | total, source:employment, source:pension, source:selfEmployment, source:entrepreneurOrdinary, source:entrepreneurSimplified, source:participation, source:buildings | 33 / 3 | 6 |
| incomeVsInflation | economia | mef-istat-real-income-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 3 |
| industryValueAddedShare | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total | 9 / 0 | 6 |
| industryWorkerShare | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total | 9 / 0 | 6 |
| innovationBusinessShare | economia | regione-toscana-indicatori-comunali | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| internalResidentialMobility | demografia | istat-demography-annual | 2024 | demography-school/internalResidentialMobility/total/v1 | total, part:arrivals, part:departures, part:balance | 40 / 0 | 7 |
| invalsiAcademicExcellence | istruzione | invalsi-open-dispersione-2025 | 2024-25 | adapter_not_implemented | — | 0 / 0 | 4 |
| invalsiCompetence | istruzione | invalsi-open-risultati-2025 | 2024-25 | adapter_not_implemented | — | 0 / 0 | 4 |
| invalsiImplicitDispersion | istruzione | invalsi-open-dispersione-2025 | 2024-25 | adapter_not_implemented | — | 0 / 0 | 4 |
| invalsiResults | istruzione | invalsi-open-risultati-2025 | 2024-25 | adapter_not_implemented | — | 0 / 0 | 4 |
| irrigatedAgriculturalArea | ambiente | istat-agriculture-census-2020 | 2020 | agriculture/irrigatedAgriculturalArea/v1 | total, view:normalized | 7 / 0 | 4 |
| ischemicHeartDiseasePrevalence | salute | ars-toscana-mixed | 2025 | ars-269-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| labourCost | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 23 / 0 | 5 |
| labourProductivity | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 23 / 0 | 6 |
| landCoverProfile | ambiente | regione-toscana-ucs-2007-2019 | 2007–2019 | soil/landCoverProfile/artificialized/v1 | total, part:artificialized, part:agricultural, part:forest_seminatural_total, part:wetlands, part:water, part:forest, part:seminativi, part:permanent_crops, part:seminatural_nonforest, part:urban_green_cartographic, hectares:artificialized, hectares:agricultural, hectares:forest_seminatural_total, hectares:wetlands, hectares:water, hectares:forest, hectares:seminativi, hectares:permanent_crops, hectares:seminatural_nonforest, hectares:urban_green_cartographic | 95 / 0 | 4 |
| landUse | ambiente | ispra-consumo-suolo-2024 | 2006, 2012, 2015–2024 | soil/landUse/percent/v1 | total, view:percent, view:hectares, view:sqmPerResident | 23 / 0 | 4 |
| landUseChange | ambiente | ispra-consumo-suolo-2024 | 2012, 2015–2024 | soil/landUseChange/net/v1 | total, view:net, view:gross | 12 / 0 | 4 |
| landslideExposure | ambiente | ispra-idrogeo-risk | 2024 | hazard/landslideExposure/residentsPct/P3+P4/v1 | total, residentsPct:P3+P4, residents:P3+P4, areaPct:P3+P4, areaKm2:P3+P4, residentsPct:P4, residents:P4, areaPct:P4, areaKm2:P4, residentsPct:P3, residents:P3, areaPct:P3, areaKm2:P3, residentsPct:P2, residents:P2, areaPct:P2, areaKm2:P2, residentsPct:P1, residents:P1, areaPct:P1, areaKm2:P1, residentsPct:AA, residents:AA, areaPct:AA, areaKm2:AA, history:areaPct:P3+P4 | 88 / 4 | 2 |
| libraryActiveBorrowersPer100 | comunita | regione-toscana-biblioteche-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| libraryLoansPerResident | comunita | regione-toscana-biblioteche-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| libraryWeeklyOpeningHours | comunita | regione-toscana-biblioteche-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| lifeExpectancy | salute | ars-toscana-mixed | 2022 | ars-1290-reviewed/v1 | total, sex:men, sex:women | 27 / 0 | 5 |
| localEmployees | economia | istat-business-annual | 2023 | istat-business/asia/v1 | total | 9 / 0 | 3 |
| localEmployeesChange | economia | istat-business-annual | 2018–2023 | istat-business/asia/v1 | total | 8 / 1 | 5 |
| localUnits | economia | istat-business-annual | 2023 | istat-business/asia/v1 | total | 9 / 0 | 4 |
| localUnitsChange | economia | istat-business-annual | 2018–2023 | istat-business/asia/v1 | total | 8 / 1 | 5 |
| lowProductivityEmployment | economia | istat-fragility-2022 | 2022 | fragility/lowProductivityEmployment/v1 | total | 2 / 0 | 1 |
| maleEmploymentRate | lavoro | istat-census-annual | 2023 | istat-census-maleEmploymentRate/v1 | total | 10 / 1 | 8 |
| managedReticulumLength | ambiente | regione-toscana-reticolo-v137 | DCRT 24/2025 · confini Istat 1 gennaio 2026 | territory/managedReticulumLength/full/v1 | total, view:full, view:managed, view:density | 13 / 0 | 3 |
| maritimeConcessionFeesDue | ambiente | mit-sid-demanio-irregular | agosto 2026 | maritime/maritimeConcessionFeesDue/canoneDovutoEur/v1 | total, view:touristDue, share:touristDue, view:mean, view:touristMean, view:median | 15 / 0 | 2 |
| maritimeConcessions | ambiente | mit-sid-demanio-irregular | agosto 2026 | maritime/maritimeConcessions/totalConcessions/v1 | total, view:tourist, share:tourist, view:minimumCount, share:minimum, view:expiryMissing | 14 / 0 | 2 |
| microUnits | economia | istat-business-annual | 2023 | istat-business/asia/v1 | total | 5 / 0 | 2 |
| mobilityMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/mobilityMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| mortalityAll | salute | ars-toscana-mixed | 2013–2022 | ars-1438-reviewed/v1 | total, sex:men, sex:women | 18 / 0 | 7 |
| mortalityCancer | salute | ars-toscana-mixed | 2013–2022 | ars-1499-reviewed/v1 | total, sex:men, sex:women | 18 / 0 | 7 |
| mortalityCirculatory | salute | ars-toscana-mixed | 2013–2022 | ars-1327-reviewed/v1 | total, sex:men, sex:women | 18 / 0 | 7 |
| mortalityRespiratory | salute | ars-toscana-mixed | 2013–2022 | ars-1606-reviewed/v1 | total, sex:men, sex:women | 18 / 0 | 7 |
| motorization | mobilita | aci-istat-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| municipalEmployeesPer1000 | bilanci | rgs-conto-annuale-annual | 2024 | rgs/municipalEmployeesPer1000/total/v1 | total, staff, residents | 8 / 0 | 4 |
| municipalFragility | ambiente | istat-fragility-2022 | 2022 | fragility/municipalFragility/v1 | total | 2 / 0 | 1 |
| municipalImuStandard | economia | mef-municipal-tax-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 0 |
| municipalIrpef | economia | mef-municipal-irpef-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 2 |
| municipalOnlineServicesAdvanced | bilanci | regione-toscana-indicatori-comunali | 2022 | adapter_not_implemented | — | 0 / 0 | 2 |
| municipalStaffAgeStructure | bilanci | rgs-conto-annuale-annual | 2024 | rgs/municipalStaffAgeStructure/age55plus/v1 | total, age:age55plus, age:age40to54, age:under40 | 12 / 0 | 4 |
| municipalStaffTraining | bilanci | rgs-conto-annuale-annual | 2024 | rgs/municipalStaffTraining/meanTotalRgs/v1 | total, measure:meanTotalRgs, measure:totalDays, measure:meanMen, measure:meanWomen, days:men, days:women | 21 / 0 | 2 |
| municipalStaffTurnover | bilanci | rgs-conto-annuale-annual | 2024 | rgs/municipalStaffTurnover/total/v1 | total, headcount, hires, cessations | 9 / 0 | 4 |
| municipalSurface | ambiente | istat-geografia-comunale-2021 | 31 dicembre 2021 | geography/municipalSurface/v1 | total | 5 / 0 | 2 |
| naturalDemographicDynamics | demografia | istat-demography-annual | 2025 | demography-school/naturalDemographicDynamics/total/v1 | total, part:balance, part:births, part:deaths | 40 / 0 | 7 |
| nonOccupiedHomesPer1000 | abitare | istat-census-annual | 2023 | istat-census-nonOccupiedHomesPer1000/v1 | total | 9 / 1 | 5 |
| oldAgeIndex | demografia | istat-census-annual | 2026 | istat-census-carriers/oldAgeIndex/v1 | total | 7 / 0 | 5 |
| omiResidential | abitare | agenzia-entrate-omi-semestral | 2° semestre 2025 | adapter_not_implemented | — | 0 / 0 | 0 |
| organicAgriculturalAreaShare | ambiente | regione-toscana-indicatori-comunali | 2024 | agriculture-profiles/organicAgriculturalAreaShare/organicAreaShare/v1 | total | 4 / 0 | 2 |
| outboundCommuters | mobilita | istat-commuting-irregular | 2021 | istat-commuting/outboundCommuters/v1 | total | 3 / 0 | 3 |
| outboundCommutersRate | mobilita | istat-commuting-irregular | 2021 | istat-commuting/outboundCommutersRate/v1 | total | 6 / 0 | 4 |
| outsideMunicipality | mobilita | istat-commuting-irregular | 2021 | adapter_not_implemented | — | 0 / 0 | 0 |
| ownRevenueShare | bilanci | openbdap-annual | 2025 | rgs-finance/ownRevenueShare/v1 | total | 9 / 0 | 3 |
| pabCompletedOperationalGrossValue | ambiente | cb1-pmo-status-2026 | 2026 | pab/pabCompletedOperationalGrossValue/total/v1 | total | 2 / 0 | 0 |
| pabInProgressOperationalGrossValue | ambiente | cb1-pmo-status-2026 | 2026 | pab/pabInProgressOperationalGrossValue/total/v1 | total | 2 / 0 | 0 |
| pabInterventionsCompleted | ambiente | cb1-pmo-status-2026 | 2026 | pab/pabInterventionsCompleted/total/v1 | total, share:operational | 5 / 0 | 0 |
| pabInterventionsInProgress | ambiente | cb1-pmo-status-2026 | 2026 | pab/pabInterventionsInProgress/total/v1 | total, share:operational | 5 / 0 | 0 |
| pabProgrammedInterventionLength | ambiente | cb1-pmo-2026 | 2026 | pab/pabProgrammedInterventionLength/total/v1 | total | 2 / 0 | 0 |
| pabProgrammedInterventions | ambiente | regione-toscana-pab-annual | 2026 | pab/pabProgrammedInterventions/total/v1 | total | 2 / 0 | 0 |
| pabProgrammedMaintenanceValue | ambiente | regione-toscana-pab-annual | 2026 | pab/pabProgrammedMaintenanceValue/total/v1 | total | 2 / 0 | 0 |
| pensionIncomeShare | economia | mef-irpef-annual | 2024 | mef/pensionIncomeShare/total/v1 | total | 6 / 0 | 5 |
| permanentRsaAssisted | salute | ars-toscana-mixed | 2024 | ars-261-reviewed/v1 | total, sex:men, sex:women | 19 / 0 | 7 |
| pharmaciesPer1000 | salute | health-ministry-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 2 |
| pnrrConcluded | comunita | regione-toscana-pnrr-monthly | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| pnrrFunding | comunita | regione-toscana-pnrr-monthly | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| pollutingCars | mobilita | aci-istat-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |
| population | demografia | istat-demography-annual | 2026 | istat-posas-population/v1 | total, sex:men, sex:women | 13 / 0 | 6 |
| populationChange | demografia | istat-demography-annual | 2019–2026 | demography-school/populationChange/total/v1 | total | 9 / 1 | 6 |
| populationDensity | ambiente | istat-geografia-comunale-2021 | 2026 | geography/populationDensity/v1 | total | 6 / 0 | 4 |
| primaryFullTimeShare | istruzione | mim-school-year | a.s. 2024/25 | demography-school/primaryFullTimeShare/total/v1 | total | 6 / 0 | 4 |
| priorStrokePrevalence | salute | ars-toscana-mixed | 2025 | ars-273-reviewed/v1 | total, sex:men, sex:women, age:16-44\|total, age:16-44\|sex:men, age:16-44\|sex:women, age:45-64\|total, age:45-64\|sex:men, age:45-64\|sex:women, age:65-84\|total, age:65-84\|sex:men, age:65-84\|sex:women, age:85+\|total, age:85+\|sex:men, age:85+\|sex:women | 79 / 0 | 8 |
| protectedNaturalAreas | ambiente | regione-toscana-aree-protette-v137 | archivi geografici ufficiali Regione Toscana · consultati 12 settembre 2026 | territory/protectedNaturalAreas/total/v1 | total, part:total, part:parksReserves, part:anpil, part:natura2000, part:zsc, part:zps, part:ramsar, hectares:total, hectares:parksReserves, hectares:anpil, hectares:natura2000, hectares:zsc, hectares:zps, hectares:ramsar | 53 / 0 | 3 |
| publicWorks | comunita | openbdap-continuous | 2026 | distinct-finance/publicWorks/total/v1 | total | 3 / 0 | 1 |
| recycling | ambiente | ispra-environment-annual | 2024 | environment/recycling/v1 | total | 6 / 0 | 3 |
| remediationProceedings | ambiente | sisbon-weekly | 29 agosto 2026 | remediation/active/v1 | total, view:active, view:closed, view:all, share:active | 11 / 0 | 1 |
| residualWaste | ambiente | ispra-environment-annual | 2024 | environment/residualWaste/v1 | total | 6 / 0 | 3 |
| rigidDefenceProtectedCoast | ambiente | ispra-coast-irregular | 2020 | coast/rigidDefenceProtectedCoast/protectedShare/v1 | total, view:protectedKm, view:coastKm | 9 / 0 | 4 |
| rigidExpenditureShare | bilanci | openbdap-annual | 2025 | rgs-finance/rigidExpenditureShare/v1 | total | 8 / 0 | 1 |
| roadFinesPerResident | sicurezza | istat-road-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 3 |
| roadNetworkProfile | mobilita | regione-toscana-iternet-448 | 2022 | adapter_not_implemented | — | 0 / 0 | 3 |
| roadSafety | sicurezza | istat-road-annual | 2024 | adapter_not_implemented | — | 0 / 0 | 4 |
| scheduledTplTripsPer1000 | mobilita | regione-toscana-gtfs-scheduled | 26 agosto 2026 | adapter_not_implemented | — | 0 / 0 | 1 |
| schoolBuildingAccessibility | istruzione | mim-school-year | 2024/25 | demography-school/schoolBuildingAccessibility/total/v1 | total, part:yes, part:no, part:undefined | 24 / 0 | 5 |
| schoolBuildingAge | istruzione | mim-school-year | 2024/25 | demography-school/schoolBuildingAge/total/v1 | total, part:builtBy1970, part:before1800, part:1800-1899, part:1900-1933, part:1934-1949, part:1950-1970, part:1971-1975, part:1976-1992, part:1997-2008, part:2009-2017, part:undefined | 70 / 2 | 5 |
| schoolBuildingFacilities | istruzione | mim-school-year | 2024/25 | demography-school/schoolBuildingFacilities/total/v1 | total, part:canteen, part:gym | 16 / 0 | 5 |
| schoolBuildingSafetyDocs | istruzione | mim-school-year | 2024/25 | demography-school/schoolBuildingSafetyDocs/total/v1 | total, part:fullOccupancy, part:cpi, part:scia, part:renewal | 16 / 8 | 5 |
| schoolBuildingTransport | istruzione | mim-school-year | 2024/25 | demography-school/schoolBuildingTransport/total/v1 | total, part:schoolBus, part:urban, part:interurban | 20 / 0 | 5 |
| schoolSites | istruzione | mim-school-year | 2025 | demography-school/schoolSites/total/v1 | total, normalized | 6 / 0 | 1 |
| schoolStudents | istruzione | mim-school-year | a.s. 2024/25 | demography-school/schoolStudents/total/v1 | total | 3 / 0 | 2 |
| securityMissionExpenditurePerResident | sicurezza | openbdap-annual | 2025 | distinct-finance/securityMissionExpenditurePerResident/total/v1 | total | 6 / 0 | 1 |
| selfContainment | mobilita | istat-commuting-irregular | 2021 | istat-commuting/selfContainment/v1 | total | 6 / 0 | 2 |
| shorelineDynamics | ambiente | ispra-coast-irregular | 2006–2020 | coast/shorelineDynamics/erosionShare/v1 | total, share:erosion, share:stable, share:advance, kilometres:erosion, kilometres:stable, kilometres:advance, view:analysedKm | 20 / 0 | 3 |
| singleHouseholds | abitare | istat-census-annual | 2023 | istat-census-carriers/singleHouseholds/v1 | total | 9 / 1 | 5 |
| siopePayments | bilanci | siope-monthly | 2025 | rgs-finance/siopePayments/v1 | total | 8 / 0 | 3 |
| slowMobilityBici | mobilita | percorsi-curated | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| slowMobilityCammini | mobilita | percorsi-curated | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| slowMobilityMtb | mobilita | percorsi-curated | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| slowMobilityRoutes | mobilita | percorsi-curated | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| slowMobilityTrekking | mobilita | percorsi-curated | 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| socialMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/socialMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| socialSpendingByUserArea | comunita | istat-social-services-annual | 2022 | adapter_not_implemented | — | 0 / 0 | 1 |
| socialSpendingPerResident | comunita | istat-social-services-annual | 2022 | adapter_not_implemented | — | 0 / 0 | 3 |
| specialistVisits7Psr | salute | ars-toscana-mixed | 2025 | ars-1425-reviewed/v1 | total, sex:men, sex:women | 19 / 0 | 7 |
| statisticalCoastlineLength | ambiente | istat-geografie-funzionali-2021 | 31 dicembre 2021 | coast/statisticalCoastlineLength/lengthKm/v1 | total | 2 / 0 | 2 |
| studentsPerClass | istruzione | mim-school-year | a.s. 2024/25 | demography-school/studentsPerClass/total/v1 | total | 6 / 0 | 4 |
| tariStandardHousehold | economia | mef-municipal-tax-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 0 |
| taxpayersAdultPopulationRate | economia | mef-irpef-annual | MEF a.i. 2024 · residenti 1.1.2026 | mef/taxpayersAdultPopulationRate/total/v1 | total | 5 / 0 | 4 |
| territorialClassification | ambiente | istat-geografie-funzionali-2021 | 2021 | classification/degurba/v1 | total, part:degurba, part:littoral, part:coastalZone | 4 / 0 | 0 |
| territorialPlanningMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/territorialPlanningMissionExpenditurePerResident/v1 | total | 7 / 0 | 1 |
| tertiary | istruzione | istat-census-annual | 2024 | istat-census-carriers/tertiary/v1 | total, age:9-24\|sex:total, age:9-24\|sex:men, age:9-24\|sex:women, age:25-49\|sex:total, age:25-49\|sex:men, age:25-49\|sex:women, age:50-64\|sex:total, age:50-64\|sex:men, age:50-64\|sex:women, age:65plus\|sex:total, age:65plus\|sex:men, age:65plus\|sex:women, age:25-64\|sex:total, age:25-64\|sex:men, age:25-64\|sex:women, age:9plus\|sex:total, age:9plus\|sex:men, age:9plus\|sex:women | 64 / 90 | 8 |
| thirdSector | comunita | runts-continuous | 2025 | adapter_not_implemented | — | 0 / 0 | 1 |
| totalResidentialMobility | demografia | istat-demography-annual | 2024 | demography-school/totalResidentialMobility/total/v1 | total, part:arrivals, part:departures, part:balance | 40 / 0 | 7 |
| tourismArrivals | economia | regione-toscana-tourism-annual | 2025 | tourism/tourismArrivals/total/v1 | total | 4 / 0 | 2 |
| tourismAverageStay | economia | regione-toscana-tourism-annual | 2025 | tourism/tourismAverageStay/total/v1 | total | 5 / 0 | 2 |
| tourismBeds | economia | istat-tourism-annual | 2024 | tourism/tourismBeds/total/v1 | total | 5 / 0 | 4 |
| tourismBedsPer1000 | economia | istat-tourism-annual | 2024 | tourism/tourismBedsPer1000/total/v1 | total | 5 / 0 | 4 |
| tourismDevelopmentMissionExpenditurePerResident | bilanci | openbdap-annual | 2025 | rgs-finance/tourismDevelopmentMissionExpenditurePerResident/v1 | total | 8 / 0 | 3 |
| tourismIntensity | economia | regione-toscana-tourism-annual | 2025 | tuscany-tourismIntensity/v1 | total | 5 / 0 | 3 |
| tourismPresences | economia | regione-toscana-tourism-annual | 2025 | tourism/tourismPresences/total/v1 | total | 8 / 0 | 3 |
| tourismSeasonality | economia | regione-toscana-tourism-annual | 2025 | adapter_not_implemented | — | 0 / 0 | 1 |
| tourismStructuresPer1000 | economia | istat-tourism-annual | 2024 | tourism/tourismStructuresPer1000/total/v1 | total | 5 / 0 | 2 |
| tplServiceSpan | mobilita | regione-toscana-gtfs-scheduled | 26 agosto 2026 | adapter_not_implemented | — | 0 / 0 | 0 |
| turnoverPerPersonEmployed | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 26 / 0 | 6 |
| unemploymentRate | lavoro | istat-census-annual | 2024 | istat-census-carriers/unemploymentRate/v1 | total, age:15-24\|sex:total, age:15-24\|sex:men, age:15-24\|sex:women, age:25-49\|sex:total, age:25-49\|sex:men, age:25-49\|sex:women, age:50-64\|sex:total, age:50-64\|sex:men, age:50-64\|sex:women, age:65plus\|sex:total, age:65plus\|sex:men, age:65plus\|sex:women, age:25-64\|sex:total, age:25-64\|sex:men, age:25-64\|sex:women, age:15plus\|sex:total, age:15plus\|sex:men, age:15plus\|sex:women | 64 / 90 | 8 |
| vacantHomes | abitare | istat-census-annual | 2023 | istat-census-carriers/vacantHomes/v1 | total | 9 / 1 | 5 |
| valueAddedTurnoverShare | economia | istat-business-annual | 2023 | istat-business/frame-sbs/v1 | total, sector:industry, sector:services | 26 / 0 | 6 |
| voterTurnout | comunita | dait-eligendo-irregular | 2026 | adapter_not_implemented | — | 0 / 0 | 6 |
| wastePerResident | ambiente | ispra-environment-annual | 2024 | environment/wastePerResident/v1 | total | 6 / 0 | 3 |
| wasteServiceCost | ambiente | ispra-environment-annual | 2024 | environment/wasteServiceCost/v1 | total | 6 / 0 | 2 |
| waterNetworkLosses | ambiente | istat-water-irregular | 2018 | environment/waterNetworkLosses/v1 | total | 11 / 0 | 3 |
| yearEndCashFundPerResident | bilanci | openbdap-annual | 2025 | rgs-finance/yearEndCashFundPerResident/v1 | total | 7 / 0 | 1 |
| youthOtherStatus | lavoro | regione-toscana-indicatori-comunali | 2024 | adapter_not_implemented | — | 0 / 0 | 2 |

## Collegamenti tipizzati

| Collegamento | Tipo | Verifica | Associazione |
|---|---|---|---|
| territorialClassification → statisticalCoastlineLength | context | observations_available_context_only | not_computable: classification_category_arithmetic_or_association_not_supported |
| pabProgrammedInterventions → pabInterventionsCompleted | context | observations_available_context_only | not_computable: pab_approved_operational_or_risk_pair_not_reviewed |
| agriculturalRenewalAndLeadership → agriculturalFarms | context | observations_available_context_only | not_computable: agriculture_profiles_pair_not_jointly_reviewed |
| agriculturalDiversificationAndModernization → organicAgriculturalAreaShare | context | observations_available_context_only | not_computable: agriculture_profiles_pair_not_jointly_reviewed |
| climateTminTrend → climateTmaxTrend | context | observations_available_context_only | not_computable: climate_pair_not_jointly_reviewed |
| pabInterventionsCompleted → pabCompletedOperationalGrossValue | context | observations_available_context_only | not_computable: pab_approved_operational_or_risk_pair_not_reviewed |
| extractiveSites → extractiveProduction | context | observations_available_context_only | not_computable: extractive_universes_not_jointly_comparable |
| extractiveSites → extractivePlanning | context | observations_available_context_only | not_computable: extractive_universes_not_jointly_comparable |
| maritimeConcessions → maritimeConcessionFeesDue | context | observations_available_context_only | not_computable: maritime_context_pair_not_reviewed |
| maritimeConcessions → statisticalCoastlineLength | context | observations_available_context_only | not_computable: maritime_context_pair_not_reviewed |
| bathingWaterQuality → bathingNonCompliantSamples | context | observations_available_context_only | not_computable: bathing_universes_not_jointly_comparable |
| blueFlagBeaches → bathingWaterQuality | context | observations_available_context_only | not_computable: bathing_universes_not_jointly_comparable |
| statisticalCoastlineLength → rigidDefenceProtectedCoast | context | observations_available_context_only | not_computable: coast_universes_not_jointly_comparable |
| rigidDefenceProtectedCoast → shorelineDynamics | context | observations_available_context_only | not_computable: coast_universes_not_jointly_comparable |
| municipalFragility → essentialServicesAccessibility | context | observations_available_context_only | not_computable: fragility_ordinal_operation_not_supported |
| lowProductivityEmployment → municipalFragility | context | observations_available_context_only | not_computable: fragility_ordinal_operation_not_supported |
| floodExposure → landslideExposure | context | observations_available_context_only | not_computable: paired_period_mismatch |
| protectedNaturalAreas → managedReticulumLength | context | observations_available_context_only | not_computable: paired_period_mismatch |
| landUse → landCoverProfile | context | observations_available_context_only | not_computable: paired_period_mismatch |
| municipalSurface → populationDensity | context | observations_available_context_only | not_computable: paired_period_mismatch |
| altitudeProfile → forestCoverIndex | context | observations_available_context_only | not_computable: paired_period_mismatch |
| agriculturalFarms → irrigatedAgriculturalArea | context | observations_available_context_only | computed:  |
| agriculturalUsedArea → irrigatedAgriculturalArea | context | observations_available_context_only | not_computable: agriculture_localized_and_center_scopes_not_jointly_comparable |
| wastePerResident → residualWaste | derived_product | components_reconciled | Non richiesta: dipendenza matematica |
| wasteServiceCost → wastePerResident | context | observations_available_context_only | computed:  |
| waterNetworkLosses → wastePerResident | context | observations_available_context_only | not_computable: paired_frequency_mismatch, paired_period_mismatch |
| inboundCommuters → inboundCommutersRate | shared_numerator | components_reconciled | Non richiesta: dipendenza matematica |
| outboundCommuters → outboundCommutersRate | shared_numerator | components_reconciled | Non richiesta: dipendenza matematica |
| commuterBalance → commuterBalanceRate | shared_numerator | components_reconciled | Non richiesta: dipendenza matematica |
| inboundCommutersRate → outboundCommutersRate | context | observations_available_context_only | computed:  |
| inboundCommutersRate → commuterBalanceRate | context | observations_available_context_only | not_computable: commuting_hybrid_denominator_pair_not_aligned |
| selfContainment → employmentRate | context | observations_available_context_only | not_computable: paired_frequency_mismatch, paired_period_mismatch |
| naturalDemographicDynamics → totalResidentialMobility | context | observations_available_context_only | computed:  |
| foreignResidents → foreignResidentialMobility | context | observations_available_context_only | not_computable: paired_period_mismatch |
| primaryFullTimeShare → schoolBuildingFacilities | context | observations_available_context_only | computed:  |
| schoolBuildingAccessibility → schoolBuildingTransport | context | observations_available_context_only | computed:  |
| schoolSites → schoolStudents | context | observations_available_context_only | not_computable: demography_school_site_observation_dates_not_attested_for_pairing |
| financialDebtProfile → financialDebtProfile | context | observations_available_context_only | computed:  |
| fiscalRecoveryActivity → currentRevenueAccruedPerResident | context | observations_available_context_only | computed:  |
| publicWorks → capitalExpenditureCommittedPerResident | context | observations_available_context_only | not_computable: paired_period_mismatch |
| securityMissionExpenditurePerResident → socialMissionExpenditurePerResident | context | observations_available_context_only | computed:  |
| cashReceiptsPerResident → cashBalancePerResident | derived_difference | components_reconciled | Non richiesta: dipendenza matematica |
| cashReceiptsPerResident → currentRevenueAccruedPerResident | context | observations_available_context_only | computed:  |
| educationMissionExpenditurePerResident → socialMissionExpenditurePerResident | context | observations_available_context_only | computed:  |
| maleEmploymentRate → employmentGenderGap | derived_difference | components_reconciled | Non richiesta: dipendenza matematica |
| diplomaPlus → employmentRate | context | observations_available_context_only | computed:  |
| singleHouseholds → vacantHomes | context | observations_available_context_only | computed:  |
| localUnits → employeesPerLocalUnit | ratio_component | components_reconciled | Non richiesta: dipendenza matematica |
| localEmployees → employeesPerLocalUnit | shared_numerator | components_reconciled | Non richiesta: dipendenza matematica |
| businessTurnover → turnoverPerPersonEmployed | shared_numerator | components_reconciled | Non richiesta: dipendenza matematica |
| localEmployees → femaleEmploymentRate | context | observations_available_context_only | computed:  |
| localUnits → tourismPresences | context | observations_available_context_only | not_computable: paired_period_mismatch |
| businessValueAdded → income | context | observations_available_context_only | not_computable: paired_period_mismatch |
| population → ageDistribution | ratio_component | components_reconciled | Non richiesta: dipendenza matematica |
| tourismPresences → tourismIntensity | shared_numerator | components_reconciled | Non richiesta: dipendenza matematica |
| population → tourismIntensity | ratio_component | components_reconciled | Non richiesta: dipendenza matematica |
| ageDistribution → elderlyHomeCare | context | observations_available_context_only | not_computable: paired_period_mismatch |
| femaleEmploymentRate → earlyChildhoodPotentialCapacityRate | context | observations_available_context_only | not_computable: paired_frequency_mismatch, paired_period_mismatch |

## Collegamenti companion A3 già governati

Derivati dal contratto esistente e ricontrollati con il suo resolver. Una prova A3 non abilita automaticamente query A6 o confronti fra periodi.

| Indicatore | Riferimenti | Relazione | Dimensioni | Verifica / motivo |
|---|---|---|---|---|
| population | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| populationChange | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| naturalDemographicDynamics | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| internalResidentialMobility | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| foreignResidentialMobility | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| totalResidentialMobility | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| foreignResidents | companionMetricId=ageDistribution | age_breakdown | eta | a3_companion_evidence_verified |
| tourismIntensity | numeratorMetricId=tourismPresences, denominatorMetricId=population | ratio_formula | assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| commuterBalanceRate | numeratorMetricId=commuterBalance, denominatorMetricId=population | ratio_formula | assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| populationChange | companionMetricId=population | series_change_formula | assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| dependencyIndices | companionMetricId=ageDistribution | parts_ratio_formula | eta, assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| inboundCommutersRate | numeratorMetricId=inboundCommuters, denominatorMetricId=population | ratio_formula | assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| outboundCommutersRate | numeratorMetricId=outboundCommuters, denominatorMetricId=population | ratio_formula | assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| tourismBedsPer1000 | numeratorMetricId=tourismBeds, denominatorMetricId=population | ratio_formula | assoluto_normalizzato, numeratore_denominatore | a3_companion_evidence_verified |
| municipalStaffTurnover | companionMetricId=municipalStaffAgeStructure | age_breakdown | eta | a3_companion_evidence_verified |
| municipalStaffTurnover | companionMetricId=municipalStaffAgeStructure | target_fields_ratio_formula | numeratore_denominatore | a3_companion_evidence_verified |
| municipalEmployeesPer1000 | companionMetricId=municipalStaffAgeStructure | age_breakdown | eta | a3_companion_evidence_verified |
| commuterBalance | normalizedMetricId=commuterBalanceRate, denominatorMetricId=population | normalized_companion_formula | assoluto_normalizzato | a3_companion_evidence_verified |
| inboundCommuters | normalizedMetricId=inboundCommutersRate, denominatorMetricId=population | normalized_companion_formula | assoluto_normalizzato | a3_companion_evidence_verified |
| outboundCommuters | normalizedMetricId=outboundCommutersRate, denominatorMetricId=population | normalized_companion_formula | assoluto_normalizzato | a3_companion_evidence_verified |
| internalResidentialMobility | companionMetricId=population | part_count_average_population_formula | numeratore_denominatore | a3_companion_evidence_verified |
| foreignResidentialMobility | companionMetricId=population | part_count_average_population_formula | numeratore_denominatore | a3_companion_evidence_verified |
| totalResidentialMobility | companionMetricId=population | part_count_average_population_formula | numeratore_denominatore | a3_companion_evidence_verified |
| naturalDemographicDynamics | companionMetricId=population | part_count_average_population_formula | numeratore_denominatore | a3_companion_evidence_verified |
| currentPayments | denominatorMetricId=population | canonical_field_ratio_formula | numeratore_denominatore | a3_companion_evidence_verified |
| capitalPayments | denominatorMetricId=population | canonical_field_ratio_formula | numeratore_denominatore | a3_companion_evidence_verified |
| siopePayments | denominatorMetricId=population | canonical_field_ratio_formula | numeratore_denominatore | a3_companion_evidence_verified |
| publicWorks | denominatorMetricId=population | canonical_field_ratio_formula | numeratore_denominatore | a3_companion_evidence_verified |
| population | normalizedMetricId=populationDensity, denominatorMetricId=municipalSurface | normalized_companion_formula | assoluto_normalizzato | a3_companion_evidence_verified |

I gruppi per tema/fonte coprono tutti i nodi, senza generare migliaia di pseudo-relazioni. Nel JSON ogni collegamento esplicito conserva osservazioni, fonti, hash, componenti e periodi. Nessun collegamento causale.

## Opportunità di riuso degli adapter

| Profilo | Indicatori senza adapter | Dimensioni A3 già acquisite su questi indicatori |
|---|---|---|
| regione-toscana-indicatori-comunali | 6 | 12 |
| invalsi-open-dispersione-2025 | 2 | 8 |
| invalsi-open-risultati-2025 | 2 | 8 |
| istat-road-annual | 2 | 7 |
| regione-toscana-biblioteche-annual | 3 | 6 |
| dait-eligendo-irregular | 1 | 6 |
| regione-toscana-infocamere-annual | 1 | 6 |
| agcom-quarterly | 4 | 4 |
| aci-istat-annual | 2 | 4 |
| istat-social-services-annual | 2 | 4 |
| health-ministry-annual | 2 | 3 |
| erp-lucca-annual-balance-sheet | 1 | 3 |
| mef-istat-real-income-annual | 1 | 3 |
| mimit-fuel-daily | 1 | 3 |
| regione-toscana-iternet-448 | 1 | 3 |
| regione-toscana-gtfs-scheduled | 3 | 2 |
| mef-municipal-irpef-annual | 1 | 2 |
| regione-toscana-rsa | 1 | 1 |
| regione-toscana-tourism-annual | 1 | 1 |
| runts-continuous | 1 | 1 |
| percorsi-curated | 5 | 0 |
| mef-municipal-tax-annual | 2 | 0 |
| regione-toscana-pnrr-monthly | 2 | 0 |
| agenzia-entrate-omi-semestral | 1 | 0 |
| istat-commuting-irregular | 1 | 0 |
| pun-continuous | 1 | 0 |

Ordine diagnostico per riuso di dati acquisiti, non priorità politica o stima di costo. Le lacune di acquisizione A3 restano distinte dalle lacune del motore. Nessuna nuova acquisizione, UI o modifica dei dati.
