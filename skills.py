# skills.py
MASTER_SKILLS = [
    "React", "Angular", "Vue.js", "JavaScript", "TypeScript", "HTML5", "CSS3", "Tailwind",
    "Python", "Django", "Flask", "FastAPI", "Data Analysis", "Pandas", "Machine Learning",
    "Java", "Spring Boot", "C++", "C#", ".NET", "Ruby on Rails", "PHP", "Laravel",
    "Node.js", "Express", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Firebase",
    "AWS", "Docker", "Kubernetes", "CI/CD", "Git", "Linux", "Cybersecurity",
    "Figma", "UI/UX", "Adobe Illustrator", "Photoshop", "Graphic Design", "Video Editing", "Premiere Pro",
    "Copywriting", "SEO", "Content Marketing", "Social Media Management", "Email Marketing",
    "Excel", "Financial Modeling", "Accounting", "Business Analysis", "Project Management", "Agile"
]

# cities
indian_cities_by_state = {
    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", 
        "Kakinada", "Rajahmundry", "Tirupati", "Kadapa", "Anantapur"
    ],
    "Arunachal Pradesh": [
        "Itanagar", "Tawang", "Pasighat", "Roing", "Ziro", 
        "Tezu", "Bomdila", "Dirang", "Naharlagun", "Khonsa"
    ],
    "Assam": [
        "Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Nagaon", 
        "Tinsukia", "Tezpur", "Bongaigaon", "Diphu", "Dhubri"
    ],
    "Bihar": [
        "Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", 
        "Darbhanga", "Bihar Sharif", "Arrah", "Begusarai", "Katihar"
    ],
    "Chhattisgarh": [
        "Raipur", "Bhilai", "Bilaspur", "Korba", "Rajnandgaon", 
        "Raigarh", "Jagdalpur", "Ambikapur", "Dhamtari", "Mahasamund"
    ],
    "Goa": [
        "Vasco da Gama", "Panaji", "Margao", "Mapusa", "Ponda", 
        "Bicholim", "Curchorem", "Sanquelim", "Sanguem", "Cuncolim"
    ],
    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", 
        "Jamnagar", "Junagadh", "Gandhinagar", "Nadiad", "Anand"
    ],
    "Haryana": [
        "Faridabad", "Gurugram", "Panipat", "Ambala", "Yamunanagar", 
        "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula"
    ],
    "Himachal Pradesh": [
        "Shimla", "Mandi", "Solan", "Dharamshala", "Palampur", 
        "Baddi", "Nahan", "Paonta Sahib", "Sundarnagar", "Chamba"
    ],
    "Jharkhand": [
        "Ranchi", "Jamshedpur", "Dhanbad", "Bokaro Steel City", "Deoghar", 
        "Phusro", "Hazaribagh", "Giridih", "Ramgarh", "Medininagar"
    ],
    "Karnataka": [
        "Bengaluru", "Mysuru", "Hubballi-Dharwad", "Mangaluru", "Belagavi", 
        "Kalaburagi", "Davanagere", "Ballari", "Vijayapura", "Shivamogga"
    ],
    "Kerala": [
        "Thiruvananthapuram", "Kochi", "Kozhikode", "Kollam", "Thrissur", 
        "Kannur", "Alappuzha", "Kottayam", "Palakkad", "Manjeri"
    ],
    "Madhya Pradesh": [
        "Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain", 
        "Sagar", "Dewas", "Satna", "Ratlam", "Rewa"
    ],
    "Maharashtra": [
        "Mumbai", "Pune", "Nagpur", "Nashik", "Thane", 
        "Chhatrapati Sambhajinagar", "Solapur", "Kalyan-Dombivli", "Vasai-Virar", "Navi Mumbai"
    ],
    "Manipur": [
        "Imphal", "Thoubal", "Kakching", "Ukhrul", "Churachandpur", 
        "Bishnupur", "Senapati", "Tamenglong", "Jiribam", "Noney"
    ],
    "Meghalaya": [
        "Shillong", "Tura", "Nongstoin", "Jowai", "Baghmara", 
        "Williamnagar", "Nongpoh", "Resubelpara", "Khliehriat", "Mairang"
    ],
    "Mizoram": [
        "Aizawl", "Lunglei", "Saiha", "Champhai", "Kolasib", 
        "Serchhip", "Lawngtlai", "Hnahthial", "Khawzawl", "Saitual"
    ],
    "Nagaland": [
        "Dimapur", "Kohima", "Mokokchung", "Tuensang", "Wokha", 
        "Zunheboto", "Phek", "Mon", "Kiphire", "Longleng"
    ],
    "Odisha": [
        "Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur", 
        "Puri", "Balasore", "Bhadrak", "Baripada", "Jharsuguda"
    ],
    "Punjab": [
        "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", 
        "Mohali", "Hoshiarpur", "Moga", "Pathankot", "Khanna"
    ],
    "Rajasthan": [
        "Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer", 
        "Udaipur", "Bhilwara", "Alwar", "Bharatpur", "Sikar"
    ],
    "Sikkim": [
        "Gangtok", "Namchi", "Geyzing", "Mangan", "Singtam", 
        "Rangpo", "Jorethang", "Nayabazar", "Sadar", "Ravangla"
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", 
        "Tirunelveli", "Tiruppur", "Vellore", "Erode", "Thoothukudi"
    ],
    "Telangana": [
        "Hyderabad", "Warangal", "Nizamabad", "Khammam", "Karimnagar", 
        "Ramagundam", "Mahbubnagar", "Nalgonda", "Adilabad", "Suryapet"
    ],
    "Tripura": [
        "Agartala", "Dharmanagar", "Udaipur", "Kailashahar", "Bishalgarh", 
        "Teliamura", "Khowai", "Belonia", "Melaghar", "Ambassa"
    ],
    "Uttar Pradesh": [
        "Lucknow", "Kanpur", "Ghaziabad", "Agra", "Varanasi", 
        "Meerut", "Prayagraj", "Bareilly", "Aligarh", "Moradabad"
    ],
    "Uttarakhand": [
        "Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", 
        "Kashipur", "Rishikesh", "Pithoragarh", "Ramnagar", "Manglaur"
    ],
    "West Bengal": [
        "Kolkata", "Asansol", "Siliguri", "Durgapur", "Bardhaman", 
        "Malda", "Baharampur", "Habra", "Kharagpur", "Shantipur"
    ]
}

# Helper
def citytostateMap(cityName):
    for key,value in indian_cities_by_state.items():
        if cityName in value:
            return key
    return ""    
        
def getAllCities():
    return indian_cities_by_state.values()        

def getStoredSkills():
    return MASTER_SKILLS