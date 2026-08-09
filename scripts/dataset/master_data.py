"""Human-readable vocabulary for the fictional Peruvian retail company."""

LOCATIONS = (
    ("Lima", "Lima", "LIM"),
    ("Arequipa", "Arequipa", "ARE"),
    ("Trujillo", "La Libertad", "TRU"),
    ("Piura", "Piura", "PIU"),
    ("Cusco", "Cusco", "CUS"),
    ("Chiclayo", "Lambayeque", "CHI"),
    ("Huancayo", "Junin", "HUA"),
)

CATEGORIES = (
    ("Technology", ("Laptop", "Monitor", "Tablet", "Desktop"), (150_000, 500_000)),
    ("Home", ("Lamp", "Chair", "Storage Unit", "Desk"), (8_000, 80_000)),
    ("Office", ("Printer", "Keyboard", "Mouse", "Webcam"), (3_000, 120_000)),
    ("Appliances", ("Blender", "Fan", "Microwave", "Air Fryer"), (12_000, 180_000)),
    ("Gaming", ("Console", "Controller", "Gaming Chair", "Headset"), (8_000, 250_000)),
    ("Audio", ("Speaker", "Soundbar", "Earbuds", "Microphone"), (5_000, 150_000)),
    ("Mobile", ("Smartphone", "Smartwatch", "Charger", "Power Bank"), (4_000, 350_000)),
    ("Accessories", ("Backpack", "Cable", "Adapter", "Phone Case"), (1_500, 45_000)),
    ("Personal Care", ("Hair Dryer", "Trimmer", "Electric Toothbrush", "Scale"), (4_000, 90_000)),
    ("Small Appliances", ("Coffee Maker", "Toaster", "Kettle", "Iron"), (5_000, 100_000)),
    ("Photography", ("Camera", "Tripod", "Lens", "Camera Bag"), (8_000, 300_000)),
    ("Networking", ("Router", "Switch", "Access Point", "Network Cable"), (3_000, 150_000)),
    ("Smart Home", ("Smart Bulb", "Smart Plug", "Doorbell", "Security Camera"), (3_000, 130_000)),
    ("Travel", ("Suitcase", "Travel Adapter", "Neck Pillow", "Luggage Scale"), (2_500, 100_000)),
    ("Sports", ("Fitness Band", "Yoga Mat", "Massage Gun", "Water Bottle"), (2_000, 110_000)),
)

BRAND_NAMES = (
    "Nova", "Vision", "Pulse", "Orion", "Atlas", "Nexa", "Vanta", "Lumina", "Aero", "Vertex",
    "Solara", "Kinetix", "Prisma", "Cobalt", "Helio", "Terralux", "Zenith", "Marea", "Quanta", "Rivon",
    "Arden", "Boreal", "Cirrus", "Dynamo", "Evolve", "Flux", "Glint", "Harbor", "Ion", "Juno",
    "Kora", "Lyra", "Monarch", "Nimble", "Oasis", "Pinnacle", "Quartz", "Radial", "Sierra", "Talon",
    "Umbra", "Verde", "Warden", "Xenon", "Yara", "Zafiro", "Atria", "Brava", "Cenit", "Delta",
    "Eon", "Faro", "Gala", "Horizon", "Indigo", "Jade", "Karma", "Lumen", "Mistral", "Norte",
    "Optima", "Pulsar", "Radian", "Senda", "Triton", "Unison", "Vigor", "Wavelength", "Xira", "Zonda",
)
FIRST_NAMES = ("Ana", "Luis", "Maria", "Diego", "Sofia", "Carlos", "Valeria", "Jorge", "Camila", "Mateo")
LAST_NAMES = ("Quispe", "Flores", "Rojas", "Garcia", "Huaman", "Torres", "Vega", "Paredes", "Salazar", "Mendoza")
SUPPLIER_PREFIXES = ("Andes", "Pacifico", "Inka", "Cordillera", "Sur", "Norte", "Altura", "Cumbre")
SUPPLIER_SUFFIXES = ("Distribuciones", "Comercial", "Abastecimiento", "Importaciones", "Supply")
BUSINESS_PREFIXES = ("Andes", "Grupo Boreal", "Soluciones Vertice", "Pacifico", "Inka", "Cumbre")
BUSINESS_CORES = ("Digital", "Comercial", "Tecnologica", "Logistica", "Integral", "Corporativa")
BUSINESS_SUFFIXES = ("SAC", "Comercial SAC", "Distribuciones SAC")
CUSTOMER_SEGMENTS = (
    (1, "CONSUMER", "Consumer", "Individual retail customers."),
    (2, "SMALL_BUSINESS", "Small Business", "Small and medium business customers."),
    (3, "CORPORATE", "Corporate", "Large corporate customers."),
    (4, "DISTRIBUTOR", "Distributor", "Reseller and distribution partners."),
)
