ROUTES = [
    {
        "route_name": "Patagonia W Trek",
        "region": "Torres del Paine National Park, Chile",
        "difficulty": "Hard",
        "duration_days": 5,
        "distance_km": 80,
        "elevation_gain_m": 1500,
        "max_elevation_m": 1200,
        "base_elevation_m": 50,   # Lake Pehoe / Pudeto dock
        "highlights": "Grey Glacier, French Valley, Torres Towers, Lake Pehoe",
        "best_season": "October to April",
        "climate": "Cold/Mountain",
        "remoteness": "High",
        "permit_required": True,
        "transport_complexity": "Moderate",
        "description": (
            "The Patagonia W Trek is a world-famous multi-day trail through Torres del Paine. "
            "It includes challenging terrain, unpredictable weather, and iconic views of glaciers, lakes, and granite towers. "
            "Hikers should be prepared for long daily hiking segments and rugged mountain conditions."
        ),
        "recommended_nights": 4,
        "recommended_activities": [
            "Glacier viewpoints",
            "Valleys and lakeside hiking",
            "Alpine trail sections",
        ],
        "route_type": "Point-to-point",
        "recommended_fitness_level": "Advanced",
        "lat": -51.03,
        "lon": -73.05,
        "image_url": None,
    },
    {
        "route_name": "Tour du Mont Blanc",
        "region": "Chamonix, France / Courmayeur, Italy / Champex, Switzerland",
        "difficulty": "Hard",
        "duration_days": 11,
        "distance_km": 170,
        "elevation_gain_m": 10000,
        "max_elevation_m": 2665,
        "base_elevation_m": 1035,  # Chamonix trailhead
        "highlights": "Mont Blanc massif, Chamonix valley, alpine refuges, glacier views",
        "best_season": "June to September",
        "climate": "Cold/Mountain",
        "remoteness": "Moderate",
        "permit_required": False,
        "transport_complexity": "Moderate",
        "description": (
            "The Tour du Mont Blanc is a classic long-distance trek circumnavigating the Mont Blanc massif "
            "through France, Italy, and Switzerland. The route crosses multiple high alpine passes and offers "
            "spectacular views of glaciers and peaks above 4,000 m. A network of mountain refuges makes "
            "logistics manageable, but daily elevation gain demands good fitness."
        ),
        "recommended_nights": 10,
        "recommended_activities": [
            "High alpine pass crossings",
            "Glacier viewpoints",
            "Mountain refuge stays",
            "Three-country border crossing",
        ],
        "route_type": "Loop",
        "recommended_fitness_level": "Advanced",
        "lat": 45.9237,
        "lon": 6.8694,
        "image_url": None,
    },
    {
        "route_name": "Milford Track",
        "region": "Fiordland National Park, New Zealand",
        "difficulty": "Moderate",
        "duration_days": 4,
        "distance_km": 53,
        "elevation_gain_m": 1150,
        "max_elevation_m": 1154,
        "base_elevation_m": 200,   # Te Anau Downs boat ramp
        "highlights": "Mackinnon Pass, Sutherland Falls, Clinton and Arthur valleys, fiord scenery",
        "best_season": "October to April",
        "climate": "Temperate",
        "remoteness": "High",
        "permit_required": True,
        "transport_complexity": "Moderate",
        "description": (
            "Known as 'the finest walk in the world', the Milford Track winds through the heart of Fiordland. "
            "Hikers pass through ancient beech forest, glacier-carved valleys, and over the dramatic Mackinnon Pass. "
            "The route is strictly permit-controlled with hut-to-hut travel; independent walkers must book months ahead. "
            "Rainfall is heavy and unpredictable year-round."
        ),
        "recommended_nights": 3,
        "recommended_activities": [
            "Mackinnon Pass crossing",
            "Sutherland Falls side trip",
            "Fiordland rainforest",
            "Glacier-carved valley walking",
        ],
        "route_type": "Point-to-point",
        "recommended_fitness_level": "Intermediate",
        "lat": -44.667,
        "lon": 167.927,
        "image_url": None,
    },
    {
        "route_name": "Inca Trail",
        "region": "Cusco Region, Peru",
        "difficulty": "Hard",
        "duration_days": 4,
        "distance_km": 43,
        "elevation_gain_m": 1200,
        "max_elevation_m": 4215,
        "base_elevation_m": 2650,  # KM 82 trailhead on the Urubamba river
        "highlights": "Dead Woman's Pass, Inca ruins, cloud forest, Sun Gate, Machu Picchu",
        "best_season": "May to September",
        "climate": "Cold/Mountain",
        "remoteness": "Moderate",
        "permit_required": True,
        "transport_complexity": "High",
        "description": (
            "The Classic Inca Trail is a four-day trek through the Andes to Machu Picchu, passing Inca ruins, "
            "cloud forest, and alpine tundra. The route crosses three high mountain passes, peaking at Dead "
            "Woman's Pass (4,215 m). Altitude acclimatisation in Cusco is essential before attempting the trail. "
            "Permits are strictly limited and sell out months in advance."
        ),
        "recommended_nights": 3,
        "recommended_activities": [
            "Dead Woman's Pass summit",
            "Inca ruin sites along the trail",
            "Cloud forest wildlife",
            "Sun Gate sunrise over Machu Picchu",
        ],
        "route_type": "Point-to-point",
        "recommended_fitness_level": "Advanced",
        "lat": -13.163,
        "lon": -72.545,
        "image_url": None,
    },
    {
        "route_name": "Camino Francés",
        "region": "Pyrenees to Santiago de Compostela, Spain",
        "difficulty": "Moderate",
        "duration_days": 30,
        "distance_km": 780,
        "elevation_gain_m": 12500,
        "max_elevation_m": 1450,
        "base_elevation_m": 163,   # St Jean Pied de Port
        "highlights": "Pyrenean crossing, Pamplona, Burgos cathedral, Meseta plateau, Santiago de Compostela",
        "best_season": "April to June, September to October",
        "climate": "Temperate",
        "remoteness": "Low",
        "permit_required": False,
        "transport_complexity": "Low",
        "description": (
            "The Camino Francés is the most popular route of the Camino de Santiago pilgrimage, running 780 km "
            "from Saint-Jean-Pied-de-Port in France to Santiago de Compostela in Galicia. The trail crosses the "
            "Pyrenees, the Meseta plateau, and the green hills of Galicia. A dense network of pilgrim hostels "
            "(albergues) makes logistics straightforward, and the route is well-marked throughout."
        ),
        "recommended_nights": 29,
        "recommended_activities": [
            "Pyrenean crossing on Day 1",
            "Medieval towns and cathedrals",
            "Meseta plateau walking",
            "Pilgrim community and culture",
        ],
        "route_type": "Point-to-point",
        "recommended_fitness_level": "Intermediate",
        "lat": 42.8805,
        "lon": -8.5457,
        "image_url": None,
    },
]


def get_route_by_name(route_name):
    return next((route for route in ROUTES if route["route_name"] == route_name), None)
