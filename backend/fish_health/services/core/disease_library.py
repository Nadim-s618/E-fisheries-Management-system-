DEFAULT_DISEASES = [
    {
        'name': 'Bacterial Gill Disease',
        'species': [],
        'symptoms': [
            'gasping at surface',
            'rapid gill movement',
            'pale gills',
            'lethargy',
            'reduced feeding',
        ],
        'description': 'A bacterial infection that damages gill tissue and reduces oxygen exchange.',
        'risk_level': 'High',
        'recommended_treatments': [
            'Improve aeration immediately.',
            'Reduce feeding for 24 to 48 hours.',
            'Consult an aquaculture specialist for approved antibacterial treatment.',
        ],
        'prevention': [
            'Keep dissolved oxygen stable.',
            'Avoid overcrowding.',
            'Remove organic waste regularly.',
        ],
        'environmental_triggers': ['low dissolved oxygen', 'high ammonia', 'high organic load'],
    },
    {
        'name': 'Ich or White Spot Disease',
        'species': [],
        'symptoms': [
            'white spots',
            'rubbing body',
            'scratching',
            'flashing',
            'clamped fins',
            'reduced feeding',
        ],
        'description': 'A parasitic infection recognized by white cyst-like spots and rubbing behavior.',
        'risk_level': 'High',
        'recommended_treatments': [
            'Isolate visibly affected fish where possible.',
            'Raise salinity or temperature only under species-safe guidance.',
            'Use an approved anti-parasitic treatment after confirming diagnosis.',
        ],
        'prevention': [
            'Quarantine new stock.',
            'Avoid sudden temperature changes.',
            'Disinfect equipment between ponds.',
        ],
        'environmental_triggers': ['temperature fluctuation', 'stress', 'new stocking'],
    },
    {
        'name': 'Fin Rot',
        'species': [],
        'symptoms': [
            'frayed fins',
            'ragged tail',
            'red fin edges',
            'lethargy',
            'loss of appetite',
        ],
        'description': 'A bacterial condition where fins or tails deteriorate, often after stress or injury.',
        'risk_level': 'Moderate',
        'recommended_treatments': [
            'Improve water quality and remove injured fish if needed.',
            'Apply approved antibacterial treatment when fin damage progresses.',
            'Reduce handling and crowding stress.',
        ],
        'prevention': [
            'Maintain clean water.',
            'Avoid sharp pond equipment.',
            'Keep stocking density within capacity.',
        ],
        'environmental_triggers': ['poor water quality', 'crowding', 'injury'],
    },
    {
        'name': 'Columnaris',
        'species': [],
        'symptoms': [
            'cotton like patches',
            'mouth fungus',
            'skin ulcers',
            'frayed fins',
            'rapid breathing',
        ],
        'description': 'A fast-moving bacterial disease that can look like fungal growth around mouth, gills, or skin.',
        'risk_level': 'Critical',
        'recommended_treatments': [
            'Separate heavily affected fish if possible.',
            'Increase aeration and reduce feeding.',
            'Seek rapid diagnosis and approved antibacterial treatment.',
        ],
        'prevention': [
            'Avoid overcrowding.',
            'Minimize transport and handling stress.',
            'Keep ammonia and nitrite low.',
        ],
        'environmental_triggers': ['warm water', 'high ammonia', 'stress'],
    },
    {
        'name': 'Fungal Infection',
        'species': [],
        'symptoms': [
            'cotton like growth',
            'white fuzzy patches',
            'skin wound',
            'eggs fungus',
            'lethargy',
        ],
        'description': 'A fungal growth that often appears on damaged skin, eggs, or weakened fish.',
        'risk_level': 'Moderate',
        'recommended_treatments': [
            'Remove dead fish and organic debris.',
            'Improve water exchange and aeration.',
            'Use an approved antifungal treatment after confirming the issue.',
        ],
        'prevention': [
            'Handle fish gently.',
            'Remove dead eggs or fish quickly.',
            'Keep water clean and stable.',
        ],
        'environmental_triggers': ['skin injury', 'organic waste', 'poor water quality'],
    },
    {
        'name': 'Ammonia Poisoning',
        'species': [],
        'symptoms': [
            'red gills',
            'gasping at surface',
            'erratic swimming',
            'lethargy',
            'sudden death',
        ],
        'description': 'A toxic water condition that burns gill tissue and can cause rapid losses.',
        'risk_level': 'Critical',
        'recommended_treatments': [
            'Stop feeding temporarily.',
            'Increase aeration.',
            'Perform a partial water exchange if safe for the pond.',
            'Retest ammonia and pH before restarting full feeding.',
        ],
        'prevention': [
            'Avoid overfeeding.',
            'Remove sludge and excess organic matter.',
            'Monitor ammonia after rain, heat, or heavy feeding.',
        ],
        'environmental_triggers': ['high ammonia', 'high pH', 'overfeeding'],
    },
    {
        'name': 'Oxygen Stress',
        'species': [],
        'symptoms': [
            'gasping at surface',
            'crowding near inlet',
            'slow movement',
            'morning mortality',
            'reduced feeding',
        ],
        'description': 'A stress condition caused by low dissolved oxygen, often worst before sunrise.',
        'risk_level': 'High',
        'recommended_treatments': [
            'Start aeration immediately.',
            'Stop feeding until fish behavior normalizes.',
            'Check dissolved oxygen in early morning.',
        ],
        'prevention': [
            'Maintain emergency aeration.',
            'Avoid heavy night feeding.',
            'Watch oxygen risk after cloudy or rainy days.',
        ],
        'environmental_triggers': ['low dissolved oxygen', 'cloudy weather', 'heavy biomass'],
    },
    {
        'name': 'Anchor Worm',
        'species': [],
        'symptoms': [
            'visible worms',
            'red sores',
            'rubbing body',
            'flashing',
            'skin inflammation',
        ],
        'description': 'An external parasite that attaches to fish and leaves inflamed wounds.',
        'risk_level': 'Moderate',
        'recommended_treatments': [
            'Confirm parasite visually before treatment.',
            'Use an approved pond-safe parasiticide.',
            'Monitor secondary bacterial infection around wounds.',
        ],
        'prevention': [
            'Quarantine new fish.',
            'Avoid moving equipment between ponds without disinfection.',
            'Inspect fish during sampling.',
        ],
        'environmental_triggers': ['new stocking', 'shared equipment', 'stress'],
    },
]


DISEASE_TREATMENT_GUIDES = {
    'Bacterial Gill Disease': {
        'treatment_protocols': [
            {
                'medicine': 'Aquaculture-approved broad-spectrum antibacterial treatment',
                'dosage': 'Use label dose based on pond volume; confirm with fisheries officer before applying antibiotics.',
                'duration': '3 to 5 days, then reassess gill color and breathing.',
                'estimated_cost': 'Medium to high; depends on pond volume and medicine brand.',
                'maintenance': 'Increase aeration, stop feeding for 24 hours, remove sludge and organic waste.',
            },
            {
                'medicine': 'Salt support bath or pond salinity adjustment where species-safe',
                'dosage': 'Use only species-safe salinity guidance; avoid sudden salinity changes.',
                'duration': 'Short supportive use during acute stress.',
                'estimated_cost': 'Low to medium.',
                'maintenance': 'Monitor dissolved oxygen and ammonia twice daily during recovery.',
            },
        ],
        'maintenance_actions': [
            'Run aeration continuously until breathing normalizes.',
            'Retest dissolved oxygen, ammonia, nitrite, and pH before restarting full feed.',
            'Remove dead or severely weak fish quickly to reduce bacterial load.',
        ],
    },
    'Ich or White Spot Disease': {
        'treatment_protocols': [
            {
                'medicine': 'Approved anti-parasitic treatment for Ich',
                'dosage': 'Follow product label by pond volume; repeat according to parasite life cycle guidance.',
                'duration': '5 to 7 days or as product label requires.',
                'estimated_cost': 'Medium; depends on pond volume.',
                'maintenance': 'Increase aeration and avoid water-quality shock during treatment.',
            },
            {
                'medicine': 'Non-iodized salt support where species-safe',
                'dosage': 'Apply only within safe salinity limits for the stocked species.',
                'duration': 'Short supportive use while anti-parasitic treatment works.',
                'estimated_cost': 'Low.',
                'maintenance': 'Inspect fish daily for reduced flashing and fewer white spots.',
            },
        ],
        'maintenance_actions': [
            'Quarantine new fish before adding to the pond.',
            'Disinfect nets and sampling equipment between ponds.',
            'Avoid sudden temperature changes during treatment.',
        ],
    },
    'Fin Rot': {
        'treatment_protocols': [
            {
                'medicine': 'Approved antibacterial treatment if fin damage is spreading',
                'dosage': 'Use label dose based on pond volume after confirming bacterial infection.',
                'duration': '3 to 5 days, then review fin edges and appetite.',
                'estimated_cost': 'Medium.',
                'maintenance': 'Improve water quality and reduce crowding stress.',
            },
            {
                'medicine': 'Water quality correction and wound-support care',
                'dosage': 'No medicine when mild; prioritize clean water, aeration, and reduced handling.',
                'duration': 'Observe for 3 days before escalating.',
                'estimated_cost': 'Low.',
                'maintenance': 'Remove sharp objects and reduce sampling stress.',
            },
        ],
        'maintenance_actions': [
            'Retest ammonia and nitrite.',
            'Remove injured fish for observation if practical.',
            'Keep feeding moderate until appetite and behavior improve.',
        ],
    },
    'Columnaris': {
        'treatment_protocols': [
            {
                'medicine': 'Urgent approved antibacterial treatment',
                'dosage': 'Use veterinarian or fisheries-officer guidance; wrong dosing can cause fast losses.',
                'duration': 'Start immediately after confirmation; reassess within 24 hours.',
                'estimated_cost': 'High for large ponds.',
                'maintenance': 'Increase aeration, reduce feeding, and remove dead fish immediately.',
            },
        ],
        'maintenance_actions': [
            'Separate heavily affected fish where possible.',
            'Keep ammonia and nitrite near zero.',
            'Avoid netting or transport stress during outbreak.',
        ],
    },
    'Fungal Infection': {
        'treatment_protocols': [
            {
                'medicine': 'Approved antifungal pond treatment',
                'dosage': 'Use product label by water volume after confirming fungal growth.',
                'duration': '3 to 5 days or label schedule.',
                'estimated_cost': 'Medium.',
                'maintenance': 'Remove dead fish, dead eggs, and organic debris.',
            },
            {
                'medicine': 'Salt support where species-safe',
                'dosage': 'Use only safe salinity levels for the species.',
                'duration': 'Short supportive use.',
                'estimated_cost': 'Low.',
                'maintenance': 'Improve water exchange and reduce organic load.',
            },
        ],
        'maintenance_actions': [
            'Handle fish gently to prevent skin damage.',
            'Remove decaying material daily during outbreak.',
            'Watch wounds for secondary bacterial infection.',
        ],
    },
    'Ammonia Poisoning': {
        'treatment_protocols': [
            {
                'medicine': 'No primary medicine; emergency water-quality correction',
                'dosage': 'Stop feeding, increase aeration, and perform partial water exchange if safe.',
                'duration': 'Immediate correction, then retest every 6 to 12 hours.',
                'estimated_cost': 'Low to medium; mainly water exchange, aeration, and testing cost.',
                'maintenance': 'Remove sludge and uneaten feed; restart feeding gradually.',
            },
            {
                'medicine': 'Zeolite or approved ammonia binder',
                'dosage': 'Use label dose by pond volume and ammonia level.',
                'duration': 'Short emergency use until ammonia stabilizes.',
                'estimated_cost': 'Medium.',
                'maintenance': 'Retest ammonia and pH after application.',
            },
        ],
        'maintenance_actions': [
            'Stop feeding until ammonia drops.',
            'Retest ammonia, pH, nitrite, and dissolved oxygen.',
            'Review feeding amount and pond sludge management.',
        ],
    },
    'Oxygen Stress': {
        'treatment_protocols': [
            {
                'medicine': 'No medicine; emergency aeration and oxygen recovery',
                'dosage': 'Run aerators continuously; add emergency oxygen support if available.',
                'duration': 'Until fish stop surfacing and early-morning dissolved oxygen is safe.',
                'estimated_cost': 'Low to medium; fuel or electricity cost for aeration.',
                'maintenance': 'Stop feeding and remove organic waste pressure.',
            },
        ],
        'maintenance_actions': [
            'Check dissolved oxygen before sunrise.',
            'Reduce night feeding and heavy organic load.',
            'Prepare backup aeration for cloudy or rainy weather.',
        ],
    },
    'Anchor Worm': {
        'treatment_protocols': [
            {
                'medicine': 'Approved pond-safe parasiticide for crustacean parasites',
                'dosage': 'Use product label by pond volume; repeat if label requires to target life cycle.',
                'duration': 'Usually repeated treatment cycle; follow product schedule.',
                'estimated_cost': 'Medium to high.',
                'maintenance': 'Monitor wounds for secondary infection.',
            },
        ],
        'maintenance_actions': [
            'Quarantine new stock.',
            'Disinfect nets and shared equipment.',
            'Inspect sampled fish for remaining parasites after treatment.',
        ],
    },
}
