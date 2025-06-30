PRODUCT_TOP_K = 10
KNOWLEDGE_TOP_K = 5
same_manufacturer_query = "AND recManufacturer.name_en = baseManufacturer.name_en"
different_manufacturer_query = "AND recManufacturer.name_en <> baseManufacturer.name_en"
vehicle_codes = ["Jeep Wrangler JK",
                "Jeep Wrangler LJ",
                "Jeep Wrangler TJ",
                "Jeep Wrangler JL",
                "Jeep Gladiator JT",
                "Jeep Cherokee XJ",
                "Jeep Grand Cherokee",
                "Jeep CJ5",
                "Jeep Wrangler YJ",
                "Jeep J20",
                "Jeep Cherokee",
                "Jeep Grand Wagoneer",
                "Jeep CJ6",
                "Jeep Commando",
                "Jeep CJ7",
                "Jeep Willys",
                "Jeep Renegade",
                "Jeep Wagoneer",
                "Jeep CJ3",
                "Jeep Commander",
                "Jeep Commander 65th",
                "Jeep Willys Sedan",
                "Jeep CJ5 Golden",
                "Jeep CJ7 Golden",
                "Jeep Cherokee Wide"
            ]