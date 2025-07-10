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

css = """
.partner-title {
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 14px;
  color: #2c3e50;
}

@media (prefers-color-scheme: dark) {
  .partner-title {
    color: white;
  }
}

.partner-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 16px;
  margin: 12px 0;
  color: #2c3e50 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
  width: 85% !important;
  margin-left: auto;
  margin-right: auto;
}

.partner-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}

.partner-card h3 {
  color: #2c3e50 !important;
  font-size: 16px;
  margin-bottom: 10px;
}

.partner-card p {
  color: #2c3e50 !important;
}

.partner-card a {
  color: #007bff !important;
  text-decoration: underline !important;
}

#chat-input textarea {
    height: 48px !important;
    padding-top: 8px;
    padding-bottom: 8px;
}

#send-btn {
    height: 48px !important;
}
"""