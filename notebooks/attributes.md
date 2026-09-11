# List of attributes

## Chicago
| Type | Variable | Description |
| - | - | - |
| Sociodemographic | per_capita_income | General community wealth |
| Morphological | Street centerlines | Lines representing the center of each street. |
| Morphological | Cook county parcels | Boundaries of each property parcel. |
| Built form | Building footprints | Outlines of each building. |
| Built form | | |
| Built form | | |
| Functional | Active businesses | Locations of active businesses. |
| Functional | Zoning districts | Boundaries of zoning districts. |
| Functional | CMAP Land Use | Land use classification. |
| Functional | ACS Population | Demographic data including population. |
| Transit | CTA L stops | Locations of elevated train stations. |
| Transit | CTA Bus stops | Locations of bus stops. |

### Socioeconomic-Morphological model
#### Morphology
Building coverage ratio
Street-network density
Intersection density
open_and_green_spaces
Land-use mix (zoning)
Functional centrality / activity intensity

#### Socioeconomic
per_capita_income

### Sidewalk model
sidewalk_coverage_ratio


---------------------------


## Socioeconomic-Morphological model
### Morphology

M1 - Street-network density
M2 - Intersection density
M3 - Block-size distribution
M4 - Block-shape distribution (evaluate with M3)
M6 - Street hierarchy
M7 - Parcel Density

(drop M5)

### Built Form

B1 - Building coverage ratio
B2 - Building height / verticality
B3 - Built-form density / Built-volume / FAR proxy

### Typology and Urban Structure

U1 - Land-use mix
U2 - Economic Activity
U3 - Population Density
U4 - Transit Accessibility

(drop U5)