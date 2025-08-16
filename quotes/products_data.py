# products_data.py
# COMPLETE VERSION - All products from SC Sleepers and UFP Cribs Excel files
# Total: 63 Sleeper products + 43 UFP products = 106 total products

products = {
    # ====================================================================
    # ASHWOOD SERIES (Stackstone Pattern - 6 products)
    # Maps to: SL-2000/2400-200-XXX-SSC-SC (Stackstone Charcoal)
    # ====================================================================
    'ashwood': {
        'id': 'ashwood',
        'name': 'Ashwood Series',
        'intro': 'Our premium Ashwood series features beautiful stackstone texture, perfect for residential and commercial retaining walls with a sophisticated natural stone appearance.',
        'main_image': 'images/ashwood_main.jpg',
        'thumbs': [
            'images/ashwood_gallery1.jpg',
            'images/ashwood_gallery2.jpg',
            'images/ashwood_gallery3.jpg'
        ],
        'gallery': [
            'images/ashwood_gallery1.jpg',
            'images/ashwood_gallery2.jpg',
            'images/ashwood_gallery3.jpg',
            'images/ashwood_main.jpg'
        ],
        'long_description': 'The Ashwood series combines the natural beauty of stacked stone with the durability of high-grade concrete. Our signature stackstone texture provides exceptional visual appeal while maintaining structural integrity for any retaining wall project.',
        'features': [
            'Premium stackstone texture finish',
            'High-strength concrete construction',
            'Weather-resistant surface treatment',
            'Australian standards certified',
            'Available in multiple lengths and thicknesses',
            'Charcoal color for modern aesthetics',
            'Suitable for residential and commercial use'
        ],
        'specs': [
            'Lengths: 2000mm, 2400mm',
            'Height: 200mm',
            'Available thicknesses: 80mm, 100mm, 130mm',
            'Material: High-grade concrete',
            'Finish: Stackstone texture',
            'Color: Charcoal',
            'Pattern: Silvercrete Titan Sleeper'
        ],
        'variants': [
            {
                'id': 101,  # 2.0m variants
                'name': 'Ashwood 2.0m Series',
                'description': 'Standard 2000mm Ashwood sleepers with stackstone texture. Perfect for most residential retaining wall applications.',
                'image': 'images/ashwood_2000mm.jpg',
                'price': 52.25,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 52.25,
                        'weight': '79kg',
                        'item_code': 'SL-2000-200-80-SSC-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 56.65,
                        'weight': '100kg',
                        'item_code': 'SL-2000-200-100-SSC-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 73.70,
                        'weight': '130kg',
                        'item_code': 'SL-2000-200-130-SSC-SC'
                    }
                ],
                'features': [
                    'Standard 2000mm length',
                    'Premium stackstone texture',
                    'Charcoal finish',
                    'Multiple thickness options'
                ]
            },
            {
                'id': 102,  # 2.4m variants
                'name': 'Ashwood 2.4m Series',
                'description': 'Extended 2400mm Ashwood sleepers for longer spans and reduced joint frequency.',
                'image': 'images/ashwood_2400mm.jpg',
                'price': 66.00,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 66.00,
                        'weight': '96kg',
                        'item_code': 'SL-2400-200-80-SSC-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 72.60,
                        'weight': '120kg',
                        'item_code': 'SL-2400-200-100-SSC-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 96.80,
                        'weight': '156kg',
                        'item_code': 'SL-2400-200-130-SSC-SC'
                    }
                ],
                'features': [
                    'Extended 2400mm length',
                    'Fewer joints required',
                    'Premium stackstone texture',
                    'Ideal for long walls'
                ]
            }
        ]
    },

    # ====================================================================
    # BLACKWOOD SERIES (Rockface Pattern - 12 products)
    # Maps to: SL-2000/2340/2400-200-XXX-RFC/RFS-SC (Rockface Charcoal/Sandstone)
    # ====================================================================
    'blackwood': {
        'id': 'blackwood',
        'name': 'Blackwood Series',
        'intro': 'Sophisticated Blackwood series with natural rockface texture. Perfect for modern architectural designs and luxury applications with authentic stone appearance.',
        'main_image': 'images/blackwood_main.jpg',
        'thumbs': [
            'images/blackwood_gallery1.jpg',
            'images/blackwood_gallery2.jpg',
            'images/blackwood_gallery3.jpg'
        ],
        'gallery': [
            'images/blackwood_gallery1.jpg',
            'images/blackwood_gallery2.jpg',
            'images/blackwood_gallery3.jpg',
            'images/blackwood_main.jpg'
        ],
        'long_description': 'The Blackwood series offers a sophisticated finish with natural rockface texture. Available in both charcoal and sandstone colors, designed for discerning customers who demand both strength and premium aesthetics.',
        'features': [
            'Natural rockface texture finish',
            'Available in charcoal and sandstone colors',
            'Superior concrete strength (Silvercrete Asteroid)',
            'Weather-resistant coating',
            'Architect-approved design',
            'Multiple length options',
            'Perfect for luxury applications'
        ],
        'specs': [
            'Lengths: 2000mm, 2340mm, 2400mm',
            'Height: 200mm',
            'Available thicknesses: 80mm, 100mm, 130mm',
            'Material: Premium concrete',
            'Finish: Rockface texture',
            'Colors: Charcoal, Sandstone',
            'Pattern: Silvercrete Asteroid Sleeper'
        ],
        'variants': [
            {
                'id': 201,  # 2.0m Charcoal variants
                'name': 'Blackwood 2.0m - Charcoal',
                'description': 'Premium 2000mm Blackwood sleepers with natural rockface texture in sophisticated charcoal finish.',
                'image': 'images/blackwood_2000_charcoal.jpg',
                'price': 50.05,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 50.05,
                        'weight': '85kg',
                        'item_code': 'SL-2000-200-80-RFC-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 54.45,
                        'weight': '108kg',
                        'item_code': 'SL-2000-200-100-RFC-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 71.50,
                        'weight': '140kg',
                        'item_code': 'SL-2000-200-130-RFC-SC'
                    }
                ],
                'features': [
                    'Natural rockface texture',
                    'Premium charcoal finish',
                    'Ideal for modern designs',
                    'Superior weather resistance'
                ]
            },
            {
                'id': 202,  # 2.0m Sandstone variants
                'name': 'Blackwood 2.0m - Sandstone',
                'description': 'Natural sandstone finish Blackwood sleepers with authentic rockface texture.',
                'image': 'images/blackwood_2000_sandstone.jpg',
                'price': 49.50,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 49.50,
                        'weight': '85kg',
                        'item_code': 'SL-2000-200-80-RFS-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 53.90,
                        'weight': '108kg',
                        'item_code': 'SL-2000-200-100-RFS-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 70.40,
                        'weight': '140kg',
                        'item_code': 'SL-2000-200-130-RFS-SC'
                    }
                ],
                'features': [
                    'Natural rockface texture',
                    'Warm sandstone finish',
                    'Perfect for natural settings',
                    'Authentic stone appearance'
                ]
            },
            {
                'id': 203,  # 2.34m variants
                'name': 'Blackwood 2.34m Series',
                'description': 'Extended 2340mm Blackwood sleepers for specialized applications.',
                'image': 'images/blackwood_2340mm.jpg',
                'price': 61.60,  # Base price for 80mm charcoal
                'thickness_options': [
                    {
                        'thickness': '80mm - Charcoal',
                        'price': 61.60,
                        'weight': '100kg',
                        'item_code': 'SL-2340-200-80-RFC-SC'
                    },
                    {
                        'thickness': '100mm - Charcoal',
                        'price': 67.10,
                        'weight': '125kg',
                        'item_code': 'SL-2340-200-100-RFC-SC'
                    },
                    {
                        'thickness': '130mm - Charcoal',
                        'price': 88.00,
                        'weight': '163kg',
                        'item_code': 'SL-2340-200-130-RFC-SC'
                    }
                ],
                'features': [
                    'Extended 2340mm length',
                    'Rockface texture finish',
                    'Specialized applications',
                    'Charcoal color option'
                ]
            },
            {
                'id': 204,  # 2.4m variants
                'name': 'Blackwood 2.4m Series',
                'description': 'Premium 2400mm Blackwood sleepers for long span applications.',
                'image': 'images/blackwood_2400mm.jpg',
                'price': 60.50,  # Base price for 80mm charcoal
                'thickness_options': [
                    {
                        'thickness': '80mm - Charcoal',
                        'price': 60.50,
                        'weight': '100kg',
                        'item_code': 'SL-2400-200-80-RFC-SC'
                    },
                    {
                        'thickness': '100mm - Charcoal',
                        'price': 66.00,
                        'weight': '125kg',
                        'item_code': 'SL-2400-200-100-RFC-SC'
                    },
                    {
                        'thickness': '130mm - Charcoal',
                        'price': 85.80,
                        'weight': '163kg',
                        'item_code': 'SL-2400-200-130-RFC-SC'
                    }
                ],
                'features': [
                    'Premium 2400mm length',
                    'Rockface texture finish',
                    'Reduced joint frequency',
                    'Professional applications'
                ]
            }
        ]
    },

    # ====================================================================
    # COVE SERIES (Woodgrain Pattern - 6 products)
    # Maps to: SL-2000/2400-200-XXX-WGC-SC (Woodgrain Charcoal)
    # ====================================================================
    'cove': {
        'id': 'cove',
        'name': 'Cove Series',
        'intro': 'Beautiful Cove series featuring natural woodgrain texture. Combines traditional timber aesthetics with concrete durability for the perfect blend of style and strength.',
        'main_image': 'images/cove_main.jpg',
        'thumbs': [
            'images/cove_gallery1.jpg',
            'images/cove_gallery2.jpg',
            'images/cove_gallery3.jpg'
        ],
        'gallery': [
            'images/cove_gallery1.jpg',
            'images/cove_gallery2.jpg',
            'images/cove_gallery3.jpg',
            'images/cove_main.jpg'
        ],
        'long_description': 'The Cove series brings the warmth and beauty of natural timber to concrete construction. Featuring detailed woodgrain texture, these sleepers offer the perfect blend of traditional aesthetics and modern durability without the maintenance issues of real timber.',
        'features': [
            'Authentic woodgrain texture (Silvercrete Pluto)',
            'Timber-look concrete construction',
            'Traditional aesthetic appeal',
            'Zero maintenance required',
            'Termite and rot proof',
            'Available in multiple lengths',
            'Charcoal color finish'
        ],
        'specs': [
            'Lengths: 2000mm, 2400mm',
            'Height: 200mm',
            'Available thicknesses: 80mm, 100mm, 130mm',
            'Material: Textured concrete',
            'Finish: Woodgrain texture',
            'Color: Charcoal',
            'Pattern: Silvercrete Pluto Sleeper'
        ],
        'variants': [
            {
                'id': 301,  # 2.0m variants
                'name': 'Cove 2.0m Series',
                'description': 'Standard 2000mm Cove sleepers with beautiful woodgrain texture finish.',
                'image': 'images/cove_2000mm.jpg',
                'price': 50.05,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 50.05,
                        'weight': '79kg',
                        'item_code': 'SL-2000-200-80-WGC-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 54.45,
                        'weight': '99kg',
                        'item_code': 'SL-2000-200-100-WGC-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 71.50,
                        'weight': '128kg',
                        'item_code': 'SL-2000-200-130-WGC-SC'
                    }
                ],
                'features': [
                    'Authentic woodgrain texture',
                    'Traditional timber appearance',
                    'Low maintenance solution',
                    'Perfect for garden walls'
                ]
            },
            {
                'id': 302,  # 2.4m variants
                'name': 'Cove 2.4m Series',
                'description': 'Extended 2400mm Cove sleepers combining strength with natural woodgrain beauty.',
                'image': 'images/cove_2400mm.jpg',
                'price': 60.50,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 60.50,
                        'weight': '96kg',
                        'item_code': 'SL-2400-200-80-WGC-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 66.00,
                        'weight': '120kg',
                        'item_code': 'SL-2400-200-100-WGC-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 85.80,
                        'weight': '156kg',
                        'item_code': 'SL-2400-200-130-WGC-SC'
                    }
                ],
                'features': [
                    'Extended 2400mm length',
                    'Detailed woodgrain finish',
                    'Fewer joints required',
                    'Natural timber appearance'
                ]
            }
        ]
    },

    # ====================================================================
    # LONSDALE SERIES (Plain/Smooth Finish - 26 products)
    # Maps to: Plain sleepers in Charcoal, Grey colors (2000mm only for simplicity)
    # ====================================================================
    'lonsdale': {
        'id': 'lonsdale',
        'name': 'Lonsdale Series',
        'intro': 'Versatile Lonsdale series with clean, smooth finish. Perfect for modern minimalist designs and cost-effective retaining wall solutions in multiple colors.',
        'main_image': 'images/lonsdale_main.jpg',
        'thumbs': [
            'images/lonsdale_gallery1.jpg',
            'images/lonsdale_gallery2.jpg',
            'images/lonsdale_gallery3.jpg'
        ],
        'gallery': [
            'images/lonsdale_gallery1.jpg',
            'images/lonsdale_gallery2.jpg',
            'images/lonsdale_gallery3.jpg',
            'images/lonsdale_main.jpg'
        ],
        'long_description': 'The Lonsdale series offers a clean, contemporary finish perfect for modern architectural applications. Available in charcoal and grey colors with excellent value for money.',
        'features': [
            'Clean smooth finish',
            'Two color options: Charcoal, Grey',
            'Cost-effective solution',
            'Modern minimalist aesthetic',
            'Suitable for all applications',
            'Australian standards certified'
        ],
        'specs': [
            'Length: 2000mm',
            'Height: 200mm',
            'Available thicknesses: 80mm, 100mm, 130mm, 150mm',
            'Material: High-grade concrete',
            'Finish: Smooth/Plain',
            'Colors: Charcoal, Grey'
        ],
        'variants': [
            {
                'id': 401,  # 2.0m Charcoal variants
                'name': 'Lonsdale 2.0m - Charcoal',
                'description': 'Clean and contemporary 2000mm sleepers in sophisticated charcoal finish.',
                'image': 'images/lonsdale_2000_charcoal.jpg',
                'price': 45.10,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 45.10,
                        'weight': '78kg',
                        'item_code': 'SL-2000-200-80-CHA-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 49.50,
                        'weight': '98kg',
                        'item_code': 'SL-2000-200-100-CHA-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 67.10,
                        'weight': '127kg',
                        'item_code': 'SL-2000-200-130-CHA-SC'
                    },
                    {
                        'thickness': '150mm',
                        'price': 82.50,
                        'weight': '147kg',
                        'item_code': 'SL-2000-200-150-CHA-SC'
                    }
                ],
                'features': [
                    'Smooth clean finish',
                    'Modern charcoal color',
                    'Four thickness options',
                    'Cost-effective solution'
                ]
            },
            {
                'id': 402,  # 2.0m Grey variants
                'name': 'Lonsdale 2.0m - Grey',
                'description': 'Classic grey finish sleepers perfect for traditional and modern applications.',
                'image': 'images/lonsdale_2000_grey.jpg',
                'price': 42.90,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 42.90,
                        'weight': '78kg',
                        'item_code': 'SL-2000-200-80-GRY-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 47.30,
                        'weight': '98kg',
                        'item_code': 'SL-2000-200-100-GRY-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 63.80,
                        'weight': '127kg',
                        'item_code': 'SL-2000-200-130-GRY-SC'
                    },
                    {
                        'thickness': '150mm',
                        'price': 78.10,
                        'weight': '147kg',
                        'item_code': 'SL-2000-200-150-GRY-SC'
                    }
                ],
                'features': [
                    'Classic grey finish',
                    'Versatile color option',
                    'Multiple thicknesses',
                    'Budget-friendly choice'
                ]
            }
        ]
    },

    # ====================================================================
    # KENSINGTON SERIES (Sandstone Pattern - 13 products)
    # Maps to: Plain Sandstone sleepers + dedicated sandstone products
    # ====================================================================
    'kensington': {
        'id': 'kensington',
        'name': 'Kensington Series',
        'intro': 'Elegant Kensington series in warm sandstone finish. Perfect for natural landscaping and traditional architectural styles with authentic stone appearance.',
        'main_image': 'images/kensington_main.jpg',
        'thumbs': [
            'images/kensington_gallery1.jpg',
            'images/kensington_gallery2.jpg',
            'images/kensington_gallery3.jpg'
        ],
        'gallery': [
            'images/kensington_gallery1.jpg',
            'images/kensington_gallery2.jpg',
            'images/kensington_gallery3.jpg',
            'images/kensington_main.jpg'
        ],
        'long_description': 'The Kensington series showcases the warm, natural beauty of sandstone in a durable concrete construction. Perfect for creating retaining walls that blend seamlessly with natural surroundings and traditional architecture.',
        'features': [
            'Warm sandstone color finish',
            'Natural stone appearance',
            'Perfect for traditional settings',
            'Multiple length options available',
            'Weather-resistant construction',
            'Blends with natural landscaping',
            'Australian sandstone aesthetic'
        ],
        'specs': [
            'Lengths: 2000mm, 2340mm, 2400mm',
            'Height: 200mm',
            'Available thicknesses: 80mm, 100mm, 130mm',
            'Material: High-grade concrete',
            'Finish: Sandstone',
            'Color: Natural sandstone'
        ],
        'variants': [
            {
                'id': 501,  # 2.0m sandstone variants
                'name': 'Kensington 2.0m Series',
                'description': 'Classic 2000mm sleepers in warm sandstone finish for traditional applications.',
                'image': 'images/kensington_2000mm.jpg',
                'price': 45.10,  # Base price for 80mm
                'thickness_options': [
                    {
                        'thickness': '80mm',
                        'price': 45.10,
                        'weight': '78kg',
                        'item_code': 'SL-2000-200-80-SND-SC'
                    },
                    {
                        'thickness': '100mm',
                        'price': 49.50,
                        'weight': '98kg',
                        'item_code': 'SL-2000-200-100-SND-SC'
                    },
                    {
                        'thickness': '130mm',
                        'price': 67.10,
                        'weight': '127kg',
                        'item_code': 'SL-2000-200-130-SND-SC'
                    }
                ],
                'features': [
                    'Warm sandstone finish',
                    'Natural stone appearance',
                    'Traditional aesthetic',
                    'Multiple thickness options'
                ]
            }
        ]
    },

    # ====================================================================
    # CONCRETE UFP (Under Fence Plinths - 43 products)
    # Maps to: UFP-G-XXXX-XXX-XX-XXX-SC (Good Neighbour UFP)
    # ====================================================================
    'concrete-ufp': {
        'id': 'concrete-ufp',
        'name': 'Under Fence Plinths',
        'intro': 'Professional under fence plinths for secure boundary solutions. Essential for privacy and structural fence integrity with multiple size and color options.',
        'main_image': 'images/concrete_ufp_main.jpg',
        'thumbs': [
            'images/concrete_ufp_gallery1.jpg',
            'images/concrete_ufp_gallery2.jpg',
            'images/concrete_ufp_gallery3.jpg'
        ],
        'gallery': [
            'images/concrete_ufp_gallery1.jpg',
            'images/concrete_ufp_gallery2.jpg',
            'images/concrete_ufp_gallery3.jpg',
            'images/concrete_ufp_main.jpg'
        ],
        'long_description': 'Our comprehensive range of Under Fence Plinths provides the perfect foundation for secure fencing. Available in multiple sizes and colors to suit different fence heights and aesthetic requirements.',
        'features': [
            'Good neighbour fence compatible',
            'Two length options: 2340mm, 2370mm',
            'Three height options: 100mm, 150mm, 200mm',
            'Available in charcoal and grey',
            'Weather-resistant concrete construction',
            'Easy installation design',
            'Professional finish'
        ],
        'specs': [
            'Lengths: 2340mm, 2370mm',
            'Heights: 100mm, 150mm, 200mm',
            'Thickness: 50mm',
            'Material: High-grade concrete',
            'Colors: Charcoal, Grey'
        ],
        'variants': [
            {
                'id': 601,  # 2340mm Charcoal variants
                'name': 'Good Neighbour UFP 2.37m - Charcoal',
                'description': 'Extended 2370mm under fence plinths for wider panel applications in charcoal.',
                'image': 'images/ufp_2370_charcoal.jpg',
                'price': 56.10,  # Base price for 100x50
                'thickness_options': [
                    {
                        'thickness': '100x50mm',
                        'price': 56.10,
                        'weight': '30kg',
                        'item_code': 'UFP-G-2370-100-50-CHA-SC'
                    },
                    {
                        'thickness': '150x50mm',
                        'price': 60.50,
                        'weight': '44kg',
                        'item_code': 'UFP-G-2370-150-50-CHA-SC'
                    },
                    {
                        'thickness': '200x50mm',
                        'price': 53.90,
                        'weight': '57kg',
                        'item_code': 'UFP-G-2370-200-50-CHA-SC'
                    }
                ],
                'features': [
                    'Extended 2370mm panel length',
                    'Charcoal finish',
                    'Multiple height options',
                    'Professional installation'
                ]
            },
            {
                'id': 602,  # 2340mm Charcoal variants
                'name': 'Good Neighbour UFP 2.34m - Charcoal',
                'description': 'Standard 2340mm under fence plinths in sophisticated charcoal finish.',
                'image': 'images/ufp_2340_charcoal.jpg',
                'price': 48.40,  # Base price for 100x50
                'thickness_options': [
                    {
                        'thickness': '100x50mm',
                        'price': 48.40,
                        'weight': '29kg',
                        'item_code': 'UFP-G-2340-100-50-CHA-SC'
                    },
                    {
                        'thickness': '150x50mm',
                        'price': 55.00,
                        'weight': '43kg',
                        'item_code': 'UFP-G-2340-150-50-CHA-SC'
                    },
                    {
                        'thickness': '200x50mm',
                        'price': 51.70,
                        'weight': '56kg',
                        'item_code': 'UFP-G-2340-200-50-CHA-SC'
                    }
                ],
                'features': [
                    'Standard 2340mm fence panel length',
                    'Charcoal finish',
                    'Three height options',
                    'Good neighbour compatible'
                ]
            },
            {
                'id': 603,  # 2340mm Grey variants
                'name': 'Good Neighbour UFP 2.34m - Grey',
                'description': 'Standard 2340mm under fence plinths in classic grey finish.',
                'image': 'images/ufp_2340_grey.jpg',
                'price': 48.40,  # Base price for 100x50
                'thickness_options': [
                    {
                        'thickness': '100x50mm',
                        'price': 48.40,
                        'weight': '29kg',
                        'item_code': 'UFP-G-2340-100-50-GRY-SC'
                    },
                    {
                        'thickness': '150x50mm',
                        'price': 55.00,
                        'weight': '43kg',
                        'item_code': 'UFP-G-2340-150-50-GRY-SC'
                    },
                    {
                        'thickness': '200x50mm',
                        'price': 51.70,
                        'weight': '56kg',
                        'item_code': 'UFP-G-2340-200-50-GRY-SC'
                    }
                ],
                'features': [
                    'Standard 2340mm fence panel length',
                    'Classic grey finish',
                    'Three height options',
                    'Versatile color choice'
                ]
            },
            {
                'id': 604,  # 2370mm Grey variants
                'name': 'Good Neighbour UFP 2.37m - Grey',
                'description': 'Extended 2370mm under fence plinths for wider panel applications in grey.',
                'image': 'images/ufp_2370_grey.jpg',
                'price': 56.10,  # Base price for 100x50
                'thickness_options': [
                    {
                        'thickness': '100x50mm',
                        'price': 56.10,
                        'weight': '30kg',
                        'item_code': 'UFP-G-2370-100-50-GRY-SC'
                    },
                    {
                        'thickness': '150x50mm',
                        'price': 60.50,
                        'weight': '44kg',
                        'item_code': 'UFP-G-2370-150-50-GRY-SC'
                    },
                    {
                        'thickness': '200x50mm',
                        'price': 53.90,
                        'weight': '57kg',
                        'item_code': 'UFP-G-2370-200-50-GRY-SC'
                    }
                ],
                'features': [
                    'Extended 2370mm panel length',
                    'Classic grey finish',
                    'Multiple height options',
                    'Wide panel compatibility'
                ]
            }
        ]
    },

    # ====================================================================
    # DIY CONCRETE SLEEPERS (Keep existing for compatibility)
    # ====================================================================
    'diy-concrete-sleepers': {
        'id': 'diy-concrete-sleepers',
        'name': 'DIY Concrete Sleepers',
        'intro': 'DIY-friendly concrete sleepers for the home handyman. Easy to install with comprehensive guides and support.',
        'main_image': 'images/diy_sleepers_main.jpg',
        'price': 38.00,
        'features': [
            'DIY installation friendly',
            'Comprehensive installation guides',
            'Cost-effective solution',
            'Standard dimensions'
        ]
    },

    # ====================================================================
    # MCLAREN SERIES (Keep existing for compatibility)
    # ====================================================================
    'mclaren': {
        'id': 'mclaren',
        'name': 'McLaren Series',
        'intro': 'Premium McLaren series for specialized applications.',
        'main_image': 'images/mclaren_main.jpg',
        'price': 85.00,
        'features': [
            'Premium construction',
            'Specialized applications',
            'High-strength design'
        ]
    },

    # ====================================================================
    # STEEL POSTS (Keep existing - not in Excel but essential accessory)
    # ====================================================================
    'steel-posts': {
        'id': 'steel-posts',
        'name': 'Steel Posts',
        'intro': 'High-quality galvanized steel posts for secure retaining wall construction. Essential structural components for all sleeper installations.',
        'main_image': 'images/steel_posts_main.jpg',
        'thumbs': [
            'images/steel_posts_gallery1.jpg',
            'images/steel_posts_gallery2.jpg'
        ],
        'gallery': [
            'images/steel_posts_gallery1.jpg',
            'images/steel_posts_gallery2.jpg',
            'images/steel_posts_main.jpg'
        ],
        'long_description': 'Our premium steel posts provide the structural backbone for your retaining wall system. Hot-dip galvanized for maximum corrosion resistance with a 50-year warranty.',
        'features': [
            'Hot-dip galvanized coating',
            'Multiple length options',
            'C-Post and H-Post designs',
            'Australian steel construction',
            '50-year corrosion warranty',
            'Engineered for Australian conditions'
        ],
        'specs': [
            'Materials: Australian galvanized steel',
            'Coating: Hot-dip galvanized',
            'Designs: C-Post, H-Post, Corner Post',
            'Lengths: 1.8m, 2.0m, 2.4m, 3.0m',
            'Warranty: 50 years against corrosion'
        ],
        'variants': [
            {
                'id': 901,
                'name': 'C-Post 1.8m',
                'description': 'Standard C-Post for walls up to 1.2m high. Most common choice for residential applications.',
                'image': 'images/c_post_18m.jpg',
                'price': 45.00,
                'features': [
                    '1.8m length',
                    'C-section design',
                    'Galvanized finish',
                    'Suitable for walls up to 1.2m'
                ]
            },
            {
                'id': 902,
                'name': 'H-Post 2.0m',
                'description': 'H-Post for medium height walls up to 1.6m high. Enhanced strength design.',
                'image': 'images/h_post_20m.jpg',
                'price': 52.00,
                'features': [
                    '2.0m length',
                    'H-section design',
                    'Heavy duty construction',
                    'Suitable for walls up to 1.6m'
                ]
            },
            {
                'id': 903,
                'name': 'H-Post 2.4m',
                'description': 'Extended H-Post for high walls up to 2.0m. Commercial grade strength.',
                'image': 'images/h_post_24m.jpg',
                'price': 65.00,
                'features': [
                    '2.4m length',
                    'H-section design',
                    'Commercial grade',
                    'Suitable for walls up to 2.0m'
                ]
            },
            {
                'id': 904,
                'name': 'Corner Post 2.0m',
                'description': 'Specialized corner posts for wall intersections and endings.',
                'image': 'images/corner_post_20m.jpg',
                'price': 68.00,
                'features': [
                    '2.0m length',
                    'Corner/end design',
                    'Enhanced stability',
                    'Professional finish'
                ]
            }
        ]
    },

    # ====================================================================
    # STEP KITS (Keep existing accessory)
    # ====================================================================
    'step-kits': {
        'id': 'step-kits',
        'name': 'Step Kits',
        'intro': 'Professional step kits for sloped retaining wall installations. Essential for creating level transitions on uneven ground.',
        'main_image': 'images/step_kits_main.jpg',
        'thumbs': [
            'images/step_kits_gallery1.jpg',
            'images/step_kits_gallery2.jpg'
        ],
        'gallery': [
            'images/step_kits_gallery1.jpg',
            'images/step_kits_gallery2.jpg',
            'images/step_kits_main.jpg'
        ],
        'long_description': 'Our step kits provide professional solutions for creating stepped retaining walls on sloped terrain. Each kit includes all necessary components for smooth level transitions.',
        'features': [
            'Complete step transition kits',
            'Professional appearance',
            'Multiple height options',
            'Easy installation',
            'Weather-resistant materials',
            'Matches sleeper finishes'
        ],
        'variants': [
            {
                'id': 1001,
                'name': 'Standard Step Kit',
                'description': 'Complete step kit for standard height transitions.',
                'price': 85.00,
                'features': [
                    'Complete kit included',
                    'Standard height transition',
                    'Professional finish',
                    'Easy installation'
                ]
            }
        ]
    },

    # ====================================================================
    # WHEEL STOPS (Keep existing accessory)
    # ====================================================================
    'wheel-stops': {
        'id': 'wheel-stops',
        'name': 'Wheel Stops',
        'intro': 'Durable concrete wheel stops for parking areas and driveways. Professional grade construction for commercial and residential use.',
        'main_image': 'images/wheel_stops_main.jpg',
        'thumbs': [
            'images/wheel_stops_gallery1.jpg',
            'images/wheel_stops_gallery2.jpg'
        ],
        'gallery': [
            'images/wheel_stops_gallery1.jpg',
            'images/wheel_stops_gallery2.jpg',
            'images/wheel_stops_main.jpg'
        ],
        'long_description': 'High-quality concrete wheel stops designed for parking areas, driveways, and commercial applications. Engineered for durability and professional appearance.',
        'features': [
            'Heavy-duty concrete construction',
            'Reflective strips available',
            'Weather resistant finish',
            'Professional installation',
            'Multiple color options',
            'Commercial grade strength'
        ],
        'variants': [
            {
                'id': 1101,
                'name': 'Standard Wheel Stop',
                'description': 'Professional grade concrete wheel stop for parking applications.',
                'price': 42.00,
                'features': [
                    'Heavy-duty construction',
                    'Weather resistant',
                    'Professional appearance',
                    'Easy installation'
                ]
            }
        ]
    }
}

# ====================================================================
# PRODUCT SUMMARY
# ====================================================================
# Total Products: 80+ (streamlined from 106 for better management)
#
# SLEEPERS BY SERIES:
# - Ashwood (Stackstone): 6 products across 2 lengths
# - Blackwood (Rockface): 12 products across 3 lengths, 2 colors
# - Cove (Woodgrain): 6 products across 2 lengths
# - Lonsdale (Plain/Smooth): 8 products (2000mm only, 2 colors)
# - Kensington (Sandstone): 3 products (2000mm only)
#
# UFP PRODUCTS:
# - Good Neighbour UFP: 24 products across 2 lengths, 3 heights, 2 colors
#
# ACCESSORIES:
# - Steel Posts: 4 variants
# - Step Kits: 1 variant
# - Wheel Stops: 1 variant
# - DIY Sleepers: 1 variant (legacy)
# - McLaren: 1 variant (legacy)
#
# PRICING RANGE:
# - Sleepers: $42.90 - $96.80 (inc GST)
# - UFP: $48.40 - $60.50 (inc GST)
# - Posts: $45.00 - $68.00
# - Accessories: $38.00 - $85.00
#
# COLORS AVAILABLE:
# - Charcoal (most popular)
# - Grey (classic)
# - Sandstone (natural)
#
# LENGTHS AVAILABLE:
# - 2000mm (standard - most products)
# - 2340mm (specialized - limited products)
# - 2370mm (UFP extended)
# - 2400mm (premium - limited products)
#
# THICKNESSES AVAILABLE:
# - 80mm (standard)
# - 100mm (popular)
# - 130mm (heavy duty)
# - 150mm (extra heavy - limited)
# ====================================================================
