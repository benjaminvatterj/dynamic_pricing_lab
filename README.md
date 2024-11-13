
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
    - [2. Clone This Repository](#2-clone-this-repository)
    - [On Mac/Linux:](#on-maclinux)
    - [On Windows:](#on-windows)
    - [3. Install Required Python Packages](#3-install-required-python-packages)
      - [On Mac/Linux:](#on-maclinux-1)
      - [On Windows:](#on-windows-1)
    - [4. Prepare Your Google Spreadsheet](#4-prepare-your-google-spreadsheet)
      - [**a. Create the Spreadsheet**](#a-create-the-spreadsheet)
      - [**b. Sheet Structure**](#b-sheet-structure)
      - [**c. Share the Spreadsheet**](#c-share-the-spreadsheet)
    - [5. Place the `credentials.json` File in Your Project Directory](#5-place-the-credentialsjson-file-in-your-project-directory)
  - [Running the Script](#running-the-script)
    - [**1. Navigate to the Script Directory**](#1-navigate-to-the-script-directory)
    - [**2. Register your section**](#2-register-your-section)
    - [**3. Run the Script**](#3-run-the-script)
    - [**4. Authorize the Application**](#4-authorize-the-application)
  - [Usage](#usage)
  - [Notes](#notes)
  - [License](#license)

---

## Features

- Interactive terminal interface for teachers to control the game.
- Random pairing of students for competition rounds.
- Supports several demand and differentiation models:
  - **Homogenous Bertrand** : winner-takes-all with market share curve `s1(p1, p2)=1 - p1` if `p1 < p2` and `0` otherwise. Total demand = 100.
  - **Low differentaition Logit**: market share `s1(p1,p2) = exp(-p1) / (exp(-p1) + exp(-p2))`. Total demand = 100.
  - **High differentiation Hotelling**: transportation cost `t=1` and market share `s1(p1,p2) = (p2 + t - p1) / 2t`.  Total demand = 100.
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

### 2. Clone This Repository

### On Mac/Linux:

```bash
mkdir pricing_game
git clone https://github.com/benjaminvatterj/dynamic_pricing_lab.git ./pricing_game/
```

### On Windows:
Either download the repository as a ZIP file from [https://github.com/benjaminvatterj/dynamic_pricing_lab](https://github.com/benjaminvatterj/dynamic_pricing_lab) or install git for continuous updatings


   - **Download Git for Windows**:
     - Visit [https://git-scm.com/download/win](https://git-scm.com/download/win).
     - Click on **"64-bit Git for Windows Setup"** to download the installer.
   - **Install Git**:
     - Run the downloaded installer.
     - Follow the default settings during installation.
   - **Access Git Bash**:
     - After installation, you can access **Git Bash** from the Start Menu or by right-clicking on your desktop and selecting **"Git Bash Here"**.
   - **Create a New Folder**:
     - Open **File Explorer** and navigate to where you want to store the project.
     - Right-click and select **"New" > "Folder"** and name it `pricing_game`.
   - **Clone the Repository**:
     - Open **Git Bash** by right-clicking inside the `pricing_Game` folder and selecting **"Git Bash Here"**.
     - Run the following command:

       ```bash
       git clone https://github.com/benjaminvatterj/dynamic_pricing_lab.git ./
       ```

     - *Note*: If you have SSH set up, you can use the SSH URL instead.

---
### 3. Install Required Python Packages

#### On Mac/Linux:

  - **Install mamba if not already installed**
    ```bash
    # On Mac
    # Install homebrew if you don't have it
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Then install miniforge
    brew install miniforge

    # on Linux
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    bash Miniforge3-$(uname)-$(uname -m).sh
    ```
  - **Create the mamba environment**
    ```bash
    # Cd into the code directory if you are not already there
    cd pricing_game
    # create the environment
    mamba env create --name pricing_game --file dynamic_pricing_lab.yaml
    ```
  - **Activate the environment**
    ```bash
    mamba activate pricing_game
    ```

#### On Windows:


   - **Download Miniconda**:
     - Visit [https://docs.conda.io/en/latest/miniconda.html#windows-installers](https://docs.conda.io/en/latest/miniconda.html#windows-installers).
     - Download the **"Windows x86_64 executable installer"** for Python 3.x.
   - **Install Miniconda**:
     - Run the installer and follow the prompts.
     - Choose **"Add Miniconda3 to PATH environment variable"** when prompted.
   - **Install Mamba**:
     - Open **Anaconda Prompt** from the Start Menu.
     - Run the following command:

       ```bash
       conda install mamba -n base -c conda-forge
       ```
   - **Open Anaconda Prompt**:
     - Find **Anaconda Prompt** in the Start Menu.
   - **Navigate to the `code` Directory**:

     ```bash
     cd C:\path\to\pricing_game
     ```
   - **Create the Environment**:
     ```bash
     mamba env create --name pricing_game --file dynamic_pricing_game.yaml
     ```

  - **Activate the Environment**:
     ```bash
     mamba activate pricing_game
     ```
---

### 4. Prepare Your Google Spreadsheet

#### **a. Create the Spreadsheet**

- Open **Google Sheets** and create a new spreadsheet.

#### **b. Sheet Structure**
  You can see an example structure in this link [example sheet](https://docs.google.com/spreadsheets/d/1myQtsawgrc1Fy1l_eq8qO5IHmjlbWosj_ydJe-3O9eA/edit?usp=sharing)

#### **c. Share the Spreadsheet**

- Click on the **"Share"** button in the top-right corner.
- Enter the email address associated with your Google Cloud project or the one used to create the `credentials.json`.
- Set the permission to **"Editor"** and click **"Send"**.

**Note**: Ensure that students have edit access to **"OpenSheet"** but not to **"ProtectedSheet"**.

---

### 5. Place the `credentials.json` File in Your Project Directory

- Create a new directory for your project (e.g., `pricing_game`).
- Place the `credentials.json` file you downloaded into this directory.

---

## Running the Script

### **1. Navigate to the Script Directory**

Open your terminal or command prompt and navigate to the directory containing `game_app.py` and `credentials.json`:

```bash
cd path/to/your/project/directory
```

### **2. Register your section**
  This is needed only once per section
```bash
mamba activate pricing_game
python main.py --register <section_name> <section_id>
```
  Where "Section Name" is the name of the section and "Section Sheet ID" is the ID of the Google Sheet,
  which is the string in the URL after 'https://docs.google.com/spreadsheets/d/' and before '/edit'.

### **3. Run the Script**

Execute the script by running:

```bash
mamba activate pricing_game
python game_app.py
```

### **4. Authorize the Application**

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

  - The variable `cost` in the script is set to `0`. Adjust this value if your game uses a different cost.

---

## License

This project is licensed under the MIT License.

---

By following these instructions and using the provided script, you should be able to set up and run the pricing game as described. The script automates the process of pairing students, processing their pricing decisions, calculating market shares and profits, and updating the Google Spreadsheet accordingly.

---