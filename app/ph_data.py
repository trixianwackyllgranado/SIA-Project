"""Philippine-flavored word lists for the fake data generator.

All companies are invented. Mobile prefixes are real network prefixes, but
every generated number is random and fake.
"""

MALE_FIRST_NAMES = (
    "Juan", "Jose", "Mark", "John Paul", "Christian", "Angelo", "Carlo", "Miguel",
    "Rafael", "Gabriel", "Paolo", "Joshua", "Kevin", "Bryan", "Jerome", "Ramon",
    "Antonio", "Emmanuel", "Francis", "Renz", "Kyle", "Adrian", "Vincent", "Arnel",
    "Rodel", "Jericho", "Nathaniel", "Luis", "Daniel", "Patrick", "Eduardo", "Rommel",
)

FEMALE_FIRST_NAMES = (
    "Maria", "Ana", "Kristine", "Angelica", "Jasmine", "Nicole", "Patricia", "Camille",
    "Bea", "Andrea", "Princess", "Mary Grace", "Joy", "Rica", "Sofia", "Isabel",
    "Lorna", "Carmela", "Erika", "Danica", "Shaira", "Bianca", "Hazel", "Rowena",
    "Trisha", "Liza", "Cristina", "Janelle", "Mae", "Regina", "Abigail", "Leah",
)

LAST_NAMES = (
    "Dela Cruz", "Santos", "Reyes", "Garcia", "Mendoza", "Bautista", "Villanueva",
    "Ramos", "Aquino", "Castillo", "Flores", "Gonzales", "Torres", "Navarro",
    "Mercado", "Aguilar", "Domingo", "Pascual", "Salazar", "Soriano", "Manalo",
    "Ocampo", "Valdez", "Rivera", "Lopez", "Fernandez", "Ibañez", "Macaraeg",
    "Dizon", "Panganiban", "Tolentino", "De Guzman", "Cabrera", "Magbanua",
)

STREETS = (
    "Rizal", "Mabini", "Bonifacio", "Luna", "Burgos", "Del Pilar", "Quezon",
    "Aguinaldo", "Sampaguita", "Narra", "Molave", "Acacia", "Kamagong", "Ilang-Ilang",
    "Jasmin", "Mango", "Kalayaan", "Maginhawa", "Katipunan", "Magsaysay",
)

BARANGAYS = (
    "San Isidro", "San Roque", "Santo Niño", "Poblacion", "San Antonio", "Bagong Silang",
    "Malanday", "Sta. Cruz", "San Jose", "Bagumbayan", "Maligaya", "Pag-asa",
    "Mabuhay", "San Miguel", "Holy Spirit", "Commonwealth", "Payatas", "Batasan Hills",
)

# (city, province or region)
CITIES = (
    ("Quezon City", "Metro Manila"),
    ("Manila", "Metro Manila"),
    ("Makati", "Metro Manila"),
    ("Pasig", "Metro Manila"),
    ("Taguig", "Metro Manila"),
    ("Caloocan", "Metro Manila"),
    ("Marikina", "Metro Manila"),
    ("Antipolo", "Rizal"),
    ("Bacoor", "Cavite"),
    ("Dasmariñas", "Cavite"),
    ("Calamba", "Laguna"),
    ("Santa Rosa", "Laguna"),
    ("Batangas City", "Batangas"),
    ("Malolos", "Bulacan"),
    ("San Fernando", "Pampanga"),
    ("Angeles", "Pampanga"),
    ("Baguio", "Benguet"),
    ("Dagupan", "Pangasinan"),
    ("Naga", "Camarines Sur"),
    ("Iloilo City", "Iloilo"),
    ("Bacolod", "Negros Occidental"),
    ("Cebu City", "Cebu"),
    ("Tacloban", "Leyte"),
    ("Cagayan de Oro", "Misamis Oriental"),
    ("Davao City", "Davao del Sur"),
    ("General Santos", "South Cotabato"),
    ("Zamboanga City", "Zamboanga del Sur"),
)

MOBILE_PREFIXES = (
    "905", "906", "915", "916", "917", "926", "927", "935", "936", "945", "953",
    "955", "956", "965", "966", "967", "975", "977", "995", "997",          # Globe/TM
    "907", "908", "909", "910", "912", "918", "919", "920", "921", "928", "929",
    "930", "938", "939", "946", "947", "948", "949", "950", "951", "961", "998",
    "999",                                                                    # Smart/TNT
    "991", "992", "993", "994",                                               # DITO
)

EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com", "ymail.com", "hotmail.com")

OCCUPATIONS = (
    "Software Developer", "Registered Nurse", "Public School Teacher", "Accountant",
    "Call Center Agent", "Civil Engineer", "Sales Associate", "Graphic Designer",
    "Pharmacist", "Bookkeeper", "Marketing Officer", "HR Specialist", "Cashier",
    "Electrician", "Data Analyst", "Bank Teller", "Seaman", "Chef", "Architect",
    "IT Support Specialist", "Virtual Assistant", "Medical Technologist",
    "Customs Broker", "Police Officer", "Entrepreneur", "Mechanical Engineer",
)

# Invented company names (not real businesses).
COMPANY_WORDS = (
    "Bayanihan", "Mabuhay", "Perlas", "Bagwis", "Tala", "Alon", "Haraya", "Sinag",
    "Kalinaw", "Dalisay", "Masagana", "Silangan", "Habagat", "Amihan", "Banaag",
    "Diwata", "Likha", "Hiraya", "Tanglaw", "Kalayaan",
)

COMPANY_KINDS = (
    "Logistics", "Solutions", "Trading", "Foods", "Tech Systems", "Builders",
    "Marketing", "Pharma", "Holdings", "Digital", "Manufacturing", "Realty",
    "Outsourcing", "Ventures", "Industries",
)

COMPANY_SUFFIXES = ("Inc.", "Corp.", "Co.", "Enterprises", "OPC")
