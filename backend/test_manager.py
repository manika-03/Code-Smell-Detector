import urllib.request, json

code = (
    "class Manager:\n"
    "    def __init__(self):\n"
    "        self.data = []\n"
    "    def add_user(self, user):\n"
    "        self.data.append(user)\n"
    "    def remove_user(self, user):\n"
    "        self.data.remove(user)\n"
    "    def calculate_salary(self, hours):\n"
    "        return hours * 100\n"
    "    def generate_report(self):\n"
    "        print('Generating report...')\n"
    "        for d in self.data:\n"
    "            print(d)\n"
    "    def send_email(self, message):\n"
    "        print('Sending email:', message)\n"
    "    def backup_database(self):\n"
    "        print('Backing up database...')\n"
)

data = json.dumps({'code': code}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8000/analyze',
    data=data,
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as f:
    r = json.loads(f.read())
    print('SEVERITY:     ', r['severity'])
    print('SMELLS:       ', r['smells'])
    print('MODEL USED:   ', r['model_used'])
    m = r['metrics']
    print(f"num_functions={m['num_functions']} num_classes={m['num_classes']} cc={m['cyclomatic_complexity']} loc={m['loc']}")
