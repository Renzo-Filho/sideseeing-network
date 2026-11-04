# Historical model implementation checklist

This checklist was moved from `docs/README.md` on 22 September 2026. It records an earlier implementation outline and is not the current completion status. See [current model status](../../STATUS.md).

## Model Implementation Tasks

### São Paulo Model (SP)

1. Data acquisition
    1. Base Support & Geometries
        1. GeoSampa - Municipal Districts (distrito_municipal_v2.gpkg)
        2. GeoSampa - Water Masses (massa_d_agua.gpkg)
    2. Street Network Morphology and Connectivity
        1. GeoSampa - Street Network (SIRGAS_GPKG_logradouronbl.gpkg, classvias.gpkg)
        2. GeoSampa - Overpasses and Bridges (obra_arte.gpkg)
    3. Urban Grain & Block Shapes
        1. GeoSampa - Street Blocks (quadra_viaria_editada.gpkg)
    4. Cadastral Density, Built Area & Land Use
        1. GeoSampa - Lots and Tax Accounts (Lotes/, IPTU_2026.csv)
    5. Building Footprints
        1. Overture Maps (2026-08-19) - Building Morphology (sao_paulo_building_morphology.gpkg)
    6. Socioeconomic and Demographic Data
        1. RAIS (Ministry of Labor) - Formal Employment (rais_empregos_sp_2022.csv)
        2. IBGE (Census 2022) - Population Density (CNEFE_2022/, densidade_demografica.gpkg)
    7. Public Transit
        1. SPTrans - GTFS Bus Data (f-6gy-sptrans-latest/)

2. Feature Engineering and Transformations
    1. Spatial Aggregation
        1. M1-M4, M6 Features (Morphology)
            1. Calculate geometric street length density per km² (M1)
            2. Calculate street intersection density excluding overpasses (M2)
            3. Evaluate block log area (median/IQR) and shape (compactness/elongation) (M3, M4)
            4. Calculate length-weighted composition of road hierarchy (M6)
        2. B1-B3 Features (Buildings)
            1. Calculate physical building footprint land coverage (B1)
            2. Derive cadastral floor count statistics (median, P90) (B2)
            3. Calculate constructed floor-area density (B3)
        3. U1-U4 Features (Urban Functions)
            1. Calculate land-use diversity via count-based Shannon Entropy (U1)
            2. Calculate probabilistically allocated formal workplace job density (U2)
            3. Calculate residential population density (U3)
            4. Calculate population-weighted bus service access within 400m walking distance (U4)
    2. Feature Scaling and Transformation
        1. Apply natural logarithm `ln(x)` or `ln(1+x)` to heavily skewed density/count metrics.
        2. Apply Robust Scaling (Median/IQR) with population standard deviation fallback.
        3. Apply Squared Hellinger distance for compositional share features (M6).

3. Model Application
    1. Distance Computation
        1. Calculate within-family dissimilarity (squared standardized differences).
        2. Apply family calibration (median of positive distances).
        3. Compute primary Euclidean-embeddable distance using equal family weights (1/13).
    2. Robustness and Alternatives
        1. Calculate Regularized Mahalanobis distance (Ledoit-Wolf covariance).
        2. Execute Unwhitened Principal Component Analysis (PCA).
        3. Run leave-one-family-out and weight perturbation scenarios.

4. Output Viz
    1. 96x96 Symmetric Distance Matrix
    2. Top-10 Candidate Review and Rank Tables
    3. Family Contribution Breakdowns and Candidate Profiles
    4. Spatial Maps with Rank and Distance Annotations


### Chicago Model

1. Data acquisition
    1. Base Support & Geometries
        1. Chicago Data Portal - Community Areas Boundaries
        2. CMAP - Hydrography / Land Use proxy for water masks
    2. Street Network
        1. Chicago Data Portal - Street Center Lines
        2. Overture Maps (2026-08-19) - Shared roads and connectors
    3. Building Footprints
        1. Chicago Data Portal - Building Footprints (ACTIVE polygons)
        2. Overture Maps (2026-08-19) - Shared footprints
    4. Land Use and Zoning
        1. CMAP - Land Use Inventory (Polygon-based observed use)
        2. Chicago Data Portal - Zoning Districts
    5. Socioeconomic and Demographic Data
        1. Census - LODES WAC (Workplace employment jobs)
        2. Census - TIGER/Line Geography and 2020 Census block populations
        3. ACS - Community Areas Population estimates
    6. Public Transit
        1. CTA - Static GTFS feed (Bus service schedules and stops)

2. Feature Engineering and Transformations
    1. Spatial Aggregation
        1. M1-M4, M6 Features (Morphology)
            1. Calculate geometric street length density (M1)
            2. Planarize and polygonize local roads to establish experimental blocks (M3, M4)
            3. Classify road hierarchy composition using local taxonomies (M6)
        2. B1-B3 Features (Buildings)
            1. Execute untiled footprint unions to calculate land coverage (B1)
            2. Extract positive stories reports for floor count statistics (median, P90) (B2)
        3. U1-U4 Features (Urban Functions)
            1. Calculate area-based land-use entropy from CMAP categories (U1)
            2. Calculate gross-area population density (U3)
            3. Prepare bus frequency scenarios (400m/800m, weekday/weekend) (U4)
    2. Harmonization & Scaling
        1. Apply the identical SP fitted state (Median/IQR transforms and calibrations) to anchor Chicago data.
        2. Log-transform heavily skewed metrics to match the SP baseline.

3. Model Application
    1. SP-Anchored Distance Calculation
        1. Score Chicago Community Areas using the frozen SP reference scaling.
        2. Calculate cross-city Euclidean-embeddable primary distance.
    2. Sensitivities and Pooled Models
        1. Compute jointly-fitted pooled sensitivities with city-balanced weighting.
        2. Evaluate alternative source scenarios and cross-city grid supports.

4. Output Viz
    1. Cross-city Similarity Rankings (Chicago to Brás)
    2. Explanatory Profiles (Raw and Transformed Candidate Comparisons)
    3. Spatial Maps displaying Harmonization Constraints and Analogues
