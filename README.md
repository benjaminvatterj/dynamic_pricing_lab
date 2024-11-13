Certainly! Below is the `README.md` file with the installation instructions converted into Markdown format:

---

# Pricing Game Application

This repository contains a Python script that allows teachers to conduct an interactive pricing game using Google Sheets and a terminal interface. The game involves students submitting pricing decisions over multiple rounds, with the script handling student pairing, processing decisions, and updating outcomes.

---

## Table of Contents

- [Pricing Game Application](#pricing-game-application)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Setup Instructions](#setup-instructions)
    - [1. Enable Google Sheets API and Obtain Credentials](#1-enable-google-sheets-api-and-obtain-credentials)
      - [**a. Create a Google Cloud Project**](#a-create-a-google-cloud-project)
      - [**b. Enable the Google Sheets API**](#b-enable-the-google-sheets-api)
      - [**c. Create OAuth 2.0 Credentials**](#c-create-oauth-20-credentials)
    - [2. Install Required Python Packages](#2-install-required-python-packages)
    - [3. Prepare Your Google Spreadsheet](#3-prepare-your-google-spreadsheet)
      - [**a. Create the Spreadsheet**](#a-create-the-spreadsheet)
      - [**b. Sheet Structure**](#b-sheet-structure)
      - [**c. Share the Spreadsheet**](#c-share-the-spreadsheet)
    - [4. Place the `credentials.json` File in Your Project Directory](#4-place-the-credentialsjson-file-in-your-project-directory)
  - [Running the Script](#running-the-script)
    - [**1. Navigate to the Script Directory**](#1-navigate-to-the-script-directory)
    - [**2. Run the Script**](#2-run-the-script)
    - [**3. Authorize the Application**](#3-authorize-the-application)
  - [Usage](#usage)
  - [Notes](#notes)
  - [License](#license)

---

## Features

- Interactive terminal interface for teachers to control the game.
- Random pairing of students for competition rounds.
- Supports two demand modes: homogeneous and heterogeneous.
- Processes pricing decisions and calculates market shares and profits.
- Updates Google Sheets in real-time with game outcomes.
- Generates additional sheets with results and plots for analysis.

---

## Prerequisites

- **Python 3.6 or higher**.
- **Google account** with access to Google Cloud Console.
- Basic familiarity with terminal commands.

---

## Setup Instructions

### 1. Enable Google Sheets API and Obtain Credentials

To allow the Python script to interact with Google Sheets, you need to enable the Google Sheets API and obtain OAuth 2.0 credentials.

#### **a. Create a Google Cloud Project**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account.
3. Click on the project dropdown at the top and select **"New Project"**.
4. Enter a project name (e.g., `PricingGameProject`) and click **"Create"**.
5. Ensure the new project is selected in the project dropdown.

#### **b. Enable the Google Sheets API**

1. With your project selected, navigate to the **[APIs & Services Dashboard](https://console.cloud.google.com/apis/dashboard)**.
2. Click on **"+ ENABLE APIS AND SERVICES"**.
3. Search for **"Google Sheets API"** and select it.
4. Click **"Enable"**.

#### **c. Create OAuth 2.0 Credentials**

1. Go to the **[Credentials](https://console.cloud.google.com/apis/credentials)** page.
2. Click on **"Create Credentials"** and choose **"OAuth client ID"**.
3. If prompted, configure the consent screen:
   - Choose **"External"**.
   - Fill in the required fields (e.g., App name, User support email).
   - Add your email to the **"Test users"** section.
   - Save and continue.
4. Select **"Desktop app"** as the application type.
5. Name your OAuth client (e.g., `PricingGameApp`) and click **"Create"**.
6. Download the `credentials.json` file by clicking on the download icon.

---

### 2. Install Required Python Packages

Open your terminal or command prompt and run the following command to install the necessary Python packages:

```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib pandas matplotlib
```

---

### 3. Prepare Your Google Spreadsheet

#### **a. Create the Spreadsheet**

- Open **Google Sheets** and create a new spreadsheet.

#### **b. Sheet Structure**

- **Sheet 1 (OpenSheet)**:
  - Rename the first sheet to **"OpenSheet"**.
  - **Column A**: Student Names (header: `Name`)
  - **Column B**: Student IDs (header: `ID`)
  - **Columns C to L**: Pricing decisions for stages 1 to 10 (headers: `Price_1`, `Price_2`, ..., `Price_10`)

- **Sheet 2 (ProtectedSheet)**:
  - Add a new sheet and rename it to **"ProtectedSheet"**.
  - **Column A**: Student Names (header: `Name`)
  - **Column B**: Student IDs (header: `ID`)
  - **Columns C to AH**: Outcome data for each round (three columns per round):
    - `Round1_RivalPrice`, `Round1_MarketShare`, `Round1_Profit`, ..., `Round10_Profit`
  - **Column AI**: Total accumulated profit (header: `Total Profit`)

#### **c. Share the Spreadsheet**

- Click on the **"Share"** button in the top-right corner.
- Enter the email address associated with your Google Cloud project or the one used to create the `credentials.json`.
- Set the permission to **"Editor"** and click **"Send"**.

**Note**: Ensure that students have edit access to **"OpenSheet"** but not to **"ProtectedSheet"**.

---

### 4. Place the `credentials.json` File in Your Project Directory

- Create a new directory for your project (e.g., `pricing_game`).
- Place the `credentials.json` file you downloaded into this directory.

---

## Running the Script

### **1. Navigate to the Script Directory**

Open your terminal or command prompt and navigate to the directory containing `game_app.py` and `credentials.json`:

```bash
cd path/to/your/project/directory
```

### **2. Run the Script**

Execute the script by running:

```bash
python game_app.py
```

### **3. Authorize the Application**

- The first time you run the script, a browser window will open asking you to authorize the application.
- Sign in with your Google account and allow the required permissions.
- A `token.pickle` file will be saved locally for future runs, so you won't need to authorize again.

---

## Usage

1. **Enter the Spreadsheet ID**:

   - When prompted, enter the **Google Spreadsheet ID**.
   - This ID is the part of the spreadsheet's URL between `/d/` and `/edit`:

     ```
     https://docs.google.com/spreadsheets/d/your_spreadsheet_id_here/edit#gid=0
     ```

2. **Start the Game and Select Mode**:

   - When asked **"Would you like to start the game?"**, type `yes` and press **Enter**.
   - Choose the game mode by typing `homogenous` or `heterogenous`.

3. **Proceed Through Rounds**:

   - For each round, choose an option:
     - **(a)** Accept submitted prices and proceed to the next step.
     - **(b)** Save and exit the game.
   - Type `a` or `b` and press **Enter**.

4. **Students Submit Prices**:

   - Before proceeding to the next round, ensure students have submitted their pricing decisions in **"OpenSheet"** under the correct round column (e.g., `Price_1` for Round 1).

5. **End of Game**:

   - After round 10 or if you choose to save and exit, the game ends.
   - The script will generate:
     - An additional sheet named **"GameResults"** with all the matched pairs and each player's total profit.
     - Line plots of prices and profits for each team saved as PNG files in the script directory.

6. **Analyzing Results**:

   - Open the **"GameResults"** sheet to view the final outcomes.
   - Review the generated plots (`Prices_student1ID_student2ID.png`, `Profits_student1ID_student2ID.png`) for each pair.

---

## Notes

- **Spreadsheet Sharing**:

  - Ensure the spreadsheet is shared with the email address associated with your Google API credentials.

- **Data Validation**:

  - The script assumes that the student IDs are unique and that the pricing columns are correctly filled out.
  - Prices should be numeric values without any special characters or text.

- **Adjusting the Demand Function**:

  - The demand function in the script is a placeholder.
  - Adjust the `demand_and_profits(p1, p2, mode)` function according to the specific rules of your game.

- **Dependencies**:

  - The script relies on the installed Python packages and the presence of `credentials.json` and `token.pickle`.

- **Error Handling**:

  - The script includes basic error handling for missing prices and invalid inputs.
  - Ensure that all required data is entered correctly to prevent runtime errors.

- **Cost of Production**:

  - The variable `cost` in the script is set to `10`. Adjust this value if your game uses a different cost.

---

## License

This project is licensed under the MIT License.

---

By following these instructions and using the provided script, you should be able to set up and run the pricing game as described. The script automates the process of pairing students, processing their pricing decisions, calculating market shares and profits, and updating the Google Spreadsheet accordingly.

---