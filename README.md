# workshift-scheduler

Simple script that scrap workshift hours from Google Sheets, convert them and
create corresponding events in Google Calendar.

## Credentials

This script use Service Account credentials to authenticate in Google Workspace
for reading Google Sheets and OAuth2 Client ID credentials for inserting events
in Google Calendar.

### **Create service account**

---

1. Open the **Google Cloud Console**.
2. At the top left, click Menu > **IAM & Admin** > **Service Account**.
3. Click **Create service account**.
4. Fill in the service account details, then click **Create and continue**.
5. Click **Continue**.
6. Click **Done**.

### **Create credentials for a service account**

---

1. Open the **Google Cloud Console**.
2. At the top left, click Menu > **IAM & Admin > Service Account**.
3. Select your service account.
4. Click **Keys > Add keys > Create new key**.
5. Select **JSON**, then click **Create**.

   _Your new public/private key pair is generated and downloaded to your machine
   as a new file. Move it to your project directory._

6. Click **Close**.

### **OAuth client ID credentials**

---

1. Open **Google Cloud Console**.
2. At the top left, click **Menu > APIs & Services > Credentials**.
3. Click Create **Credentials > OAuth cliend ID**.
4. Click **Application type > Web application**.
5. In the "Name" field, type a name of the credential. This name is only shown
   in the Cloud Console.
6. Add authorized URIs related to your app:

   - **Client-side apps (JavaScript)** - Under Authorized JavaScript origins,
     click **Add URI**. Then, enter a URI to use for browser requests. This
     identifies the domains from which your application can send API requests to
     the OAuth 2.0 server.
   - **Server-side apps (Java, Python, .NET and more)** - Under "Authorized
     redirect URIs," click **Add URI**. Then, enter an endpoint URI to which the
     OAuth 2.0 server can send responses.

7. Click **Create**. The OAuth client created screen appears, showing your new
   Client ID and Client secret.
8. Note the Client ID. Client secret aren't used for Web applications.
9. Click **OK**. The newly created credential appears under "OAuth2.0 Client
   IDs".

## Quickstart

### 1. Create Virtual Environment

```bash
python venv -m path/to/virtual/environment
```

### 2. Activate virtual environment

```bash
cd venv_name/Scripts && activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run python script

To run the script properly you have to provide sheet title and your full name:

```bash
Enter spredsheet name:
<YOUR SHEET NAME>

Enter your full name:
<YOUR FULL NAME>
```

### 5. (Optional) Provide authorize token for Google Calendar

You need to login with your google account and copy generated authorize code
while running script for the first time:

```bash
Enter the authorization code: <GENERATED CODE>
```

After that JSON file containing token will be created and used in other script
runs.
